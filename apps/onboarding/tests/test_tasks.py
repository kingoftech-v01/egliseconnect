"""Tests for onboarding Celery tasks."""
import pytest
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from apps.communication.models import Notification
from apps.core.constants import (
    InterviewStatus,
    LessonStatus,
    MembershipStatus,
)
from apps.members.tests.factories import MemberFactory, UserFactory
from apps.onboarding.tasks import (
    check_expired_forms,
    send_form_deadline_reminders,
    send_interview_reminders,
    send_lesson_reminders,
)
from apps.onboarding.tests.factories import (
    InterviewFactory,
    LessonFactory,
    MemberTrainingFactory,
    ScheduledLessonFactory,
    TrainingCourseFactory,
)


@pytest.mark.django_db
class TestCheckExpiredForms:
    """Tests for check_expired_forms task."""

    def test_calls_service_and_returns_count(self):
        """Task delegates to OnboardingService.expire_overdue_members and returns count."""
        with patch(
            'apps.onboarding.services.OnboardingService.expire_overdue_members',
            return_value=5,
        ) as mock_expire:
            result = check_expired_forms()

        mock_expire.assert_called_once()
        assert result == 5

    def test_returns_zero_when_none_expired(self):
        """Task returns 0 when no members are overdue."""
        with patch(
            'apps.onboarding.services.OnboardingService.expire_overdue_members',
            return_value=0,
        ):
            result = check_expired_forms()

        assert result == 0


@pytest.mark.django_db
class TestSendFormDeadlineReminders:
    """Tests for send_form_deadline_reminders task."""

    def _make_member_with_deadline(self, days_from_now, status=MembershipStatus.REGISTERED):
        """Create a member with form_deadline set to `days_from_now` days from now."""
        # Use localdate + noon to ensure the date matches in Django's __date lookup
        # which converts to the project's TIME_ZONE (America/Toronto)
        from datetime import datetime, time
        target_date = timezone.localdate() + timedelta(days=days_from_now)
        deadline = timezone.make_aware(
            datetime.combine(target_date, time(12, 0)),
            timezone.get_current_timezone(),
        )
        member = MemberFactory(
            user=None,
            membership_status=status,
            registration_date=timezone.now() - timedelta(days=10),
            form_deadline=deadline,
        )
        return member

    def test_reminder_7_days(self):
        """Notification created for member whose deadline is 7 days away."""
        member = self._make_member_with_deadline(7, MembershipStatus.REGISTERED)
        send_form_deadline_reminders()

        notif = Notification.objects.filter(member=member)
        assert notif.count() == 1
        assert '7 jour(s)' in notif.first().title

    def test_reminder_3_days(self):
        """Notification created for member whose deadline is 3 days away."""
        member = self._make_member_with_deadline(3, MembershipStatus.FORM_PENDING)
        send_form_deadline_reminders()

        notif = Notification.objects.filter(member=member)
        assert notif.count() == 1
        assert '3 jour(s)' in notif.first().title

    def test_reminder_1_day(self):
        """Notification created for member whose deadline is 1 day away."""
        member = self._make_member_with_deadline(1, MembershipStatus.REGISTERED)
        send_form_deadline_reminders()

        notif = Notification.objects.filter(member=member)
        assert notif.count() == 1
        assert '1 jour(s)' in notif.first().title

    def test_all_three_reminders_at_once(self):
        """When members fall on 7, 3, and 1-day marks, all get notified."""
        m7 = self._make_member_with_deadline(7)
        m3 = self._make_member_with_deadline(3)
        m1 = self._make_member_with_deadline(1)

        send_form_deadline_reminders()

        assert Notification.objects.filter(member=m7).count() == 1
        assert Notification.objects.filter(member=m3).count() == 1
        assert Notification.objects.filter(member=m1).count() == 1

    def test_no_reminder_for_non_matching_deadline(self):
        """No notification for members whose deadline is not at 7, 3, or 1 day."""
        member = self._make_member_with_deadline(5)
        send_form_deadline_reminders()

        assert Notification.objects.filter(member=member).count() == 0

    def test_no_reminder_for_wrong_status(self):
        """Members not in REGISTERED or FORM_PENDING don't receive reminders."""
        member = self._make_member_with_deadline(7, MembershipStatus.FORM_SUBMITTED)
        send_form_deadline_reminders()

        assert Notification.objects.filter(member=member).count() == 0

    def test_notification_content(self):
        """Notification message contains correct days and link."""
        member = self._make_member_with_deadline(3, MembershipStatus.REGISTERED)
        send_form_deadline_reminders()

        notif = Notification.objects.get(member=member)
        assert '3 jour(s)' in notif.message
        assert notif.notification_type == 'general'
        assert notif.link == '/onboarding/form/'

    def test_form_pending_status_also_triggers(self):
        """FORM_PENDING status members also get reminders."""
        member = self._make_member_with_deadline(7, MembershipStatus.FORM_PENDING)
        send_form_deadline_reminders()

        assert Notification.objects.filter(member=member).count() == 1


