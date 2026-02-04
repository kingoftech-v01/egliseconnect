"""Communication frontend view tests."""
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
    """Authenticated user without member profile."""
    return UserFactory()


@pytest.fixture
def staff_user_no_profile():
    """Staff user without member profile."""
    return UserFactory(is_staff=True)


# =============================================================================
# NEWSLETTER LIST VIEW
# =============================================================================


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
        """Admin sees all newsletters."""
        user, _ = admin_user
        client.force_login(user)

        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)

        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 2

    def test_member_sees_only_sent(self, client, member_user):
        """Regular member sees only sent newsletters."""
        user, _ = member_user
        client.force_login(user)

        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)
        NewsletterFactory(status=NewsletterStatus.SENT)

        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 2

    def test_user_no_profile_sees_only_sent(self, client, user_no_profile):
        """User without profile sees only sent newsletters."""
        client.force_login(user_no_profile)

        NewsletterFactory(status=NewsletterStatus.DRAFT)
        NewsletterFactory(status=NewsletterStatus.SENT)

        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 1

    def test_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pagination(self, client, pastor_user):
        """Newsletter list is paginated."""
        user, _ = pastor_user
        client.force_login(user)

        NewsletterFactory.create_batch(25)

        response = client.get(reverse('frontend:communication:newsletter_list'))
        assert response.status_code == 200
        assert response.context['newsletters'].paginator.num_pages == 2

    def test_pagination_page_2(self, client, pastor_user):
        """Can access page 2 of newsletters."""
        user, _ = pastor_user
        client.force_login(user)

        NewsletterFactory.create_batch(25)

        response = client.get(
            reverse('frontend:communication:newsletter_list') + '?page=2'
        )
        assert response.status_code == 200
        assert len(response.context['newsletters'].object_list) == 5


# =============================================================================
# NEWSLETTER DETAIL VIEW
# =============================================================================


@pytest.mark.django_db
class TestNewsletterDetailView:
    """Tests for newsletter_detail view."""

    def test_view_newsletter(self, client, member_user):
        """Authenticated member can view newsletter detail."""
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
        """Returns 404 for nonexistent newsletter."""
        user, _ = member_user
        client.force_login(user)

        import uuid
        fake_pk = uuid.uuid4()

        response = client.get(
            reverse('frontend:communication:newsletter_detail', kwargs={'pk': fake_pk})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        newsletter = NewsletterFactory()
        response = client.get(
            reverse('frontend:communication:newsletter_detail', kwargs={'pk': newsletter.pk})
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# NEWSLETTER CREATE VIEW
# =============================================================================


@pytest.mark.django_db
class TestNewsletterCreateView:
    """Tests for newsletter_create view."""

    def test_get_form_as_pastor(self, client, pastor_user):
        """Pastor can access newsletter creation form."""
        user, _ = pastor_user
        client.force_login(user)

        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_get_form_as_admin(self, client, admin_user):
        """Admin can access newsletter creation form."""
        user, _ = admin_user
        client.force_login(user)

        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 200

    def test_post_valid_form_as_pastor(self, client, pastor_user):
        """Pastor can submit newsletter creation form."""
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
        """Invalid form re-renders the page."""
        user, _ = pastor_user
        client.force_login(user)

        data = {
            'subject': '',  # required field
            'content': '<p>Content</p>',
        }

        response = client.post(
            reverse('frontend:communication:newsletter_create'), data
        )
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_member_denied(self, client, member_user):
        """Regular member is denied access to create newsletter."""
        user, _ = member_user
        client.force_login(user)

        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_user_no_profile_not_staff_denied(self, client, user_no_profile):
        """Non-staff user without profile is denied."""
        client.force_login(user_no_profile)

        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_staff_user_no_profile_allowed(self, client, staff_user_no_profile):
        """Staff user without member profile can access."""
        client.force_login(staff_user_no_profile)

        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 200

    def test_post_without_member_profile(self, client, staff_user_no_profile):
        """Staff user without profile can create, created_by not set."""
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
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:communication:newsletter_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# NOTIFICATION LIST VIEW
# =============================================================================


@pytest.mark.django_db
class TestNotificationListView:
    """Tests for notification_list view."""

    def test_list_own_notifications(self, client, member_user):
        """Member sees own notifications."""
        user, member = member_user
        client.force_login(user)

        NotificationFactory.create_batch(3, member=member)
        NotificationFactory.create_batch(2)  # other member's notifications

        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 200
        assert len(response.context['notifications'].object_list) == 3

    def test_no_member_profile_redirects(self, client, user_no_profile):
        """User without member profile is redirected."""
        client.force_login(user_no_profile)

        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pagination(self, client, member_user):
        """Notification list is paginated."""
        user, member = member_user
        client.force_login(user)

        NotificationFactory.create_batch(25, member=member)

        response = client.get(reverse('frontend:communication:notification_list'))
        assert response.status_code == 200
        assert response.context['notifications'].paginator.num_pages == 2


# =============================================================================
# PREFERENCES VIEW
# =============================================================================


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
        """GET returns existing preferences."""
        user, member = member_user
        client.force_login(user)

        NotificationPreference.objects.create(
            member=member, email_newsletter=False
        )

        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 200
        assert response.context['prefs'].email_newsletter is False

    def test_post_updates_preferences(self, client, member_user):
        """POST updates preferences."""
        user, member = member_user
        client.force_login(user)

        NotificationPreference.objects.create(member=member)

        data = {
            'email_newsletter': 'on',
            'email_events': 'on',
            # email_birthdays not checked (absent = False)
            # push_enabled not checked (absent = False)
            # sms_enabled not checked (absent = False)
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
        """POST with nothing checked sets all to False."""
        user, member = member_user
        client.force_login(user)

        NotificationPreference.objects.create(
            member=member,
            email_newsletter=True,
            email_events=True,
        )

        # Empty POST = all checkboxes unchecked
        response = client.post(reverse('frontend:communication:preferences'), {})
        assert response.status_code == 200

        prefs = NotificationPreference.objects.get(member=member)
        assert prefs.email_newsletter is False
        assert prefs.email_events is False
        assert prefs.email_birthdays is False
        assert prefs.push_enabled is False
        assert prefs.sms_enabled is False

    def test_no_member_profile_redirects(self, client, user_no_profile):
        """User without member profile is redirected."""
        client.force_login(user_no_profile)

        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
