"""Tests for attendance models - targeting 99% coverage."""
import datetime
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.utils import timezone

from apps.attendance.models import (
    AbsenceAlert,
    AttendanceRecord,
    AttendanceSession,
    MemberQRCode,
    generate_qr_image,
    generate_secure_qr_code,
)
from apps.core.constants import AttendanceSessionType, CheckInMethod
from apps.members.tests.factories import MemberFactory

from .factories import (
    AbsenceAlertFactory,
    AttendanceRecordFactory,
    AttendanceSessionFactory,
    MemberQRCodeFactory,
)


# ---------------------------------------------------------------------------
# generate_secure_qr_code()
# ---------------------------------------------------------------------------

class TestGenerateSecureQRCode:

    def test_returns_string_starting_with_ec(self):
        code = generate_secure_qr_code()
        assert isinstance(code, str)
        assert code.startswith('EC-')

    def test_unique_each_call(self):
        codes = {generate_secure_qr_code() for _ in range(50)}
        assert len(codes) == 50

    def test_format_has_two_dashes(self):
        code = generate_secure_qr_code()
        parts = code.split('-')
        # EC - <uuid8> - <signature16>
        assert len(parts) == 3
        assert parts[0] == 'EC'


# ---------------------------------------------------------------------------
# generate_qr_image()
# ---------------------------------------------------------------------------

class TestGenerateQRImage:

    def test_returns_content_file(self):
        result = generate_qr_image('EC-test1234-abcdef0123456789')
        assert isinstance(result, ContentFile)

    def test_callable(self):
        assert callable(generate_qr_image)

    def test_filename_contains_code_prefix(self):
        code = 'EC-abcd1234-sig'
        result = generate_qr_image(code)
        assert result.name.startswith('qr_EC-abcd1')

    def test_produces_png_data(self):
        result = generate_qr_image('EC-test')
        # PNG magic bytes
        data = result.read()
        assert data[:4] == b'\x89PNG'


# ---------------------------------------------------------------------------
# MemberQRCode model
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMemberQRCode:

    def test_save_auto_generates_code(self):
        qr = MemberQRCodeFactory()
        assert qr.code.startswith('EC-')

    def test_save_auto_generates_expires_at(self):
        qr = MemberQRCodeFactory()
        assert qr.expires_at is not None
        # Should expire roughly 7 days from now
        delta = qr.expires_at - timezone.now()
        assert 6 <= delta.days <= 7

    def test_save_auto_generates_qr_image(self):
        qr = MemberQRCodeFactory()
        assert qr.qr_image is not None
        assert qr.qr_image.name != ''

    def test_save_does_not_overwrite_existing_code(self):
        qr = MemberQRCodeFactory()
        original_code = qr.code
        qr.save()
        assert qr.code == original_code

    def test_is_valid_when_not_expired(self):
        qr = MemberQRCodeFactory()
        assert qr.is_valid is True

    def test_is_valid_when_expired(self):
        qr = MemberQRCodeFactory()
        qr.expires_at = timezone.now() - datetime.timedelta(hours=1)
        qr.save()
        assert qr.is_valid is False

    def test_regenerate_creates_new_code(self):
        qr = MemberQRCodeFactory()
        old_code = qr.code
        qr.regenerate()
        assert qr.code != old_code
        assert qr.code.startswith('EC-')

    def test_regenerate_updates_expires_at(self):
        qr = MemberQRCodeFactory()
        qr.expires_at = timezone.now() - datetime.timedelta(days=1)
        qr.save()
        assert qr.is_valid is False
        qr.regenerate()
        assert qr.is_valid is True

    def test_regenerate_updates_qr_image(self):
        qr = MemberQRCodeFactory()
        old_image_name = qr.qr_image.name
        qr.regenerate()
        # Image name changes because code changes
        assert qr.qr_image.name != old_image_name

    def test_str(self):
        qr = MemberQRCodeFactory()
        expected = f'QR {qr.member.full_name}'
        assert str(qr) == expected

    def test_code_is_unique(self):
        qr1 = MemberQRCodeFactory()
        member2 = MemberFactory()
        qr2 = MemberQRCode(member=member2, code=qr1.code)
        with pytest.raises(IntegrityError):
            qr2.save()

    def test_one_to_one_member(self):
        qr = MemberQRCodeFactory()
        with pytest.raises(IntegrityError):
            MemberQRCode.objects.create(member=qr.member)


