"""Calendar service — iCal generation, Google/Apple/Outlook calendar links."""
from datetime import datetime, timezone as dt_timezone
from urllib.parse import quote

from django.conf import settings
from django.utils import timezone

try:
    from icalendar import Calendar, Event as ICalEvent, vDatetime
except ImportError:
    Calendar = None
    ICalEvent = None
    vDatetime = None


class CalendarService:
    """Generate iCal data and external calendar URLs for events."""

    @staticmethod
    def generate_ical_event(event):
        """Generate an iCal VEVENT component for a single Event instance."""
        if ICalEvent is None:
            raise ImportError("icalendar library is required for calendar export.")

        cal = Calendar()
        cal.add('prodid', '-//EgliseConnect//FR')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')

        vevent = ICalEvent()
        vevent.add('uid', f'{event.pk}@egliseconnect')
        vevent.add('dtstart', event.start_datetime)
        vevent.add('dtend', event.end_datetime)
        vevent.add('summary', event.title)
        if event.description:
            vevent.add('description', event.description)
        location_parts = []
        if event.location:
            location_parts.append(event.location)
        if event.location_address:
            location_parts.append(event.location_address)
        if location_parts:
            vevent.add('location', ', '.join(location_parts))
        vevent.add('dtstamp', timezone.now())
        if event.updated_at:
            vevent.add('last-modified', event.updated_at)

        cal.add_component(vevent)
        return cal.to_ical()

    @staticmethod
    def generate_ical_feed(events):
        """Generate a full iCal feed for multiple events."""
        if Calendar is None:
            raise ImportError("icalendar library is required for calendar export.")

        cal = Calendar()
        cal.add('prodid', '-//EgliseConnect//FR')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'EgliseConnect')

        for event in events:
            vevent = ICalEvent()
            vevent.add('uid', f'{event.pk}@egliseconnect')
            vevent.add('dtstart', event.start_datetime)
            vevent.add('dtend', event.end_datetime)
            vevent.add('summary', event.title)
            if event.description:
                vevent.add('description', event.description)
            location_parts = []
            if event.location:
                location_parts.append(event.location)
            if event.location_address:
                location_parts.append(event.location_address)
            if location_parts:
                vevent.add('location', ', '.join(location_parts))
            vevent.add('dtstamp', timezone.now())
            cal.add_component(vevent)

        return cal.to_ical()

    @staticmethod
    def google_calendar_url(event):
        """Generate a Google Calendar 'Add Event' URL."""
        fmt = '%Y%m%dT%H%M%SZ'
        # Convert to UTC for Google Calendar
        start = event.start_datetime
        end = event.end_datetime
        if timezone.is_aware(start):
            start = start.astimezone(dt_timezone.utc)
        if timezone.is_aware(end):
            end = end.astimezone(dt_timezone.utc)

        params = {
            'action': 'TEMPLATE',
            'text': event.title,
            'dates': f'{start.strftime(fmt)}/{end.strftime(fmt)}',
        }
        if event.description:
            params['details'] = event.description
        location_parts = []
        if event.location:
            location_parts.append(event.location)
        if event.location_address:
            location_parts.append(event.location_address)
        if location_parts:
            params['location'] = ', '.join(location_parts)

        query = '&'.join(f'{k}={quote(str(v))}' for k, v in params.items())
        return f'https://calendar.google.com/calendar/render?{query}'

    @staticmethod
    def outlook_calendar_url(event):
        """Generate an Outlook.com 'Add Event' URL."""
        fmt = '%Y-%m-%dT%H:%M:%S'
        start = event.start_datetime
        end = event.end_datetime
        if timezone.is_aware(start):
            start = start.astimezone(dt_timezone.utc)
        if timezone.is_aware(end):
            end = end.astimezone(dt_timezone.utc)

        params = {
            'path': '/calendar/action/compose',
            'rru': 'addevent',
            'subject': event.title,
            'startdt': start.strftime(fmt) + 'Z',
            'enddt': end.strftime(fmt) + 'Z',
        }
        if event.description:
            params['body'] = event.description
        location_parts = []
        if event.location:
            location_parts.append(event.location)
        if event.location_address:
            location_parts.append(event.location_address)
        if location_parts:
            params['location'] = ', '.join(location_parts)

        query = '&'.join(f'{k}={quote(str(v))}' for k, v in params.items())
        return f'https://outlook.live.com/calendar/0/deeplink/compose?{query}'
