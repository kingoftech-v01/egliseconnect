"""JWT authentication views for API v2."""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


class MemberProfileInlineSerializer(serializers.Serializer):
    """Inline member profile for auth responses."""
    id = serializers.UUIDField()
    member_number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(allow_blank=True)
    role = serializers.CharField()
    membership_status = serializers.CharField()
    photo = serializers.ImageField(allow_null=True)
    has_full_access = serializers.BooleanField()
    is_staff_member = serializers.BooleanField()
    two_factor_enabled = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')
    invitation_code = serializers.CharField(max_length=32, required=False, default='')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value.lower()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return data


def _get_member_data(user):
    """Get member profile data if exists."""
    if hasattr(user, 'member_profile'):
        member = user.member_profile
        return MemberProfileInlineSerializer(member).data
    return None


def _get_tokens_for_user(user):
    """Generate JWT token pair for user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class LoginView(APIView):
    """POST /api/v2/auth/login/ - Email + password login, returns JWT tokens + member profile."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Email ou mot de passe incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"error": "Email ou mot de passe incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "Ce compte est désactivé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = _get_tokens_for_user(user)
        member = _get_member_data(user)

        return Response({
            **tokens,
            'user': {
                'id': user.id,
                'email': user.email,
            },
            'member': member,
        })


class RegisterView(APIView):
    """POST /api/v2/auth/register/ - Create account with optional invitation code."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )

        from apps.members.models import Member
        from apps.core.constants import MembershipStatus

        member = Member.objects.create(
            user=user,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data['email'],
            membership_status=MembershipStatus.REGISTERED,
        )

        invitation_code = data.get('invitation_code', '').upper().strip()
        if invitation_code:
            from apps.onboarding.models import InvitationCode
            try:
                invitation = InvitationCode.objects.get(code=invitation_code)
                if invitation.is_usable:
                    from apps.onboarding.services import OnboardingService
                    OnboardingService.accept_invitation(invitation, member)
            except InvitationCode.DoesNotExist:
                pass

        tokens = _get_tokens_for_user(user)
        member_data = _get_member_data(user)

        return Response({
            **tokens,
            'user': {
                'id': user.id,
                'email': user.email,
            },
            'member': member_data,
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """POST /api/v2/auth/logout/ - Blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {"error": "Refresh token requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"error": "Token invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Déconnexion réussie."})


class MeView(APIView):
    """GET /api/v2/auth/me/ - Get current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        member = _get_member_data(user)

        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
            },
            'member': member,
        })

    def patch(self, request):
        """Update own member profile fields."""
        user = request.user
        if not hasattr(user, 'member_profile'):
            return Response(
                {"error": "Aucun profil membre associé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        member = user.member_profile
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'phone_secondary',
            'birth_date', 'address', 'city', 'province', 'postal_code',
            'family_status',
        ]

        for field in allowed_fields:
            if field in request.data:
                setattr(member, field, request.data[field])

        member.save()
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
            },
            'member': _get_member_data(user),
        })


class ChangePasswordView(APIView):
    """POST /api/v2/auth/change-password/ - Change current user's password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current = request.data.get('current_password', '')
        new_pwd = request.data.get('new_password', '')
        confirm = request.data.get('new_password_confirm', '')

        if not current or not new_pwd or not confirm:
            return Response(
                {"error": "Tous les champs sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(current):
            return Response(
                {"error": "Le mot de passe actuel est incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_pwd != confirm:
            return Response(
                {"error": "Les nouveaux mots de passe ne correspondent pas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_pwd, request.user)
        except DjangoValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_pwd)
        request.user.save()
        return Response({"message": "Mot de passe modifié avec succès."})


class CustomTokenRefreshView(TokenRefreshView):
    """POST /api/v2/auth/refresh/ - Refresh access token."""
    pass


class ForgotPasswordView(APIView):
    """POST /api/v2/auth/forgot-password/ - Send password reset email."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response(
                {"error": "Le courriel est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Always return success to prevent email enumeration
        try:
            user = User.objects.get(email__iexact=email)
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.core.mail import send_mail
            from django.conf import settings as django_settings

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            frontend_url = getattr(django_settings, 'FRONTEND_URL', 'http://localhost:3000')
            reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"

            send_mail(
                subject="Réinitialisation de votre mot de passe - ÉgliseConnect",
                message=f"Bonjour,\n\nCliquez sur le lien suivant pour réinitialiser votre mot de passe:\n{reset_url}\n\nCe lien expire dans 24 heures.\n\nSi vous n'avez pas fait cette demande, ignorez ce message.",
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass

        return Response({"message": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."})


class ResetPasswordView(APIView):
    """POST /api/v2/auth/reset-password/ - Reset password with token."""
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_decode

        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        new_password = request.data.get('new_password', '')
        confirm = request.data.get('new_password_confirm', '')

        if not all([uid, token, new_password, confirm]):
            return Response(
                {"error": "Tous les champs sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm:
            return Response(
                {"error": "Les mots de passe ne correspondent pas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (ValueError, User.DoesNotExist, OverflowError):
            return Response(
                {"error": "Lien de réinitialisation invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Le lien a expiré ou est invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response({"message": "Mot de passe réinitialisé avec succès."})
