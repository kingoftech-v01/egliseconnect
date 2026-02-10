"""Tests for attendance frontend views - targeting 99% coverage."""
import datetime
from unittest.mock import patch, MagicMock

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.attendance.models import AttendanceRecord, AttendanceSession, MemberQRCode
from apps.core.constants import (
    AttendanceSessionType,
    CheckInMethod,
    MembershipStatus,
    Roles,
)
from apps.members.tests.factories import MemberFactory, UserFactory
from apps.onboarding.models import TrainingCourse, Lesson, MemberTraining, ScheduledLesson

from .factories import AttendanceSessionFactory, MemberQRCodeFactory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return Client()


@pytest.fixture
def member_user():
    """Regular member with ACTIVE status (can use QR)."""
    user = UserFactory()
    member = MemberFactory(
        user=user,
        role=Roles.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
        registration_date=timezone.now(),
    )
    return user, member


@pytest.fixture
def admin_user():
    """Admin member."""
    user = UserFactory()
    member = MemberFactory(
        user=user,
        role=Roles.ADMIN,
        membership_status=MembershipStatus.ACTIVE,
        registration_date=timezone.now(),
    )
    return user, member


@pytest.fixture
def pastor_user():
    """Pastor member."""
    user = UserFactory()
    member = MemberFactory(
        user=user,
        role=Roles.PASTOR,
        membership_status=MembershipStatus.ACTIVE,
        registration_date=timezone.now(),
    )
    return user, member


@pytest.fixture
def group_leader_user():
    """Group leader member."""
    user = UserFactory()
    member = MemberFactory(
        user=user,
        role=Roles.GROUP_LEADER,
        membership_status=MembershipStatus.ACTIVE,
        registration_date=timezone.now(),
    )
    return user, member


@pytest.fixture
def user_no_member():
    """User with no member profile attached."""
    return UserFactory()


@pytest.fixture
def suspended_member_user():
    """Member with SUSPENDED status (cannot use QR)."""
    user = UserFactory()
    member = MemberFactory(
        user=user,
        role=Roles.MEMBER,
        membership_status=MembershipStatus.SUSPENDED,
        registration_date=timezone.now(),
    )
    return user, member


