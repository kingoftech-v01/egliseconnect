"""Tests for direct messaging and group chat models and views."""
import pytest

from django.utils import timezone

from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.communication.models import DirectMessage, GroupChat, GroupChatMessage
from apps.communication.tests.factories import (
    DirectMessageFactory, GroupChatFactory, GroupChatMessageFactory,
)

pytestmark = pytest.mark.django_db


# ─── DirectMessage Model Tests ───────────────────────────────────────────────────


class TestDirectMessageModel:
    def test_str(self):
        dm = DirectMessageFactory()
        assert '->' in str(dm)

    def test_is_read_false_by_default(self):
        dm = DirectMessageFactory()
        assert dm.is_read is False
        assert dm.read_at is None

    def test_is_read_property(self):
        dm = DirectMessageFactory(read_at=timezone.now())
        assert dm.is_read is True

    def test_ordering(self):
        """Most recent first."""
        dm1 = DirectMessageFactory()
        dm2 = DirectMessageFactory()
        msgs = list(DirectMessage.objects.all())
        assert msgs[0].created_at >= msgs[1].created_at


# ─── GroupChat Model Tests ───────────────────────────────────────────────────────


class TestGroupChatModel:
    def test_str(self):
        chat = GroupChatFactory(name='Youth Group')
        assert str(chat) == 'Youth Group'

    def test_members_m2m(self):
        chat = GroupChatFactory()
        m1 = MemberFactory()
        m2 = MemberFactory()
        chat.members.add(m1, m2)
        assert chat.members.count() == 2


class TestGroupChatMessageModel:
    def test_str(self):
        chat = GroupChatFactory(name='Test Chat')
        msg = GroupChatMessageFactory(chat=chat)
        assert 'Test Chat' in str(msg)

    def test_ordering_by_sent_at(self):
        chat = GroupChatFactory()
        msg1 = GroupChatMessageFactory(chat=chat)
        msg2 = GroupChatMessageFactory(chat=chat)
        msgs = list(chat.messages.all())
        assert msgs[0].sent_at <= msgs[1].sent_at


# ─── Direct Message Frontend View Tests ─────────────────────────────────────────


class TestMessageInboxView:
    def test_inbox_requires_member_profile(self, client):
        """Users without member profile are redirected."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user('testuser', 'test@test.com', 'pass123')
        client.force_login(user)
        resp = client.get('/communication/messages/')
        assert resp.status_code == 302

    def test_inbox_accessible(self, client):
        """Members can access inbox."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/messages/')
        assert resp.status_code == 200

    def test_inbox_shows_received(self, client):
        """Inbox tab shows received messages."""
        user = MemberWithUserFactory().user
        DirectMessageFactory(recipient=user.member_profile)
        client.force_login(user)
        resp = client.get('/communication/messages/?tab=inbox')
        assert resp.status_code == 200

    def test_inbox_sent_tab(self, client):
        """Sent tab shows sent messages."""
        user = MemberWithUserFactory().user
        DirectMessageFactory(sender=user.member_profile)
        client.force_login(user)
        resp = client.get('/communication/messages/?tab=sent')
        assert resp.status_code == 200


class TestMessageComposeView:
    def test_compose_get(self, client):
        """Members can access compose form."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/messages/compose/')
        assert resp.status_code == 200

    def test_compose_post(self, client):
        """Members can send a direct message."""
        user = MemberWithUserFactory().user
        recipient = MemberFactory()
        client.force_login(user)
        resp = client.post('/communication/messages/compose/', {
            'recipient': str(recipient.pk),
            'body': 'Hello there!',
        })
        assert resp.status_code == 302
        assert DirectMessage.objects.filter(
            sender=user.member_profile, recipient=recipient,
        ).exists()


class TestMessageDetailView:
    def test_detail_marks_as_read(self, client):
        """Viewing a received message marks it as read."""
        user = MemberWithUserFactory().user
        dm = DirectMessageFactory(recipient=user.member_profile)
        assert dm.read_at is None

        client.force_login(user)
        resp = client.get(f'/communication/messages/{dm.pk}/')
        assert resp.status_code == 200

        dm.refresh_from_db()
        assert dm.read_at is not None

    def test_detail_sender_can_view(self, client):
        """Sender can view the message."""
        user = MemberWithUserFactory().user
        dm = DirectMessageFactory(sender=user.member_profile)
        client.force_login(user)
        resp = client.get(f'/communication/messages/{dm.pk}/')
        assert resp.status_code == 200

    def test_detail_unauthorized(self, client):
        """Third party cannot view."""
        user = MemberWithUserFactory().user
        dm = DirectMessageFactory()
        client.force_login(user)
        resp = client.get(f'/communication/messages/{dm.pk}/')
        assert resp.status_code == 302


# ─── Group Chat Frontend View Tests ──────────────────────────────────────────────


class TestGroupChatListView:
    def test_list_accessible(self, client):
        """Members can access group chat list."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/group-chats/')
        assert resp.status_code == 200

    def test_list_only_my_chats(self, client):
        """Only shows chats the member belongs to."""
        user = MemberWithUserFactory().user
        chat = GroupChatFactory()
        chat.members.add(user.member_profile)
        other_chat = GroupChatFactory()

        client.force_login(user)
        resp = client.get('/communication/group-chats/')
        assert chat in resp.context['chats']
        assert other_chat not in resp.context['chats']


class TestGroupChatCreateView:
    def test_create_staff_only(self, client):
        """Non-staff redirected."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/group-chats/create/')
        assert resp.status_code == 302

    def test_create_accessible(self, client):
        """Staff can create group chats."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/group-chats/create/')
        assert resp.status_code == 200


class TestGroupChatDetailView:
    def test_detail_accessible_to_member(self, client):
        """Chat members can view and post."""
        user = MemberWithUserFactory().user
        chat = GroupChatFactory()
        chat.members.add(user.member_profile)

        client.force_login(user)
        resp = client.get(f'/communication/group-chats/{chat.pk}/')
        assert resp.status_code == 200

    def test_detail_non_member_redirected(self, client):
        """Non-members are redirected."""
        user = MemberWithUserFactory().user
        chat = GroupChatFactory()

        client.force_login(user)
        resp = client.get(f'/communication/group-chats/{chat.pk}/')
        assert resp.status_code == 302

    def test_post_message(self, client):
        """Members can post messages."""
        user = MemberWithUserFactory().user
        chat = GroupChatFactory()
        chat.members.add(user.member_profile)

        client.force_login(user)
        resp = client.post(f'/communication/group-chats/{chat.pk}/', {
            'body': 'Hello group!',
        })
        assert resp.status_code == 302
        assert GroupChatMessage.objects.filter(
            chat=chat, sender=user.member_profile,
        ).exists()


# ─── Social Media Dashboard View Tests ───────────────────────────────────────────


class TestSocialMediaDashboard:
    def test_dashboard_staff_only(self, client):
        """Non-staff redirected."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/social-media/')
        assert resp.status_code == 302

    def test_dashboard_accessible(self, client):
        """Staff can access."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/social-media/')
        assert resp.status_code == 200
        assert resp.context['facebook_connected'] is False
        assert resp.context['instagram_connected'] is False
        assert resp.context['whatsapp_connected'] is False
