"""Volunteers API Views."""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import ScheduleStatus

from .models import VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest
from .serializers import VolunteerPositionSerializer, VolunteerAvailabilitySerializer, VolunteerScheduleSerializer, SwapRequestSerializer


class VolunteerPositionViewSet(viewsets.ModelViewSet):
    queryset = VolunteerPosition.objects.all()
    serializer_class = VolunteerPositionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role_type', 'is_active']
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class VolunteerScheduleViewSet(viewsets.ModelViewSet):
    queryset = VolunteerSchedule.objects.all().select_related('member', 'position')
    serializer_class = VolunteerScheduleSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['position', 'status', 'date', 'member']
    ordering_fields = ['date']
    ordering = ['date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_schedule']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def my_schedule(self, request):
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Profil requis'}, status=status.HTTP_404_NOT_FOUND)
        schedules = self.queryset.filter(member=request.user.member_profile)
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        schedule = self.get_object()
        schedule.status = ScheduleStatus.CONFIRMED
        schedule.save()
        return Response(self.get_serializer(schedule).data)


class VolunteerAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = VolunteerAvailability.objects.all()
    serializer_class = VolunteerAvailabilitySerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        if hasattr(self.request.user, 'member_profile'):
            return self.queryset.filter(member=self.request.user.member_profile)
        return self.queryset.none()


class SwapRequestViewSet(viewsets.ModelViewSet):
    queryset = SwapRequest.objects.all()
    serializer_class = SwapRequestSerializer
    permission_classes = [IsMember]