# ---------------------------------------------------------------------------
# my_qr view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMyQRView:
    url = reverse('frontend:attendance:my_qr')

    def test_login_required(self, client):
        resp = client.get(self.url)
        assert resp.status_code == 302
        assert '/accounts/login/' in resp.url or 'login' in resp.url

    def test_no_member_profile_redirects(self, client, user_no_member):
        client.force_login(user_no_member)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_suspended_member_cannot_use_qr(self, client, suspended_member_user):
        user, member = suspended_member_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_active_member_sees_qr(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert 'qr' in resp.context

    def test_creates_qr_if_not_exists(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        assert not MemberQRCode.objects.filter(member=member).exists()
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert MemberQRCode.objects.filter(member=member).exists()

    def test_regenerates_expired_qr(self, client, member_user):
        user, member = member_user
        qr = MemberQRCodeFactory(member=member)
        qr.expires_at = timezone.now() - datetime.timedelta(hours=1)
        qr.save()
        old_code = qr.code
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        qr.refresh_from_db()
        assert qr.code != old_code
        assert qr.is_valid

    def test_does_not_regenerate_valid_qr(self, client, member_user):
        user, member = member_user
        qr = MemberQRCodeFactory(member=member)
        old_code = qr.code
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        qr.refresh_from_db()
        assert qr.code == old_code


# ---------------------------------------------------------------------------
# scanner view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestScannerView:
    url = reverse('frontend:attendance:scanner')

    def test_login_required(self, client):
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_member):
        client.force_login(user_no_member)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_admin_can_access(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert 'active_sessions' in resp.context

    def test_pastor_can_access(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200

    def test_group_leader_can_access(self, client, group_leader_user):
        user, _ = group_leader_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200

    def test_shows_todays_open_sessions(self, client, admin_user):
        user, _ = admin_user
        today_open = AttendanceSessionFactory(
            date=timezone.now().date(), is_open=True
        )
        today_closed = AttendanceSessionFactory(
            date=timezone.now().date(), is_open=False
        )
        yesterday_open = AttendanceSessionFactory(
            date=timezone.now().date() - datetime.timedelta(days=1), is_open=True
        )
        client.force_login(user)
        resp = client.get(self.url)
        sessions = list(resp.context['active_sessions'])
        assert today_open in sessions
        assert today_closed not in sessions
        assert yesterday_open not in sessions


# ---------------------------------------------------------------------------
# create_session view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateSessionView:
    url = reverse('frontend:attendance:create_session')

    def test_login_required(self, client):
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_member):
        client.force_login(user_no_member)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_group_leader_denied(self, client, group_leader_user):
        user, _ = group_leader_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_admin_get_shows_form(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert 'session_types' in resp.context

    def test_pastor_get_shows_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200

    def test_post_creates_session(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        resp = client.post(self.url, {
            'name': 'Culte du dimanche',
            'session_type': AttendanceSessionType.WORSHIP,
        })
        assert resp.status_code == 302
        session = AttendanceSession.objects.get(name='Culte du dimanche')
        assert session.opened_by == member
        assert session.date == timezone.now().date()

    def test_post_empty_name_does_not_create(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        count_before = AttendanceSession.objects.count()
        resp = client.post(self.url, {
            'name': '',
            'session_type': AttendanceSessionType.WORSHIP,
        })
        assert resp.status_code == 200
        assert AttendanceSession.objects.count() == count_before

    def test_post_redirects_to_scanner(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.post(self.url, {
            'name': 'Test Session',
            'session_type': AttendanceSessionType.EVENT,
        })
        assert resp.status_code == 302
        assert 'scanner' in resp.url


# ---------------------------------------------------------------------------
# process_checkin view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProcessCheckinView:
    url = reverse('frontend:attendance:process_checkin')

    def test_login_required(self, client):
        resp = client.post(self.url)
        assert resp.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_member):
        client.force_login(user_no_member)
        resp = client.post(self.url)
        assert resp.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        resp = client.post(self.url)
        assert resp.status_code == 302

    def test_get_redirects_to_scanner(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302
        assert 'scanner' in resp.url

    def test_missing_qr_code_or_session(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.post(self.url, {'qr_code': '', 'session_id': ''})
        assert resp.status_code == 302

    def test_invalid_qr_code(self, client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': 'INVALID-CODE',
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302

    def test_expired_qr_code(self, client, admin_user):
        user, _ = admin_user
        qr = MemberQRCodeFactory()
        qr.expires_at = timezone.now() - datetime.timedelta(hours=1)
        qr.save()
        session = AttendanceSessionFactory()
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        assert AttendanceRecord.objects.count() == 0

    def test_closed_session(self, client, admin_user):
        user, _ = admin_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory(is_open=False)
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        assert AttendanceRecord.objects.count() == 0

    def test_successful_checkin(self, client, admin_user):
        user, admin_member = admin_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        record = AttendanceRecord.objects.get(
            session=session, member=qr.member
        )
        assert record.checked_in_by == admin_member
        assert record.method == CheckInMethod.QR_SCAN

    def test_duplicate_checkin(self, client, admin_user):
        user, _ = admin_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        # First checkin
        AttendanceRecord.objects.create(
            session=session,
            member=qr.member,
            method=CheckInMethod.QR_SCAN,
        )
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        # Still only 1 record
        assert AttendanceRecord.objects.filter(
            session=session, member=qr.member
        ).count() == 1

    @patch('apps.onboarding.services.OnboardingService.mark_lesson_attended')
    def test_marks_lesson_if_linked(self, mock_mark, client, admin_user):
        user, admin_member = admin_user
        qr = MemberQRCodeFactory()
        # Create a real ScheduledLesson
        course = TrainingCourse.objects.create(name='Test Course')
        lesson = Lesson.objects.create(course=course, order=1, title='Lesson 1')
        training = MemberTraining.objects.create(
            member=qr.member, course=course, assigned_by=admin_member
        )
        scheduled = ScheduledLesson.objects.create(
            training=training, lesson=lesson, scheduled_date=timezone.now()
        )
        session = AttendanceSessionFactory(scheduled_lesson=scheduled)

        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        mock_mark.assert_called_once_with(
            scheduled, admin_member
        )

    @patch('apps.onboarding.services.OnboardingService.mark_lesson_attended')
    def test_no_lesson_marking_when_no_scheduled_lesson(self, mock_mark, client, admin_user):
        user, _ = admin_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        assert session.scheduled_lesson is None
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        mock_mark.assert_not_called()

    def test_group_leader_can_checkin(self, client, group_leader_user):
        user, leader_member = group_leader_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        assert AttendanceRecord.objects.filter(
            session=session, member=qr.member
        ).exists()

    def test_pastor_can_checkin(self, client, pastor_user):
        user, _ = pastor_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        client.force_login(user)
        resp = client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == 302
        assert AttendanceRecord.objects.filter(
            session=session, member=qr.member
        ).exists()

    def test_missing_only_session_id(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.post(self.url, {'qr_code': 'some-code', 'session_id': ''})
        assert resp.status_code == 302

    def test_missing_only_qr_code(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.post(self.url, {'qr_code': '', 'session_id': 'some-id'})
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# session_list view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSessionListView:
    url = reverse('frontend:attendance:session_list')

    def test_login_required(self, client):
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_member):
        client.force_login(user_no_member)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_group_leader_denied(self, client, group_leader_user):
        user, _ = group_leader_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_admin_can_access(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert 'sessions' in resp.context

    def test_pastor_can_access(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200

    def test_lists_all_sessions(self, client, admin_user):
        user, _ = admin_user
        s1 = AttendanceSessionFactory()
        s2 = AttendanceSessionFactory()
        client.force_login(user)
        resp = client.get(self.url)
        sessions = list(resp.context['sessions'])
        assert s1 in sessions
        assert s2 in sessions


# ---------------------------------------------------------------------------
# session_detail view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSessionDetailView:

    def test_login_required(self, client):
        session = AttendanceSessionFactory()
        url = reverse('frontend:attendance:session_detail', args=[session.pk])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_member):
        session = AttendanceSessionFactory()
        url = reverse('frontend:attendance:session_detail', args=[session.pk])
        client.force_login(user_no_member)
        resp = client.get(url)
        assert resp.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        session = AttendanceSessionFactory()
        url = reverse('frontend:attendance:session_detail', args=[session.pk])
        client.force_login(user)
        resp = client.get(url)
        assert resp.status_code == 302

    def test_admin_can_view(self, client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        url = reverse('frontend:attendance:session_detail', args=[session.pk])
        client.force_login(user)
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context['session'] == session

    def test_pastor_can_view(self, client, pastor_user):
        user, _ = pastor_user
        session = AttendanceSessionFactory()
        url = reverse('frontend:attendance:session_detail', args=[session.pk])
        client.force_login(user)
        resp = client.get(url)
        assert resp.status_code == 200

    def test_shows_records(self, client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        member = MemberFactory(registration_date=timezone.now())
        record = AttendanceRecord.objects.create(
            session=session,
            member=member,
            method=CheckInMethod.QR_SCAN,
        )
        url = reverse('frontend:attendance:session_detail', args=[session.pk])
        client.force_login(user)
        resp = client.get(url)
        assert record in list(resp.context['attendance_records'])

    def test_nonexistent_session_404(self, client, admin_user):
        import uuid
        user, _ = admin_user
        url = reverse('frontend:attendance:session_detail', args=[uuid.uuid4()])
        client.force_login(user)
        resp = client.get(url)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# my_history view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMyHistoryView:
    url = reverse('frontend:attendance:my_history')

    def test_login_required(self, client):
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_member):
        client.force_login(user_no_member)
        resp = client.get(self.url)
        assert resp.status_code == 302

    def test_member_can_see_own_history(self, client, member_user):
        user, member = member_user
        session = AttendanceSessionFactory()
        record = AttendanceRecord.objects.create(
            session=session,
            member=member,
            method=CheckInMethod.QR_SCAN,
        )
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert record in list(resp.context['attendance_records'])
        assert resp.context['member'] == member

    def test_does_not_show_other_members_records(self, client, member_user):
        user, member = member_user
        other_member = MemberFactory(registration_date=timezone.now())
        session = AttendanceSessionFactory()
        other_record = AttendanceRecord.objects.create(
            session=session,
            member=other_member,
            method=CheckInMethod.QR_SCAN,
        )
        client.force_login(user)
        resp = client.get(self.url)
        assert other_record not in list(resp.context['attendance_records'])

    def test_empty_history(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert len(resp.context['attendance_records']) == 0

    def test_admin_sees_own_history(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        resp = client.get(self.url)
        assert resp.status_code == 200
        assert resp.context['member'] == member
