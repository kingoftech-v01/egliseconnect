"""Celery tasks for volunteer schedule reminders."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.constants import ScheduleStatus
from apps.communication.models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_volunteer_schedule_reminders():
    """Send 5d/3d/1d/same-day reminders for volunteer schedules."""
    from .models import VolunteerSchedule

    now = timezone.now()
    today = now.date()

    upcoming = VolunteerSchedule.objects.filter(
        date__gte=today,
        status__in=[ScheduleStatus.SCHEDULED, ScheduleStatus.CONFIRMED],
    ).select_related('member', 'position')

    total_sent = 0

    for schedule in upcoming:
        days_until = (schedule.date - today).days
        sent = False

        if days_until <= 5 and not schedule.reminder_5days_sent:
            schedule.reminder_5days_sent = True
            sent = True
            msg = (
                f'Rappel: vous êtes planifié(e) pour "{schedule.position.name}" '
                f'le {schedule.date:%d/%m/%Y} (dans 5 jours).'
            )

        elif days_until <= 3 and not schedule.reminder_3days_sent:
            schedule.reminder_3days_sent = True
            sent = True
            msg = (
                f'Rappel: votre service "{schedule.position.name}" '
                f'est dans 3 jours ({schedule.date:%d/%m/%Y}).'
            )

        elif days_until <= 1 and not schedule.reminder_1day_sent:
            schedule.reminder_1day_sent = True
            sent = True
            msg = (
                f'Rappel: votre service "{schedule.position.name}" '
                f'est DEMAIN ({schedule.date:%d/%m/%Y}).'
            )

        elif days_until == 0 and not schedule.reminder_sameday_sent:
            schedule.reminder_sameday_sent = True
            sent = True
            msg = (
                f"C'est aujourd'hui! Service: \"{schedule.position.name}\"."
            )

        if sent:
            schedule.reminder_sent = True
            schedule.save()
            Notification.objects.create(
                member=schedule.member,
                title='Rappel de bénévolat',
                message=msg,
                notification_type='volunteer',
                link='/volunteers/',
            )
            total_sent += 1

    logger.info(f'Sent {total_sent} volunteer schedule reminders.')
    return total_sent
