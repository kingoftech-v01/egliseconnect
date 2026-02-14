"""Events API views — events, rooms, bookings, templates, waitlist,
volunteer needs, photos, surveys."""
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import RSVPStatus

from .models import (
    Event, EventRSVP, Room, RoomBooking, EventTemplate,
    RegistrationForm, RegistrationEntry,
    EventWaitlist, EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)
from .serializers import (
    EventSerializer, EventListSerializer, EventRSVPSerializer,
    RoomSerializer, RoomBookingSerializer, EventTemplateSerializer,
    RegistrationFormSerializer, RegistrationEntrySerializer,
    EventWaitlistSerializer, EventVolunteerNeedSerializer,
    EventVolunteerSignupSerializer, EventPhotoSerializer,
    EventSurveySerializer, SurveyResponseSerializer,
)


class EventViewSet(viewsets.ModelViewSet):
    """CRUD operations for events."""

    queryset = Event.objects.all().select_related('organizer')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'is_published', 'is_cancelled', 'campus']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_datetime', 'title']
    ordering = ['start_datetime']

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'upcoming', 'calendar']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Return next 10 published events."""
        events = self.queryset.filter(
            start_datetime__gte=timezone.now(),
            is_published=True,
            is_cancelled=False
        )[:10]
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Return events within optional start/end date range."""
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        queryset = self.queryset.filter(is_published=True)
        if start:
            queryset = queryset.filter(start_datetime__gte=start)
        if end:
            queryset = queryset.filter(start_datetime__lte=end)
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rsvp(self, request, pk=None):
        """Create or update RSVP for the current user."""
        event = self.get_object()
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Profil membre requis'}, status=status.HTTP_400_BAD_REQUEST)

        member = request.user.member_profile
        rsvp_status = request.data.get('status', RSVPStatus.CONFIRMED)

        rsvp, created = EventRSVP.objects.update_or_create(
            event=event,
            member=member,
            defaults={'status': rsvp_status, 'guests': request.data.get('guests', 0)}
        )
        return Response(EventRSVPSerializer(rsvp).data)

    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """Return confirmed attendees for this event."""
        event = self.get_object()
        rsvps = event.rsvps.filter(status=RSVPStatus.CONFIRMED).select_related('member')
        serializer = EventRSVPSerializer(rsvps, many=True)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    """CRUD for rooms."""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class RoomBookingViewSet(viewsets.ModelViewSet):
    """CRUD for room bookings."""
    queryset = RoomBooking.objects.all().select_related('room', 'booked_by', 'event')
    serializer_class = RoomBookingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['room', 'status']
    ordering = ['start_datetime']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class EventTemplateViewSet(viewsets.ModelViewSet):
    """CRUD for event templates."""
    queryset = EventTemplate.objects.all()
    serializer_class = EventTemplateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class EventVolunteerNeedViewSet(viewsets.ModelViewSet):
    """CRUD for volunteer needs."""
    queryset = EventVolunteerNeed.objects.all().select_related('event')
    serializer_class = EventVolunteerNeedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class EventPhotoViewSet(viewsets.ModelViewSet):
    """CRUD for event photos."""
    queryset = EventPhoto.objects.all().select_related('event', 'uploaded_by')
    serializer_class = EventPhotoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'is_approved']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]


class EventSurveyViewSet(viewsets.ModelViewSet):
    """CRUD for surveys."""
    queryset = EventSurvey.objects.all().select_related('event')
    serializer_class = EventSurveySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]
