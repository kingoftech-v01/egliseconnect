"""Tests for the generic reminder utility."""
import pytest
from datetime import timedelta
from unittest.mock import MagicMock

from django.utils import timezone

from apps.communication.models import Notification
from apps.core.reminders import send_reminder_batch
from apps.members.tests.factories import MemberFactory


class FakeItem:
    """Fake item with reminder fields for testing send_reminder_batch."""

    def __init__(self, target_date, member):
        self.target_date = target_date
        self.member = member
        self.reminder_5days_sent = False
        self.reminder_3days_sent = False
        self.reminder_1day_sent = False
        self.reminder_sameday_sent = False
        self.saved = False

    def save(self):
        self.saved = True


@pytest.mark.django_db
class TestSendReminderBatch:
    """Tests for the generic send_reminder_batch utility."""

    def _make_item(self, days_from_now, **overrides):
        member = MemberFactory()
        target_date = timezone.now().date() + timedelta(days=days_from_now)
        item = FakeItem(target_date=target_date, member=member)
        for k, v in overrides.items():
            setattr(item, k, v)
        return item

    def _run(self, items, link='/test/'):
        return send_reminder_batch(
            items=items,
            get_date=lambda it: it.target_date,
            get_member=lambda it: it.member,
            make_message=lambda it, label: f'Rappel {label}',
            link=link,
        )

    def test_5_day_reminder(self):
        """Item 5 days away gets 5-day reminder."""
        item = self._make_item(5)
        result = self._run([item])

        assert result == 1
        assert item.reminder_5days_sent is True
        assert item.saved is True
        notif = Notification.objects.get(member=item.member)
        assert '5 jours' in notif.message

    def test_3_day_reminder(self):
        """Item 3 days away (with 5-day already sent) gets 3-day reminder."""
        item = self._make_item(3, reminder_5days_sent=True)
        result = self._run([item])

        assert result == 1
        assert item.reminder_3days_sent is True

    def test_1_day_reminder(self):
        """Item 1 day away (with 5/3 already sent) gets 1-day reminder."""
        item = self._make_item(1, reminder_5days_sent=True, reminder_3days_sent=True)
        result = self._run([item])

        assert result == 1
        assert item.reminder_1day_sent is True

    def test_same_day_reminder(self):
        """Item today (with 5/3/1 already sent) gets same-day reminder."""
        item = self._make_item(
            0,
            reminder_5days_sent=True,
            reminder_3days_sent=True,
            reminder_1day_sent=True,
        )
        result = self._run([item])

        assert result == 1
        assert item.reminder_sameday_sent is True

    def test_no_duplicate(self):
        """All flags already set → no notification sent."""
        item = self._make_item(
            0,
            reminder_5days_sent=True,
            reminder_3days_sent=True,
            reminder_1day_sent=True,
            reminder_sameday_sent=True,
        )
        result = self._run([item])

        assert result == 0
        assert Notification.objects.filter(member=item.member).count() == 0

    def test_6_days_away_no_reminder(self):
        """Item more than 5 days away gets no reminder."""
        item = self._make_item(6)
        result = self._run([item])

        assert result == 0
        assert item.saved is False

    def test_none_date_skipped(self):
        """Item with None target_date is skipped."""
        item = self._make_item(5)
        item.target_date = None
        result = self._run([item])

        assert result == 0
        assert item.saved is False

    def test_notification_link(self):
        """Notification uses the provided link."""
        item = self._make_item(5)
        self._run([item], link='/my-link/')

        notif = Notification.objects.get(member=item.member)
        assert notif.link == '/my-link/'

    def test_multiple_items(self):
        """Multiple items all get processed."""
        items = [
            self._make_item(5),
            self._make_item(3, reminder_5days_sent=True),
            self._make_item(0, reminder_5days_sent=True, reminder_3days_sent=True, reminder_1day_sent=True),
        ]
        result = self._run(items)

        assert result == 3
        assert items[0].reminder_5days_sent is True
        assert items[1].reminder_3days_sent is True
        assert items[2].reminder_sameday_sent is True

    def test_empty_items(self):
        """Empty list returns 0."""
        result = self._run([])
        assert result == 0
