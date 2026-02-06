"""Tests for volunteers API views."""
import pytest
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.constants import (
    Roles, VolunteerRole, ScheduleStatus, VolunteerFrequency,
)
from apps.members.tests.factories import UserFactory, MemberWithUserFactory
from apps.events.tests.factories import EventFactory
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory,
    VolunteerAvailabilityFactory,
    VolunteerScheduleFactory,
    SwapRequestFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user():
    member = MemberWithUserFactory(role=Roles.MEMBER)
    return member.user


@pytest.fixture
def pastor_user():
    member = MemberWithUserFactory(role=Roles.PASTOR)
    return member.user


@pytest.fixture
def user_no_profile():
    return UserFactory()


@pytest.fixture
def staff_user_no_profile():
    return UserFactory(is_staff=True)


class TestVolunteerPositionList:

    def test_list_authenticated(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        VolunteerPositionFactory.create_batch(3)
        response = api_client.get('/api/v1/volunteers/positions/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_list_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/volunteers/positions/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_by_role_type(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        VolunteerPositionFactory(role_type=VolunteerRole.WORSHIP)
        VolunteerPositionFactory(role_type=VolunteerRole.TECHNICAL)
        response = api_client.get(
            '/api/v1/volunteers/positions/',
            {'role_type': VolunteerRole.WORSHIP},
        )
        assert response.data['count'] == 1

    def test_search_by_name(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        VolunteerPositionFactory(name='Pianist')
        VolunteerPositionFactory(name='Sound Tech')
        response = api_client.get(
            '/api/v1/volunteers/positions/', {'search': 'Pianist'}
        )
        assert response.data['count'] == 1


class TestVolunteerPositionRetrieve:

    def test_retrieve_authenticated(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        position = VolunteerPositionFactory()
        response = api_client.get(f'/api/v1/volunteers/positions/{position.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == position.name
        assert 'role_type_display' in response.data

    def test_retrieve_unauthenticated(self, api_client):
        position = VolunteerPositionFactory()
        response = api_client.get(f'/api/v1/volunteers/positions/{position.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerPositionCreate:

    def test_create_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        data = {
            'name': 'New Position',
            'role_type': VolunteerRole.HOSPITALITY,
            'description': 'Welcome guests',
            'min_volunteers': 2,
        }
        response = api_client.post(
            '/api/v1/volunteers/positions/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Position'

    def test_create_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        data = {
            'name': 'Blocked',
            'role_type': VolunteerRole.WORSHIP,
            'min_volunteers': 1,
        }
        response = api_client.post(
            '/api/v1/volunteers/positions/', data, format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerPositionUpdate:

    def test_update_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        position = VolunteerPositionFactory(name='Old Name')
        response = api_client.patch(
            f'/api/v1/volunteers/positions/{position.id}/',
            {'name': 'New Name'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'New Name'

    def test_update_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        position = VolunteerPositionFactory()
        response = api_client.patch(
            f'/api/v1/volunteers/positions/{position.id}/',
            {'name': 'Nope'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerPositionDelete:

    def test_delete_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        position = VolunteerPositionFactory()
        response = api_client.delete(
            f'/api/v1/volunteers/positions/{position.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        position = VolunteerPositionFactory()
        response = api_client.delete(
            f'/api/v1/volunteers/positions/{position.id}/'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerScheduleList:

    def test_list_authenticated(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        VolunteerScheduleFactory.create_batch(2)
        response = api_client.get('/api/v1/volunteers/schedules/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_list_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/volunteers/schedules/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_by_status(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        VolunteerScheduleFactory(status=ScheduleStatus.SCHEDULED)
        VolunteerScheduleFactory(status=ScheduleStatus.CONFIRMED)
        response = api_client.get(
            '/api/v1/volunteers/schedules/',
            {'status': ScheduleStatus.SCHEDULED},
        )
        assert response.data['count'] == 1

    def test_ordering_by_date(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        today = timezone.now().date()
        VolunteerScheduleFactory(date=today + timedelta(days=10))
        VolunteerScheduleFactory(date=today + timedelta(days=1))
        response = api_client.get(
            '/api/v1/volunteers/schedules/', {'ordering': 'date'}
        )
        dates = [r['date'] for r in response.data['results']]
        assert dates == sorted(dates)


class TestVolunteerScheduleRetrieve:

    def test_retrieve_authenticated(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        schedule = VolunteerScheduleFactory()
        response = api_client.get(
            f'/api/v1/volunteers/schedules/{schedule.id}/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'member_name' in response.data
        assert 'position_name' in response.data
        assert 'status_display' in response.data


class TestVolunteerScheduleCreate:

    def test_create_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        member = MemberWithUserFactory()
        position = VolunteerPositionFactory()
        data = {
            'member': str(member.id),
            'position': str(position.id),
            'date': (timezone.now().date() + timedelta(days=7)).isoformat(),
            'status': ScheduleStatus.SCHEDULED,
        }
        response = api_client.post(
            '/api/v1/volunteers/schedules/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        position = VolunteerPositionFactory()
        data = {
            'member': str(member_user.member_profile.id),
            'position': str(position.id),
            'date': (timezone.now().date() + timedelta(days=7)).isoformat(),
        }
        response = api_client.post(
            '/api/v1/volunteers/schedules/', data, format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerScheduleMySchedule:

    def test_my_schedule_returns_own_schedules(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        VolunteerScheduleFactory(member=member)
        VolunteerScheduleFactory(member=member)
        VolunteerScheduleFactory()  # another member's schedule

        response = api_client.get('/api/v1/volunteers/schedules/my-schedule/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_my_schedule_no_member_profile(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        response = api_client.get('/api/v1/volunteers/schedules/my-schedule/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'Profil requis'

    def test_my_schedule_empty(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        response = api_client.get('/api/v1/volunteers/schedules/my-schedule/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestVolunteerScheduleConfirm:

    def test_confirm_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        schedule = VolunteerScheduleFactory(status=ScheduleStatus.SCHEDULED)
        response = api_client.post(
            f'/api/v1/volunteers/schedules/{schedule.id}/confirm/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == ScheduleStatus.CONFIRMED

    def test_confirm_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        schedule = VolunteerScheduleFactory()
        response = api_client.post(
            f'/api/v1/volunteers/schedules/{schedule.id}/confirm/'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerScheduleUpdateDelete:

    def test_update_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        schedule = VolunteerScheduleFactory()
        response = api_client.patch(
            f'/api/v1/volunteers/schedules/{schedule.id}/',
            {'notes': 'Updated note'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['notes'] == 'Updated note'

    def test_delete_as_pastor(self, api_client, pastor_user):
        api_client.force_authenticate(user=pastor_user)
        schedule = VolunteerScheduleFactory()
        response = api_client.delete(
            f'/api/v1/volunteers/schedules/{schedule.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_update_as_member_forbidden(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        schedule = VolunteerScheduleFactory()
        response = api_client.patch(
            f'/api/v1/volunteers/schedules/{schedule.id}/',
            {'notes': 'nope'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerAvailabilityList:

    def test_staff_sees_all(self, api_client, staff_user_no_profile):
        api_client.force_authenticate(user=staff_user_no_profile)
        VolunteerAvailabilityFactory.create_batch(3)
        response = api_client.get('/api/v1/volunteers/availability/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_member_sees_only_own(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        VolunteerAvailabilityFactory(member=member)
        VolunteerAvailabilityFactory()
        VolunteerAvailabilityFactory()
        response = api_client.get('/api/v1/volunteers/availability/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_user_no_profile_sees_empty(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        VolunteerAvailabilityFactory.create_batch(2)
        response = api_client.get('/api/v1/volunteers/availability/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/volunteers/availability/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVolunteerAvailabilityCRUD:

    def test_create(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        position = VolunteerPositionFactory()
        data = {
            'member': str(member_user.member_profile.id),
            'position': str(position.id),
            'is_available': True,
            'frequency': VolunteerFrequency.WEEKLY,
        }
        response = api_client.post(
            '/api/v1/volunteers/availability/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        avail = VolunteerAvailabilityFactory(member=member_user.member_profile)
        response = api_client.get(
            f'/api/v1/volunteers/availability/{avail.id}/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'member_name' in response.data
        assert 'position_name' in response.data

    def test_update(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        avail = VolunteerAvailabilityFactory(member=member_user.member_profile)
        response = api_client.patch(
            f'/api/v1/volunteers/availability/{avail.id}/',
            {'is_available': False},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_available'] is False

    def test_delete(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        avail = VolunteerAvailabilityFactory(member=member_user.member_profile)
        response = api_client.delete(
            f'/api/v1/volunteers/availability/{avail.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestSwapRequestList:

    def test_staff_sees_all(self, api_client, staff_user_no_profile):
        api_client.force_authenticate(user=staff_user_no_profile)
        SwapRequestFactory.create_batch(3)
        response = api_client.get('/api/v1/volunteers/swap-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_member_sees_own_requested(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        SwapRequestFactory(requested_by=member)
        SwapRequestFactory()
        response = api_client.get('/api/v1/volunteers/swap-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_member_sees_swap_with_them(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        SwapRequestFactory(swap_with=member)
        SwapRequestFactory()
        response = api_client.get('/api/v1/volunteers/swap-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_member_sees_both_requested_and_swap_with(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        SwapRequestFactory(requested_by=member)
        SwapRequestFactory(swap_with=member)
        SwapRequestFactory()
        response = api_client.get('/api/v1/volunteers/swap-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_user_no_profile_sees_empty(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        SwapRequestFactory.create_batch(2)
        response = api_client.get('/api/v1/volunteers/swap-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/volunteers/swap-requests/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSwapRequestCRUD:

    def test_create(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        schedule = VolunteerScheduleFactory(member=member)
        swap_member = MemberWithUserFactory()
        data = {
            'original_schedule': str(schedule.id),
            'requested_by': str(member.id),
            'swap_with': str(swap_member.id),
            'status': 'pending',
            'reason': 'Schedule conflict',
        }
        response = api_client.post(
            '/api/v1/volunteers/swap-requests/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'

    def test_retrieve(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        swap = SwapRequestFactory(requested_by=member)
        response = api_client.get(
            f'/api/v1/volunteers/swap-requests/{swap.id}/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'requested_by_name' in response.data

    def test_update(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        swap = SwapRequestFactory(requested_by=member, status='pending')
        response = api_client.patch(
            f'/api/v1/volunteers/swap-requests/{swap.id}/',
            {'reason': 'Updated reason'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['reason'] == 'Updated reason'

    def test_delete(self, api_client, member_user):
        api_client.force_authenticate(user=member_user)
        member = member_user.member_profile
        swap = SwapRequestFactory(requested_by=member)
        response = api_client.delete(
            f'/api/v1/volunteers/swap-requests/{swap.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
