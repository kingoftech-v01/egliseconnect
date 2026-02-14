"""Celery tasks for help requests follow-up reminders and escalation."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.constants import CareStatus

logger = logging.getLogger(__name__)


@shared_task
def send_follow_up_reminders():
    """Auto-notify assigned staff when follow_up_date arrives (today)."""
    from .models import PastoralCare
    from apps.communication.models import Notification

    today = timezone.now().date()
    due_today = PastoralCare.objects.filter(
        follow_up_date=today,
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
    ).select_related('member', 'assigned_to')

    total_sent = 0
    for care in due_today:
        recipient = care.assigned_to or care.created_by
        if recipient:
            Notification.objects.create(
                member=recipient,
                title='Rappel de suivi pastoral',
                message=(
                    f'Suivi prévu aujourd\'hui pour {care.member.full_name} '
                    f'({care.get_care_type_display()}).'
                ),
                notification_type='help_request',
                link=f'/help-requests/care/{care.pk}/',
            )
            total_sent += 1

    logger.info(f'Sent {total_sent} follow-up reminders.')
    return total_sent


@shared_task
def escalate_overdue_follow_ups(days_overdue=7):
    """Escalate cases with no follow-up after X days to pastors/admins."""
    from .models import PastoralCare
    from apps.communication.models import Notification
    from apps.members.models import Member

    today = timezone.now().date()
    cutoff = today - timedelta(days=days_overdue)

    overdue = PastoralCare.objects.filter(
        follow_up_date__lte=cutoff,
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
    ).select_related('member', 'assigned_to')

    # Get all pastors/admins as escalation targets
    supervisors = Member.objects.filter(
        role__in=['pastor', 'admin'],
        is_active=True,
    )

    total_sent = 0
    for care in overdue:
        for supervisor in supervisors:
            Notification.objects.create(
                member=supervisor,
                title='Escalade: suivi en retard',
                message=(
                    f'Le suivi pour {care.member.full_name} est en retard de '
                    f'{(today - care.follow_up_date).days} jours '
                    f'({care.get_care_type_display()}).'
                ),
                notification_type='help_request',
                link=f'/help-requests/care/{care.pk}/',
            )
            total_sent += 1

    logger.info(f'Sent {total_sent} escalation notifications.')
    return total_sent


@shared_task
def snooze_follow_up(care_id, days=1):
    """Postpone a follow-up by a given number of days (1, 3, or 7)."""
    from .models import PastoralCare

    try:
        care = PastoralCare.objects.get(pk=care_id)
    except PastoralCare.DoesNotExist:
        logger.warning(f'PastoralCare {care_id} not found for snooze.')
        return None

    if care.follow_up_date:
        care.follow_up_date = care.follow_up_date + timedelta(days=days)
    else:
        care.follow_up_date = timezone.now().date() + timedelta(days=days)

    care.save(update_fields=['follow_up_date', 'updated_at'])
    logger.info(f'Snoozed follow-up for care {care_id} by {days} days.')
    return str(care.follow_up_date)


@shared_task
def log_follow_up_completion(care_id, notes='', next_steps=''):
    """Log completion of a follow-up with notes and next steps."""
    from .models import PastoralCare

    try:
        care = PastoralCare.objects.get(pk=care_id)
    except PastoralCare.DoesNotExist:
        logger.warning(f'PastoralCare {care_id} not found for completion log.')
        return False

    completion_note = f"[Suivi complété] {notes}"
    if next_steps:
        completion_note += f"\n[Prochaines étapes] {next_steps}"

    if care.notes:
        care.notes += f"\n\n{completion_note}"
    else:
        care.notes = completion_note

    care.status = CareStatus.FOLLOW_UP
    care.save(update_fields=['notes', 'status', 'updated_at'])

    logger.info(f'Logged follow-up completion for care {care_id}.')
    return True
