"""Celery tasks for volunteer schedule reminders, background check alerts, and milestone checks."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.constants import ScheduleStatus, BackgroundCheckStatus
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
                f'Rappel: vous etes planifie(e) pour "{schedule.position.name}" '
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
                title='Rappel de benevolat',
                message=msg,
                notification_type='volunteer',
                link='/volunteers/',
            )
            total_sent += 1

    logger.info(f'Sent {total_sent} volunteer schedule reminders.')
    return total_sent


@shared_task
def check_background_check_expiry():
    """
    Check for background checks expiring within 30 days and send alerts.
    Also auto-update status to EXPIRED for past-due checks.
    """
    from .models import VolunteerBackgroundCheck

    today = timezone.now().date()
    alert_window = today + timedelta(days=30)

    total_alerts = 0

    # Auto-expire past-due checks
    expired = VolunteerBackgroundCheck.objects.filter(
        expiry_date__lt=today,
        status=BackgroundCheckStatus.APPROVED,
        is_active=True,
    )
    for check in expired:
        check.status = BackgroundCheckStatus.EXPIRED
        check.save(update_fields=['status', 'updated_at'])
        Notification.objects.create(
            member=check.member,
            title='Verification des antecedents expiree',
            message=(
                f'Votre verification des antecedents pour le poste '
                f'"{check.position.name if check.position else "general"}" a expire. '
                f'Veuillez la renouveler.'
            ),
            notification_type='volunteer',
            link='/volunteers/background-checks/',
        )
        total_alerts += 1

    # Alert for checks expiring within 30 days
    expiring_soon = VolunteerBackgroundCheck.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=alert_window,
        status=BackgroundCheckStatus.APPROVED,
        is_active=True,
    )
    for check in expiring_soon:
        days_remaining = (check.expiry_date - today).days
        Notification.objects.create(
            member=check.member,
            title='Verification des antecedents - renouvellement a venir',
            message=(
                f'Votre verification des antecedents expire dans {days_remaining} jours '
                f'({check.expiry_date:%d/%m/%Y}). Planifiez votre renouvellement.'
            ),
            notification_type='volunteer',
            link='/volunteers/background-checks/',
        )
        total_alerts += 1

    logger.info(f'Processed {total_alerts} background check expiry alerts.')
    return total_alerts


@shared_task
def check_volunteer_milestones():
    """
    Check all active volunteers for new milestone achievements.
    Runs periodically (e.g., weekly) to award milestones and send notifications.
    """
    from .models import VolunteerHours
    from .services_recognition import RecognitionService

    # Get all members who have logged hours
    member_ids = (
        VolunteerHours.objects.filter(is_active=True)
        .values_list('member_id', flat=True)
        .distinct()
    )

    from apps.members.models import Member
    members = Member.objects.filter(id__in=member_ids)

    total_new = 0
    for member in members:
        new_achievements = RecognitionService.check_milestones(member)
        for achievement in new_achievements:
            RecognitionService.trigger_notification(achievement)
            total_new += 1

    logger.info(f'Awarded {total_new} new milestone achievements.')
    return total_new


@shared_task
def send_shift_reminders(hours_before=24):
    """
    Send shift reminders X hours before a scheduled shift.
    This is complementary to the day-based reminders above.
    """
    from .models import VolunteerSchedule

    now = timezone.now()
    target_time = now + timedelta(hours=hours_before)
    today = now.date()

    schedules = VolunteerSchedule.objects.filter(
        date=target_time.date(),
        status__in=[ScheduleStatus.SCHEDULED, ScheduleStatus.CONFIRMED],
        is_active=True,
    ).select_related('member', 'position')

    total_sent = 0
    for schedule in schedules:
        Notification.objects.create(
            member=schedule.member,
            title='Rappel de service',
            message=(
                f'Votre service "{schedule.position.name}" est prevu pour '
                f'{schedule.date:%d/%m/%Y}. Merci de votre engagement!'
            ),
            notification_type='volunteer',
            link='/volunteers/my-schedule/',
        )
        total_sent += 1

    logger.info(f'Sent {total_sent} shift reminders ({hours_before}h before).')
    return total_sent


@shared_task
def notify_schedule_changes(schedule_id, change_type='updated'):
    """
    Send push notification when a schedule is changed.

    Args:
        schedule_id: UUID of the changed schedule
        change_type: 'created', 'updated', or 'cancelled'
    """
    from .models import VolunteerSchedule

    try:
        schedule = VolunteerSchedule.objects.select_related('member', 'position').get(pk=schedule_id)
    except VolunteerSchedule.DoesNotExist:
        logger.warning(f'Schedule {schedule_id} not found for change notification.')
        return 0

    messages_map = {
        'created': f'Nouvel horaire: "{schedule.position.name}" le {schedule.date:%d/%m/%Y}.',
        'updated': f'Horaire modifie: "{schedule.position.name}" le {schedule.date:%d/%m/%Y}.',
        'cancelled': f'Horaire annule: "{schedule.position.name}" le {schedule.date:%d/%m/%Y}.',
    }

    Notification.objects.create(
        member=schedule.member,
        title='Changement d\'horaire',
        message=messages_map.get(change_type, messages_map['updated']),
        notification_type='volunteer',
        link='/volunteers/my-schedule/',
    )

    logger.info(f'Schedule change notification sent for {schedule_id} ({change_type}).')
    return 1
