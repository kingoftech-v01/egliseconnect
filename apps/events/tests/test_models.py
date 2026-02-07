"""Tests for events models."""
import pytest
from django.utils import timezone

from apps.core.constants import RSVPStatus
from apps.events.models import Event, EventRSVP
from apps.members.tests.factories import MemberFactory

from .factories import EventFactory, EventRSVPFactory


@pytest.mark.django_db
class TestEventModel:
    """Tests for Event model."""

    def test_event_str(self):
        """Event.__str__ returns title and date (line 38)."""
        now = timezone.now()
        event = EventFactory(title='Sunday Worship', start_datetime=now)
        result = str(event)
        assert 'Sunday Worship' in result
        assert str(now.date()) in result

    def test_is_full_with_max_attendees_reached(self):
        """is_full returns True when confirmed_count >= max_attendees (line 48)."""
        event = EventFactory(max_attendees=2)
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        assert event.is_full is True

    def test_is_full_with_max_attendees_not_reached(self):
        """is_full returns False when confirmed_count < max_attendees."""
        event = EventFactory(max_attendees=5)
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        assert event.is_full is False

    def test_is_full_no_max_attendees(self):
        """is_full returns False when max_attendees is None."""
        event = EventFactory(max_attendees=None)
        assert event.is_full is False


@pytest.mark.django_db
class TestEventRSVPModel:
    """Tests for EventRSVP model."""

    def test_event_rsvp_str(self):
        """EventRSVP.__str__ returns member name and event title (line 66)."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        event = EventFactory(title='Prayer Meeting')
        rsvp = EventRSVPFactory(event=event, member=member)
        result = str(rsvp)
        assert 'Jean Dupont' in result
        assert 'Prayer Meeting' in result
