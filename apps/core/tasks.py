"""Celery tasks for core app: webhook delivery, audit cleanup, etc."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_webhook(self, delivery_id: str):
    """
    Deliver a single webhook. Retries on failure with exponential backoff.

    Args:
        delivery_id: UUID string of the WebhookDelivery record.
    """
    from apps.core.services_webhook import WebhookService

    success = WebhookService.deliver(delivery_id)

    if not success:
        from apps.core.models_extended import WebhookDelivery
        try:
            delivery = WebhookDelivery.all_objects.get(pk=delivery_id)
            if delivery.status == 'retrying':
                # Retry with exponential backoff
                retry_delay = 60 * (2 ** (delivery.attempts - 1))
                raise self.retry(countdown=retry_delay)
        except WebhookDelivery.DoesNotExist:
            pass


@shared_task
def retry_failed_webhooks():
    """Periodic task: retry all failed webhook deliveries."""
    from apps.core.services_webhook import WebhookService
    count = WebhookService.retry_failed()
    logger.info(f'Retried {count} failed webhook deliveries')


@shared_task
def cleanup_old_audit_logs(days: int = 365):
    """Periodic task: clean up audit logs older than N days."""
    from datetime import timedelta
    from django.utils import timezone
    from apps.core.models_extended import AuditLog

    cutoff = timezone.now() - timedelta(days=days)
    count, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
    logger.info(f'Cleaned up {count} audit log entries older than {days} days')


@shared_task
def cleanup_old_webhook_deliveries(days: int = 90):
    """Periodic task: clean up webhook deliveries older than N days."""
    from datetime import timedelta
    from django.utils import timezone
    from apps.core.models_extended import WebhookDelivery

    cutoff = timezone.now() - timedelta(days=days)
    count, _ = WebhookDelivery.objects.filter(created_at__lt=cutoff).delete()
    logger.info(f'Cleaned up {count} webhook delivery records older than {days} days')
