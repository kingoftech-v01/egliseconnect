"""Worship service API views."""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import AssignmentStatus

from .models import WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList
from .serializers import (
    WorshipServiceSerializer, ServiceSectionSerializer,
    ServiceAssignmentSerializer, EligibleMemberListSerializer,
)


class WorshipServiceViewSet(viewsets.ModelViewSet):
    """CRUD operations for worship services."""
    queryset = WorshipService.objects.all().select_related('created_by')
    serializer_class = WorshipServiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'date']
    search_fields = ['theme', 'notes']
    ordering_fields = ['date', 'start_time']
    ordering = ['-date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    def perform_create(self, serializer):
        member = getattr(self.request.user, 'member_profile', None)
        serializer.save(created_by=member)


class ServiceSectionViewSet(viewsets.ModelViewSet):
    """CRUD operations for service sections."""
    queryset = ServiceSection.objects.all().select_related('service', 'department')
    serializer_class = ServiceSectionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['service', 'section_type']
    ordering_fields = ['order']
    ordering = ['order']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class ServiceAssignmentViewSet(viewsets.ModelViewSet):
    """CRUD operations for service assignments."""
    queryset = ServiceAssignment.objects.all().select_related(
        'section__service', 'member', 'task_type'
    )
    serializer_class = ServiceAssignmentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['section', 'member', 'status']
    ordering_fields = ['section__service__date']
    ordering = ['section__service__date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_assignments', 'confirm', 'decline']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    @action(detail=False, methods=['get'], url_path='my-assignments')
    def my_assignments(self, request):
        """Return assignments for the current user."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Profil requis'}, status=status.HTTP_404_NOT_FOUND)
        assignments = self.queryset.filter(member=request.user.member_profile)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an assignment."""
        assignment = self.get_object()
        if not hasattr(request.user, 'member_profile') or assignment.member != request.user.member_profile:
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        from .services import WorshipServiceManager
        WorshipServiceManager.member_respond(assignment, accepted=True)
        return Response(self.get_serializer(assignment).data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline an assignment."""
        assignment = self.get_object()
        if not hasattr(request.user, 'member_profile') or assignment.member != request.user.member_profile:
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        from .services import WorshipServiceManager
        WorshipServiceManager.member_respond(assignment, accepted=False)
        return Response(self.get_serializer(assignment).data)


class EligibleMemberListViewSet(viewsets.ModelViewSet):
    """CRUD operations for eligible member lists."""
    queryset = EligibleMemberList.objects.all().prefetch_related('members')
    serializer_class = EligibleMemberListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['section_type']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]