@pytest.mark.django_db
class TestSendLessonReminders:
    """Tests for send_lesson_reminders task."""

    def _make_scheduled_lesson(self, days_from_now, **overrides):
        """Create a ScheduledLesson scheduled `days_from_now` days in the future."""
        from datetime import datetime, time
        target_date = timezone.localdate() + timedelta(days=days_from_now)
        scheduled = timezone.make_aware(
            datetime.combine(target_date, time(10, 0)),
            timezone.get_current_timezone(),
        )
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course)
        training = MemberTrainingFactory(course=course)
        defaults = {
            'training': training,
            'lesson': lesson,
            'scheduled_date': scheduled,
            'status': LessonStatus.UPCOMING,
            'reminder_3days_sent': False,
            'reminder_1day_sent': False,
            'reminder_sameday_sent': False,
        }
        defaults.update(overrides)
        return ScheduledLessonFactory(**defaults)

    def test_5_day_reminder(self):
        """Notification created and flag set for lesson 5 days away."""
        sl = self._make_scheduled_lesson(5)
        send_lesson_reminders()

        sl.refresh_from_db()
        assert sl.reminder_5days_sent is True
        notifs = Notification.objects.filter(member=sl.training.member)
        assert notifs.count() == 1
        assert '5 jours' in notifs.first().title

    def test_3_day_reminder(self):
        """Notification created and flag set for lesson 3 days away."""
        sl = self._make_scheduled_lesson(3)
        send_lesson_reminders()

        sl.refresh_from_db()
        assert sl.reminder_3days_sent is True
        notifs = Notification.objects.filter(member=sl.training.member)
        assert notifs.count() == 1
        assert '3 jours' in notifs.first().title

    def test_1_day_reminder(self):
        """Notification created and flag set for lesson 1 day away."""
        sl = self._make_scheduled_lesson(1)
        send_lesson_reminders()

        sl.refresh_from_db()
        assert sl.reminder_1day_sent is True
        notifs = Notification.objects.filter(member=sl.training.member)
        assert notifs.count() == 1
        assert 'DEMAIN' in notifs.first().title

    def test_same_day_reminder(self):
        """Notification created and flag set for lesson scheduled today."""
        sl = self._make_scheduled_lesson(0)
        send_lesson_reminders()

        sl.refresh_from_db()
        assert sl.reminder_sameday_sent is True
        notifs = Notification.objects.filter(member=sl.training.member)
        assert notifs.count() == 1
        assert "AUJOURD'HUI" in notifs.first().title

    def test_no_duplicate_5day_reminder(self):
        """If 5-day reminder already sent, skip it."""
        sl = self._make_scheduled_lesson(5, reminder_5days_sent=True)
        send_lesson_reminders()

        assert Notification.objects.filter(member=sl.training.member).count() == 0

    def test_no_duplicate_3day_reminder(self):
        """If 3-day reminder already sent, skip it."""
        sl = self._make_scheduled_lesson(3, reminder_3days_sent=True)
        send_lesson_reminders()

        assert Notification.objects.filter(member=sl.training.member).count() == 0

    def test_no_duplicate_1day_reminder(self):
        """If 1-day reminder already sent, skip it."""
        sl = self._make_scheduled_lesson(1, reminder_1day_sent=True)
        send_lesson_reminders()

        assert Notification.objects.filter(member=sl.training.member).count() == 0

    def test_no_duplicate_sameday_reminder(self):
        """If same-day reminder already sent, skip it."""
        sl = self._make_scheduled_lesson(0, reminder_sameday_sent=True)
        send_lesson_reminders()

        assert Notification.objects.filter(member=sl.training.member).count() == 0

    def test_non_upcoming_status_ignored(self):
        """Lessons with non-UPCOMING status are not reminded."""
        sl = self._make_scheduled_lesson(3, status=LessonStatus.COMPLETED)
        send_lesson_reminders()

        assert Notification.objects.filter(member=sl.training.member).count() == 0

    def test_notification_link(self):
        """Notification link points to training page."""
        sl = self._make_scheduled_lesson(3)
        send_lesson_reminders()

        notif = Notification.objects.get(member=sl.training.member)
        assert notif.link == '/onboarding/training/'
        assert notif.notification_type == 'event'

    def test_notification_message_contains_lesson_title(self):
        """Notification message includes the lesson title."""
        sl = self._make_scheduled_lesson(3)
        send_lesson_reminders()

        notif = Notification.objects.get(member=sl.training.member)
        assert sl.lesson.title in notif.message

    def test_multiple_lessons_multiple_windows(self):
        """Multiple lessons at different windows all get processed."""
        sl3 = self._make_scheduled_lesson(3)
        sl1 = self._make_scheduled_lesson(1)
        sl0 = self._make_scheduled_lesson(0)

        send_lesson_reminders()

        sl3.refresh_from_db()
        sl1.refresh_from_db()
        sl0.refresh_from_db()

        assert sl3.reminder_3days_sent is True
        assert sl1.reminder_1day_sent is True
        assert sl0.reminder_sameday_sent is True

    def test_lesson_at_6_days_not_reminded(self):
        """Lessons 6 days away get no reminder."""
        sl = self._make_scheduled_lesson(6)
        send_lesson_reminders()

        assert Notification.objects.filter(member=sl.training.member).count() == 0


