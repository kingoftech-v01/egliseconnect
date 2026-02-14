"""Worship service API views."""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import AssignmentStatus

from .models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
    Sermon, SermonSeries, Song, Setlist, SetlistSong,
    VolunteerPreference, LiveStream, Rehearsal, RehearsalAttendee,
    SongRequest,
)
from .serializers import (
    WorshipServiceSerializer, ServiceSectionSerializer,
    ServiceAssignmentSerializer, EligibleMemberListSerializer,
    SermonSerializer, SermonSeriesSerializer,
    SongSerializer, SetlistSerializer, SetlistSongSerializer,
    VolunteerPreferenceSerializer, LiveStreamSerializer,
    RehearsalSerializer, RehearsalAttendeeSerializer,
    SongRequestSerializer,
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
            return Response({'error': 'Non autorise'}, status=status.HTTP_403_FORBIDDEN)
        from .services import WorshipServiceManager
        WorshipServiceManager.member_respond(assignment, accepted=True)
        return Response(self.get_serializer(assignment).data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline an assignment."""
        assignment = self.get_object()
        if not hasattr(request.user, 'member_profile') or assignment.member != request.user.member_profile:
            return Response({'error': 'Non autorise'}, status=status.HTTP_403_FORBIDDEN)
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


# ─── New model ViewSets ──────────────────────────────────────────────────────


class SermonViewSet(viewsets.ModelViewSet):
    """CRUD operations for sermons."""
    queryset = Sermon.objects.all().select_related('speaker', 'series', 'service')
    serializer_class = SermonSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'speaker', 'series', 'date']
    search_fields = ['title', 'scripture_reference', 'notes']
    ordering_fields = ['date']
    ordering = ['-date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class SermonSeriesViewSet(viewsets.ModelViewSet):
    """CRUD operations for sermon series."""
    queryset = SermonSeries.objects.all()
    serializer_class = SermonSeriesSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'description']
    ordering = ['-start_date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class SongViewSet(viewsets.ModelViewSet):
    """CRUD operations for songs."""
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['song_key']
    search_fields = ['title', 'artist', 'tags', 'ccli_number']
    ordering_fields = ['title', 'play_count', 'last_played']
    ordering = ['title']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class SetlistViewSet(viewsets.ModelViewSet):
    """CRUD operations for setlists."""
    queryset = Setlist.objects.all().select_related('service').prefetch_related('songs__song')
    serializer_class = SetlistSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class SetlistSongViewSet(viewsets.ModelViewSet):
    """CRUD operations for setlist songs."""
    queryset = SetlistSong.objects.all().select_related('setlist', 'song')
    serializer_class = SetlistSongSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['setlist', 'song']
    ordering_fields = ['order']
    ordering = ['order']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class VolunteerPreferenceViewSet(viewsets.ModelViewSet):
    """CRUD operations for volunteer preferences."""
    queryset = VolunteerPreference.objects.all().select_related('member')
    serializer_class = VolunteerPreferenceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['member']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class LiveStreamViewSet(viewsets.ModelViewSet):
    """CRUD operations for live streams."""
    queryset = LiveStream.objects.all().select_related('service')
    serializer_class = LiveStreamSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service', 'platform']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class RehearsalViewSet(viewsets.ModelViewSet):
    """CRUD operations for rehearsals."""
    queryset = Rehearsal.objects.all().select_related('service').prefetch_related('attendees__member')
    serializer_class = RehearsalSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['service', 'date']
    ordering_fields = ['date']
    ordering = ['-date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class SongRequestViewSet(viewsets.ModelViewSet):
    """CRUD operations for song requests."""
    queryset = SongRequest.objects.all().select_related('requested_by')
    serializer_class = SongRequestSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'requested_by']
    ordering_fields = ['votes', 'created_at']
    ordering = ['-votes', '-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    def perform_create(self, serializer):
        member = getattr(self.request.user, 'member_profile', None)
        serializer.save(requested_by=member)
