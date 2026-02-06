"""Tests for events frontend views."""
import pytest
from datetime import timedelta

from django.test import Client
from django.utils import timezone

from apps.core.constants import RSVPStatus, EventType, Roles
from apps.members.tests.factories import UserFactory, MemberWithUserFactory
from apps.events.tests.factories import EventFactory, EventRSVPFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def member_user():
    member = MemberWithUserFactory(role=Roles.MEMBER)
    return member.user


@pytest.fixture
def user_no_profile():
    return UserFactory()


class TestEventList:

    def test_authenticated_access(self, client, member_user):
        client.force_login(member_user)
        EventFactory.create_batch(3)
        response = client.get('/events/')
        assert response.status_code == 200

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get('/events/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_context_contains_events_and_title(self, client, member_user):
        client.force_login(member_user)
        EventFactory()
        response = client.get('/events/')
        assert 'events' in response.context
        assert 'page_title' in response.context

    def test_filter_by_event_type(self, client, member_user):
        client.force_login(member_user)
        EventFactory(event_type=EventType.WORSHIP)
        EventFactory(event_type=EventType.MEAL)
        response = client.get('/events/', {'type': EventType.WORSHIP})
        assert response.status_code == 200
        events = list(response.context['events'])
        assert len(events) == 1
        assert events[0].event_type == EventType.WORSHIP

    def test_filter_upcoming(self, client, member_user):
        client.force_login(member_user)
        EventFactory(start_datetime=timezone.now() + timedelta(days=5))
        EventFactory(
            start_datetime=timezone.now() - timedelta(days=5),
            end_datetime=timezone.now() - timedelta(days=5, hours=-2),
        )
        response = client.get('/events/', {'upcoming': '1'})
        assert response.status_code == 200
        events = list(response.context['events'])
        assert len(events) == 1

    def test_excludes_unpublished_and_cancelled(self, client, member_user):
        client.force_login(member_user)
        EventFactory(is_published=True, is_cancelled=False)
        EventFactory(is_published=False)
        EventFactory(is_cancelled=True)
        response = client.get('/events/')
        events = list(response.context['events'])
        assert len(events) == 1

    def test_pagination(self, client, member_user):
        client.force_login(member_user)
        for i in range(25):
            EventFactory(start_datetime=timezone.now() + timedelta(days=i))
        response = client.get('/events/')
        events_page = response.context['events']
        assert len(list(events_page)) == 20

        response_p2 = client.get('/events/', {'page': 2})
        events_p2 = list(response_p2.context['events'])
        assert len(events_p2) == 5


class TestEventDetail:

    def test_authenticated_access(self, client, member_user):
        client.force_login(member_user)
        event = EventFactory()
        response = client.get(f'/events/{event.id}/')
        assert response.status_code == 200

    def test_unauthenticated_redirects(self, client):
        event = EventFactory()
        response = client.get(f'/events/{event.id}/')
        assert response.status_code == 302

    def test_context_keys(self, client, member_user):
        client.force_login(member_user)
        event = EventFactory()
        response = client.get(f'/events/{event.id}/')
        assert response.context['event'] == event
        assert 'user_rsvp' in response.context
        assert 'attendees' in response.context
        assert response.context['page_title'] == event.title

    def test_user_rsvp_with_member_profile(self, client, member_user):
        client.force_login(member_user)
        member = member_user.member_profile
        event = EventFactory()
        rsvp = EventRSVPFactory(event=event, member=member, status=RSVPStatus.CONFIRMED)
        response = client.get(f'/events/{event.id}/')
        assert response.context['user_rsvp'] == rsvp

    def test_user_rsvp_none_when_no_rsvp(self, client, member_user):
        client.force_login(member_user)
        event = EventFactory()
        response = client.get(f'/events/{event.id}/')
        assert response.context['user_rsvp'] is None

    def test_user_rsvp_none_when_no_member_profile(self, client, user_no_profile):
        client.force_login(user_no_profile)
        event = EventFactory()
        response = client.get(f'/events/{event.id}/')
        assert response.context['user_rsvp'] is None

    def test_attendees_limited_to_confirmed(self, client, member_user):
        client.force_login(member_user)
        event = EventFactory()
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        EventRSVPFactory(event=event, status=RSVPStatus.DECLINED)
        response = client.get(f'/events/{event.id}/')
        assert len(response.context['attendees']) == 1

    def test_404_for_nonexistent_event(self, client, member_user):
        import uuid
        client.force_login(member_user)
        response = client.get(f'/events/{uuid.uuid4()}/')
        assert response.status_code == 404


class TestEventRSVP:

    def test_post_creates_rsvp(self, client, member_user):
        client.force_login(member_user)
        event = EventFactory()
        response = client.post(
            f'/events/{event.id}/rsvp/',
            {'status': RSVPStatus.CONFIRMED, 'guests': '2'},
        )
        assert response.status_code == 302
        from apps.events.models import EventRSVP
        rsvp = EventRSVP.objects.get(event=event, member=member_user.member_profile)
        assert rsvp.status == RSVPStatus.CONFIRMED
        assert rsvp.guests == 2

    def test_post_updates_existing_rsvp(self, client, member_user):
        client.force_login(member_user)
        member = member_user.member_profile
        event = EventFactory()
        EventRSVPFactory(event=event, member=member, status=RSVPStatus.PENDING)

        response = client.post(
            f'/events/{event.id}/rsvp/',
            {'status': RSVPStatus.CONFIRMED, 'guests': '1'},
        )
        assert response.status_code == 302
        from apps.events.models import EventRSVP
        rsvp = EventRSVP.objects.get(event=event, member=member)
        assert rsvp.status == RSVPStatus.CONFIRMED
        assert rsvp.guests == 1

    def test_post_default_status_and_guests(self, client, member_user):
        """Empty POST defaults to CONFIRMED status and 0 guests."""
        client.force_login(member_user)
        event = EventFactory()
        response = client.post(f'/events/{event.id}/rsvp/', {})
        assert response.status_code == 302
        from apps.events.models import EventRSVP
        rsvp = EventRSVP.objects.get(event=event, member=member_user.member_profile)
        assert rsvp.status == RSVPStatus.CONFIRMED
        assert rsvp.guests == 0

    def test_post_invalid_guests_defaults_to_zero(self, client, member_user):
        """Non-numeric guests value defaults to 0."""
        client.force_login(member_user)
        event = EventFactory()
        response = client.post(
            f'/events/{event.id}/rsvp/', {'guests': 'abc'}
        )
        assert response.status_code == 302
        from apps.events.models import EventRSVP
        rsvp = EventRSVP.objects.get(event=event, member=member_user.member_profile)
        assert rsvp.guests == 0

    def test_get_redirects_without_creating_rsvp(self, client, member_user):
        """GET request just redirects without creating an RSVP."""
        client.force_login(member_user)
        event = EventFactory()
        response = client.get(f'/events/{event.id}/rsvp/')
        assert response.status_code == 302
        from apps.events.models import EventRSVP
        assert not EventRSVP.objects.filter(
            event=event, member=member_user.member_profile
        ).exists()

    def test_no_member_profile_redirects_with_error(self, client, user_no_profile):
        client.force_login(user_no_profile)
        event = EventFactory()
        response = client.post(
            f'/events/{event.id}/rsvp/',
            {'status': RSVPStatus.CONFIRMED},
        )
        assert response.status_code == 302
        assert str(event.id) in response.url

    def test_unauthenticated_redirects_to_login(self, client):
        event = EventFactory()
        response = client.post(f'/events/{event.id}/rsvp/', {})
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_404_for_nonexistent_event(self, client, member_user):
        import uuid
        client.force_login(member_user)
        response = client.post(f'/events/{uuid.uuid4()}/rsvp/', {})
        assert response.status_code == 404


class TestEventCalendar:

    def test_authenticated_access(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/events/calendar/')
        assert response.status_code == 200

    def test_context_has_page_title(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/events/calendar/')
        assert 'page_title' in response.context

    def test_unauthenticated_redirects(self, client):
        response = client.get('/events/calendar/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