@pytest.mark.django_db
class TestSendInterviewReminders:
    """Tests for send_interview_reminders task."""

    def _make_interview(self, days_from_now, status=InterviewStatus.CONFIRMED, **overrides):
        """Create an Interview with confirmed_date `days_from_now` days away."""
        from datetime import datetime, time
        target_date = timezone.localdate() + timedelta(days=days_from_now)
        interview_dt = timezone.make_aware(
            datetime.combine(target_date, time(14, 0)),
            timezone.get_current_timezone(),
        )
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(course=course)
        defaults = {
            'training': training,
            'member': training.member,
            'status': status,
            'proposed_date': interview_dt,
            'confirmed_date': interview_dt,
            'reminder_3days_sent': False,
            'reminder_1day_sent': False,
            'reminder_sameday_sent': False,
        }
        defaults.update(overrides)
        return InterviewFactory(**defaults)

    def test_5_day_reminder(self):
        """Notification created and flag set for interview 5 days away."""
        iv = self._make_interview(5, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        iv.refresh_from_db()
        assert iv.reminder_5days_sent is True
        notifs = Notification.objects.filter(member=iv.member)
        assert notifs.count() == 1
        assert '5 jours' in notifs.first().title

    def test_3_day_reminder_confirmed(self):
        """Notification created and flag set for interview 3 days away (CONFIRMED)."""
        iv = self._make_interview(3, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        iv.refresh_from_db()
        assert iv.reminder_3days_sent is True
        notifs = Notification.objects.filter(member=iv.member)
        assert notifs.count() == 1
        assert '3 jours' in notifs.first().title

    def test_3_day_reminder_accepted(self):
        """ACCEPTED status interviews also get 3-day reminder."""
        iv = self._make_interview(3, InterviewStatus.ACCEPTED)
        send_interview_reminders()

        iv.refresh_from_db()
        assert iv.reminder_3days_sent is True
        assert Notification.objects.filter(member=iv.member).count() == 1

    def test_1_day_reminder(self):
        """Notification created and flag set for interview 1 day away."""
        iv = self._make_interview(1, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        iv.refresh_from_db()
        assert iv.reminder_1day_sent is True
        notifs = Notification.objects.filter(member=iv.member)
        assert notifs.count() == 1
        assert 'DEMAIN' in notifs.first().title

    def test_same_day_reminder(self):
        """Notification created and flag set for interview today."""
        iv = self._make_interview(0, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        iv.refresh_from_db()
        assert iv.reminder_sameday_sent is True
        notifs = Notification.objects.filter(member=iv.member)
        assert notifs.count() == 1
        assert "AUJOURD'HUI" in notifs.first().title

    def test_no_duplicate_5day_reminder(self):
        """If 5-day reminder already sent, skip it."""
        iv = self._make_interview(5, reminder_5days_sent=True)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_no_duplicate_3day_reminder(self):
        """If 3-day reminder already sent, skip it."""
        iv = self._make_interview(3, reminder_3days_sent=True)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_no_duplicate_1day_reminder(self):
        """If 1-day reminder already sent, skip it."""
        iv = self._make_interview(1, reminder_1day_sent=True)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_no_duplicate_sameday_reminder(self):
        """If same-day reminder already sent, skip it."""
        iv = self._make_interview(0, reminder_sameday_sent=True)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_proposed_status_not_reminded(self):
        """Interviews in PROPOSED status are not reminded."""
        iv = self._make_interview(3, InterviewStatus.PROPOSED)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_cancelled_status_not_reminded(self):
        """Interviews in CANCELLED status are not reminded."""
        iv = self._make_interview(3, InterviewStatus.CANCELLED)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_completed_pass_not_reminded(self):
        """Completed interviews are not reminded."""
        iv = self._make_interview(3, InterviewStatus.COMPLETED_PASS)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_no_confirmed_date_not_reminded(self):
        """Interviews without confirmed_date are not reminded."""
        iv = self._make_interview(3, confirmed_date=None)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0

    def test_notification_link(self):
        """Notification link points to interview page."""
        iv = self._make_interview(3, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        notif = Notification.objects.get(member=iv.member)
        assert notif.link == '/onboarding/interview/'
        assert notif.notification_type == 'event'

    def test_notification_message_contains_date(self):
        """Notification message includes the interview date."""
        iv = self._make_interview(3, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        notif = Notification.objects.get(member=iv.member)
        # The message uses final_date which is confirmed_date or proposed_date
        assert iv.final_date.strftime('%d/%m/%Y') in notif.message

    def test_multiple_interviews_different_windows(self):
        """Multiple interviews at different reminder windows all processed."""
        iv3 = self._make_interview(3, InterviewStatus.CONFIRMED)
        iv1 = self._make_interview(1, InterviewStatus.ACCEPTED)
        iv0 = self._make_interview(0, InterviewStatus.CONFIRMED)

        send_interview_reminders()

        iv3.refresh_from_db()
        iv1.refresh_from_db()
        iv0.refresh_from_db()

        assert iv3.reminder_3days_sent is True
        assert iv1.reminder_1day_sent is True
        assert iv0.reminder_sameday_sent is True

    def test_interview_at_6_days_not_reminded(self):
        """Interviews 6 days away get no reminder."""
        iv = self._make_interview(6, InterviewStatus.CONFIRMED)
        send_interview_reminders()

        assert Notification.objects.filter(member=iv.member).count() == 0
