"""Tests for follow-up reminder Celery tasks."""
import pytest
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from apps.core.constants import CareStatus
from apps.help_requests.models import PastoralCare
from apps.help_requests.tasks import (
    send_follow_up_reminders,
    escalate_overdue_follow_ups,
    snooze_follow_up,
    log_follow_up_completion,
)
from apps.members.tests.factories import MemberFactory, PastorFactory
from .factories import PastoralCareFactory


@pytest.mark.django_db
class TestFollowUpReminderTask:
    """Tests for the send_follow_up_reminders task."""

    def test_sends_reminder_for_today(self):
        today = timezone.now().date()
        care = PastoralCareFactory(
            follow_up_date=today,
            status=CareStatus.OPEN,
        )
        result = send_follow_up_reminders()
        assert result >= 1

    def test_no_reminder_for_future_date(self):
        future = (timezone.now() + timedelta(days=7)).date()
        PastoralCareFactory(
            follow_up_date=future,
            status=CareStatus.OPEN,
        )
        result = send_follow_up_reminders()
        assert result == 0

    def test_no_reminder_for_closed_cases(self):
        today = timezone.now().date()
        PastoralCareFactory(
            follow_up_date=today,
            status=CareStatus.CLOSED,
        )
        result = send_follow_up_reminders()
        assert result == 0


@pytest.mark.django_db
class TestEscalationTask:
    """Tests for the escalate_overdue_follow_ups task."""

    def test_escalates_overdue(self):
        overdue_date = (timezone.now() - timedelta(days=10)).date()
        PastoralCareFactory(
            follow_up_date=overdue_date,
            status=CareStatus.OPEN,
        )
        # Need at least one pastor to receive notifications
        PastorFactory()
        result = escalate_overdue_follow_ups(days_overdue=7)
        assert result >= 1

    def test_no_escalation_for_recent(self):
        recent = (timezone.now() - timedelta(days=3)).date()
        PastoralCareFactory(
            follow_up_date=recent,
            status=CareStatus.OPEN,
        )
        result = escalate_overdue_follow_ups(days_overdue=7)
        assert result == 0


@pytest.mark.django_db
class TestSnoozeTask:
    """Tests for the snooze_follow_up task."""

    def test_snooze_by_one_day(self):
        today = timezone.now().date()
        care = PastoralCareFactory(follow_up_date=today)
        result = snooze_follow_up(str(care.pk), days=1)
        care.refresh_from_db()
        assert care.follow_up_date == today + timedelta(days=1)
        assert result is not None

    def test_snooze_by_seven_days(self):
        today = timezone.now().date()
        care = PastoralCareFactory(follow_up_date=today)
        result = snooze_follow_up(str(care.pk), days=7)
        care.refresh_from_db()
        assert care.follow_up_date == today + timedelta(days=7)

    def test_snooze_nonexistent_care(self):
        import uuid
        result = snooze_follow_up(str(uuid.uuid4()), days=1)
        assert result is None

    def test_snooze_without_existing_date(self):
        care = PastoralCareFactory(follow_up_date=None)
        result = snooze_follow_up(str(care.pk), days=3)
        care.refresh_from_db()
        assert care.follow_up_date is not None


@pytest.mark.django_db
class TestFollowUpCompletionLog:
    """Tests for the log_follow_up_completion task."""

    def test_log_completion(self):
        care = PastoralCareFactory(status=CareStatus.OPEN, notes='Initial notes')
        result = log_follow_up_completion(
            str(care.pk),
            notes='Called the family',
            next_steps='Schedule visit next week',
        )
        assert result is True
        care.refresh_from_db()
        assert '[Suivi complété]' in care.notes
        assert 'Called the family' in care.notes
        assert '[Prochaines étapes]' in care.notes
        assert care.status == CareStatus.FOLLOW_UP

    def test_log_completion_nonexistent(self):
        import uuid
        result = log_follow_up_completion(str(uuid.uuid4()), notes='Test')
        assert result is False
