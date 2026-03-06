"""Recurrence service — generate recurring event instances and handle exceptions."""
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from apps.core.constants import RecurrenceFrequency
from .models import Event


class RecurrenceService:
    """Generate and manage recurring event instances."""

    FREQUENCY_DELTAS = {
        RecurrenceFrequency.DAILY: timedelta(days=1),
        RecurrenceFrequency.WEEKLY: timedelta(weeks=1),
        RecurrenceFrequency.BIWEEKLY: timedelta(weeks=2),
        RecurrenceFrequency.MONTHLY: None,  # use relativedelta
        RecurrenceFrequency.YEARLY: None,   # use relativedelta
    }

    @staticmethod
    def generate_instances(parent_event, count=None):
        """
        Generate recurring event instances from a parent event.
        Returns list of created Event instances.

        If count is None, generates until recurrence_end_date.
        If neither count nor recurrence_end_date is set, generates 12 instances.
        """
        if not parent_event.is_recurring or not parent_event.recurrence_frequency:
            return []

        freq = parent_event.recurrence_frequency
        end_date = parent_event.recurrence_end_date
        max_count = count or (52 if not end_date else 365)  # safety limit

        # Calculate event duration
        duration = parent_event.end_datetime - parent_event.start_datetime

        instances = []
        current_start = parent_event.start_datetime
        generated = 0

        while generated < max_count:
            # Advance to next occurrence
            current_start = RecurrenceService._next_occurrence(current_start, freq)
            current_end = current_start + duration

            # Check end_date
            if end_date and current_start.date() > end_date:
                break

            # Check count limit (default 12 if no end date)
            if not end_date and count is None and generated >= 12:
                break

            # Check if this instance already exists (by start_datetime)
            if Event.all_objects.filter(
                parent_event=parent_event,
                start_datetime=current_start,
            ).exists():
                generated += 1
                continue

            instance = Event.objects.create(
                title=parent_event.title,
                description=parent_event.description,
                event_type=parent_event.event_type,
                start_datetime=current_start,
                end_datetime=current_end,
                all_day=parent_event.all_day,
                location=parent_event.location,
                location_address=parent_event.location_address,
                is_online=parent_event.is_online,
                online_link=parent_event.online_link,
                organizer=parent_event.organizer,
                max_attendees=parent_event.max_attendees,
                requires_rsvp=parent_event.requires_rsvp,
                is_published=parent_event.is_published,
                is_recurring=False,
                parent_event=parent_event,
                virtual_url=parent_event.virtual_url,
                virtual_platform=parent_event.virtual_platform,
                is_hybrid=parent_event.is_hybrid,
                campus=parent_event.campus,
                kiosk_mode_enabled=parent_event.kiosk_mode_enabled,
            )
            # Auto-create attendance session for child event
            from apps.attendance.models import AttendanceSession
            from apps.core.constants import AttendanceSessionType, EventType
            session_type_map = {
                EventType.WORSHIP: AttendanceSessionType.WORSHIP,
                EventType.TRAINING: AttendanceSessionType.LESSON,
            }
            AttendanceSession.objects.create(
                name=instance.title,
                session_type=session_type_map.get(instance.event_type, AttendanceSessionType.EVENT),
                date=current_start.date(),
                start_time=current_start.time(),
                end_time=current_end.time() if current_end else None,
                event=instance,
                opened_by=parent_event.organizer,
            )
            instances.append(instance)
            generated += 1

        return instances

    @staticmethod
    def _next_occurrence(current_dt, frequency):
        """Calculate the next occurrence datetime."""
        if frequency == RecurrenceFrequency.DAILY:
            return current_dt + timedelta(days=1)
        elif frequency == RecurrenceFrequency.WEEKLY:
            return current_dt + timedelta(weeks=1)
        elif frequency == RecurrenceFrequency.BIWEEKLY:
            return current_dt + timedelta(weeks=2)
        elif frequency == RecurrenceFrequency.MONTHLY:
            return current_dt + relativedelta(months=1)
        elif frequency == RecurrenceFrequency.YEARLY:
            return current_dt + relativedelta(years=1)
        else:
            return current_dt + timedelta(weeks=1)

    @staticmethod
    def handle_exception(instance, skip=False, **overrides):
        """
        Handle a recurring event exception.
        If skip=True, cancel the instance.
        Otherwise, apply overrides (title, start_datetime, etc.) to the instance.
        """
        if skip:
            instance.is_cancelled = True
            instance.save(update_fields=['is_cancelled', 'updated_at'])
            return instance

        for field, value in overrides.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        instance.save()
        return instance

    @staticmethod
    def delete_future_instances(parent_event, after_date=None):
        """Delete all future instances of a recurring event."""
        qs = Event.objects.filter(parent_event=parent_event)
        if after_date:
            qs = qs.filter(start_datetime__date__gt=after_date)
        else:
            qs = qs.filter(start_datetime__gt=timezone.now())
        count = qs.count()
        qs.delete()
        return count
