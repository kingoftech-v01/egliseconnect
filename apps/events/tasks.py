"""Celery tasks for events — registration confirmations, survey sending."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_registration_confirmation(entry_id):
    """Send email confirmation when a member registers for an event."""
    from .models import RegistrationEntry
    from apps.communication.models import Notification

    try:
        entry = RegistrationEntry.objects.select_related(
            'member', 'form__event',
        ).get(pk=entry_id)
    except RegistrationEntry.DoesNotExist:
        logger.warning(f'RegistrationEntry {entry_id} not found.')
        return

    event = entry.form.event
    Notification.objects.create(
        member=entry.member,
        title='Confirmation d\'inscription',
        message=(
            f'Votre inscription à l\'événement "{event.title}" '
            f'du {event.start_datetime:%d/%m/%Y à %H:%M} a été confirmée.'
        ),
        notification_type='event',
        link=f'/events/{event.pk}/',
    )
    logger.info(f'Registration confirmation sent for {entry.member.full_name} -> {event.title}')


@shared_task
def send_pending_surveys():
    """Check for surveys that should be sent after their event ends."""
    from .models import EventSurvey
    from apps.core.constants import RSVPStatus
    from apps.communication.models import Notification

    now = timezone.now()
    surveys = EventSurvey.objects.filter(
        survey_sent=False,
        is_active=True,
        event__is_cancelled=False,
    ).select_related('event')

    total_sent = 0
    for survey in surveys:
        send_after = survey.event.end_datetime + timedelta(hours=survey.send_after_hours)
        if now >= send_after:
            # Send notification to all confirmed attendees
            rsvps = survey.event.rsvps.filter(
                status=RSVPStatus.CONFIRMED,
            ).select_related('member')

            for rsvp in rsvps:
                Notification.objects.create(
                    member=rsvp.member,
                    title=f'Sondage: {survey.title}',
                    message=(
                        f'Merci d\'avoir participé à "{survey.event.title}". '
                        f'Veuillez remplir notre court sondage.'
                    ),
                    notification_type='event',
                    link=f'/events/{survey.event.pk}/survey/{survey.pk}/respond/',
                )
                total_sent += 1

            survey.survey_sent = True
            survey.save(update_fields=['survey_sent', 'updated_at'])

    logger.info(f'Sent {total_sent} survey notifications.')
    return total_sent


@shared_task
def send_waitlist_promotion_notification(waitlist_entry_id):
    """Notify a member that they've been promoted from the waitlist."""
    from .models import EventWaitlist
    from apps.communication.models import Notification

    try:
        entry = EventWaitlist.objects.select_related(
            'member', 'event',
        ).get(pk=waitlist_entry_id)
    except EventWaitlist.DoesNotExist:
        logger.warning(f'EventWaitlist {waitlist_entry_id} not found.')
        return

    Notification.objects.create(
        member=entry.member,
        title='Place disponible!',
        message=(
            f'Une place s\'est libérée pour l\'événement "{entry.event.title}". '
            f'Vous avez été inscrit(e) automatiquement.'
        ),
        notification_type='event',
        link=f'/events/{entry.event.pk}/',
    )
    logger.info(f'Waitlist promotion notification sent to {entry.member.full_name}')
