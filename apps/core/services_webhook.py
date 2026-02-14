"""Webhook delivery service with retry mechanism and HMAC signing."""
import json
import logging

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Handles webhook delivery with HMAC-SHA256 signing and retry logic.

    Usage:
        WebhookService.dispatch('member.created', {'id': '...', 'name': '...'})
    """

    TIMEOUT = 10  # seconds

    @classmethod
    def dispatch(cls, event: str, payload: dict):
        """
        Find all active endpoints subscribed to this event and queue deliveries.
        Uses Celery for async delivery.
        """
        from .models_extended import WebhookEndpoint

        endpoints = WebhookEndpoint.objects.filter(
            is_active=True,
        )

        for endpoint in endpoints:
            if event in (endpoint.events or []):
                cls._create_delivery(endpoint, event, payload)

    @classmethod
    def _create_delivery(cls, endpoint, event: str, payload: dict):
        """Create a delivery record and queue async task."""
        from .models_extended import WebhookDelivery

        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            event=event,
            payload=payload,
            status='pending',
        )

        # Queue async delivery via Celery
        from .tasks import deliver_webhook
        deliver_webhook.delay(str(delivery.pk))

        return delivery

    @classmethod
    def deliver(cls, delivery_id: str) -> bool:
        """
        Execute a webhook delivery attempt.
        Returns True if successful, False otherwise.
        """
        from .models_extended import WebhookDelivery

        try:
            delivery = WebhookDelivery.all_objects.get(pk=delivery_id)
        except WebhookDelivery.DoesNotExist:
            logger.error(f'WebhookDelivery {delivery_id} not found')
            return False

        endpoint = delivery.endpoint
        payload_json = json.dumps(delivery.payload, default=str)

        # Sign the payload
        signature = endpoint.sign_payload(payload_json)

        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': delivery.event,
            'X-Webhook-Signature': f'sha256={signature}',
            'X-Webhook-Delivery-Id': str(delivery.pk),
            'User-Agent': 'EgliseConnect-Webhook/1.0',
        }

        # Merge custom headers
        if endpoint.headers:
            headers.update(endpoint.headers)

        delivery.attempts += 1
        delivery.last_attempt_at = timezone.now()

        try:
            response = requests.post(
                endpoint.url,
                data=payload_json,
                headers=headers,
                timeout=cls.TIMEOUT,
            )

            delivery.response_code = response.status_code
            delivery.response_body = response.text[:2000]

            if 200 <= response.status_code < 300:
                delivery.status = 'success'
                delivery.save()
                return True
            else:
                delivery.error_message = f'HTTP {response.status_code}'
                delivery.status = 'retrying' if delivery.attempts < endpoint.max_retries else 'failed'
                delivery.save()
                return False

        except requests.Timeout:
            delivery.error_message = 'Request timed out'
            delivery.status = 'retrying' if delivery.attempts < endpoint.max_retries else 'failed'
            delivery.save()
            return False

        except requests.ConnectionError as e:
            delivery.error_message = f'Connection error: {str(e)[:500]}'
            delivery.status = 'retrying' if delivery.attempts < endpoint.max_retries else 'failed'
            delivery.save()
            return False

        except Exception as e:
            delivery.error_message = f'Unexpected error: {str(e)[:500]}'
            delivery.status = 'failed'
            delivery.save()
            logger.exception(f'Webhook delivery {delivery_id} failed')
            return False

    @classmethod
    def retry_failed(cls):
        """Retry all failed deliveries that haven't exceeded max attempts."""
        from .models_extended import WebhookDelivery

        retryable = WebhookDelivery.objects.filter(
            status='retrying',
        ).select_related('endpoint')

        count = 0
        for delivery in retryable:
            if delivery.attempts < delivery.endpoint.max_retries:
                from .tasks import deliver_webhook
                deliver_webhook.delay(str(delivery.pk))
                count += 1

        return count
