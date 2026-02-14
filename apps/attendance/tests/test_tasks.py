"""Tests for attendance inactivity tracking tasks."""
import pytest
from datetime import timedelta

from django.utils import timezone

from apps.core.constants import MembershipStatus, AttendanceSessionType, Roles
from apps.communication.models import Notification
from apps.members.tests.factories import MemberFactory
from apps.attendance.tests.factories import (
    AttendanceSessionFactory, AttendanceRecordFactory,
)
from apps.attendance.models import AbsenceAlert
from apps.attendance.tasks import check_member_inactivity, check_absence_alerts


@pytest.mark.django_db
class TestCheckMemberInactivity:
    """Tests for check_member_inactivity task."""

    def test_active_with_recent_attendance_stays_active(self):
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        session = AttendanceSessionFactory()
        AttendanceRecordFactory(member=member, session=session)

        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.ACTIVE
        assert result['inactive'] == 0

    def test_active_without_attendance_for_2_months_becomes_inactive(self):
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        # Create old attendance record (3 months ago)
        session = AttendanceSessionFactory(
            date=(timezone.now() - timedelta(days=90)).date()
        )
        record = AttendanceRecordFactory(member=member, session=session)
        # Force the checked_in_at to be old
        from apps.attendance.models import AttendanceRecord
        AttendanceRecord.objects.filter(pk=record.pk).update(
            checked_in_at=timezone.now() - timedelta(days=90)
        )

        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.INACTIVE
        assert result['inactive'] == 1

    def test_brand_new_member_without_attendance_stays_active(self):
        """Members with no attendance history at all are not marked inactive."""
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)

        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.ACTIVE
        assert result['inactive'] == 0

    def test_inactive_for_6_months_becomes_expired(self):
        member = MemberFactory(membership_status=MembershipStatus.INACTIVE)
        # Create very old attendance record (7 months ago)
        session = AttendanceSessionFactory(
            date=(timezone.now() - timedelta(days=210)).date()
        )
        record = AttendanceRecordFactory(member=member, session=session)
        from apps.attendance.models import AttendanceRecord
        AttendanceRecord.objects.filter(pk=record.pk).update(
            checked_in_at=timezone.now() - timedelta(days=210)
        )

        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.EXPIRED
        assert member.is_active is False
        assert result['expired'] == 1

    def test_inactive_with_recent_attendance_stays_inactive(self):
        """If an inactive member has attendance within 6 months, don't expire."""
        member = MemberFactory(membership_status=MembershipStatus.INACTIVE)
        session = AttendanceSessionFactory(
            date=(timezone.now() - timedelta(days=100)).date()
        )
        record = AttendanceRecordFactory(member=member, session=session)
        from apps.attendance.models import AttendanceRecord
        AttendanceRecord.objects.filter(pk=record.pk).update(
            checked_in_at=timezone.now() - timedelta(days=100)
        )

        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.INACTIVE
        assert result['expired'] == 0

    def test_non_active_members_not_affected(self):
        """Only ACTIVE members are checked for inactivity."""
        member = MemberFactory(membership_status=MembershipStatus.REGISTERED)
        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REGISTERED
        assert result['inactive'] == 0

    def test_suspended_members_not_affected(self):
        member = MemberFactory(membership_status=MembershipStatus.SUSPENDED)
        result = check_member_inactivity()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.SUSPENDED


