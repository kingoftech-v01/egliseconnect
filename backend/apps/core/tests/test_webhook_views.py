"""Tests for webhook frontend views."""
import pytest
from django.contrib.auth import get_user_model

from apps.core.constants import Roles
from apps.core.models_extended import WebhookEndpoint, WebhookDelivery
from apps.members.tests.factories import MemberWithUserFactory

User = get_user_model()


@pytest.fixture
def admin_member():
    return MemberWithUserFactory(role=Roles.ADMIN)


@pytest.fixture
def webhook(admin_member):
    return WebhookEndpoint.objects.create(
        name='Test Hook',
        url='https://example.com/hook',
        secret='test-secret',
        events=['member.created'],
        created_by=admin_member.user,
    )


@pytest.mark.django_db
class TestWebhookListView:
    def test_requires_login(self, client):
        response = client.get('/settings/webhooks/')
        assert response.status_code == 302

    def test_requires_admin(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/settings/webhooks/')
        assert response.status_code == 302

    def test_admin_can_access(self, client, admin_member):
        client.force_login(admin_member.user)
        response = client.get('/settings/webhooks/')
        assert response.status_code == 200

    def test_lists_webhooks(self, client, admin_member, webhook):
        client.force_login(admin_member.user)
        response = client.get('/settings/webhooks/')
        assert 'Test Hook' in response.content.decode()


@pytest.mark.django_db
class TestWebhookCreateView:
    def test_get_form(self, client, admin_member):
        client.force_login(admin_member.user)
        response = client.get('/settings/webhooks/create/')
        assert response.status_code == 200

    def test_create_webhook(self, client, admin_member):
        client.force_login(admin_member.user)
        response = client.post('/settings/webhooks/create/', {
            'name': 'New Hook',
            'url': 'https://example.com/new',
            'secret': 'new-secret',
            'events': ['member.created'],
            'max_retries': 3,
        })
        assert response.status_code == 302
        assert WebhookEndpoint.objects.filter(name='New Hook').exists()


@pytest.mark.django_db
class TestWebhookEditView:
    def test_get_edit_form(self, client, admin_member, webhook):
        client.force_login(admin_member.user)
        response = client.get(f'/settings/webhooks/{webhook.pk}/edit/')
        assert response.status_code == 200

    def test_edit_webhook(self, client, admin_member, webhook):
        client.force_login(admin_member.user)
        response = client.post(f'/settings/webhooks/{webhook.pk}/edit/', {
            'name': 'Updated Hook',
            'url': 'https://example.com/updated',
            'secret': 'updated-secret',
            'events': ['donation.received'],
            'max_retries': 5,
        })
        assert response.status_code == 302
        webhook.refresh_from_db()
        assert webhook.name == 'Updated Hook'


@pytest.mark.django_db
class TestWebhookDeleteView:
    def test_get_confirm(self, client, admin_member, webhook):
        client.force_login(admin_member.user)
        response = client.get(f'/settings/webhooks/{webhook.pk}/delete/')
        assert response.status_code == 200

    def test_delete_deactivates(self, client, admin_member, webhook):
        client.force_login(admin_member.user)
        response = client.post(f'/settings/webhooks/{webhook.pk}/delete/')
        assert response.status_code == 302
        webhook.refresh_from_db()
        assert webhook.is_active is False


@pytest.mark.django_db
class TestWebhookDeliveriesView:
    def test_view_deliveries(self, client, admin_member, webhook):
        WebhookDelivery.objects.create(
            endpoint=webhook,
            event='member.created',
            payload={'id': '123'},
            status='success',
            response_code=200,
        )
        client.force_login(admin_member.user)
        response = client.get(f'/settings/webhooks/{webhook.pk}/deliveries/')
        assert response.status_code == 200
        assert 'member.created' in response.content.decode()
