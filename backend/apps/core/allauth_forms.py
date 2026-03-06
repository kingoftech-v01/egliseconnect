"""Custom allauth forms for EgliseConnect."""
from django import forms
from django.utils.translation import gettext_lazy as _

from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """Signup form with optional invitation code field."""

    invitation_code = forms.CharField(
        required=False,
        max_length=32,
        label=_("Code d'invitation"),
        widget=forms.TextInput(attrs={'placeholder': 'Ex: AB12CD34'}),
        help_text=_("Optionnel. Entrez votre code si vous en avez un."),
    )

    def clean_invitation_code(self):
        """Validate the invitation code if provided."""
        code = self.cleaned_data.get('invitation_code', '').upper().strip()
        if not code:
            return ''
        from apps.onboarding.models import InvitationCode
        try:
            invitation = InvitationCode.objects.get(code=code)
        except InvitationCode.DoesNotExist:
            raise forms.ValidationError(_("Code d'invitation invalide."))
        if not invitation.is_usable:
            raise forms.ValidationError(
                _("Ce code d'invitation a expiré ou a été utilisé.")
            )
        self._invitation = invitation
        return code

    def save(self, request):
        """Save user and create Member profile."""
        user = super().save(request)

        from apps.members.models import Member
        from apps.core.constants import MembershipStatus

        member = Member.objects.create(
            user=user,
            first_name=user.first_name or '',
            last_name=user.last_name or '',
            email=user.email,
            membership_status=MembershipStatus.REGISTERED,
        )

        if hasattr(self, '_invitation'):
            from apps.onboarding.services import OnboardingService
            OnboardingService.accept_invitation(self._invitation, member)

        return user
