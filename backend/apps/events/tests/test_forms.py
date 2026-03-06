"""Tests for events forms."""
import pytest
from django.utils import timezone

from apps.core.constants import EventType, RSVPStatus
from apps.events.forms import EventForm, RSVPForm
from apps.members.tests.factories import MemberFactory

from .factories import EventFactory, EventRSVPFactory


@pytest.mark.django_db
class TestEventForm:
    """Tests for EventForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'title': 'Culte du dimanche',
            'start_datetime': '2026-03-01T10:00',
            'end_datetime': '2026-03-01T12:00',
            'event_type': EventType.WORSHIP,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Valid form with all fields."""
        organizer = MemberFactory()
        data = self._get_valid_data(
            description='Un culte spécial',
            location='Église principale',
            location_address='123 Rue Test, Montreal, QC H1A 1A1',
            all_day=False,
            is_online=False,
            organizer=organizer.pk,
            max_attendees=100,
            requires_rsvp=True,
            is_published=True,
        )
        form = EventForm(data=data)
        assert form.is_valid(), form.errors

    def test_valid_form_minimal(self):
        """Valid form with only required fields."""
        data = self._get_valid_data()
        form = EventForm(data=data)
        assert form.is_valid(), form.errors

    def test_title_required(self):
        """Title is a required field."""
        data = self._get_valid_data(title='')
        form = EventForm(data=data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_start_datetime_required(self):
        """Start datetime is a required field."""
        data = self._get_valid_data(start_datetime='')
        form = EventForm(data=data)
        assert not form.is_valid()
        assert 'start_datetime' in form.errors

    def test_end_datetime_required(self):
        """End datetime is a required field."""
        data = self._get_valid_data(end_datetime='')
        form = EventForm(data=data)
        assert not form.is_valid()
        assert 'end_datetime' in form.errors

    def test_optional_fields_blank(self):
        """Optional fields can be blank."""
        data = self._get_valid_data(
            description='',
            location='',
            location_address='',
            online_link='',
        )
        form = EventForm(data=data)
        assert form.is_valid(), form.errors

    def test_all_day_event(self):
        """All-day event flag is valid."""
        data = self._get_valid_data(all_day=True)
        form = EventForm(data=data)
        assert form.is_valid(), form.errors

    def test_online_event_with_link(self):
        """Online event with valid URL."""
        data = self._get_valid_data(
            is_online=True,
            online_link='https://zoom.us/j/123456789',
        )
        form = EventForm(data=data)
        assert form.is_valid(), form.errors

    def test_event_with_max_attendees(self):
        """Event with max attendees limit."""
        data = self._get_valid_data(
            max_attendees=50,
            requires_rsvp=True,
        )
        form = EventForm(data=data)
        assert form.is_valid(), form.errors

    def test_all_event_types(self):
        """All valid event types accepted."""
        for event_type, _ in EventType.CHOICES:
            data = self._get_valid_data(event_type=event_type)
            form = EventForm(data=data)
            assert form.is_valid(), f"Failed for event_type={event_type}: {form.errors}"

    def test_save_creates_event(self):
        """Save creates event correctly."""
        organizer = MemberFactory()
        data = self._get_valid_data(
            organizer=organizer.pk,
            description='Test event description',
            location='Test location',
        )
        form = EventForm(data=data)
        assert form.is_valid()
        event = form.save()
        assert event.pk is not None
        assert event.title == 'Culte du dimanche'
        assert event.organizer == organizer
        assert event.location == 'Test location'

    def test_update_existing_event(self):
        """Updates existing event correctly."""
        event = EventFactory()
        data = {
            'title': 'Updated Event Title',
            'start_datetime': event.start_datetime.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': event.end_datetime.strftime('%Y-%m-%dT%H:%M'),
            'event_type': event.event_type,
            'description': 'Updated description',
            'is_published': True,
        }
        form = EventForm(data=data, instance=event)
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.title == 'Updated Event Title'
        assert saved.description == 'Updated description'


@pytest.mark.django_db
class TestRSVPForm:
    """Tests for RSVPForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'status': RSVPStatus.CONFIRMED,
            'guests': 0,
            'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Valid form with all fields."""
        data = self._get_valid_data(
            status=RSVPStatus.CONFIRMED,
            guests=2,
            notes='Will attend with family',
        )
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors

    def test_valid_form_minimal(self):
        """Valid form with default values."""
        data = self._get_valid_data()
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors

    def test_all_rsvp_statuses(self):
        """All valid RSVP statuses accepted."""
        for status, _ in RSVPStatus.CHOICES:
            data = self._get_valid_data(status=status)
            form = RSVPForm(data=data)
            assert form.is_valid(), f"Failed for status={status}: {form.errors}"

    def test_guests_zero_valid(self):
        """Zero guests is valid."""
        data = self._get_valid_data(guests=0)
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors

    def test_guests_positive_valid(self):
        """Positive guest count is valid."""
        data = self._get_valid_data(guests=5)
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors

    def test_notes_optional(self):
        """Notes field is optional."""
        data = self._get_valid_data(notes='')
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors

    def test_save_creates_rsvp(self):
        """Save creates RSVP correctly."""
        event = EventFactory()
        member = MemberFactory()
        data = self._get_valid_data(
            status=RSVPStatus.CONFIRMED,
            guests=3,
            notes='Looking forward to it!',
        )
        form = RSVPForm(data=data)
        assert form.is_valid()
        rsvp = form.save(commit=False)
        rsvp.event = event
        rsvp.member = member
        rsvp.save()
        assert rsvp.pk is not None
        assert rsvp.status == RSVPStatus.CONFIRMED
        assert rsvp.guests == 3
        assert rsvp.notes == 'Looking forward to it!'

    def test_update_existing_rsvp(self):
        """Updates existing RSVP correctly."""
        rsvp = EventRSVPFactory(status=RSVPStatus.PENDING, guests=0)
        data = {
            'status': RSVPStatus.CONFIRMED,
            'guests': 2,
            'notes': 'Changed my mind, will attend',
        }
        form = RSVPForm(data=data, instance=rsvp)
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.status == RSVPStatus.CONFIRMED
        assert saved.guests == 2
        assert saved.notes == 'Changed my mind, will attend'

    def test_decline_rsvp(self):
        """Can decline RSVP."""
        data = self._get_valid_data(
            status=RSVPStatus.DECLINED,
            guests=0,
            notes='Unable to attend',
        )
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors

    def test_maybe_status(self):
        """Maybe status is valid."""
        data = self._get_valid_data(
            status=RSVPStatus.MAYBE,
            guests=1,
            notes='Not sure yet',
        )
        form = RSVPForm(data=data)
        assert form.is_valid(), form.errors