@pytest.mark.django_db
class TestCheckAbsenceAlerts:
    """Tests for check_absence_alerts task."""

    def _create_worship_sessions(self, count=4):
        """Create `count` worship sessions over the last 30 days.

        Uses a single non-active opener to avoid creating extra active members
        that would be checked by the task.
        """
        opener = MemberFactory(membership_status=MembershipStatus.REGISTERED)
        sessions = []
        for i in range(count):
            date = (timezone.now() - timedelta(days=i * 7)).date()
            sessions.append(AttendanceSessionFactory(
                session_type=AttendanceSessionType.WORSHIP,
                date=date,
                opened_by=opener,
            ))
        return sessions

    def test_no_sessions_returns_zero(self):
        """No worship sessions in 30 days → no alerts."""
        result = check_absence_alerts()
        assert result == 0

    def test_member_attending_all_sessions_no_alert(self):
        """Member attending all sessions gets no alert."""
        sessions = self._create_worship_sessions(4)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        for s in sessions:
            AttendanceRecordFactory(member=member, session=s)

        result = check_absence_alerts()
        assert result == 0
        assert AbsenceAlert.objects.filter(member=member).count() == 0

    def test_member_missing_2_sessions_no_alert(self):
        """Member missing only 2 sessions (below threshold) gets no alert."""
        sessions = self._create_worship_sessions(4)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        # Attend 2 of 4 sessions
        AttendanceRecordFactory(member=member, session=sessions[0])
        AttendanceRecordFactory(member=member, session=sessions[1])

        result = check_absence_alerts()
        assert result == 0

    def test_member_missing_3_sessions_gets_alert(self):
        """Member missing 3+ sessions gets an absence alert."""
        sessions = self._create_worship_sessions(4)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        # Attend only 1 of 4 → 3 missed
        AttendanceRecordFactory(member=member, session=sessions[0])

        result = check_absence_alerts()

        assert result == 1
        alert = AbsenceAlert.objects.get(member=member)
        assert alert.consecutive_absences == 3
        assert alert.alert_sent is True
        assert alert.alert_sent_at is not None

    def test_alert_notifies_admins_and_pastors(self):
        """Alert creation sends notifications to admins and pastors."""
        sessions = self._create_worship_sessions(3)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        # Attend 0 of 3 → 3 missed
        admin = MemberFactory(role=Roles.ADMIN, membership_status=MembershipStatus.ACTIVE)
        pastor = MemberFactory(role=Roles.PASTOR, membership_status=MembershipStatus.ACTIVE)

        check_absence_alerts()

        admin_notifs = Notification.objects.filter(
            member=admin, message__contains=member.full_name
        )
        pastor_notifs = Notification.objects.filter(
            member=pastor, message__contains=member.full_name
        )
        assert admin_notifs.count() == 1
        assert pastor_notifs.count() == 1
        assert 'absence' in admin_notifs.first().title.lower()

    def test_no_duplicate_alert_if_unacknowledged(self):
        """If an unacknowledged alert exists, don't create another."""
        sessions = self._create_worship_sessions(4)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        # First run creates alert
        check_absence_alerts()
        assert AbsenceAlert.objects.filter(member=member).count() == 1

        # Second run does NOT create duplicate
        result = check_absence_alerts()
        assert result == 0
        assert AbsenceAlert.objects.filter(member=member).count() == 1

    def test_alert_updates_count_if_increased(self):
        """If member misses more sessions, the existing alert count is updated."""
        sessions = self._create_worship_sessions(3)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)

        check_absence_alerts()
        alert = AbsenceAlert.objects.get(member=member)
        assert alert.consecutive_absences == 3

        # Add a 4th session (still 0 attendance)
        AttendanceSessionFactory(
            session_type=AttendanceSessionType.WORSHIP,
            date=timezone.now().date(),
        )
        check_absence_alerts()
        alert.refresh_from_db()
        assert alert.consecutive_absences == 4

    def test_inactive_members_not_checked(self):
        """Only ACTIVE members are checked for absence alerts."""
        sessions = self._create_worship_sessions(4)
        member = MemberFactory(membership_status=MembershipStatus.INACTIVE)

        result = check_absence_alerts()
        assert result == 0
        assert AbsenceAlert.objects.filter(member=member).count() == 0

    def test_last_attendance_date_set(self):
        """Alert records the member's last attendance date."""
        sessions = self._create_worship_sessions(4)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        AttendanceRecordFactory(member=member, session=sessions[0])

        check_absence_alerts()

        alert = AbsenceAlert.objects.get(member=member)
        assert alert.last_attendance_date == sessions[0].date

    def test_notification_type_and_link(self):
        """Notification has correct type and link."""
        sessions = self._create_worship_sessions(3)
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        admin = MemberFactory(role=Roles.ADMIN, membership_status=MembershipStatus.ACTIVE)

        check_absence_alerts()

        notif = Notification.objects.filter(
            member=admin,
            message__contains=member.full_name,
        ).first()
        assert notif is not None
        assert notif.notification_type == 'attendance'
        assert notif.link == '/attendance/alerts/'
