"""Tests for volunteers frontend views."""
import pytest

from django.test import Client

from apps.core.constants import Roles, VolunteerFrequency
from apps.members.tests.factories import UserFactory, MemberWithUserFactory
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory,
    VolunteerScheduleFactory,
    VolunteerAvailabilityFactory,
)
from apps.volunteers.models import VolunteerAvailability

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


class TestPositionList:

    def test_authenticated_access(self, client, member_user):
        client.force_login(member_user)
        VolunteerPositionFactory.create_batch(3)
        response = client.get('/volunteers/positions/')
        assert response.status_code == 200

    def test_context_contains_positions(self, client, member_user):
        client.force_login(member_user)
        VolunteerPositionFactory(name='Sound Tech')
        response = client.get('/volunteers/positions/')
        positions = list(response.context['positions'])
        assert len(positions) == 1
        assert positions[0].name == 'Sound Tech'

    def test_context_has_page_title(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/positions/')
        assert 'page_title' in response.context

    def test_only_active_positions_shown(self, client, member_user):
        client.force_login(member_user)
        VolunteerPositionFactory(is_active=True)
        VolunteerPositionFactory(is_active=False)
        response = client.get('/volunteers/positions/')
        positions = list(response.context['positions'])
        assert len(positions) == 1

    def test_unauthenticated_redirects(self, client):
        response = client.get('/volunteers/positions/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


class TestScheduleList:

    def test_authenticated_access(self, client, member_user):
        client.force_login(member_user)
        VolunteerScheduleFactory.create_batch(2)
        response = client.get('/volunteers/schedule/')
        assert response.status_code == 200

    def test_context_contains_schedules(self, client, member_user):
        client.force_login(member_user)
        VolunteerScheduleFactory()
        response = client.get('/volunteers/schedule/')
        schedules = list(response.context['schedules'])
        assert len(schedules) == 1

    def test_context_has_page_title(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/schedule/')
        assert 'page_title' in response.context

    def test_only_active_schedules_shown(self, client, member_user):
        client.force_login(member_user)
        VolunteerScheduleFactory(is_active=True)
        VolunteerScheduleFactory(is_active=False)
        response = client.get('/volunteers/schedule/')
        schedules = list(response.context['schedules'])
        assert len(schedules) == 1

    def test_unauthenticated_redirects(self, client):
        response = client.get('/volunteers/schedule/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


class TestMySchedule:

    def test_with_member_profile(self, client, member_user):
        client.force_login(member_user)
        member = member_user.member_profile
        VolunteerScheduleFactory(member=member)
        VolunteerScheduleFactory()  # another member's schedule
        response = client.get('/volunteers/my-schedule/')
        assert response.status_code == 200
        schedules = list(response.context['schedules'])
        assert len(schedules) == 1

    def test_context_has_page_title(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/my-schedule/')
        assert 'page_title' in response.context

    def test_without_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get('/volunteers/my-schedule/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get('/volunteers/my-schedule/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


class TestAvailabilityUpdate:

    def test_get_with_member_profile(self, client, member_user):
        client.force_login(member_user)
        VolunteerPositionFactory.create_batch(2)
        response = client.get('/volunteers/availability/')
        assert response.status_code == 200
        assert 'positions' in response.context
        assert 'availabilities' in response.context
        assert 'page_title' in response.context

    def test_get_shows_existing_availabilities(self, client, member_user):
        client.force_login(member_user)
        member = member_user.member_profile
        position = VolunteerPositionFactory()
        avail = VolunteerAvailabilityFactory(member=member, position=position)
        response = client.get('/volunteers/availability/')
        availabilities_map = response.context['availabilities']
        assert position.id in availabilities_map
        assert availabilities_map[position.id] == avail

    def test_post_creates_availability(self, client, member_user):
        client.force_login(member_user)
        pos1 = VolunteerPositionFactory()
        pos2 = VolunteerPositionFactory()

        response = client.post('/volunteers/availability/', {
            f'position_{pos1.id}': 'on',
            f'frequency_{pos1.id}': VolunteerFrequency.WEEKLY,
            f'frequency_{pos2.id}': VolunteerFrequency.MONTHLY,
        })
        assert response.status_code == 302

        member = member_user.member_profile
        avail1 = VolunteerAvailability.objects.get(member=member, position=pos1)
        assert avail1.is_available is True
        assert avail1.frequency == VolunteerFrequency.WEEKLY

        avail2 = VolunteerAvailability.objects.get(member=member, position=pos2)
        assert avail2.is_available is False
        assert avail2.frequency == VolunteerFrequency.MONTHLY

    def test_post_updates_existing_availability(self, client, member_user):
        client.force_login(member_user)
        member = member_user.member_profile
        position = VolunteerPositionFactory()
        VolunteerAvailabilityFactory(
            member=member,
            position=position,
            is_available=False,
            frequency=VolunteerFrequency.MONTHLY,
        )

        response = client.post('/volunteers/availability/', {
            f'position_{position.id}': 'on',
            f'frequency_{position.id}': VolunteerFrequency.WEEKLY,
        })
        assert response.status_code == 302

        avail = VolunteerAvailability.objects.get(member=member, position=position)
        assert avail.is_available is True
        assert avail.frequency == VolunteerFrequency.WEEKLY

    def test_post_redirects_to_my_schedule(self, client, member_user):
        client.force_login(member_user)
        response = client.post('/volunteers/availability/', {})
        assert response.status_code == 302
        assert 'my-schedule' in response.url

    def test_post_default_frequency(self, client, member_user):
        """Missing frequency defaults to 'monthly'."""
        client.force_login(member_user)
        position = VolunteerPositionFactory()
        response = client.post('/volunteers/availability/', {})
        assert response.status_code == 302
        member = member_user.member_profile
        avail = VolunteerAvailability.objects.get(member=member, position=position)
        assert avail.frequency == 'monthly'

    def test_without_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get('/volunteers/availability/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_post_without_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.post('/volunteers/availability/', {})
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get('/volunteers/availability/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
