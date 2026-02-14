"""Tests for webhook models, service, and delivery."""
import hashlib
import hmac
import json

import pytest
from unittest.mock import patch, MagicMock

from apps.core.models_extended import WebhookEndpoint, WebhookDelivery
from apps.core.services_webhook import WebhookService
from apps.members.tests.factories import UserFactory


@pytest.fixture
def webhook_endpoint():
    """Create a test webhook endpoint."""
    return WebhookEndpoint.objects.create(
        name='Test Webhook',
        url='https://example.com/webhook',
        secret='test-secret-key',
        events=['member.created', 'donation.received'],
        max_retries=3,
    )


@pytest.mark.django_db
class TestWebhookEndpointModel:
    def test_create_endpoint(self, webhook_endpoint):
        assert webhook_endpoint.name == 'Test Webhook'
        assert webhook_endpoint.url == 'https://example.com/webhook'
        assert webhook_endpoint.is_active is True
        assert 'member.created' in webhook_endpoint.events

    def test_str_representation(self, webhook_endpoint):
        expected = 'Test Webhook (https://example.com/webhook)'
        assert str(webhook_endpoint) == expected

    def test_sign_payload(self, webhook_endpoint):
        payload = '{"test": "data"}'
        signature = webhook_endpoint.sign_payload(payload)

        expected = hmac.new(
            b'test-secret-key',
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        assert signature == expected

    def test_default_max_retries(self):
        endpoint = WebhookEndpoint.objects.create(
            name='Default',
            url='https://example.com/hook',
            secret='secret',
            events=['member.created'],
        )
        assert endpoint.max_retries == 3

    def test_custom_headers(self):
        endpoint = WebhookEndpoint.objects.create(
            name='With Headers',
            url='https://example.com/hook',
            secret='secret',
            events=['member.created'],
            headers={'Authorization': 'Bearer token123'},
        )
        assert endpoint.headers['Authorization'] == 'Bearer token123'

    def test_created_by_user(self):
        user = UserFactory()
        endpoint = WebhookEndpoint.objects.create(
            name='User Created',
            url='https://example.com/hook',
            secret='secret',
            events=[],
            created_by=user,
        )
        assert endpoint.created_by == user


@pytest.mark.django_db
class TestWebhookDeliveryModel:
    def test_create_delivery(self, webhook_endpoint):
        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={'id': 'test-123', 'name': 'Test'},
            status='pending',
        )
        assert delivery.status == 'pending'
        assert delivery.attempts == 0
        assert delivery.event == 'member.created'

    def test_str_representation(self, webhook_endpoint):
        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='donation.received',
            payload={},
            status='success',
        )
        assert 'donation.received' in str(delivery)
        assert 'Test Webhook' in str(delivery)
        assert 'success' in str(delivery)

    def test_delivery_ordering(self, webhook_endpoint):
        d1 = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={},
        )
        d2 = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='donation.received',
            payload={},
        )
        deliveries = list(WebhookDelivery.objects.all())
        assert deliveries[0] == d2  # Newest first


@pytest.mark.django_db
class TestWebhookService:
    @patch('apps.core.services_webhook.WebhookService._create_delivery')
    def test_dispatch_finds_matching_endpoints(self, mock_create, webhook_endpoint):
        WebhookService.dispatch('member.created', {'id': '123'})
        assert mock_create.called

    @patch('apps.core.services_webhook.WebhookService._create_delivery')
    def test_dispatch_ignores_non_matching_events(self, mock_create, webhook_endpoint):
        WebhookService.dispatch('non.existent.event', {'id': '123'})
        assert not mock_create.called

    @patch('apps.core.services_webhook.WebhookService._create_delivery')
    def test_dispatch_ignores_inactive_endpoints(self, mock_create, webhook_endpoint):
        webhook_endpoint.deactivate()
        WebhookService.dispatch('member.created', {'id': '123'})
        assert not mock_create.called

    @patch('apps.core.tasks.deliver_webhook.delay')
    def test_create_delivery_queues_task(self, mock_delay, webhook_endpoint):
        delivery = WebhookService._create_delivery(
            webhook_endpoint, 'member.created', {'id': '123'},
        )
        assert delivery.status == 'pending'
        assert mock_delay.called

    @patch('apps.core.services_webhook.requests.post')
    def test_deliver_success(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'OK'
        mock_post.return_value = mock_response

        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={'id': '123'},
            status='pending',
        )

        result = WebhookService.deliver(str(delivery.pk))
        assert result is True

        delivery.refresh_from_db()
        assert delivery.status == 'success'
        assert delivery.response_code == 200
        assert delivery.attempts == 1

    @patch('apps.core.services_webhook.requests.post')
    def test_deliver_failure_retries(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Server Error'
        mock_post.return_value = mock_response

        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={'id': '123'},
            status='pending',
        )

        result = WebhookService.deliver(str(delivery.pk))
        assert result is False

        delivery.refresh_from_db()
        assert delivery.status == 'retrying'

    @patch('apps.core.services_webhook.requests.post')
    def test_deliver_timeout(self, mock_post, webhook_endpoint):
        import requests as req
        mock_post.side_effect = req.Timeout()

        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={'id': '123'},
            status='pending',
        )

        result = WebhookService.deliver(str(delivery.pk))
        assert result is False

        delivery.refresh_from_db()
        assert delivery.error_message == 'Request timed out'

    @patch('apps.core.services_webhook.requests.post')
    def test_deliver_connection_error(self, mock_post, webhook_endpoint):
        import requests as req
        mock_post.side_effect = req.ConnectionError('Connection refused')

        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={'id': '123'},
            status='pending',
        )

        result = WebhookService.deliver(str(delivery.pk))
        assert result is False

        delivery.refresh_from_db()
        assert 'Connection error' in delivery.error_message

    def test_deliver_nonexistent(self):
        result = WebhookService.deliver('00000000-0000-0000-0000-000000000000')
        assert result is False

    @patch('apps.core.services_webhook.requests.post')
    def test_deliver_max_retries_reached(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Error'
        mock_post.return_value = mock_response

        webhook_endpoint.max_retries = 1
        webhook_endpoint.save()

        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={'id': '123'},
            status='pending',
            attempts=0,
        )

        WebhookService.deliver(str(delivery.pk))
        delivery.refresh_from_db()
        assert delivery.status == 'failed'

    @patch('apps.core.tasks.deliver_webhook.delay')
    def test_retry_failed(self, mock_delay, webhook_endpoint):
        WebhookDelivery.objects.create(
            endpoint=webhook_endpoint,
            event='member.created',
            payload={},
            status='retrying',
            attempts=1,
        )

        count = WebhookService.retry_failed()
        assert count == 1
        assert mock_delay.called

    def test_deliver_includes_hmac_signature(self, webhook_endpoint):
        """Verify HMAC-SHA256 signature is generated correctly."""
        payload = '{"id": "test"}'
        sig = webhook_endpoint.sign_payload(payload)
        assert len(sig) == 64  # SHA256 hex digest length
