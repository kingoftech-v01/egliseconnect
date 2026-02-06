"""Tests for attendance API views - targeting 99% coverage."""
import datetime
from unittest.mock import patch, MagicMock

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.attendance.models import AttendanceRecord, AttendanceSession, MemberQRCode
from apps.core.constants import (
    AttendanceSessionType,
    CheckInMethod,
    MembershipStatus,
    Roles,
)
from apps.members.tests.factories import MemberFactory, UserFactory
from apps.onboarding.models import TrainingCourse, Lesson, MemberTraining, ScheduledLesson

from .factories import (
    AbsenceAlertFactory,
    AttendanceRecordFactory,
    AttendanceSessionFactory,
    MemberQRCodeFactory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user():
    """Regular member with ACTIVE status."""
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
def user_no_member():
    """User without a member profile."""
    return UserFactory()


# ---------------------------------------------------------------------------
# MemberQRCodeViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMemberQRCodeViewSet:
    list_url = reverse('v1:attendance:qr-list')
    regenerate_url = reverse('v1:attendance:qr-regenerate')

    # -- list --

    def test_list_unauthenticated(self, api_client):
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_returns_own_qr_only(self, api_client, member_user):
        user, member = member_user
        qr = MemberQRCodeFactory(member=member)
        other_qr = MemberQRCodeFactory()  # another member's QR
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in resp.data['results']]
        assert str(qr.pk) in ids
        assert str(other_qr.pk) not in ids

    def test_list_no_member_profile_returns_empty(self, api_client, user_no_member):
        api_client.force_authenticate(user=user_no_member)
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['results'] == []

    def test_list_without_existing_qr(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['results'] == []

    # -- regenerate --

    def test_regenerate_unauthenticated(self, api_client):
        resp = api_client.post(self.regenerate_url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_regenerate_no_member_profile(self, api_client, user_no_member):
        api_client.force_authenticate(user=user_no_member)
        resp = api_client.post(self.regenerate_url)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in resp.data

    def test_regenerate_creates_qr_if_not_exists(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        assert not MemberQRCode.objects.filter(member=member).exists()
        resp = api_client.post(self.regenerate_url)
        assert resp.status_code == status.HTTP_200_OK
        assert MemberQRCode.objects.filter(member=member).exists()

    def test_regenerate_updates_existing_qr(self, api_client, member_user):
        user, member = member_user
        qr = MemberQRCodeFactory(member=member)
        old_code = qr.code
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.regenerate_url)
        assert resp.status_code == status.HTTP_200_OK
        qr.refresh_from_db()
        assert qr.code != old_code

    def test_regenerate_response_contains_fields(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.regenerate_url)
        assert 'code' in resp.data
        assert 'expires_at' in resp.data
        assert 'is_valid' in resp.data
        assert resp.data['is_valid'] is True


# ---------------------------------------------------------------------------
# AttendanceSessionViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAttendanceSessionViewSet:
    list_url = reverse('v1:attendance:session-list')

    def _detail_url(self, pk):
        return reverse('v1:attendance:session-detail', args=[pk])

    # -- permissions --

    def test_list_unauthenticated(self, api_client):
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_regular_member_denied(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_admin_allowed(self, api_client, admin_user):
        user, _ = admin_user
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK

    def test_list_pastor_allowed(self, api_client, pastor_user):
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK

    # -- CRUD --

    def test_create_session(self, api_client, admin_user):
        user, _ = admin_user
        api_client.force_authenticate(user=user)
        data = {
            'name': 'Culte test',
            'session_type': AttendanceSessionType.WORSHIP,
            'date': timezone.now().date().isoformat(),
            'is_open': True,
        }
        resp = api_client.post(self.list_url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['name'] == 'Culte test'

    def test_retrieve_session(self, api_client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.get(self._detail_url(session.pk))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['name'] == session.name

    def test_update_session(self, api_client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.patch(self._detail_url(session.pk), {'is_open': False})
        assert resp.status_code == status.HTTP_200_OK
        session.refresh_from_db()
        assert session.is_open is False

    def test_delete_session(self, api_client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.delete(self._detail_url(session.pk))
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_list_only_active_sessions(self, api_client, admin_user):
        user, _ = admin_user
        active = AttendanceSessionFactory(is_active=True)
        inactive = AttendanceSessionFactory(is_active=False)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url)
        ids = [item['id'] for item in resp.data['results']]
        assert str(active.pk) in ids
        assert str(inactive.pk) not in ids

    def test_filter_by_session_type(self, api_client, admin_user):
        user, _ = admin_user
        worship = AttendanceSessionFactory(session_type=AttendanceSessionType.WORSHIP)
        event = AttendanceSessionFactory(session_type=AttendanceSessionType.EVENT)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url, {'session_type': AttendanceSessionType.WORSHIP})
        ids = [item['id'] for item in resp.data['results']]
        assert str(worship.pk) in ids
        assert str(event.pk) not in ids

    def test_filter_by_is_open(self, api_client, admin_user):
        user, _ = admin_user
        open_session = AttendanceSessionFactory(is_open=True)
        closed_session = AttendanceSessionFactory(is_open=False)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.list_url, {'is_open': 'true'})
        ids = [item['id'] for item in resp.data['results']]
        assert str(open_session.pk) in ids
        assert str(closed_session.pk) not in ids

    def test_response_includes_attendee_count(self, api_client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self._detail_url(session.pk))
        assert resp.data['attendee_count'] == 2

    def test_response_includes_records(self, api_client, admin_user):
        user, _ = admin_user
        session = AttendanceSessionFactory()
        AttendanceRecordFactory(session=session)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self._detail_url(session.pk))
        assert len(resp.data['records']) == 1


# ---------------------------------------------------------------------------
# CheckInViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCheckInViewSet:
    url = reverse('v1:attendance:checkin-list')

    def test_unauthenticated(self, api_client):
        resp = api_client.post(self.url, {})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_missing_fields(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_qr_code(self, api_client, member_user):
        user, _ = member_user
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': 'INVALID-CODE-XYZ',
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'invalide' in resp.data['error'].lower() or 'invalid' in resp.data['error'].lower()

    def test_expired_qr_code(self, api_client, member_user):
        user, _ = member_user
        qr = MemberQRCodeFactory()
        qr.expires_at = timezone.now() - datetime.timedelta(hours=1)
        qr.save()
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'expir' in resp.data['error'].lower()

    def test_invalid_session_id(self, api_client, member_user):
        user, _ = member_user
        qr = MemberQRCodeFactory()
        api_client.force_authenticate(user=user)
        import uuid
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(uuid.uuid4()),
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_closed_session(self, api_client, member_user):
        user, _ = member_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory(is_open=False)
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_successful_checkin(self, api_client, member_user):
        user, member = member_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['success'] is True
        assert resp.data['member_name'] == qr.member.full_name
        record = AttendanceRecord.objects.get(session=session, member=qr.member)
        assert record.checked_in_by == member
        assert record.method == CheckInMethod.QR_SCAN

    def test_successful_checkin_member_photo_none(self, api_client, member_user):
        user, _ = member_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.data['member_photo'] is None

    def test_duplicate_checkin(self, api_client, member_user):
        user, member = member_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        # Create first record
        AttendanceRecord.objects.create(
            session=session,
            member=qr.member,
            method=CheckInMethod.QR_SCAN,
        )
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_200_OK
        assert 'warning' in resp.data
        assert AttendanceRecord.objects.filter(
            session=session, member=qr.member
        ).count() == 1

    @patch('apps.onboarding.services.OnboardingService.mark_lesson_attended')
    def test_lesson_marking_on_checkin(self, mock_mark, api_client, admin_user):
        user, admin_member = admin_user
        qr = MemberQRCodeFactory()
        # Create a real ScheduledLesson
        course = TrainingCourse.objects.create(name='Test Course')
        lesson_obj = Lesson.objects.create(course=course, order=1, title='Lesson 1')
        training = MemberTraining.objects.create(
            member=qr.member, course=course, assigned_by=admin_member
        )
        scheduled = ScheduledLesson.objects.create(
            training=training, lesson=lesson_obj, scheduled_date=timezone.now()
        )
        session = AttendanceSessionFactory(scheduled_lesson=scheduled)

        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_200_OK
        mock_mark.assert_called_once_with(scheduled, admin_member)

    @patch('apps.onboarding.services.OnboardingService.mark_lesson_attended')
    def test_no_lesson_marking_when_no_lesson(self, mock_mark, api_client, member_user):
        user, _ = member_user
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        mock_mark.assert_not_called()

    def test_checkin_user_without_member_profile(self, api_client, user_no_member):
        """User without member_profile can still check in; scanner is set to None."""
        qr = MemberQRCodeFactory()
        session = AttendanceSessionFactory()
        api_client.force_authenticate(user=user_no_member)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': str(session.pk),
        })
        assert resp.status_code == status.HTTP_200_OK
        record = AttendanceRecord.objects.get(session=session, member=qr.member)
        assert record.checked_in_by is None

    def test_checkin_invalid_uuid_session_id(self, api_client, member_user):
        user, _ = member_user
        qr = MemberQRCodeFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'qr_code': qr.code,
            'session_id': 'not-a-uuid',
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# AbsenceAlertViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAbsenceAlertViewSet:
    url = reverse('v1:attendance:alert-list')

    def test_unauthenticated(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_member_denied(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list(self, api_client, admin_user):
        user, _ = admin_user
        alert = AbsenceAlertFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['results']) >= 1

    def test_pastor_can_list(self, api_client, pastor_user):
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_only_active_alerts_returned(self, api_client, admin_user):
        user, _ = admin_user
        active_alert = AbsenceAlertFactory(is_active=True)
        inactive_alert = AbsenceAlertFactory(is_active=False)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.url)
        ids = [item['id'] for item in resp.data['results']]
        assert str(active_alert.pk) in ids
        assert str(inactive_alert.pk) not in ids

    def test_filter_by_alert_sent(self, api_client, admin_user):
        user, _ = admin_user
        sent = AbsenceAlertFactory(alert_sent=True)
        unsent = AbsenceAlertFactory(alert_sent=False)
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.url, {'alert_sent': 'true'})
        ids = [item['id'] for item in resp.data['results']]
        assert str(sent.pk) in ids
        assert str(unsent.pk) not in ids

    def test_response_contains_expected_fields(self, api_client, admin_user):
        user, _ = admin_user
        AbsenceAlertFactory()
        api_client.force_authenticate(user=user)
        resp = api_client.get(self.url)
        item = resp.data['results'][0]
        assert 'member_name' in item
        assert 'consecutive_absences' in item
        assert 'last_attendance_date' in item
        assert 'alert_sent' in item

    def test_read_only_no_post(self, api_client, admin_user):
        user, _ = admin_user
        api_client.force_authenticate(user=user)
        resp = api_client.post(self.url, {
            'consecutive_absences': 5,
        })
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_read_only_no_delete(self, api_client, admin_user):
        user, _ = admin_user
        alert = AbsenceAlertFactory()
        api_client.force_authenticate(user=user)
        detail_url = reverse('v1:attendance:alert-detail', args=[alert.pk])
        resp = api_client.delete(detail_url)
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_retrieve_single_alert(self, api_client, admin_user):
        user, _ = admin_user
        alert = AbsenceAlertFactory(consecutive_absences=7)
        api_client.force_authenticate(user=user)
        detail_url = reverse('v1:attendance:alert-detail', args=[alert.pk])
        resp = api_client.get(detail_url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['consecutive_absences'] == 7
