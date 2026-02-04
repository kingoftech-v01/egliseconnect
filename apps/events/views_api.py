"""Events API Views."""
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import RSVPStatus

from .models import Event, EventRSVP
from .serializers import EventSerializer, EventListSerializer, EventRSVPSerializer


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for Event CRUD."""

    queryset = Event.objects.all().select_related('organizer')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'is_published', 'is_cancelled']
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
        """Get upcoming events."""
        events = self.queryset.filter(
            start_datetime__gte=timezone.now(),
            is_published=True,
            is_cancelled=False
        )[:10]
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get events for calendar view."""
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
        """Submit RSVP for event."""
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
        """Get event attendees."""
        event = self.get_object()
        rsvps = event.rsvps.filter(status=RSVPStatus.CONFIRMED).select_related('member')
        serializer = EventRSVPSerializer(rsvps, many=True)
        return Response(serializer.data)