# ---------------------------------------------------------------------------
# AttendanceSession model
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAttendanceSession:

    def test_str(self):
        session = AttendanceSessionFactory(name='Culte du dimanche')
        expected = f'Culte du dimanche ({session.date})'
        assert str(session) == expected

    def test_attendee_count_zero(self):
        session = AttendanceSessionFactory()
        assert session.attendee_count == 0

    def test_attendee_count_with_records(self):
        session = AttendanceSessionFactory()
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)
        assert session.attendee_count == 2

    def test_default_session_type(self):
        session = AttendanceSessionFactory()
        assert session.session_type == AttendanceSessionType.WORSHIP

    def test_is_open_default(self):
        session = AttendanceSessionFactory()
        assert session.is_open is True

    def test_ordering(self):
        s1 = AttendanceSessionFactory(
            date=timezone.now().date() - datetime.timedelta(days=2)
        )
        s2 = AttendanceSessionFactory(
            date=timezone.now().date()
        )
        sessions = list(AttendanceSession.objects.all())
        assert sessions[0] == s2
        assert sessions[1] == s1

    def test_optional_event_null(self):
        session = AttendanceSessionFactory()
        assert session.event is None

    def test_optional_scheduled_lesson_null(self):
        session = AttendanceSessionFactory()
        assert session.scheduled_lesson is None


# ---------------------------------------------------------------------------
# AttendanceRecord model
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAttendanceRecord:

    def test_str(self):
        record = AttendanceRecordFactory()
        expected = f'{record.member.full_name} @ {record.session.name}'
        assert str(record) == expected

    def test_unique_together_session_member(self):
        record = AttendanceRecordFactory()
        with pytest.raises(IntegrityError):
            AttendanceRecord.objects.create(
                session=record.session,
                member=record.member,
                method=CheckInMethod.MANUAL,
            )

    def test_default_method(self):
        record = AttendanceRecordFactory()
        assert record.method == CheckInMethod.QR_SCAN

    def test_checked_in_at_auto_set(self):
        record = AttendanceRecordFactory()
        assert record.checked_in_at is not None

    def test_same_member_different_sessions(self):
        member = MemberFactory()
        r1 = AttendanceRecordFactory(member=member)
        r2 = AttendanceRecordFactory(member=member)
        assert r1.session != r2.session
        assert AttendanceRecord.objects.filter(member=member).count() == 2

    def test_notes_blank_by_default(self):
        record = AttendanceRecordFactory()
        assert record.notes == ''


# ---------------------------------------------------------------------------
# AbsenceAlert model
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAbsenceAlert:

    def test_str(self):
        alert = AbsenceAlertFactory(consecutive_absences=5)
        expected = f'{alert.member.full_name} - 5 absences'
        assert str(alert) == expected

    def test_default_alert_sent_false(self):
        alert = AbsenceAlertFactory()
        assert alert.alert_sent is False

    def test_ordering_by_consecutive_absences(self):
        a1 = AbsenceAlertFactory(consecutive_absences=2)
        a2 = AbsenceAlertFactory(consecutive_absences=5)
        a3 = AbsenceAlertFactory(consecutive_absences=3)
        alerts = list(AbsenceAlert.objects.all())
        assert alerts[0] == a2
        assert alerts[1] == a3
        assert alerts[2] == a1

    def test_optional_fields(self):
        alert = AbsenceAlertFactory()
        assert alert.last_attendance_date is None
        assert alert.alert_sent_at is None
        assert alert.acknowledged_by is None
        assert alert.notes == ''

    def test_alert_with_all_fields(self):
        member = MemberFactory()
        acknowledger = MemberFactory()
        now = timezone.now()
        alert = AbsenceAlert.objects.create(
            member=member,
            consecutive_absences=4,
            last_attendance_date=now.date(),
            alert_sent=True,
            alert_sent_at=now,
            acknowledged_by=acknowledger,
            notes='Called the member',
        )
        assert alert.alert_sent is True
        assert alert.acknowledged_by == acknowledger
        assert alert.notes == 'Called the member'
