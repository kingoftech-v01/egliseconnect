"""Celery tasks for worship service reminders."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.constants import AssignmentStatus, WorshipServiceStatus
from apps.communication.models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_service_assignment_reminders():
    """Send reminders at 5d/3d/1d/same-day before a worship service."""
    from .models import ServiceAssignment, WorshipService

    now = timezone.now()
    today = now.date()

    # Get upcoming confirmed/planned services
    upcoming_services = WorshipService.objects.filter(
        date__gte=today,
        status__in=[WorshipServiceStatus.PLANNED, WorshipServiceStatus.CONFIRMED],
    )

    total_sent = 0

    for service in upcoming_services:
        days_until = (service.date - today).days
        assignments = ServiceAssignment.objects.filter(
            section__service=service,
            status__in=[AssignmentStatus.ASSIGNED, AssignmentStatus.CONFIRMED],
        ).select_related('member', 'section')

        for assignment in assignments:
            sent = False

            if days_until <= 5 and not assignment.reminder_5days_sent:
                assignment.reminder_5days_sent = True
                sent = True
                msg = f'Rappel: vous \u00eates assign\u00e9(e) au culte du {service.date:%d/%m/%Y} dans 5 jours.'

            elif days_until <= 3 and not assignment.reminder_3days_sent:
                assignment.reminder_3days_sent = True
                sent = True
                msg = f'Rappel: le culte du {service.date:%d/%m/%Y} est dans 3 jours. Section: {assignment.section.name}.'

            elif days_until <= 1 and not assignment.reminder_1day_sent:
                assignment.reminder_1day_sent = True
                sent = True
                msg = f'Rappel: le culte est DEMAIN ({service.date:%d/%m/%Y}). Section: {assignment.section.name}.'

            elif days_until == 0 and not assignment.reminder_sameday_sent:
                assignment.reminder_sameday_sent = True
                sent = True
                msg = f"C'est aujourd'hui! Culte \u00e0 {service.start_time:%H:%M}. Section: {assignment.section.name}."

            if sent:
                assignment.save()
                Notification.objects.create(
                    member=assignment.member,
                    title='Rappel de culte',
                    message=msg,
                    notification_type='general',
                    link='/worship/my-assignments/',
                )
                total_sent += 1

    logger.info(f'Sent {total_sent} worship service reminders.')
    return total_sent


@shared_task
def check_validation_deadlines():
    """Alert admins about services past their validation deadline with unconfirmed assignments."""
    from .models import WorshipService, ServiceAssignment
    from apps.members.models import Member
    from apps.core.constants import Roles

    today = timezone.now().date()
    overdue_services = WorshipService.objects.filter(
        validation_deadline__lt=today,
        status__in=[WorshipServiceStatus.DRAFT, WorshipServiceStatus.PLANNED],
    )

    for service in overdue_services:
        unconfirmed = ServiceAssignment.objects.filter(
            section__service=service,
            status=AssignmentStatus.ASSIGNED,
        ).count()

        if unconfirmed > 0:
            admins = Member.objects.filter(role__in=[Roles.ADMIN, Roles.PASTOR])
            for admin in admins:
                Notification.objects.create(
                    member=admin,
                    title='Deadline de validation d\u00e9pass\u00e9e',
                    message=(
                        f'Le culte du {service.date:%d/%m/%Y} a {unconfirmed} '
                        f'assignation(s) non confirm\u00e9e(s) apr\u00e8s la date limite.'
                    ),
                    notification_type='general',
                    link=f'/worship/services/{service.pk}/',
                )


@shared_task
def update_song_usage_on_completion():
    """Track song usage for recently completed services."""
    from .models import WorshipService
    from .services import SongUsageTracker

    today = timezone.now().date()
    # Find services completed today that haven't had usage tracked
    recently_completed = WorshipService.objects.filter(
        status=WorshipServiceStatus.COMPLETED,
        date=today,
    )

    total = 0
    for service in recently_completed:
        count = SongUsageTracker.record_service_songs(service)
        total += count

    logger.info(f'Updated song usage for {total} songs from completed services.')
    return total
