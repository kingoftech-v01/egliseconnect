"""Generic reminder utility for the 5j/3j/1j/J notification pattern."""
import logging

from apps.communication.models import Notification

logger = logging.getLogger(__name__)


def send_reminder_batch(items, get_date, get_member, make_message, link=''):
    """
    Generic 5-day/3-day/1-day/same-day reminder sender.

    Args:
        items: queryset of items to check (must have reminder_*_sent fields)
        get_date: callable(item) -> date to compare against today
        get_member: callable(item) -> Member to notify
        make_message: callable(item, days_label) -> str notification message
        link: optional URL for the notification link

    Returns:
        int: number of reminders sent
    """
    from django.utils import timezone
    today = timezone.now().date()
    total_sent = 0

    for item in items:
        target_date = get_date(item)
        if target_date is None:
            continue

        days_until = (target_date - today).days
        sent = False
        days_label = ''

        if days_until <= 5 and not item.reminder_5days_sent:
            item.reminder_5days_sent = True
            sent = True
            days_label = '5 jours'

        elif days_until <= 3 and not item.reminder_3days_sent:
            item.reminder_3days_sent = True
            sent = True
            days_label = '3 jours'

        elif days_until <= 1 and not item.reminder_1day_sent:
            item.reminder_1day_sent = True
            sent = True
            days_label = 'demain'

        elif days_until == 0 and not item.reminder_sameday_sent:
            item.reminder_sameday_sent = True
            sent = True
            days_label = "aujourd'hui"

        if sent:
            item.save()
            member = get_member(item)
            msg = make_message(item, days_label)

            Notification.objects.create(
                member=member,
                title='Rappel',
                message=msg,
                notification_type='general',
                link=link,
            )
            total_sent += 1

    return total_sent
