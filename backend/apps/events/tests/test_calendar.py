"""Tests for calendar service — iCal generation, Google/Outlook URLs."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.events.services_calendar import CalendarService
from apps.events.tests.factories import EventFactory


pytestmark = pytest.mark.django_db


class TestGenerateICalEvent:
    def test_generates_valid_ical(self):
        event = EventFactory(title='Culte du dimanche', location='Église')
        ical = CalendarService.generate_ical_event(event)
        assert isinstance(ical, bytes)
        assert b'VCALENDAR' in ical
        assert b'VEVENT' in ical
        assert b'Culte du dimanche' in ical

    def test_includes_location(self):
        event = EventFactory(location='Sanctuaire', location_address='123 rue Test')
        ical = CalendarService.generate_ical_event(event)
        assert b'Sanctuaire' in ical

    def test_includes_description(self):
        event = EventFactory(description='Description de test')
        ical = CalendarService.generate_ical_event(event)
        assert b'Description de test' in ical

    def test_includes_uid(self):
        event = EventFactory()
        ical = CalendarService.generate_ical_event(event)
        assert str(event.pk).encode() in ical

    def test_event_without_location(self):
        event = EventFactory(location='', location_address='')
        ical = CalendarService.generate_ical_event(event)
        assert b'VCALENDAR' in ical


class TestGenerateICalFeed:
    def test_generates_feed_with_multiple_events(self):
        EventFactory.create_batch(3)
        from apps.events.models import Event
        events = Event.objects.all()
        ical = CalendarService.generate_ical_feed(events)
        assert isinstance(ical, bytes)
        assert ical.count(b'BEGIN:VEVENT') == 3

    def test_empty_feed(self):
        from apps.events.models import Event
        ical = CalendarService.generate_ical_feed(Event.objects.none())
        assert b'VCALENDAR' in ical
        assert b'BEGIN:VEVENT' not in ical


class TestGoogleCalendarUrl:
    def test_returns_valid_url(self):
        event = EventFactory(title='Test Event')
        url = CalendarService.google_calendar_url(event)
        assert url.startswith('https://calendar.google.com/calendar/render')
        assert 'Test%20Event' in url or 'Test+Event' in url

    def test_includes_dates(self):
        event = EventFactory()
        url = CalendarService.google_calendar_url(event)
        assert 'dates=' in url

    def test_includes_location(self):
        event = EventFactory(location='Église Centrale')
        url = CalendarService.google_calendar_url(event)
        assert 'location=' in url

    def test_includes_description(self):
        event = EventFactory(description='Test description')
        url = CalendarService.google_calendar_url(event)
        assert 'details=' in url


class TestOutlookCalendarUrl:
    def test_returns_valid_url(self):
        event = EventFactory(title='Test Event')
        url = CalendarService.outlook_calendar_url(event)
        assert url.startswith('https://outlook.live.com/calendar')
        assert 'subject=' in url

    def test_includes_dates(self):
        event = EventFactory()
        url = CalendarService.outlook_calendar_url(event)
        assert 'startdt=' in url
        assert 'enddt=' in url

    def test_includes_body(self):
        event = EventFactory(description='Test body')
        url = CalendarService.outlook_calendar_url(event)
        assert 'body=' in url
