"""Celery tasks for communication app."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_automation_steps():
    """Process all pending automation enrollment steps."""
    from .services_automation import AutomationService

    service = AutomationService()
    count = service.process_pending_steps()
    return f"Processed {count} automation steps."


@shared_task
def send_birthday_messages():
    """
    Send automated birthday messages (email/SMS/push) to members
    whose birthday is today.
    """
    from django.utils import timezone
    from apps.members.models import Member
    from apps.core.constants import NotificationType
    from .models import Notification, SMSMessage, NotificationPreference
    from .services_sms import TwilioSMSService
    from .services_push import WebPushService

    today = timezone.now().date()
    birthday_members = Member.objects.filter(
        birth_date__month=today.month,
        birth_date__day=today.day,
        is_active=True,
    )

    sms_service = TwilioSMSService()
    push_service = WebPushService()
    count = 0

    for member in birthday_members:
        # In-app notification
        Notification.objects.create(
            member=member,
            title="Joyeux anniversaire!",
            message=f"Toute l'eglise vous souhaite un joyeux anniversaire, {member.full_name}!",
            notification_type=NotificationType.BIRTHDAY,
        )

        # Check preferences
        prefs = NotificationPreference.objects.filter(member=member).first()

        # SMS if enabled
        if prefs and prefs.sms_enabled and member.phone:
            sms = SMSMessage.objects.create(
                recipient_member=member,
                phone_number=member.phone,
                body=f"Joyeux anniversaire, {member.full_name}! Votre eglise pense a vous.",
            )
            sms_service.send_sms(sms)

        # Push if enabled
        if prefs and prefs.push_enabled:
            push_service.send_to_member(
                member,
                "Joyeux anniversaire!",
                f"Toute l'eglise vous souhaite un joyeux anniversaire!",
            )

        count += 1
        logger.info("Birthday message sent to %s", member.pk)

    return f"Sent birthday messages to {count} members."


@shared_task
def send_anniversary_messages():
    """
    Send automated membership anniversary messages to members
    whose registration anniversary is today.
    """
    from django.utils import timezone
    from apps.members.models import Member
    from apps.core.constants import NotificationType
    from .models import Notification

    today = timezone.now().date()
    anniversary_members = Member.objects.filter(
        registration_date__month=today.month,
        registration_date__day=today.day,
        is_active=True,
    ).exclude(registration_date__year=today.year)  # Skip first-day members

    count = 0
    for member in anniversary_members:
        years = today.year - member.registration_date.year
        Notification.objects.create(
            member=member,
            title=f"Joyeux {years}e anniversaire de membre!",
            message=f"Felicitations {member.full_name}! Cela fait {years} an(s) que vous etes membre de notre eglise.",
            notification_type=NotificationType.GENERAL,
        )
        count += 1
        logger.info("Anniversary message sent to %s (%d years)", member.pk, years)

    return f"Sent anniversary messages to {count} members."


@shared_task
def send_reengagement_messages():
    """
    Send re-engagement messages to members who have been inactive for a
    configurable number of weeks (default 8 weeks without activity).
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.members.models import Member
    from apps.core.constants import NotificationType
    from .models import Notification

    weeks_threshold = 8
    cutoff = timezone.now() - timedelta(weeks=weeks_threshold)

    # Members who haven't updated their profile or had any recent activity
    inactive_members = Member.objects.filter(
        is_active=True,
        updated_at__lt=cutoff,
    )

    count = 0
    for member in inactive_members:
        # Avoid sending duplicate re-engagement notifications
        recent = Notification.objects.filter(
            member=member,
            title__icontains='manquez',
            created_at__gte=cutoff,
        ).exists()

        if not recent:
            Notification.objects.create(
                member=member,
                title="Vous nous manquez!",
                message=f"Bonjour {member.full_name}, nous n'avons pas eu de vos nouvelles recemment. N'hesitez pas a nous contacter!",
                notification_type=NotificationType.GENERAL,
            )
            count += 1

    return f"Sent re-engagement messages to {count} members."


@shared_task
def send_newsletter_task(newsletter_id):
    """Send a newsletter to all its recipients asynchronously."""
    from django.utils import timezone
    from apps.core.constants import NewsletterStatus
    from .models import Newsletter

    try:
        newsletter = Newsletter.all_objects.get(pk=newsletter_id)
    except Newsletter.DoesNotExist:
        logger.error("Newsletter %s not found.", newsletter_id)
        return

    newsletter.status = NewsletterStatus.SENT
    newsletter.sent_at = timezone.now()
    newsletter.save(update_fields=['status', 'sent_at', 'updated_at'])

    logger.info("Newsletter '%s' marked as sent.", newsletter.subject)
    return f"Newsletter {newsletter_id} sent."
