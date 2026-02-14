"""Help Requests API views."""
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsPastor, IsAdmin
from apps.members.models import Member
from .models import (
    HelpRequest, HelpRequestCategory, HelpRequestComment,
    PastoralCare, PrayerRequest, CareTeam, CareTeamMember,
    BenevolenceRequest, BenevolenceFund,
    MealTrain, MealSignup,
    CrisisProtocol, CrisisResource,
)
from .serializers import (
    HelpRequestSerializer,
    HelpRequestCreateSerializer,
    HelpRequestCategorySerializer,
    HelpRequestCommentSerializer,
    HelpRequestAssignSerializer,
    HelpRequestResolveSerializer,
    CommentCreateSerializer,
    PastoralCareSerializer,
    PastoralCareCreateSerializer,
    PrayerRequestSerializer,
    PrayerRequestCreateSerializer,
    CareTeamSerializer,
    CareTeamMemberSerializer,
    BenevolenceRequestSerializer,
    BenevolenceFundSerializer,
    MealTrainSerializer,
    MealSignupSerializer,
    CrisisProtocolSerializer,
    CrisisResourceSerializer,
)


class HelpRequestCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HelpRequestCategory.objects.filter(is_active=True)
    serializer_class = HelpRequestCategorySerializer
    permission_classes = [IsAuthenticated]


