"""Help Requests API views."""
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsPastor, IsAdmin
from apps.members.models import Member
from .models import HelpRequest, HelpRequestCategory, HelpRequestComment
from .serializers import (
    HelpRequestSerializer,
    HelpRequestCreateSerializer,
    HelpRequestCategorySerializer,
    HelpRequestCommentSerializer,
    HelpRequestAssignSerializer,
    HelpRequestResolveSerializer,
    CommentCreateSerializer,
)


class HelpRequestCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for help request categories."""
    queryset = HelpRequestCategory.objects.filter(is_active=True)
    serializer_class = HelpRequestCategorySerializer
    permission_classes = [IsAuthenticated]


class HelpRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for help requests."""
    serializer_class = HelpRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'urgency', 'category', 'assigned_to', 'is_confidential']
    search_fields = ['title', 'description', 'request_number']
    ordering_fields = ['created_at', 'urgency', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        member = getattr(user, 'member_profile', None)

        if not member:
            return HelpRequest.objects.none()

        # Pastors and admins see all requests
        if member.role in ['pastor', 'admin']:
            return HelpRequest.objects.select_related(
                'member', 'category', 'assigned_to'
            ).prefetch_related('comments')

        # Group leaders see their group members' non-confidential requests
        if member.role == 'group_leader':
            from apps.members.models import GroupMembership
            group_member_ids = GroupMembership.objects.filter(
                group__leader=member
            ).values_list('member_id', flat=True)

            return HelpRequest.objects.filter(
                models.Q(member=member) |
                models.Q(member_id__in=group_member_ids, is_confidential=False)
            ).select_related('member', 'category', 'assigned_to')

        # Regular members see only their own requests
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
        """Get current user's help requests."""
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
        """Assign help request to a staff member."""
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
        """Mark help request as resolved."""
        help_request = self.get_object()
        serializer = HelpRequestResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        help_request.mark_resolved(
            notes=serializer.validated_data.get('resolution_notes', '')
        )
        return Response(HelpRequestSerializer(help_request).data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Add a comment to the help request."""
        help_request = self.get_object()
        member = getattr(request.user, 'member_profile', None)

        if not member:
            return Response({'detail': 'Member profile required.'}, status=400)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Only pastors/admins can create internal comments
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
        """Get comments for a help request."""
        help_request = self.get_object()
        member = getattr(request.user, 'member_profile', None)

        comments = help_request.comments.select_related('author')

        # Hide internal comments from non-staff
        if not member or member.role not in ['pastor', 'admin']:
            comments = comments.filter(is_internal=False)

        serializer = HelpRequestCommentSerializer(comments, many=True)
        return Response(serializer.data)
