"""Tests for push notification models, service, and views."""
import pytest
from unittest.mock import patch, MagicMock

from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.communication.models import PushSubscription
from apps.communication.services_push import WebPushService
from apps.communication.tests.factories import PushSubscriptionFactory

pytestmark = pytest.mark.django_db


# ─── Model Tests ─────────────────────────────────────────────────────────────────


class TestPushSubscriptionModel:
    def test_str(self):
        sub = PushSubscriptionFactory()
        assert 'Push:' in str(sub)

    def test_default_active(self):
        sub = PushSubscriptionFactory()
        assert sub.is_active is True

    def test_unique_together(self):
        member = MemberFactory()
        PushSubscriptionFactory(member=member, endpoint='https://push.example.com/1')
        with pytest.raises(Exception):
            PushSubscriptionFactory(member=member, endpoint='https://push.example.com/1')


# ─── Service Tests ───────────────────────────────────────────────────────────────


class TestWebPushService:
    def test_subscribe_creates_subscription(self):
        member = MemberFactory()
        service = WebPushService()
        sub = service.subscribe(
            member=member,
            endpoint='https://push.example.com/test',
            p256dh_key='test_p256dh',
            auth_key='test_auth',
        )
        assert sub.pk is not None
        assert sub.is_active is True
        assert sub.member == member

    def test_subscribe_updates_existing(self):
        member = MemberFactory()
        service = WebPushService()
        sub1 = service.subscribe(member, 'https://push.example.com/1', 'key1', 'auth1')
        sub2 = service.subscribe(member, 'https://push.example.com/1', 'key2', 'auth2')
        assert sub1.pk == sub2.pk
        sub2.refresh_from_db()
        assert sub2.p256dh_key == 'key2'

    def test_unsubscribe(self):
        member = MemberFactory()
        PushSubscriptionFactory(member=member, endpoint='https://push.example.com/unsub')
        service = WebPushService()
        result = service.unsubscribe(member, 'https://push.example.com/unsub')
        assert result is True
        # Use all_objects because default manager filters is_active=True
        sub = PushSubscription.all_objects.get(member=member, endpoint='https://push.example.com/unsub')
        assert sub.is_active is False

    def test_unsubscribe_nonexistent(self):
        member = MemberFactory()
        service = WebPushService()
        result = service.unsubscribe(member, 'https://nonexistent.example.com')
        assert result is False

    def test_send_notification_stub_mode(self):
        """In stub mode (no VAPID keys), send returns True."""
        sub = PushSubscriptionFactory()
        service = WebPushService()
        result = service.send_notification(sub, 'Test Title', 'Test Body')
        assert result is True

    def test_send_notification_inactive_sub(self):
        """Inactive subscriptions should not be sent to."""
        sub = PushSubscriptionFactory(is_active=False)
        service = WebPushService()
        result = service.send_notification(sub, 'Test', 'Body')
        assert result is False

    def test_send_to_member(self):
        """send_to_member sends to all active subscriptions."""
        member = MemberFactory()
        PushSubscriptionFactory(member=member, endpoint='https://push.example.com/a')
        PushSubscriptionFactory(member=member, endpoint='https://push.example.com/b')
        PushSubscriptionFactory(member=member, endpoint='https://push.example.com/c', is_active=False)

        service = WebPushService()
        count = service.send_to_member(member, 'Title', 'Body')
        assert count == 2

    def test_send_to_all(self):
        """send_to_all sends to all active subscriptions across members."""
        m1 = MemberFactory()
        m2 = MemberFactory()
        PushSubscriptionFactory(member=m1)
        PushSubscriptionFactory(member=m2)

        service = WebPushService()
        count = service.send_to_all('Broadcast', 'Body')
        assert count == 2

    def test_is_configured_false(self):
        service = WebPushService()
        assert service.is_configured is False


# ─── Frontend View Tests ─────────────────────────────────────────────────────────


class TestPushFrontendViews:
    def test_push_test_page_staff_only(self, client):
        """Non-staff are redirected."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/push/test/')
        assert resp.status_code == 302

    def test_push_test_page_accessible(self, client):
        """Staff can access push test page."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/push/test/')
        assert resp.status_code == 200

    def test_push_test_send_post(self, client):
        """Staff can send a test push notification."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)
        resp = client.post('/communication/push/test/', {
            'title': 'Test',
            'body': 'Test body',
            'target': 'self',
        })
        assert resp.status_code == 302