class HelpRequestViewSet(viewsets.ModelViewSet):
    serializer_class = HelpRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'urgency', 'category', 'assigned_to', 'is_confidential']
    search_fields = ['title', 'description', 'request_number']
    ordering_fields = ['created_at', 'urgency', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter based on user role: pastors/admins see all, group leaders see their members' non-confidential requests, regular members see only their own."""
        user = self.request.user
        member = getattr(user, 'member_profile', None)

        if not member:
            return HelpRequest.objects.none()

        if member.role in ['pastor', 'admin']:
            return HelpRequest.objects.select_related(
                'member', 'category', 'assigned_to'
            ).prefetch_related('comments')

        if member.role == 'group_leader':
            from apps.members.models import GroupMembership
            group_member_ids = GroupMembership.objects.filter(
                group__leader=member
            ).values_list('member_id', flat=True)

            return HelpRequest.objects.filter(
                models.Q(member=member) |
                models.Q(member_id__in=group_member_ids, is_confidential=False)
            ).select_related('member', 'category', 'assigned_to')

        return HelpRequest.objects.filter(member=member).select_related(
            'member', 'category', 'assigned_to'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return HelpRequestCreateSerializer
        return HelpRequestSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        member = getattr(request.user, 'member_profile', None)
        if not member:
            return Response({'detail': 'Member profile required.'}, status=400)

        queryset = HelpRequest.objects.filter(member=member).select_related(
            'category', 'assigned_to'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsPastor | IsAdmin])
    def assign(self, request, pk=None):
        help_request = self.get_object()
        serializer = HelpRequestAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assignee = Member.objects.get(id=serializer.validated_data['assigned_to'])
        except Member.DoesNotExist:
            return Response(
                {'detail': 'Member not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        help_request.assign_to(assignee)
        return Response(HelpRequestSerializer(help_request).data)

    @action(detail=True, methods=['post'], permission_classes=[IsPastor | IsAdmin])
    def resolve(self, request, pk=None):
        help_request = self.get_object()
        serializer = HelpRequestResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        help_request.mark_resolved(
            notes=serializer.validated_data.get('resolution_notes', '')
        )
        return Response(HelpRequestSerializer(help_request).data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        help_request = self.get_object()
        member = getattr(request.user, 'member_profile', None)

        if not member:
            return Response({'detail': 'Member profile required.'}, status=400)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Non-staff cannot create internal comments
        is_internal = serializer.validated_data.get('is_internal', False)
        if is_internal and member.role not in ['pastor', 'admin']:
            is_internal = False

        comment = HelpRequestComment.objects.create(
            help_request=help_request,
            author=member,
            content=serializer.validated_data['content'],
            is_internal=is_internal
        )

        return Response(
            HelpRequestCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        help_request = self.get_object()
        member = getattr(request.user, 'member_profile', None)

        comments = help_request.comments.select_related('author')

        # Hide internal comments from non-staff
        if not member or member.role not in ['pastor', 'admin']:
            comments = comments.filter(is_internal=False)

        serializer = HelpRequestCommentSerializer(comments, many=True)
        return Response(serializer.data)


# ─── Pastoral Care API ───────────────────────────────────────────────────────


class PastoralCareViewSet(viewsets.ModelViewSet):
    serializer_class = PastoralCareSerializer
    permission_classes = [IsPastor | IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['care_type', 'status', 'assigned_to']
    search_fields = ['notes', 'member__first_name', 'member__last_name']
    ordering = ['-date']

    def get_queryset(self):
        return PastoralCare.objects.select_related(
            'member', 'assigned_to', 'created_by'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return PastoralCareCreateSerializer
        return PastoralCareSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ─── Prayer Request API ──────────────────────────────────────────────────────


class PrayerRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PrayerRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_public', 'is_anonymous', 'is_approved']
    search_fields = ['title', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        member = getattr(user, 'member_profile', None)

        if member and member.role in ['pastor', 'admin']:
            return PrayerRequest.objects.select_related('member')

        # Regular users see public+approved or their own
        qs = PrayerRequest.objects.filter(
            models.Q(is_public=True, is_approved=True) |
            models.Q(member=member)
        ).select_related('member')
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return PrayerRequestCreateSerializer
        return PrayerRequestSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['post'])
    def mark_answered(self, request, pk=None):
        prayer = self.get_object()
        member = getattr(request.user, 'member_profile', None)

        if not member:
            return Response({'detail': 'Member profile required.'}, status=400)

        is_owner = prayer.member == member
        is_staff = member.role in ['pastor', 'admin']

        if not (is_owner or is_staff):
            return Response({'detail': 'Permission denied.'}, status=403)

        testimony = request.data.get('testimony', '')
        prayer.mark_answered(testimony=testimony)
        return Response(PrayerRequestSerializer(prayer).data)

    @action(detail=False, methods=['get'])
    def wall(self, request):
        """Public prayer wall."""
        prayers = PrayerRequest.objects.filter(
            is_public=True, is_approved=True
        ).select_related('member').order_by('-created_at')
        serializer = PrayerRequestSerializer(prayers, many=True)
        return Response(serializer.data)


# ─── Care Team API ───────────────────────────────────────────────────────────


class CareTeamViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamSerializer
    permission_classes = [IsPastor | IsAdmin]
    queryset = CareTeam.objects.select_related('leader').prefetch_related('memberships__member')
    search_fields = ['name']


class CareTeamMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamMemberSerializer
    permission_classes = [IsPastor | IsAdmin]
    queryset = CareTeamMember.objects.select_related('team', 'member')
    filterset_fields = ['team']


# ─── Benevolence API ─────────────────────────────────────────────────────────


class BenevolenceFundViewSet(viewsets.ModelViewSet):
    serializer_class = BenevolenceFundSerializer
    permission_classes = [IsPastor | IsAdmin]
    queryset = BenevolenceFund.objects.all()


class BenevolenceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = BenevolenceRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        member = getattr(user, 'member_profile', None)

        if member and member.role in ['pastor', 'admin']:
            return BenevolenceRequest.objects.select_related(
                'member', 'fund', 'approved_by'
            )
        if member:
            return BenevolenceRequest.objects.filter(member=member).select_related(
                'fund', 'approved_by'
            )
        return BenevolenceRequest.objects.none()


# ─── Meal Train API ──────────────────────────────────────────────────────────


class MealTrainViewSet(viewsets.ModelViewSet):
    serializer_class = MealTrainSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-start_date']

    def get_queryset(self):
        return MealTrain.objects.select_related('recipient').prefetch_related(
            'signups__volunteer'
        )


class MealSignupViewSet(viewsets.ModelViewSet):
    serializer_class = MealSignupSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['meal_train', 'confirmed']
    queryset = MealSignup.objects.select_related('meal_train', 'volunteer')


# ─── Crisis API ──────────────────────────────────────────────────────────────


class CrisisProtocolViewSet(viewsets.ModelViewSet):
    serializer_class = CrisisProtocolSerializer
    permission_classes = [IsPastor | IsAdmin]
    queryset = CrisisProtocol.objects.all()
    search_fields = ['title', 'protocol_type']


class CrisisResourceViewSet(viewsets.ModelViewSet):
    serializer_class = CrisisResourceSerializer
    permission_classes = [IsPastor | IsAdmin]
    queryset = CrisisResource.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'description']
