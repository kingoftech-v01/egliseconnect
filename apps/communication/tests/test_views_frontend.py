"""Tests for communication frontend views."""
import pytest
from django.test import Client
from django.urls import reverse

from apps.communication.models import Newsletter, Notification, NotificationPreference
from apps.core.constants import NewsletterStatus, Roles
from .factories import NewsletterFactory, NotificationFactory
from apps.members.tests.factories import (
    MemberFactory,
    UserFactory,
)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def member_user():
    """Regular member with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.fixture
def pastor_user():
    """Pastor with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.PASTOR)
    return user, member


@pytest.fixture
def admin_user():
    """Admin with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.ADMIN)
    return user, member


@pytest.fixture
def user_no_profile():
    """User without member profile."""
    return UserFactory()


@pytest.fixture
def staff_user_no_profile():
    """Staff user without member profile."""
    return UserFactory(is_staff=True)


@pytest.mark.django_db
class TestNewsletterListView:
    """Tests for newsletter_list view."""

    def test_pastor_sees_all_newsletters(self, client, pastor_user):
        """Pastor/admin sees all newsletters regardless of status."""
        user, _ = pastor_user
        client.force_login(user)
        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        NewsletterFactory(status=NewsletterStatus.SCHEDULED)
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 3

    def test_admin_sees_all_newsletters(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 2

    def test_member_sees_only_sent(self, client, member_user):
        """Regular members only see sent newsletters, not drafts."""
        user, _ = member_user
        client.force_login(user)
        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 2

    def test_user_no_profile_sees_only_sent(self, client, user_no_profile):
        client.force_login(user_no_profile)
        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 1

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pagination(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        NewsletterFactory.create_batch(25)
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert response.context['newsletters'].paginator.num_pages == 2

    def test_pagination_page_2(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        NewsletterFactory.create_batch(25)
        response = client.get(
            reverse('frontend:communication:newsletter_list') + '?page=2'
        )
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 5


@pytest.mark.django_db
class TestNewsletterDetailView:
    """Tests for newsletter_detail view."""

    def test_view_newsletter(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        newsletter = NewsletterFactory(subject='Test Detail')
        response = client.get(
            reverse('frontend:communication:newsletter_detail', kwargs={'pk': newsletter.pk})
        )
        assert response.status_code == 200
        assert response.context['newsletter'] == newsletter
        assert response.context['page_title'] == newsletter.subject

    def test_newsletter_not_found(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        import uuid
        fake_pk = uuid.uuid4()
        response = client.get(
            reverse('frontend:communication:newsletter_detail', kwargs={'pk': fake_pk})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client):
        newsletter = NewsletterFactory()
        response = client.get(
            reverse('frontend:communication:newsletter_detail', kwargs={'pk': newsletter.pk})
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestNewsletterCreateView:
    """Tests for newsletter_create view."""

    def test_get_form_as_pastor(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_get_form_as_admin(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 200

    def test_post_valid_form_as_pastor(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        data = {
            'subject': 'New Newsletter',
            'content': '<p>Newsletter content</p>',
            'content_plain': 'Newsletter content',
            'send_to_all': True,
        }
        response = client.post(
            reverse('frontend:communication:newsletter_create'), data
        )
        assert response.status_code == 302
        newsletter = Newsletter.objects.get(subject='New Newsletter')
        assert newsletter.created_by == member

    def test_post_invalid_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        data = {
            'subject': '',
            'content': '<p>Content</p>',
        }
        response = client.post(
            reverse('frontend:communication:newsletter_create'), data
        )
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_user_no_profile_not_staff_denied(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_staff_user_no_profile_allowed(self, client, staff_user_no_profile):
        client.force_login(staff_user_no_profile)
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 200

    def test_post_without_member_profile(self, client, staff_user_no_profile):
        """Staff without profile can create but created_by is null."""
        client.force_login(staff_user_no_profile)
        data = {
            'subject': 'Staff Created',
            'content': '<p>Content</p>',
            'content_plain': 'Content',
            'send_to_all': True,
        }
        response = client.post(
            reverse('frontend:communication:newsletter_create'), data
        )
        assert response.status_code == 302
        newsletter = Newsletter.objects.get(subject='Staff Created')
        assert newsletter.created_by is None

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestNotificationListView:
    """Tests for notification_list view."""

    def test_list_own_notifications(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        NotificationFactory.create_batch(3, member=member)
        NotificationFactory.create_batch(2)  # other member's
        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 200
        assert len(response.context['notifications'].object_list) == 3

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pagination(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        NotificationFactory.create_batch(25, member=member)
        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 200
        assert response.context['notifications'].paginator.num_pages == 2


@pytest.mark.django_db
class TestPreferencesView:
    """Tests for preferences view."""

    def test_get_preferences_creates_if_absent(self, client, member_user):
        """GET creates preferences if they don't exist."""
        user, member = member_user
        client.force_login(user)
        assert not NotificationPreference.objects.filter(member=member).exists()
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 200
        assert 'prefs' in response.context
        assert NotificationPreference.objects.filter(member=member).exists()

    def test_get_preferences_existing(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        NotificationPreference.objects.create(
            member=member, email_newsletter=False
        )
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 200
        assert response.context['prefs'].email_newsletter is False

    def test_post_updates_preferences(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        NotificationPreference.objects.create(member=member)
        data = {
            'email_newsletter': 'on',
            'email_events': 'on',
        }
        response = client.post(
            reverse('frontend:communication:preferences'), data
        )
        assert response.status_code == 200
        prefs = NotificationPreference.objects.get(member=member)
        assert prefs.email_newsletter is True
        assert prefs.email_events is True
        assert prefs.email_birthdays is False
        assert prefs.push_enabled is False
        assert prefs.sms_enabled is False

    def test_post_all_off(self, client, member_user):
        """Empty POST sets all preferences to False."""
        user, member = member_user
        client.force_login(user)
        NotificationPreference.objects.create(
            member=member,
            email_newsletter=True,
            email_events=True,
        )
        response = client.post(reverse('frontend:communication:preferences'), {})
        assert response.status_code == 200
        prefs = NotificationPreference.objects.get(member=member)
        assert prefs.email_newsletter is False
        assert prefs.email_events is False
        assert prefs.email_birthdays is False
        assert prefs.push_enabled is False
        assert prefs.sms_enabled is False

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
