"""Web push notification service for PWA support."""
import json
import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class WebPushService:
    """
    Service for managing Web Push subscriptions and sending push notifications.

    Requires VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, and VAPID_CLAIMS in settings.
    When not configured, operates in stub mode.
    """

    def __init__(self):
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', '')
        self.vapid_claims = getattr(settings, 'VAPID_CLAIMS', {'sub': 'mailto:admin@egliseconnect.ca'})

    @property
    def is_configured(self):
        return bool(self.vapid_public_key and self.vapid_private_key)

    def subscribe(self, member, endpoint, p256dh_key, auth_key):
        """
        Register a push subscription for a member.
        Returns the PushSubscription instance.
        """
        from .models import PushSubscription

        subscription, created = PushSubscription.objects.update_or_create(
            member=member,
            endpoint=endpoint,
            defaults={
                'p256dh_key': p256dh_key,
                'auth_key': auth_key,
                'is_active': True,
            },
        )
        if created:
            logger.info("New push subscription for member %s", member.pk)
        return subscription

    def unsubscribe(self, member, endpoint):
        """
        Remove / deactivate a push subscription.
        Returns True if a subscription was deactivated.
        """
        from .models import PushSubscription

        updated = PushSubscription.all_objects.filter(
            member=member, endpoint=endpoint,
        ).update(is_active=False)
        return updated > 0

    def send_notification(self, subscription, title, body, url='', icon=''):
        """
        Send a push notification to a single PushSubscription instance.

        Returns True on success, False on failure.
        """
        if not subscription.is_active:
            return False

        payload = json.dumps({
            'title': str(title),
            'body': str(body),
            'url': url,
            'icon': icon,
        })

        subscription_info = {
            'endpoint': subscription.endpoint,
            'keys': {
                'p256dh': subscription.p256dh_key,
                'auth': subscription.auth_key,
            },
        }

        if not self.is_configured:
            logger.info(
                "[STUB] Push -> %s: %s - %s",
                subscription.member.pk, title, body,
            )
            return True

        try:
            from pywebpush import webpush, WebPushException
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
            )
            logger.info("Push sent to %s", subscription.endpoint[:40])
            return True
        except ImportError:
            logger.warning("pywebpush not installed -- stub mode.")
            return True
        except Exception as exc:
            logger.error("Push send failed: %s", exc)
            # Mark subscription as inactive if endpoint is gone (410)
            if hasattr(exc, 'response') and getattr(exc.response, 'status_code', None) == 410:
                subscription.is_active = False
                subscription.save(update_fields=['is_active', 'updated_at'])
            return False

    def send_to_member(self, member, title, body, url='', icon=''):
        """
        Send a push notification to all active subscriptions for a member.
        Returns the number of successful sends.
        """
        from .models import PushSubscription

        subscriptions = PushSubscription.objects.filter(member=member, is_active=True)
        success_count = 0
        for sub in subscriptions:
            if self.send_notification(sub, title, body, url, icon):
                success_count += 1
        return success_count

    def send_to_all(self, title, body, url='', icon=''):
        """
        Send a push notification to all active subscriptions.
        Returns the number of successful sends.
        """
        from .models import PushSubscription

        subscriptions = PushSubscription.objects.filter(is_active=True)
        success_count = 0
        for sub in subscriptions:
            if self.send_notification(sub, title, body, url, icon):
                success_count += 1
        return success_count
