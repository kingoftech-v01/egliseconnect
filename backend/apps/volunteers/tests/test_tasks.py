"""Tests for volunteer schedule reminder Celery tasks."""
import pytest
from datetime import timedelta

from django.utils import timezone

from apps.communication.models import Notification
from apps.core.constants import ScheduleStatus
from apps.volunteers.tasks import send_volunteer_schedule_reminders
from apps.volunteers.tests.factories import VolunteerScheduleFactory


@pytest.mark.django_db
class TestSendVolunteerScheduleReminders:
    """Tests for the send_volunteer_schedule_reminders task."""

    def _make_schedule(self, days_from_now, status=ScheduleStatus.SCHEDULED, **overrides):
        """Create a VolunteerSchedule `days_from_now` days in the future."""
        target_date = timezone.localdate() + timedelta(days=days_from_now)
        defaults = {
            'date': target_date,
            'status': status,
            'reminder_5days_sent': False,
            'reminder_3days_sent': False,
            'reminder_1day_sent': False,
            'reminder_sameday_sent': False,
        }
        defaults.update(overrides)
        return VolunteerScheduleFactory(**defaults)

    def test_5_day_reminder(self):
        """Notification sent and flag set for schedule 5 days away."""
        sched = self._make_schedule(5)
        result = send_volunteer_schedule_reminders()

        sched.refresh_from_db()
        assert sched.reminder_5days_sent is True
        assert result == 1
        notifs = Notification.objects.filter(member=sched.member)
        assert notifs.count() == 1
        assert '5 jours' in notifs.first().message

    def test_3_day_reminder(self):
        """Notification sent and flag set for schedule 3 days away."""
        sched = self._make_schedule(3, reminder_5days_sent=True)
        result = send_volunteer_schedule_reminders()

        sched.refresh_from_db()
        assert sched.reminder_3days_sent is True
        assert result == 1
        notifs = Notification.objects.filter(member=sched.member)
        assert notifs.count() == 1
        assert '3 jours' in notifs.first().message

    def test_1_day_reminder(self):
        """Notification sent and flag set for schedule 1 day away."""
        sched = self._make_schedule(1, reminder_5days_sent=True, reminder_3days_sent=True)
        result = send_volunteer_schedule_reminders()

        sched.refresh_from_db()
        assert sched.reminder_1day_sent is True
        assert result == 1
        notifs = Notification.objects.filter(member=sched.member)
        assert notifs.count() == 1
        assert 'DEMAIN' in notifs.first().message

    def test_same_day_reminder(self):
        """Notification sent and flag set for schedule today."""
        sched = self._make_schedule(
            0,
            reminder_5days_sent=True,
            reminder_3days_sent=True,
            reminder_1day_sent=True,
        )
        result = send_volunteer_schedule_reminders()

        sched.refresh_from_db()
        assert sched.reminder_sameday_sent is True
        assert result == 1
        notifs = Notification.objects.filter(member=sched.member)
        assert notifs.count() == 1
        assert "aujourd'hui" in notifs.first().message.lower()

    def test_no_duplicate_5day(self):
        """If 5-day reminder already sent, skip it."""
        sched = self._make_schedule(5, reminder_5days_sent=True)
        result = send_volunteer_schedule_reminders()

        assert result == 0
        assert Notification.objects.filter(member=sched.member).count() == 0

    def test_no_duplicate_3day(self):
        """If 3-day reminder already sent, send nothing (5-day already sent too)."""
        sched = self._make_schedule(3, reminder_5days_sent=True, reminder_3days_sent=True)
        result = send_volunteer_schedule_reminders()

        assert result == 0
        assert Notification.objects.filter(member=sched.member).count() == 0

    def test_6_days_away_no_reminder(self):
        """Schedules more than 5 days away get no reminder."""
        sched = self._make_schedule(6)
        result = send_volunteer_schedule_reminders()

        assert result == 0
        assert Notification.objects.filter(member=sched.member).count() == 0

    def test_confirmed_status_gets_reminder(self):
        """CONFIRMED status schedules also receive reminders."""
        sched = self._make_schedule(5, status=ScheduleStatus.CONFIRMED)
        result = send_volunteer_schedule_reminders()

        assert result == 1
        sched.refresh_from_db()
        assert sched.reminder_5days_sent is True

    def test_declined_status_no_reminder(self):
        """DECLINED status schedules are not reminded."""
        sched = self._make_schedule(5, status=ScheduleStatus.DECLINED)
        result = send_volunteer_schedule_reminders()

        assert result == 0
        assert Notification.objects.filter(member=sched.member).count() == 0

    def test_completed_status_no_reminder(self):
        """COMPLETED status schedules are not reminded."""
        sched = self._make_schedule(5, status=ScheduleStatus.COMPLETED)
        result = send_volunteer_schedule_reminders()

        assert result == 0

    def test_notification_type_and_link(self):
        """Notification has correct type and link."""
        sched = self._make_schedule(5)
        send_volunteer_schedule_reminders()

        notif = Notification.objects.get(member=sched.member)
        assert notif.notification_type == 'volunteer'
        assert notif.link == '/volunteers/'

    def test_notification_contains_position_name(self):
        """Notification message includes position name."""
        sched = self._make_schedule(5)
        send_volunteer_schedule_reminders()

        notif = Notification.objects.get(member=sched.member)
        assert sched.position.name in notif.message

    def test_reminder_sent_flag_set(self):
        """The legacy reminder_sent field is also set to True."""
        sched = self._make_schedule(5)
        send_volunteer_schedule_reminders()

        sched.refresh_from_db()
        assert sched.reminder_sent is True

    def test_multiple_schedules_different_windows(self):
        """Multiple schedules at different windows all get processed."""
        s5 = self._make_schedule(5)
        s3 = self._make_schedule(3, reminder_5days_sent=True)
        s1 = self._make_schedule(1, reminder_5days_sent=True, reminder_3days_sent=True)
        s0 = self._make_schedule(
            0, reminder_5days_sent=True, reminder_3days_sent=True, reminder_1day_sent=True
        )

        result = send_volunteer_schedule_reminders()

        assert result == 4
        s5.refresh_from_db()
        s3.refresh_from_db()
        s1.refresh_from_db()
        s0.refresh_from_db()
        assert s5.reminder_5days_sent is True
        assert s3.reminder_3days_sent is True
        assert s1.reminder_1day_sent is True
        assert s0.reminder_sameday_sent is True

    def test_past_schedule_not_reminded(self):
        """Schedules in the past are not reminded."""
        sched = self._make_schedule(-1)
        result = send_volunteer_schedule_reminders()

        assert result == 0
        assert Notification.objects.filter(member=sched.member).count() == 0
