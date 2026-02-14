"""Celery tasks for onboarding reminders and expiration."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.constants import LessonStatus, InterviewStatus
from apps.communication.models import Notification

logger = logging.getLogger(__name__)


@shared_task
def check_expired_forms():
    """Run daily: expire accounts that missed the form deadline."""
    from .services import OnboardingService
    count = OnboardingService.expire_overdue_members()
    logger.info(f'{count} member accounts expired')
    return count


@shared_task
def send_form_deadline_reminders():
    """Run daily: send reminders at 7 days, 3 days, and 1 day before form deadline."""
    from apps.members.models import Member
    from apps.core.constants import MembershipStatus

    today = timezone.localdate()

    for days_before in [7, 3, 1]:
        target_date = today + timedelta(days=days_before)
        members = Member.objects.filter(
            membership_status__in=[
                MembershipStatus.REGISTERED,
                MembershipStatus.FORM_PENDING,
            ],
            form_deadline__date=target_date,
        )
        for member in members:
            Notification.objects.create(
                member=member,
                title=f'Rappel: {days_before} jour(s) restant(s)',
                message=(
                    f'Il vous reste {days_before} jour(s) pour soumettre '
                    f'votre formulaire d\'adhesion.'
                ),
                notification_type='general',
                link='/onboarding/form/',
            )
            logger.info(f'Form reminder ({days_before}d) sent to {member.full_name}')


@shared_task
def send_lesson_reminders():
    """Run daily: send lesson reminders at J-3, J-1, and same day."""
    from .models import ScheduledLesson

    today = timezone.localdate()

    # 5 days before
    lessons_5d = ScheduledLesson.objects.filter(
        scheduled_date__date=today + timedelta(days=5),
        status=LessonStatus.UPCOMING,
        reminder_5days_sent=False,
    )
    for sl in lessons_5d:
        Notification.objects.create(
            member=sl.training.member,
            title='Rappel: Lecon dans 5 jours',
            message=(
                f'Lecon "{sl.lesson.title}" prevue le '
                f'{sl.scheduled_date:%d/%m/%Y a %H:%M}. Presence obligatoire.'
            ),
            notification_type='event',
            link='/onboarding/training/',
        )
        sl.reminder_5days_sent = True
        sl.save(update_fields=['reminder_5days_sent', 'updated_at'])

    # 3 days before
    lessons_3d = ScheduledLesson.objects.filter(
        scheduled_date__date=today + timedelta(days=3),
        status=LessonStatus.UPCOMING,
        reminder_3days_sent=False,
    )
    for sl in lessons_3d:
        Notification.objects.create(
            member=sl.training.member,
            title=f'Rappel: Lecon dans 3 jours',
            message=(
                f'Lecon "{sl.lesson.title}" prevue le '
                f'{sl.scheduled_date:%d/%m/%Y a %H:%M}. Presence obligatoire.'
            ),
            notification_type='event',
            link='/onboarding/training/',
        )
        sl.reminder_3days_sent = True
        sl.save(update_fields=['reminder_3days_sent', 'updated_at'])

    # 1 day before
    lessons_1d = ScheduledLesson.objects.filter(
        scheduled_date__date=today + timedelta(days=1),
        status=LessonStatus.UPCOMING,
        reminder_1day_sent=False,
    )
    for sl in lessons_1d:
        Notification.objects.create(
            member=sl.training.member,
            title='Rappel: Lecon DEMAIN',
            message=(
                f'Lecon "{sl.lesson.title}" demain a '
                f'{sl.scheduled_date:%H:%M}. Presence obligatoire.'
            ),
            notification_type='event',
            link='/onboarding/training/',
        )
        sl.reminder_1day_sent = True
        sl.save(update_fields=['reminder_1day_sent', 'updated_at'])

    # Same day
    lessons_today = ScheduledLesson.objects.filter(
        scheduled_date__date=today,
        status=LessonStatus.UPCOMING,
        reminder_sameday_sent=False,
    )
    for sl in lessons_today:
        Notification.objects.create(
            member=sl.training.member,
            title="Rappel: Lecon AUJOURD'HUI",
            message=(
                f'Lecon "{sl.lesson.title}" aujourd\'hui a '
                f'{sl.scheduled_date:%H:%M}. Presence obligatoire.'
            ),
            notification_type='event',
            link='/onboarding/training/',
        )
        sl.reminder_sameday_sent = True
        sl.save(update_fields=['reminder_sameday_sent', 'updated_at'])


@shared_task
def send_interview_reminders():
    """Run daily: send interview reminders at J-3, J-1, and same day."""
    from .models import Interview

    today = timezone.localdate()

    active_statuses = [InterviewStatus.CONFIRMED, InterviewStatus.ACCEPTED]

    # 5 days before
    interviews_5d = Interview.objects.filter(
        status__in=active_statuses,
        reminder_5days_sent=False,
    ).exclude(confirmed_date__isnull=True).filter(
        confirmed_date__date=today + timedelta(days=5)
    )
    for iv in interviews_5d:
        Notification.objects.create(
            member=iv.member,
            title='Rappel: Interview dans 5 jours',
            message=(
                f'Votre interview finale est le '
                f'{iv.final_date:%d/%m/%Y a %H:%M}. '
                'Presence obligatoire - pas de deuxieme chance.'
            ),
            notification_type='event',
            link='/onboarding/interview/',
        )
        iv.reminder_5days_sent = True
        iv.save(update_fields=['reminder_5days_sent', 'updated_at'])

    # 3 days before
    interviews_3d = Interview.objects.filter(
        status__in=active_statuses,
        reminder_3days_sent=False,
    ).exclude(confirmed_date__isnull=True).filter(
        confirmed_date__date=today + timedelta(days=3)
    )
    for iv in interviews_3d:
        Notification.objects.create(
            member=iv.member,
            title='Rappel: Interview dans 3 jours',
            message=(
                f'Votre interview finale est le '
                f'{iv.final_date:%d/%m/%Y a %H:%M}. '
                'Presence obligatoire - pas de deuxieme chance.'
            ),
            notification_type='event',
            link='/onboarding/interview/',
        )
        iv.reminder_3days_sent = True
        iv.save(update_fields=['reminder_3days_sent', 'updated_at'])

    # 1 day before
    interviews_1d = Interview.objects.filter(
        status__in=active_statuses,
        reminder_1day_sent=False,
    ).exclude(confirmed_date__isnull=True).filter(
        confirmed_date__date=today + timedelta(days=1)
    )
    for iv in interviews_1d:
        Notification.objects.create(
            member=iv.member,
            title='Rappel: Interview DEMAIN',
            message=(
                f'Votre interview finale est DEMAIN a '
                f'{iv.final_date:%H:%M}. '
                'Presence obligatoire - pas de deuxieme chance.'
            ),
            notification_type='event',
            link='/onboarding/interview/',
        )
        iv.reminder_1day_sent = True
        iv.save(update_fields=['reminder_1day_sent', 'updated_at'])

    # Same day
    interviews_today = Interview.objects.filter(
        status__in=active_statuses,
        reminder_sameday_sent=False,
    ).exclude(confirmed_date__isnull=True).filter(
        confirmed_date__date=today
    )
    for iv in interviews_today:
        Notification.objects.create(
            member=iv.member,
            title="Rappel: Interview AUJOURD'HUI",
            message=(
                f"Votre interview finale est AUJOURD'HUI a "
                f'{iv.final_date:%H:%M}. '
                'Presence obligatoire.'
            ),
            notification_type='event',
            link='/onboarding/interview/',
        )
        iv.reminder_sameday_sent = True
        iv.save(update_fields=['reminder_sameday_sent', 'updated_at'])


# ─── P1: Welcome Sequence Processing (item 13) ──────────────────────────────


@shared_task
def process_welcome_sequences():
    """Run daily: advance welcome sequences for all active members."""
    from .models import WelcomeProgress
    from .services import OnboardingService

    active_progress = WelcomeProgress.objects.filter(
        completed_at__isnull=True,
        is_active=True,
    ).select_related('member', 'sequence')

    processed = 0
    for progress in active_progress:
        step = OnboardingService.advance_welcome_sequence(progress)
        if step:
            processed += 1
            logger.info(
                f'Welcome step "{step.subject}" sent to {progress.member.full_name}'
            )

    logger.info(f'{processed} welcome sequence step(s) processed')
    return processed
