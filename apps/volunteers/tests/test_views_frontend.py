"""Tests for volunteers frontend views."""
import pytest

from django.test import Client

from apps.core.constants import Roles, VolunteerFrequency
from apps.members.tests.factories import UserFactory, MemberWithUserFactory
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory,
    VolunteerScheduleFactory,
    VolunteerAvailabilityFactory,
    PlannedAbsenceFactory,
)
from apps.volunteers.models import VolunteerAvailability, PlannedAbsence

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


class TestPlannedAbsenceList:

    def test_authenticated_access(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/planned-absences/')
        assert response.status_code == 200

    def test_context_has_absences_and_title(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/planned-absences/')
        assert 'absences' in response.context
        assert 'page_title' in response.context

    def test_regular_member_sees_own_absences_only(self, client, member_user):
        client.force_login(member_user)
        member = member_user.member_profile
        own = PlannedAbsenceFactory(member=member)
        other = PlannedAbsenceFactory()  # another member
        response = client.get('/volunteers/planned-absences/')
        absences = list(response.context['absences'])
        assert len(absences) == 1
        assert absences[0].member == member

    def test_admin_sees_all_absences(self, client):
        admin_member = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin_member.user)
        PlannedAbsenceFactory.create_batch(3)
        response = client.get('/volunteers/planned-absences/')
        absences = list(response.context['absences'])
        assert len(absences) == 3

    def test_without_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get('/volunteers/planned-absences/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get('/volunteers/planned-absences/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


class TestPlannedAbsenceCreate:

    def test_get_form(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/planned-absences/create/')
        assert response.status_code == 200
        assert 'page_title' in response.context

    def test_post_creates_absence(self, client, member_user):
        client.force_login(member_user)
        response = client.post('/volunteers/planned-absences/create/', {
            'start_date': '2026-03-01',
            'end_date': '2026-03-07',
            'reason': 'Vacances',
        })
        assert response.status_code == 302
        assert '/volunteers/planned-absences/' in response.url
        absence = PlannedAbsence.objects.get(member=member_user.member_profile)
        assert str(absence.start_date) == '2026-03-01'
        assert str(absence.end_date) == '2026-03-07'
        assert absence.reason == 'Vacances'

    def test_post_missing_dates_shows_error(self, client, member_user):
        client.force_login(member_user)
        response = client.post('/volunteers/planned-absences/create/', {
            'start_date': '',
            'end_date': '',
        })
        assert response.status_code == 200
        assert PlannedAbsence.objects.count() == 0

    def test_post_end_before_start_shows_error(self, client, member_user):
        client.force_login(member_user)
        response = client.post('/volunteers/planned-absences/create/', {
            'start_date': '2026-03-10',
            'end_date': '2026-03-01',
        })
        assert response.status_code == 200
        assert PlannedAbsence.objects.count() == 0

    def test_without_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get('/volunteers/planned-absences/create/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get('/volunteers/planned-absences/create/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.fixture
def admin_user():
    member = MemberWithUserFactory(role=Roles.ADMIN)
    return member.user


@pytest.fixture
def pastor_user():
    member = MemberWithUserFactory(role=Roles.PASTOR)
    return member.user


class TestPositionCreate:

    def test_login_required(self, client):
        response = client.get('/volunteers/positions/create/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get('/volunteers/positions/create/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_denied(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/positions/create/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_get_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/volunteers/positions/create/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_pastor_get_shows_form(self, client, pastor_user):
        client.force_login(pastor_user)
        response = client.get('/volunteers/positions/create/')
        assert response.status_code == 200

    def test_post_creates_position(self, client, admin_user):
        from apps.core.constants import VolunteerRole
        client.force_login(admin_user)
        response = client.post('/volunteers/positions/create/', {
            'name': 'Technicien son',
            'role_type': VolunteerRole.TECHNICAL,
            'min_volunteers': 2,
        })
        assert response.status_code == 302
        assert response.url == '/volunteers/positions/'
        from apps.volunteers.models import VolunteerPosition
        assert VolunteerPosition.objects.filter(name='Technicien son').exists()

    def test_post_invalid_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post('/volunteers/positions/create/', {
            'name': '',
            'role_type': '',
        })
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_context_has_page_title(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/volunteers/positions/create/')
        assert 'page_title' in response.context


class TestPositionUpdate:

    def test_login_required(self, client):
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/edit/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/edit/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_denied(self, client, member_user):
        client.force_login(member_user)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/edit/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_get_shows_form_with_instance(self, client, admin_user):
        client.force_login(admin_user)
        position = VolunteerPositionFactory(name='Original')
        response = client.get(f'/volunteers/positions/{position.pk}/edit/')
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['position'] == position

    def test_pastor_get_shows_form(self, client, pastor_user):
        client.force_login(pastor_user)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/edit/')
        assert response.status_code == 200

    def test_post_updates_position(self, client, admin_user):
        from apps.core.constants import VolunteerRole
        client.force_login(admin_user)
        position = VolunteerPositionFactory(name='Old Name')
        response = client.post(f'/volunteers/positions/{position.pk}/edit/', {
            'name': 'New Name',
            'role_type': VolunteerRole.WORSHIP,
            'min_volunteers': 1,
        })
        assert response.status_code == 302
        assert response.url == '/volunteers/positions/'
        position.refresh_from_db()
        assert position.name == 'New Name'

    def test_post_invalid_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        position = VolunteerPositionFactory()
        response = client.post(f'/volunteers/positions/{position.pk}/edit/', {
            'name': '',
        })
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_404_for_nonexistent_position(self, client, admin_user):
        import uuid
        client.force_login(admin_user)
        response = client.get(f'/volunteers/positions/{uuid.uuid4()}/edit/')
        assert response.status_code == 404


class TestPositionDelete:

    def test_login_required(self, client):
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/delete/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/delete/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_denied(self, client, member_user):
        client.force_login(member_user)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/delete/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_get_shows_confirmation(self, client, admin_user):
        client.force_login(admin_user)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/delete/')
        assert response.status_code == 200
        assert response.context['position'] == position

    def test_pastor_get_shows_confirmation(self, client, pastor_user):
        client.force_login(pastor_user)
        position = VolunteerPositionFactory()
        response = client.get(f'/volunteers/positions/{position.pk}/delete/')
        assert response.status_code == 200

    def test_post_deletes_position(self, client, admin_user):
        client.force_login(admin_user)
        position = VolunteerPositionFactory()
        pk = position.pk
        response = client.post(f'/volunteers/positions/{pk}/delete/')
        assert response.status_code == 302
        assert response.url == '/volunteers/positions/'
        from apps.volunteers.models import VolunteerPosition
        assert not VolunteerPosition.all_objects.filter(pk=pk).exists()

    def test_get_does_not_delete(self, client, admin_user):
        client.force_login(admin_user)
        position = VolunteerPositionFactory()
        client.get(f'/volunteers/positions/{position.pk}/delete/')
        from apps.volunteers.models import VolunteerPosition
        assert VolunteerPosition.objects.filter(pk=position.pk).exists()

    def test_404_for_nonexistent_position(self, client, admin_user):
        import uuid
        client.force_login(admin_user)
        response = client.get(f'/volunteers/positions/{uuid.uuid4()}/delete/')
        assert response.status_code == 404


class TestScheduleCreate:

    def test_login_required(self, client):
        response = client.get('/volunteers/schedule/create/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get('/volunteers/schedule/create/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_denied(self, client, member_user):
        client.force_login(member_user)
        response = client.get('/volunteers/schedule/create/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_get_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/volunteers/schedule/create/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_pastor_get_shows_form(self, client, pastor_user):
        client.force_login(pastor_user)
        response = client.get('/volunteers/schedule/create/')
        assert response.status_code == 200

    def test_post_creates_schedule(self, client, admin_user):
        from apps.core.constants import ScheduleStatus
        from apps.members.tests.factories import MemberFactory
        client.force_login(admin_user)
        member = MemberFactory()
        position = VolunteerPositionFactory()
        response = client.post('/volunteers/schedule/create/', {
            'member': str(member.pk),
            'position': str(position.pk),
            'date': '2026-04-01',
            'status': ScheduleStatus.SCHEDULED,
        })
        assert response.status_code == 302
        assert response.url == '/volunteers/schedule/'
        from apps.volunteers.models import VolunteerSchedule
        assert VolunteerSchedule.objects.filter(member=member, position=position).exists()

    def test_post_invalid_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post('/volunteers/schedule/create/', {
            'member': '',
            'position': '',
            'date': '',
        })
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_context_has_page_title(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/volunteers/schedule/create/')
        assert 'page_title' in response.context


class TestScheduleUpdate:

    def test_login_required(self, client):
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/edit/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/edit/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_denied(self, client, member_user):
        client.force_login(member_user)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/edit/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_get_shows_form_with_instance(self, client, admin_user):
        client.force_login(admin_user)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/edit/')
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['schedule'] == schedule

    def test_pastor_get_shows_form(self, client, pastor_user):
        client.force_login(pastor_user)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/edit/')
        assert response.status_code == 200

    def test_post_updates_schedule(self, client, admin_user):
        from apps.core.constants import ScheduleStatus
        client.force_login(admin_user)
        schedule = VolunteerScheduleFactory()
        response = client.post(f'/volunteers/schedule/{schedule.pk}/edit/', {
            'member': str(schedule.member.pk),
            'position': str(schedule.position.pk),
            'date': '2026-05-01',
            'status': ScheduleStatus.CONFIRMED,
            'notes': 'Updated',
        })
        assert response.status_code == 302
        assert response.url == '/volunteers/schedule/'
        schedule.refresh_from_db()
        assert str(schedule.date) == '2026-05-01'
        assert schedule.notes == 'Updated'

    def test_post_invalid_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        schedule = VolunteerScheduleFactory()
        response = client.post(f'/volunteers/schedule/{schedule.pk}/edit/', {
            'member': '',
            'date': '',
        })
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_404_for_nonexistent_schedule(self, client, admin_user):
        import uuid
        client.force_login(admin_user)
        response = client.get(f'/volunteers/schedule/{uuid.uuid4()}/edit/')
        assert response.status_code == 404


class TestScheduleDelete:

    def test_login_required(self, client):
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/delete/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/delete/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_denied(self, client, member_user):
        client.force_login(member_user)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/delete/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_get_shows_confirmation(self, client, admin_user):
        client.force_login(admin_user)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/delete/')
        assert response.status_code == 200
        assert response.context['schedule'] == schedule

    def test_pastor_get_shows_confirmation(self, client, pastor_user):
        client.force_login(pastor_user)
        schedule = VolunteerScheduleFactory()
        response = client.get(f'/volunteers/schedule/{schedule.pk}/delete/')
        assert response.status_code == 200

    def test_post_deletes_schedule(self, client, admin_user):
        client.force_login(admin_user)
        schedule = VolunteerScheduleFactory()
        pk = schedule.pk
        response = client.post(f'/volunteers/schedule/{pk}/delete/')
        assert response.status_code == 302
        assert response.url == '/volunteers/schedule/'
        from apps.volunteers.models import VolunteerSchedule
        assert not VolunteerSchedule.all_objects.filter(pk=pk).exists()

    def test_get_does_not_delete(self, client, admin_user):
        client.force_login(admin_user)
        schedule = VolunteerScheduleFactory()
        client.get(f'/volunteers/schedule/{schedule.pk}/delete/')
        from apps.volunteers.models import VolunteerSchedule
        assert VolunteerSchedule.objects.filter(pk=schedule.pk).exists()

    def test_404_for_nonexistent_schedule(self, client, admin_user):
        import uuid
        client.force_login(admin_user)
        response = client.get(f'/volunteers/schedule/{uuid.uuid4()}/delete/')
        assert response.status_code == 404
