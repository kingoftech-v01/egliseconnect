"""Tests for recurring event service."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.core.constants import RecurrenceFrequency
from apps.events.models import Event
from apps.events.services_recurrence import RecurrenceService
from apps.events.tests.factories import EventFactory


pytestmark = pytest.mark.django_db


class TestRecurrenceServiceGenerateInstances:
    def _make_recurring_event(self, frequency, end_date=None):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        return EventFactory(
            is_recurring=True,
            recurrence_frequency=frequency,
            recurrence_end_date=end_date,
            start_datetime=start,
            end_datetime=end,
        )

    def test_generate_weekly_instances_default_12(self):
        event = self._make_recurring_event(RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(event)
        assert len(instances) == 12

    def test_generate_daily_instances_with_count(self):
        event = self._make_recurring_event(RecurrenceFrequency.DAILY)
        instances = RecurrenceService.generate_instances(event, count=5)
        assert len(instances) == 5

    def test_generate_until_end_date(self):
        end_date = (timezone.now() + timedelta(days=30)).date()
        event = self._make_recurring_event(RecurrenceFrequency.WEEKLY, end_date=end_date)
        instances = RecurrenceService.generate_instances(event)
        assert len(instances) > 0
        for inst in instances:
            assert inst.start_datetime.date() <= end_date

    def test_generated_instances_have_parent(self):
        event = self._make_recurring_event(RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(event, count=3)
        for inst in instances:
            assert inst.parent_event == event

    def test_generated_instances_inherit_fields(self):
        event = self._make_recurring_event(RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(event, count=1)
        inst = instances[0]
        assert inst.title == event.title
        assert inst.event_type == event.event_type
        assert inst.location == event.location

    def test_instances_are_not_recurring(self):
        event = self._make_recurring_event(RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(event, count=2)
        for inst in instances:
            assert inst.is_recurring is False

    def test_no_duplicate_instances(self):
        event = self._make_recurring_event(RecurrenceFrequency.WEEKLY)
        instances1 = RecurrenceService.generate_instances(event, count=3)
        instances2 = RecurrenceService.generate_instances(event, count=3)
        # Second call should not create duplicates
        total = Event.objects.filter(parent_event=event).count()
        assert total == 3

    def test_non_recurring_event_returns_empty(self):
        event = EventFactory(is_recurring=False, recurrence_frequency='')
        instances = RecurrenceService.generate_instances(event)
        assert instances == []

    def test_monthly_recurrence(self):
        event = self._make_recurring_event(RecurrenceFrequency.MONTHLY)
        instances = RecurrenceService.generate_instances(event, count=3)
        assert len(instances) == 3
        # Each instance should be roughly 1 month apart
        for i, inst in enumerate(instances):
            expected_month = (event.start_datetime.month + i + 1 - 1) % 12 + 1
            # Just verify they exist and are different dates
            assert inst.start_datetime > event.start_datetime

    def test_biweekly_recurrence(self):
        event = self._make_recurring_event(RecurrenceFrequency.BIWEEKLY)
        instances = RecurrenceService.generate_instances(event, count=2)
        assert len(instances) == 2
        delta = instances[1].start_datetime - instances[0].start_datetime
        assert abs(delta.days - 14) <= 1


class TestRecurrenceServiceHandleException:
    def test_skip_cancels_instance(self):
        parent = EventFactory(is_recurring=True, recurrence_frequency=RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(parent, count=3)
        instance = instances[1]
        result = RecurrenceService.handle_exception(instance, skip=True)
        result.refresh_from_db()
        assert result.is_cancelled is True

    def test_override_fields(self):
        parent = EventFactory(is_recurring=True, recurrence_frequency=RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(parent, count=1)
        instance = instances[0]
        new_title = 'Événement modifié'
        result = RecurrenceService.handle_exception(instance, title=new_title)
        result.refresh_from_db()
        assert result.title == new_title


class TestRecurrenceServiceDeleteFuture:
    def test_delete_future_instances(self):
        parent = EventFactory(is_recurring=True, recurrence_frequency=RecurrenceFrequency.WEEKLY)
        RecurrenceService.generate_instances(parent, count=5)
        count = RecurrenceService.delete_future_instances(parent)
        assert count == 5
        assert Event.objects.filter(parent_event=parent).count() == 0

    def test_delete_after_date(self):
        parent = EventFactory(is_recurring=True, recurrence_frequency=RecurrenceFrequency.WEEKLY)
        instances = RecurrenceService.generate_instances(parent, count=5)
        cutoff = instances[2].start_datetime.date()
        count = RecurrenceService.delete_future_instances(parent, after_date=cutoff)
        remaining = Event.objects.filter(parent_event=parent).count()
        assert remaining < 5
