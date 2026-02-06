"""Tests for communication API views."""
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.communication.models import Newsletter, Notification, NotificationPreference
from apps.core.constants import NewsletterStatus, NotificationType
from .factories import NewsletterFactory, NotificationFactory
from apps.members.tests.factories import (
    MemberFactory,
    MemberWithUserFactory,
    UserFactory,
    PastorFactory,
    AdminMemberFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='member')
    return user, member


@pytest.fixture
def pastor_user():
    """Pastor with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='pastor')
    return user, member


@pytest.fixture
def admin_user():
    """Admin with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='admin')
    return user, member


@pytest.fixture
def user_no_profile():
    """User without member profile."""
    return UserFactory()


@pytest.mark.django_db
class TestNewsletterViewSetList:
    """Tests for newsletter list endpoint."""

    def test_list_as_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NewsletterFactory.create_batch(3)
        response = api_client.get('/api/v1/communication/newsletters/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_list_as_pastor(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        NewsletterFactory.create_batch(2)
        response = api_client.get('/api/v1/communication/newsletters/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_list_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/communication/newsletters/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_list_uses_list_serializer(self, api_client, member_user):
        """List action uses compact serializer without full content."""
        user, _ = member_user
        api_client.force_authenticate(user=user)
        NewsletterFactory()
        response = api_client.get('/api/v1/communication/newsletters/')
        assert response.status_code == status.HTTP_200_OK
        item = response.data['results'][0]
        assert 'subject' in item
        assert 'status' in item
        assert 'status_display' in item
        assert 'content' not in item

    def test_list_filter_by_status(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        response = api_client.get('/api/v1/communication/newsletters/', {'status': 'sent'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_list_search_by_subject(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        NewsletterFactory(subject='Weekly Update March')
        NewsletterFactory(subject='Monthly Report')
        response = api_client.get('/api/v1/communication/newsletters/', {'search': 'Weekly'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['subject'] == 'Weekly Update March'


@pytest.mark.django_db
class TestNewsletterViewSetRetrieve:
    """Tests for newsletter retrieve endpoint."""

    def test_retrieve_as_member(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(subject='Test Newsletter')
        response = api_client.get(f'/api/v1/communication/newsletters/{newsletter.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'Test Newsletter'
        assert 'content' in response.data

    def test_retrieve_unauthenticated(self, api_client):
        newsletter = NewsletterFactory()
        response = api_client.get(f'/api/v1/communication/newsletters/{newsletter.id}/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestNewsletterViewSetCreate:
    """Tests for newsletter create endpoint."""

    def test_create_as_pastor(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        data = {
            'subject': 'New Newsletter',
            'content': '<p>Hello world</p>',
            'content_plain': 'Hello world',
            'send_to_all': True,
        }
        response = api_client.post(
            '/api/v1/communication/newsletters/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subject'] == 'New Newsletter'
        newsletter = Newsletter.all_objects.get(id=response.data['id'])
        assert newsletter.created_by == member

    def test_create_as_admin(self, api_client, admin_user):
        user, member = admin_user
        api_client.force_authenticate(user=user)
        data = {
            'subject': 'Admin Newsletter',
            'content': '<p>Admin content</p>',
            'send_to_all': True,
        }
        response = api_client.post(
            '/api/v1/communication/newsletters/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_as_member_forbidden(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        data = {
            'subject': 'Unauthorized Newsletter',
            'content': '<p>Not allowed</p>',
            'send_to_all': True,
        }
        response = api_client.post('/api/v1/communication/newsletters/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_without_member_profile(self, api_client):
        """Staff without member profile can create but created_by is null."""
        user = UserFactory(is_staff=True)
        api_client.force_authenticate(user=user)
        data = {
            'subject': 'Staff Newsletter',
            'content': '<p>Staff content</p>',
            'send_to_all': True,
        }
        response = api_client.post(
            '/api/v1/communication/newsletters/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        newsletter = Newsletter.all_objects.get(id=response.data['id'])
        assert newsletter.created_by is None

    def test_create_sanitizes_html(self, api_client, pastor_user):
        """HTML content is sanitized to prevent XSS."""
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        data = {
            'subject': 'XSS Test',
            'content': '<p>Good</p><script>alert("xss")</script>',
            'send_to_all': True,
        }
        response = api_client.post(
            '/api/v1/communication/newsletters/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        newsletter = Newsletter.all_objects.get(id=response.data['id'])
        assert '<script>' not in newsletter.content
        assert '<p>Good</p>' in newsletter.content


@pytest.mark.django_db
class TestNewsletterViewSetUpdate:
    """Tests for newsletter update endpoint."""

    def test_update_as_pastor(self, api_client, pastor_user):
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(subject='Old Subject')
        response = api_client.patch(
            f'/api/v1/communication/newsletters/{newsletter.id}/',
            {'subject': 'New Subject'},
        )
        assert response.status_code == status.HTTP_200_OK
        newsletter.refresh_from_db()
        assert newsletter.subject == 'New Subject'

    def test_update_as_member_forbidden(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory()
        response = api_client.patch(
            f'/api/v1/communication/newsletters/{newsletter.id}/',
            {'subject': 'Hacked'},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestNewsletterViewSetDelete:
    """Tests for newsletter delete endpoint."""

    def test_delete_as_pastor(self, api_client, pastor_user):
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory()
        response = api_client.delete(
            f'/api/v1/communication/newsletters/{newsletter.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_member_forbidden(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory()
        response = api_client.delete(
            f'/api/v1/communication/newsletters/{newsletter.id}/'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestNewsletterViewSetSendAction:
    """Tests for the send action on newsletters."""

    def test_send_newsletter(self, api_client, pastor_user):
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = api_client.post(
            f'/api/v1/communication/newsletters/{newsletter.id}/send/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Envoi en cours'
        newsletter.refresh_from_db()
        assert newsletter.status == NewsletterStatus.SENDING

    def test_send_already_sent_newsletter(self, api_client, pastor_user):
        """Cannot re-send an already sent newsletter."""
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(status=NewsletterStatus.SENT)
        response = api_client.post(
            f'/api/v1/communication/newsletters/{newsletter.id}/send/'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_send_as_member_forbidden(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = api_client.post(
            f'/api/v1/communication/newsletters/{newsletter.id}/send/'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestNewsletterViewSetScheduleAction:
    """Tests for the schedule action on newsletters."""

    def test_schedule_newsletter(self, api_client, pastor_user):
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        scheduled_time = '2026-03-01T10:00:00Z'
        response = api_client.post(
            f'/api/v1/communication/newsletters/{newsletter.id}/schedule/',
            {'scheduled_for': scheduled_time},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Planifiée'
        newsletter.refresh_from_db()
        assert newsletter.status == NewsletterStatus.SCHEDULED
        assert newsletter.scheduled_for is not None

    def test_schedule_without_date(self, api_client, pastor_user):
        """Scheduling requires a scheduled_for date."""
        user, _ = pastor_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = api_client.post(
            f'/api/v1/communication/newsletters/{newsletter.id}/schedule/',
            {},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_schedule_as_member_forbidden(self, api_client, member_user):
        user, _ = member_user
        api_client.force_authenticate(user=user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = api_client.post(
            f'/api/v1/communication/newsletters/{newsletter.id}/schedule/',
            {'scheduled_for': '2026-03-01T10:00:00Z'},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestNotificationViewSetList:
    """Tests for notification list endpoint."""

    def test_list_own_notifications(self, api_client, member_user):
        """Members see only their own notifications."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationFactory.create_batch(3, member=member)
        NotificationFactory.create_batch(2)  # other member's
        response = api_client.get('/api/v1/communication/notifications/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_list_without_member_profile(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        NotificationFactory.create_batch(3)
        response = api_client.get('/api/v1/communication/notifications/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_list_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/communication/notifications/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestNotificationViewSetMarkRead:
    """Tests for the mark_read action."""

    def test_mark_specific_as_read(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        n1 = NotificationFactory(member=member, is_read=False)
        n2 = NotificationFactory(member=member, is_read=False)
        n3 = NotificationFactory(member=member, is_read=False)
        response = api_client.post(
            '/api/v1/communication/notifications/mark-read/',
            {'ids': [str(n1.id), str(n2.id)]},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        n1.refresh_from_db()
        n2.refresh_from_db()
        n3.refresh_from_db()
        assert n1.is_read is True
        assert n2.is_read is True
        assert n3.is_read is False

    def test_mark_all_as_read(self, api_client, member_user):
        """Empty ids list marks all unread as read."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationFactory.create_batch(3, member=member, is_read=False)
        response = api_client.post(
            '/api/v1/communication/notifications/mark-read/',
            {},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        unread_count = Notification.objects.filter(
            member=member, is_read=False
        ).count()
        assert unread_count == 0

    def test_mark_read_without_member_profile(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        response = api_client.post(
            '/api/v1/communication/notifications/mark-read/',
            {},
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_read_does_not_affect_other_members(self, api_client, member_user):
        """Only marks own notifications, not others."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        own_notif = NotificationFactory(member=member, is_read=False)
        other_notif = NotificationFactory(is_read=False)
        response = api_client.post(
            '/api/v1/communication/notifications/mark-read/',
            {},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        own_notif.refresh_from_db()
        other_notif.refresh_from_db()
        assert own_notif.is_read is True
        assert other_notif.is_read is False


@pytest.mark.django_db
class TestNotificationViewSetUnreadCount:
    """Tests for the unread_count action."""

    def test_unread_count(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationFactory.create_batch(3, member=member, is_read=False)
        NotificationFactory(member=member, is_read=True)
        response = api_client.get('/api/v1/communication/notifications/unread_count/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_unread_count_zero(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        # Mark the welcome notification from onboarding signal as read
        Notification.objects.filter(member=member).update(is_read=True)
        response = api_client.get('/api/v1/communication/notifications/unread_count/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_unread_count_without_member_profile(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        response = api_client.get('/api/v1/communication/notifications/unread_count/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0


@pytest.mark.django_db
class TestNotificationPreferenceViewSetMe:
    """Tests for the me action on notification preferences."""

    def test_get_preferences_creates_if_not_exist(self, api_client, member_user):
        """GET /me creates preferences if they don't exist."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        assert not NotificationPreference.objects.filter(member=member).exists()
        response = api_client.get('/api/v1/communication/preferences/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_newsletter'] is True
        assert NotificationPreference.objects.filter(member=member).exists()

    def test_get_preferences_returns_existing(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationPreference.objects.create(
            member=member,
            email_newsletter=False,
            email_events=True,
            email_birthdays=False,
            push_enabled=True,
            sms_enabled=True,
        )
        response = api_client.get('/api/v1/communication/preferences/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_newsletter'] is False
        assert response.data['sms_enabled'] is True

    def test_put_preferences(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationPreference.objects.create(member=member)
        data = {
            'email_newsletter': False,
            'email_events': False,
            'email_birthdays': False,
            'push_enabled': False,
            'sms_enabled': True,
        }
        response = api_client.put(
            '/api/v1/communication/preferences/me/',
            data,
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_newsletter'] is False
        assert response.data['sms_enabled'] is True

    def test_patch_preferences(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationPreference.objects.create(member=member, email_newsletter=True)
        response = api_client.patch(
            '/api/v1/communication/preferences/me/',
            {'email_newsletter': False},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_newsletter'] is False

    def test_put_preferences_invalid(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationPreference.objects.create(member=member)
        response = api_client.put(
            '/api/v1/communication/preferences/me/',
            {'email_newsletter': 'not_a_bool'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_me_without_member_profile(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        response = api_client.get('/api/v1/communication/preferences/me/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_preferences(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        NotificationPreference.objects.create(member=member)
        response = api_client.get('/api/v1/communication/preferences/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_preferences_without_profile(self, api_client, user_no_profile):
        api_client.force_authenticate(user=user_no_profile)
        response = api_client.get('/api/v1/communication/preferences/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
