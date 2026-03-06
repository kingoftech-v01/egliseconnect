"""Celery tasks for donation reminders and scheduled jobs."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.constants import PledgeStatus, PledgeFrequency

logger = logging.getLogger(__name__)


@shared_task
def send_pledge_reminders():
    """
    Send reminders for pledges that are due.

    Checks active pledges and sends notifications based on frequency:
    - Weekly: remind every Monday
    - Biweekly: remind every other Monday
    - Monthly: remind on the 1st of each month
    - Quarterly: remind on the 1st of each quarter
    - Annually: remind on the pledge start date anniversary
    """
    from .models import Pledge
    from apps.communication.models import Notification

    today = timezone.now().date()
    total_sent = 0

    active_pledges = Pledge.objects.filter(
        status=PledgeStatus.ACTIVE,
        is_active=True,
    ).select_related('member', 'campaign')

    for pledge in active_pledges:
        # Skip if end date has passed
        if pledge.end_date and today > pledge.end_date:
            continue

        should_remind = False

        if pledge.frequency == PledgeFrequency.WEEKLY:
            # Remind on Mondays
            should_remind = today.weekday() == 0

        elif pledge.frequency == PledgeFrequency.BIWEEKLY:
            # Remind every other Monday from start date
            if today.weekday() == 0:
                weeks_since_start = (today - pledge.start_date).days // 7
                should_remind = weeks_since_start % 2 == 0

        elif pledge.frequency == PledgeFrequency.MONTHLY:
            # Remind on the 1st of each month
            should_remind = today.day == 1

        elif pledge.frequency == PledgeFrequency.QUARTERLY:
            # Remind on the 1st of Jan, Apr, Jul, Oct
            should_remind = today.day == 1 and today.month in [1, 4, 7, 10]

        elif pledge.frequency == PledgeFrequency.ANNUALLY:
            # Remind on the start date anniversary
            should_remind = (
                today.month == pledge.start_date.month and
                today.day == pledge.start_date.day
            )

        elif pledge.frequency == PledgeFrequency.ONE_TIME:
            # Remind once if not yet fulfilled
            if pledge.progress_percentage < 100:
                days_since_start = (today - pledge.start_date).days
                should_remind = days_since_start in [7, 30]  # 1 week and 1 month

        if should_remind:
            try:
                campaign_text = (
                    f' pour {pledge.campaign.name}' if pledge.campaign else ''
                )
                Notification.objects.create(
                    member=pledge.member,
                    title='Rappel d\'engagement',
                    message=(
                        f'Rappel: votre engagement de {pledge.amount}${campaign_text} '
                        f'est de {pledge.progress_percentage}% realise. '
                        f'Reste: {pledge.remaining_amount}$.'
                    ),
                    notification_type='donation',
                    link='/donations/pledges/',
                )
                total_sent += 1
            except Exception as e:
                logger.error(
                    f'Failed to send pledge reminder for pledge {pledge.pk}: {e}'
                )

    logger.info(f'Sent {total_sent} pledge reminder(s)')
    return total_sent


@shared_task
def send_donation_confirmation_email(donation_id):
    """Send a confirmation email after a donation is recorded."""
    from .models import Donation
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        donation = Donation.objects.select_related('member').get(pk=donation_id)
    except Donation.DoesNotExist:
        logger.error(f'Donation {donation_id} not found for confirmation email')
        return

    member = donation.member
    if not member.email:
        logger.info(f'No email for member {member.pk}, skipping confirmation')
        return

    church_name = getattr(settings, 'CHURCH_NAME', 'EgliseConnect')

    subject = f'{church_name} - Confirmation de don'
    message = (
        f'Bonjour {member.full_name},\n\n'
        f'Votre don de {donation.amount}$ a ete enregistre avec succes.\n'
        f'Numero de don: {donation.donation_number}\n'
        f'Date: {donation.date}\n'
        f'Type: {donation.get_donation_type_display()}\n\n'
        f'Merci pour votre generosite!\n\n'
        f'{church_name}'
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [member.email],
            fail_silently=True,
        )
        logger.info(f'Donation confirmation email sent for {donation.donation_number}')
    except Exception as e:
        logger.error(f'Failed to send donation confirmation email: {e}')
