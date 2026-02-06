"""REST API endpoints for member management."""
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import (
    IsMember,
    IsPastor,
    IsAdmin,
    IsPastorOrAdmin,
    IsOwnerOrStaff,
    CanViewMember,
)
from apps.core.constants import Roles
from apps.core.utils import (
    get_today_birthdays,
    get_week_birthdays,
    get_month_birthdays,
)

from .models import Member, Family, Group, GroupMembership, DirectoryPrivacy
from .serializers import (
    MemberSerializer,
    MemberListSerializer,
    MemberCreateSerializer,
    MemberProfileSerializer,
    MemberAdminSerializer,
    BirthdaySerializer,
    DirectoryMemberSerializer,
    FamilySerializer,
    FamilyListSerializer,
    GroupSerializer,
    GroupListSerializer,
    GroupMembershipSerializer,
    DirectoryPrivacySerializer,
)


class MemberViewSet(viewsets.ModelViewSet):
    """CRUD operations for members with role-based access control."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'family_status', 'family', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'member_number', 'phone']
    ordering_fields = ['last_name', 'first_name', 'created_at', 'birth_date']
    ordering = ['last_name', 'first_name']
    lookup_field = 'pk'

    def get_queryset(self):
        """Filter queryset based on user's role and permissions."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return Member.objects.all().select_related('family')

        if hasattr(user, 'member_profile'):
            member = user.member_profile

            # Pastors and admins see everyone
            if member.role in [Roles.PASTOR, Roles.ADMIN]:
                return Member.objects.all().select_related('family')

            # Group leaders see their group members
            if member.role == Roles.GROUP_LEADER:
                led_groups = member.led_groups.values_list('id', flat=True)
                group_members = GroupMembership.objects.filter(
                    group_id__in=led_groups
                ).values_list('member_id', flat=True)

                return Member.objects.filter(
                    Q(id=member.id) | Q(id__in=group_members)
                ).select_related('family')

        # Regular members only see themselves
        if hasattr(user, 'member_profile'):
            return Member.objects.filter(id=user.member_profile.id)

        return Member.objects.none()

    def get_serializer_class(self):
        """Return serializer based on action and user role."""
        user = self.request.user

        if self.action == 'list':
            return MemberListSerializer

        if self.action == 'create':
            return MemberCreateSerializer

        if self.action in ['update', 'partial_update']:
            if user.is_staff or (
                hasattr(user, 'member_profile') and
                user.member_profile.role in [Roles.PASTOR, Roles.ADMIN]
            ):
                return MemberAdminSerializer
            return MemberProfileSerializer

        if self.action == 'birthdays':
            return BirthdaySerializer

        if self.action == 'directory':
            return DirectoryMemberSerializer

        return MemberSerializer

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action == 'create':
            return []  # Public registration

        if self.action in ['list']:
            return [IsMember()]

        if self.action in ['retrieve', 'me']:
            return [IsMember()]

        if self.action in ['update', 'partial_update']:
            return [IsOwnerOrStaff()]

        if self.action == 'destroy':
            return [IsPastorOrAdmin()]

        if self.action in ['birthdays']:
            return [IsMember()]

        if self.action == 'directory':
            return [IsMember()]

        return [IsMember()]

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's member profile."""
        if not hasattr(request.user, 'member_profile'):
            return Response(
                {'error': 'Aucun profil membre trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        member = request.user.member_profile

        if request.method == 'GET':
            serializer = MemberSerializer(member)
            return Response(serializer.data)

        serializer = MemberProfileSerializer(
            member,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(MemberSerializer(member).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def birthdays(self, request):
        """Get birthdays filtered by period (today/week/month)."""
        period = request.query_params.get('period', 'week')
        month = request.query_params.get('month')

        if period == 'today':
            members = get_today_birthdays()
        elif period == 'month':
            if month:
                try:
                    members = get_month_birthdays(int(month))
                except (ValueError, TypeError):
                    members = get_month_birthdays()
            else:
                members = get_month_birthdays()
        else:
            members = get_week_birthdays()

        serializer = BirthdaySerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def directory(self, request):
        """Member directory with privacy settings applied."""
        queryset = Member.objects.filter(is_active=True)

        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(member_number__icontains=search)
            )

        user = request.user
        if hasattr(user, 'member_profile'):
            member = user.member_profile

            if member.role not in Roles.STAFF_ROLES:
                user_groups = set(
                    member.group_memberships.filter(is_active=True).values_list('group_id', flat=True)
                )

                # Filter by visibility: public, same group, or self
                queryset = queryset.filter(
                    Q(privacy_settings__visibility='public') |
                    Q(
                        privacy_settings__visibility='group',
                        group_memberships__group_id__in=user_groups
                    ) |
                    Q(id=member.id)
                ).distinct()
        elif not user.is_staff:
            queryset = queryset.filter(
                privacy_settings__visibility='public'
            )

        queryset = queryset.select_related('privacy_settings').order_by('last_name', 'first_name')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DirectoryMemberSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DirectoryMemberSerializer(queryset, many=True)
        return Response(serializer.data)


class FamilyViewSet(viewsets.ModelViewSet):
    """CRUD operations for families."""

    queryset = Family.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'city']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return FamilyListSerializer
        return FamilySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]

        return [IsPastorOrAdmin()]


class GroupViewSet(viewsets.ModelViewSet):
    """CRUD operations for groups with member management actions."""

    queryset = Group.objects.all().select_related('leader')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group_type', 'leader', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return GroupListSerializer
        return GroupSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'members']:
            return [IsMember()]

        return [IsPastorOrAdmin()]

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get active members of this group."""
        group = self.get_object()
        memberships = group.memberships.filter(is_active=True).select_related('member')

        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """Add a member to this group."""
        group = self.get_object()
        member_id = request.data.get('member')
        role = request.data.get('role', 'member')

        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return Response(
                {'error': 'Membre non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        membership, created = GroupMembership.objects.get_or_create(
            member=member,
            group=group,
            defaults={'role': role}
        )

        if not created:
            return Response(
                {'error': 'Ce membre fait déjà partie du groupe'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = GroupMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        """Remove a member from this group."""
        group = self.get_object()
        member_id = request.data.get('member')

        try:
            membership = GroupMembership.objects.get(
                group=group,
                member_id=member_id
            )
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GroupMembership.DoesNotExist:
            return Response(
                {'error': 'Ce membre ne fait pas partie du groupe'},
                status=status.HTTP_404_NOT_FOUND
            )


class DirectoryPrivacyViewSet(viewsets.ModelViewSet):
    """Manage directory privacy settings (members can only access their own)."""

    serializer_class = DirectoryPrivacySerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        """Return only current user's privacy settings (staff sees all)."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return DirectoryPrivacy.objects.all()

        if hasattr(user, 'member_profile'):
            return DirectoryPrivacy.objects.filter(member=user.member_profile)

        return DirectoryPrivacy.objects.none()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's privacy settings."""
        if not hasattr(request.user, 'member_profile'):
            return Response(
                {'error': 'Aucun profil membre trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        member = request.user.member_profile

        try:
            privacy = member.privacy_settings
        except DirectoryPrivacy.DoesNotExist:
            privacy = DirectoryPrivacy.objects.create(member=member)

        if request.method == 'GET':
            serializer = DirectoryPrivacySerializer(privacy)
            return Response(serializer.data)

        serializer = DirectoryPrivacySerializer(
            privacy,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
