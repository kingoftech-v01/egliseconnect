"""Tests for events API views."""
import pytest
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.constants import RSVPStatus, EventType, Roles
from apps.members.tests.factories import UserFactory, MemberWithUserFactory
from apps.events.tests.factories import EventFactory, EventRSVPFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user():
    """Regular member with authenticated user."""
    member = MemberWithUserFactory(role=Roles.MEMBER)
    return member.user


@pytest.fixture
def pastor_user():
    """Pastor with staff-level permissions."""
    member = MemberWithUserFactory(role=Roles.PASTOR)
    return member.user


@pytest.fixture
def user_no_profile():
    """User without any member profile."""
    return UserFactory()


@pytest.fixture
def staff_user_no_profile():
    """Staff user without member profile."""
    user = UserFactory(is_staff=True)
    return user


def _event_payload(**overrides):
    """Return a minimal valid event payload dict."""
    now = timezone.now()
    data = {
        'title': 'Test Event',
        'description': 'A test event',
        'event_type': EventType.WORSHIP,
        'start_datetime': (now + timedelta(days=7)).isoformat(),
        'end_datetime': (now + timedelta(days=7, hours=2)).isoformat(),
        'location': 'Main Hall',
        'is_published': True,
    }
    data.update(overrides)
    return data


class TestEventList:

    def test_list_authenticated(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory.create_batch(3)
        response = api_client.get('/api/v1/events/events/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3

    def test_list_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/events/events/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_uses_list_serializer_fields(self, api_client, member_user):
        """Verifies list action uses compact serializer without detail-only fields."""
        api_client.force_authenticate(user=member_user)
        EventFactory()
        response = api_client.get('/api/v1/events/events/')
        result = response.data['results'][0]
        assert 'title' in result
        assert 'event_type_display' in result
        assert 'confirmed_count' in result
        assert 'is_full' not in result
        assert 'organizer_name' not in result

    def test_filter_by_event_type(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(event_type=EventType.WORSHIP)
        EventFactory(event_type=EventType.MEAL)
        response = api_client.get('/api/v1/events/events/', {'event_type': EventType.WORSHIP})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['event_type'] == EventType.WORSHIP

    def test_filter_by_is_published(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(is_published=True)
        EventFactory(is_published=False)
        response = api_client.get('/api/v1/events/events/', {'is_published': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_filter_by_is_cancelled(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(is_cancelled=False)
        EventFactory(is_cancelled=True)
        response = api_client.get('/api/v1/events/events/', {'is_cancelled': 'false'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_search_events(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(title='Sunday Worship')
        EventFactory(title='Youth Meeting')
        response = api_client.get('/api/v1/events/events/', {'search': 'Worship'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Sunday Worship'

    def test_ordering_by_title(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(title='Beta Event')
        EventFactory(title='Alpha Event')
        response = api_client.get('/api/v1/events/events/', {'ordering': 'title'})
        assert response.status_code == status.HTTP_200_OK
        titles = [r['title'] for r in response.data['results']]
        assert titles == sorted(titles)

    def test_ordering_by_start_datetime(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        now = timezone.now()
        EventFactory(start_datetime=now + timedelta(days=10))
        EventFactory(start_datetime=now + timedelta(days=1))
        response = api_client.get('/api/v1/events/events/', {'ordering': 'start_datetime'})
        assert response.status_code == status.HTTP_200_OK
        dates = [r['start_datetime'] for r in response.data['results']]
        assert dates == sorted(dates)


class TestEventRetrieve:

    def test_retrieve_authenticated(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        event = EventFactory()
        response = api_client.get(f'/api/v1/events/events/{event.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == event.title

    def test_retrieve_uses_detail_serializer(self, api_client, member_user):
        """Detail view includes extra fields like is_full and organizer_name."""
        api_client.force_authenticate(user=member_user)
        event = EventFactory()
        response = api_client.get(f'/api/v1/events/events/{event.id}/')
        assert 'is_full' in response.data
        assert 'organizer_name' in response.data

    def test_retrieve_unauthenticated(self, api_client):
        event = EventFactory()
        response = api_client.get(f'/api/v1/events/events/{event.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_nonexistent(self, api_client, member_user):
        import uuid
        api_client.force_authenticate(user=member_user)
        response = api_client.get(f'/api/v1/events/events/{uuid.uuid4()}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEventCreate:

    def test_create_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        data = _event_payload()
        response = api_client.post('/api/v1/events/events/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Test Event'

    def test_create_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        data = _event_payload()
        response = api_client.post('/api/v1/events/events/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_unauthenticated(self, api_client):
        data = _event_payload()
        response = api_client.post('/api/v1/events/events/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEventUpdate:

    def test_full_update_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        data = _event_payload(title='Fully Updated')
        response = api_client.put(
            f'/api/v1/events/events/{event.id}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Fully Updated'

    def test_partial_update_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory(title='Original')
        response = api_client.patch(
            f'/api/v1/events/events/{event.id}/',
            {'title': 'Patched'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Patched'

    def test_update_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        event = EventFactory()
        response = api_client.patch(
            f'/api/v1/events/events/{event.id}/',
            {'title': 'Nope'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEventDelete:

    def test_delete_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        response = api_client.delete(f'/api/v1/events/events/{event.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        event = EventFactory()
        response = api_client.delete(f'/api/v1/events/events/{event.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEventUpcoming:

    def test_upcoming_returns_future_published_not_cancelled(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        good = EventFactory(
            start_datetime=timezone.now() + timedelta(days=1),
            is_published=True,
            is_cancelled=False,
        )
        response = api_client.get('/api/v1/events/events/upcoming/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == str(good.id)

    def test_upcoming_excludes_past_events(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(
            start_datetime=timezone.now() - timedelta(days=1),
            end_datetime=timezone.now() - timedelta(hours=22),
            is_published=True,
        )
        response = api_client.get('/api/v1/events/events/upcoming/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_upcoming_excludes_cancelled(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(
            start_datetime=timezone.now() + timedelta(days=1),
            is_published=True,
            is_cancelled=True,
        )
        response = api_client.get('/api/v1/events/events/upcoming/')
        assert len(response.data) == 0

    def test_upcoming_excludes_unpublished(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(
            start_datetime=timezone.now() + timedelta(days=1),
            is_published=False,
        )
        response = api_client.get('/api/v1/events/events/upcoming/')
        assert len(response.data) == 0

    def test_upcoming_limited_to_ten(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        for i in range(15):
            EventFactory(
                start_datetime=timezone.now() + timedelta(days=i + 1),
                is_published=True,
                is_cancelled=False,
            )
        response = api_client.get('/api/v1/events/events/upcoming/')
        assert len(response.data) == 10


class TestEventCalendar:

    def test_calendar_returns_published_only(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(is_published=True)
        EventFactory(is_published=False)
        response = api_client.get('/api/v1/events/events/calendar/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_calendar_with_start_param(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        now = timezone.now()
        EventFactory(start_datetime=now - timedelta(days=10), is_published=True)
        EventFactory(start_datetime=now + timedelta(days=5), is_published=True)
        start = (now - timedelta(days=1)).isoformat()
        response = api_client.get('/api/v1/events/events/calendar/', {'start': start})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_calendar_with_end_param(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        now = timezone.now()
        EventFactory(start_datetime=now + timedelta(days=2), is_published=True)
        EventFactory(start_datetime=now + timedelta(days=30), is_published=True)
        end = (now + timedelta(days=10)).isoformat()
        response = api_client.get('/api/v1/events/events/calendar/', {'end': end})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_calendar_with_start_and_end(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        now = timezone.now()
        EventFactory(start_datetime=now + timedelta(days=5), is_published=True)
        EventFactory(start_datetime=now + timedelta(days=50), is_published=True)
        EventFactory(start_datetime=now - timedelta(days=50), is_published=True)
        start = (now + timedelta(days=1)).isoformat()
        end = (now + timedelta(days=10)).isoformat()
        response = api_client.get(
            '/api/v1/events/events/calendar/', {'start': start, 'end': end}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_calendar_no_params(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        EventFactory(is_published=True)
        EventFactory(is_published=True)
        response = api_client.get('/api/v1/events/events/calendar/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


class TestEventRSVP:

    def test_rsvp_create_confirmed(self, api_client, pastor_user):
        """RSVP action requires IsPastorOrAdmin permission."""
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        response = api_client.post(
            f'/api/v1/events/events/{event.id}/rsvp/',
            {'status': RSVPStatus.CONFIRMED, 'guests': 2},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == RSVPStatus.CONFIRMED
        assert response.data['guests'] == 2

    def test_rsvp_update_existing(self, api_client, pastor_user):
        """Submitting RSVP again updates the existing record."""
        api_client.force_authenticate(user=pastor_user)
        member = pastor_user.member_profile
        event = EventFactory()
        EventRSVPFactory(event=event, member=member, status=RSVPStatus.PENDING, guests=0)

        response = api_client.post(
            f'/api/v1/events/events/{event.id}/rsvp/',
            {'status': RSVPStatus.CONFIRMED, 'guests': 3},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == RSVPStatus.CONFIRMED
        assert response.data['guests'] == 3

    def test_rsvp_default_status_and_guests(self, api_client, pastor_user):
        """Defaults to status=CONFIRMED and guests=0."""
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        response = api_client.post(
            f'/api/v1/events/events/{event.id}/rsvp/', {}, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == RSVPStatus.CONFIRMED
        assert response.data['guests'] == 0

    def test_rsvp_no_member_profile(self, api_client, staff_user_no_profile):
        """Staff without member profile gets 400."""
        api_client.force_authenticate(user=staff_user_no_profile)
        event = EventFactory()
        response = api_client.post(
            f'/api/v1/events/events/{event.id}/rsvp/', {}, format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'Profil membre requis'

    def test_rsvp_as_member_forbidden(self, api_client, member_user):
        """Regular member cannot access RSVP action due to IsPastorOrAdmin."""
        api_client.force_authenticate(user=member_user)
        event = EventFactory()
        response = api_client.post(
            f'/api/v1/events/events/{event.id}/rsvp/', {}, format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_rsvp_declined(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        response = api_client.post(
            f'/api/v1/events/events/{event.id}/rsvp/',
            {'status': RSVPStatus.DECLINED},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == RSVPStatus.DECLINED


class TestEventAttendees:

    def test_attendees_returns_confirmed_only(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        EventRSVPFactory(event=event, status=RSVPStatus.DECLINED)
        EventRSVPFactory(event=event, status=RSVPStatus.PENDING)

        response = api_client.get(f'/api/v1/events/events/{event.id}/attendees/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_attendees_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        event = EventFactory()
        response = api_client.get(f'/api/v1/events/events/{event.id}/attendees/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_attendees_empty_event(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        event = EventFactory()
        response = api_client.get(f'/api/v1/events/events/{event.id}/attendees/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestEventAccessNoProfile:
    """Tests using user_no_profile fixture (covers fixture line 38)."""

    def test_list_events_user_no_profile(self, api_client, user_no_profile):
        """User without member profile can list events (IsMember checks auth only)."""
        api_client.force_authenticate(user=user_no_profile)
        EventFactory()
        response = api_client.get('/api/v1/events/events/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
