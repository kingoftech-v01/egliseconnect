"""
Members API Views - REST API endpoints for member management.

ViewSets:
- MemberViewSet: Full CRUD for members
- FamilyViewSet: Family management
- GroupViewSet: Group management
- GroupMembershipViewSet: Group membership management

Endpoints follow the namespace: api:v1:members:resource-name
"""
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


# =============================================================================
# MEMBER VIEWSET
# =============================================================================

class MemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Member CRUD operations.

    Provides:
    - list: GET /api/v1/members/members/
    - retrieve: GET /api/v1/members/members/{uuid}/
    - create: POST /api/v1/members/members/
    - update: PUT /api/v1/members/members/{uuid}/
    - partial_update: PATCH /api/v1/members/members/{uuid}/
    - destroy: DELETE /api/v1/members/members/{uuid}/

    Custom actions:
    - me: GET /api/v1/members/members/me/
    - birthdays: GET /api/v1/members/members/birthdays/
    - directory: GET /api/v1/members/members/directory/
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'family_status', 'family', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'member_number', 'phone']
    ordering_fields = ['last_name', 'first_name', 'created_at', 'birth_date']
    ordering = ['last_name', 'first_name']
    lookup_field = 'pk'

    def get_queryset(self):
        """
        Return queryset based on user permissions.
        """
        user = self.request.user

        # Staff sees everything
        if user.is_staff or user.is_superuser:
            return Member.objects.all().select_related('family')

        # Check member role
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
        """Return appropriate serializer based on action and user role."""
        user = self.request.user

        if self.action == 'list':
            return MemberListSerializer

        if self.action == 'create':
            return MemberCreateSerializer

        if self.action in ['update', 'partial_update']:
            # Check if user is admin/staff
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
            # Anyone can register
            return []

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
        """
        Get or update current user's member profile.

        GET /api/v1/members/members/me/
        PUT/PATCH /api/v1/members/members/me/
        """
        if not hasattr(request.user, 'member_profile'):
            return Response(
                {'error': 'Aucun profil membre trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        member = request.user.member_profile

        if request.method == 'GET':
            serializer = MemberSerializer(member)
            return Response(serializer.data)

        # PUT or PATCH
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
        """
        Get birthdays for today, this week, or this month.

        GET /api/v1/members/members/birthdays/
        GET /api/v1/members/members/birthdays/?period=today
        GET /api/v1/members/members/birthdays/?period=week
        GET /api/v1/members/members/birthdays/?period=month&month=6
        """
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
        else:  # week
            members = get_week_birthdays()

        serializer = BirthdaySerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def directory(self, request):
        """
        Get member directory with privacy settings applied.

        GET /api/v1/members/members/directory/
        GET /api/v1/members/members/directory/?search=dupont
        """
        # Get members with public or group visibility
        queryset = Member.objects.filter(is_active=True)

        # Apply search
        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(member_number__icontains=search)
            )

        # Filter by privacy settings
        user = request.user
        if hasattr(user, 'member_profile'):
            member = user.member_profile

            # Staff sees everyone
            if member.role in Roles.STAFF_ROLES:
                pass
            else:
                # Get user's groups
                user_groups = set(
                    member.group_memberships.filter(is_active=True).values_list('group_id', flat=True)
                )

                # Filter by visibility
                queryset = queryset.filter(
                    Q(privacy_settings__visibility='public') |
                    Q(
                        privacy_settings__visibility='group',
                        group_memberships__group_id__in=user_groups
                    ) |
                    Q(id=member.id)  # Always include self
                ).distinct()
        elif not user.is_staff:
            # Users without member_profile and not staff see only public profiles
            queryset = queryset.filter(
                privacy_settings__visibility='public'
            )

        queryset = queryset.select_related('privacy_settings').order_by('last_name', 'first_name')

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DirectoryMemberSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DirectoryMemberSerializer(queryset, many=True)
        return Response(serializer.data)


# =============================================================================
# FAMILY VIEWSET
# =============================================================================

class FamilyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Family CRUD operations.

    Provides:
    - list: GET /api/v1/members/families/
    - retrieve: GET /api/v1/members/families/{uuid}/
    - create: POST /api/v1/members/families/
    - update: PUT /api/v1/members/families/{uuid}/
    - destroy: DELETE /api/v1/members/families/{uuid}/
    """

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


# =============================================================================
# GROUP VIEWSET
# =============================================================================

class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Group CRUD operations.

    Provides:
    - list: GET /api/v1/members/groups/
    - retrieve: GET /api/v1/members/groups/{uuid}/
    - create: POST /api/v1/members/groups/
    - update: PUT /api/v1/members/groups/{uuid}/
    - destroy: DELETE /api/v1/members/groups/{uuid}/

    Custom actions:
    - members: GET /api/v1/members/groups/{uuid}/members/
    - add_member: POST /api/v1/members/groups/{uuid}/add-member/
    - remove_member: POST /api/v1/members/groups/{uuid}/remove-member/
    """

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
        """
        Get members of this group.

        GET /api/v1/members/groups/{uuid}/members/
        """
        group = self.get_object()
        memberships = group.memberships.filter(is_active=True).select_related('member')

        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """
        Add a member to this group.

        POST /api/v1/members/groups/{uuid}/add-member/
        Body: {"member": "<uuid>", "role": "member"}
        """
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
        """
        Remove a member from this group.

        POST /api/v1/members/groups/{uuid}/remove-member/
        Body: {"member": "<uuid>"}
        """
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


# =============================================================================
# PRIVACY VIEWSET
# =============================================================================

class DirectoryPrivacyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing directory privacy settings.

    Members can only access their own privacy settings.
    """

    serializer_class = DirectoryPrivacySerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        """Return only current user's privacy settings."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return DirectoryPrivacy.objects.all()

        if hasattr(user, 'member_profile'):
            return DirectoryPrivacy.objects.filter(member=user.member_profile)

        return DirectoryPrivacy.objects.none()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update current user's privacy settings.

        GET /api/v1/members/privacy/me/
        PUT/PATCH /api/v1/members/privacy/me/
        """
        if not hasattr(request.user, 'member_profile'):
            return Response(
                {'error': 'Aucun profil membre trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        member = request.user.member_profile

        try:
            privacy = member.privacy_settings
        except DirectoryPrivacy.DoesNotExist:
            # Create default settings
            privacy = DirectoryPrivacy.objects.create(member=member)

        if request.method == 'GET':
            serializer = DirectoryPrivacySerializer(privacy)
            return Response(serializer.data)

        # PUT or PATCH
        serializer = DirectoryPrivacySerializer(
            privacy,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
