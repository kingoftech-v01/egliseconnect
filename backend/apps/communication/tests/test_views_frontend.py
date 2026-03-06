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

    def test_post_all_on(self, client, member_user):
        """POST with all checkboxes 'on' saves all preferences as True."""
        user, member = member_user
        client.force_login(user)
        NotificationPreference.objects.create(member=member)
        data = {
            'email_newsletter': 'on',
            'email_events': 'on',
            'email_birthdays': 'on',
            'push_enabled': 'on',
            'sms_enabled': 'on',
        }
        response = client.post(
            reverse('frontend:communication:preferences'), data
        )
        assert response.status_code == 200
        prefs = NotificationPreference.objects.get(member=member)
        assert prefs.email_newsletter is True
        assert prefs.email_events is True
        assert prefs.email_birthdays is True
        assert prefs.push_enabled is True
        assert prefs.sms_enabled is True

    def test_post_partial_save(self, client, member_user):
        """POST with some checkboxes saves correct mix of True/False."""
        user, member = member_user
        client.force_login(user)
        NotificationPreference.objects.create(member=member)
        data = {
            'email_newsletter': 'on',
            'sms_enabled': 'on',
        }
        response = client.post(
            reverse('frontend:communication:preferences'), data
        )
        assert response.status_code == 200
        prefs = NotificationPreference.objects.get(member=member)
        assert prefs.email_newsletter is True
        assert prefs.email_events is False
        assert prefs.email_birthdays is False
        assert prefs.push_enabled is False
        assert prefs.sms_enabled is True

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 302
        assert response.url == '/'

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:communication:preferences'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestNewsletterEditView:
    """Tests for newsletter_edit view."""

    def test_get_form_as_pastor(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["newsletter"] == newsletter

    def test_get_form_as_admin(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_non_draft_cannot_edit(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.SENT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 302

    def test_post_valid_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        data = {
            "subject": "Updated Subject",
            "content": "<p>Updated content</p>",
            "content_plain": "Updated content",
            "send_to_all": True,
        }
        response = client.post(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk}),
            data,
        )
        assert response.status_code == 302
        newsletter.refresh_from_db()
        assert newsletter.subject == "Updated Subject"

    def test_post_invalid_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        data = {"subject": "", "content": "<p>Content</p>"}
        response = client.post(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk}),
            data,
        )
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_not_found(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        import uuid
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client):
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_staff_user_no_profile_allowed(self, client, staff_user_no_profile):
        client.force_login(staff_user_no_profile)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200

    def test_recipient_count_in_context(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_edit", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200
        assert "recipient_count" in response.context



@pytest.mark.django_db
class TestNewsletterDeleteView:
    """Tests for newsletter_delete view."""

    def test_get_confirmation_page(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory()
        response = client.get(
            reverse("frontend:communication:newsletter_delete", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200
        assert response.context["newsletter"] == newsletter

    def test_post_deletes_newsletter(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory()
        pk = newsletter.pk
        response = client.post(
            reverse("frontend:communication:newsletter_delete", kwargs={"pk": pk})
        )
        assert response.status_code == 302
        assert not Newsletter.objects.filter(pk=pk).exists()

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        newsletter = NewsletterFactory()
        response = client.get(
            reverse("frontend:communication:newsletter_delete", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_admin_can_delete(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        newsletter = NewsletterFactory()
        pk = newsletter.pk
        response = client.post(
            reverse("frontend:communication:newsletter_delete", kwargs={"pk": pk})
        )
        assert response.status_code == 302
        assert not Newsletter.objects.filter(pk=pk).exists()

    def test_not_found(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        import uuid
        response = client.get(
            reverse("frontend:communication:newsletter_delete", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client):
        newsletter = NewsletterFactory()
        response = client.get(
            reverse("frontend:communication:newsletter_delete", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestNewsletterSendView:
    """Tests for newsletter_send view."""

    def test_send_draft_newsletter(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "send"},
        )
        assert response.status_code == 302
        newsletter.refresh_from_db()
        assert newsletter.status == NewsletterStatus.SENT
        assert newsletter.sent_at is not None

    def test_schedule_newsletter(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "schedule", "scheduled_for": "2026-03-01 10:00:00"},
        )
        assert response.status_code == 302
        newsletter.refresh_from_db()
        assert newsletter.status == NewsletterStatus.SCHEDULED

    def test_schedule_without_date(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "schedule"},
        )
        assert response.status_code == 302
        newsletter.refresh_from_db()
        assert newsletter.status == NewsletterStatus.DRAFT

    def test_cannot_send_already_sent(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.SENT)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "send"},
        )
        assert response.status_code == 302

    def test_get_redirects_to_detail(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.get(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 302

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "send"},
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_not_found(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        import uuid
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": uuid.uuid4()}),
            {"action": "send"},
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client):
        newsletter = NewsletterFactory(status=NewsletterStatus.DRAFT)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "send"},
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_send_scheduled_newsletter(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.SCHEDULED)
        response = client.post(
            reverse("frontend:communication:newsletter_send", kwargs={"pk": newsletter.pk}),
            {"action": "send"},
        )
        assert response.status_code == 302
        newsletter.refresh_from_db()
        assert newsletter.status == NewsletterStatus.SENT



@pytest.mark.django_db
class TestMarkAllReadView:
    """Tests for mark_all_read view."""

    def test_marks_all_as_read(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        NotificationFactory.create_batch(5, member=member, is_read=False)
        response = client.post(reverse("frontend:communication:mark_all_read"))
        assert response.status_code == 302
        assert Notification.objects.filter(member=member, is_read=False).count() == 0
        assert Notification.objects.filter(member=member, is_read=True).count() == 5

    def test_get_redirects(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse("frontend:communication:mark_all_read"))
        assert response.status_code == 302
        assert "/communication/notifications/" in response.url

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.post(reverse("frontend:communication:mark_all_read"))
        assert response.status_code == 302
        assert response.url == "/"

    def test_unauthenticated_redirects(self, client):
        response = client.post(reverse("frontend:communication:mark_all_read"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_does_not_affect_other_users(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        NotificationFactory.create_batch(3, member=member, is_read=False)
        other_notifs = NotificationFactory.create_batch(2, is_read=False)
        client.post(reverse("frontend:communication:mark_all_read"))
        for n in other_notifs:
            n.refresh_from_db()
            assert n.is_read is False


@pytest.mark.django_db
class TestNotificationListFilter:
    """Tests for notification_list type filter."""

    def test_filter_by_type(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        from apps.core.constants import NotificationType
        NotificationFactory(member=member, notification_type=NotificationType.EVENT)
        NotificationFactory(member=member, notification_type=NotificationType.BIRTHDAY)
        NotificationFactory(member=member, notification_type=NotificationType.EVENT)
        response = client.get(
            reverse("frontend:communication:notification_list") + "?type=event"
        )
        assert response.status_code == 200
        assert len(response.context["notifications"].object_list) == 2
        assert response.context["current_type"] == "event"

    def test_no_filter_shows_all(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        from apps.core.constants import NotificationType
        NotificationFactory(member=member, notification_type=NotificationType.EVENT)
        NotificationFactory(member=member, notification_type=NotificationType.BIRTHDAY)
        response = client.get(reverse("frontend:communication:notification_list"))
        assert response.status_code == 200
        assert len(response.context["notifications"].object_list) == 2
        assert response.context["current_type"] is None

    def test_notification_types_in_context(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse("frontend:communication:notification_list"))
        assert response.status_code == 200
        assert "notification_types" in response.context


@pytest.mark.django_db
class TestNewsletterCreateRecipientCount:
    """Tests for recipient count in newsletter_create."""

    def test_recipient_count_in_context(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(reverse("frontend:communication:newsletter_create"))
        assert response.status_code == 200
        assert "recipient_count" in response.context


@pytest.mark.django_db
class TestNewsletterDetailStaff:
    """Tests for is_staff context in newsletter_detail."""

    def test_staff_sees_is_staff_true(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        newsletter = NewsletterFactory()
        response = client.get(
            reverse("frontend:communication:newsletter_detail", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200
        assert response.context["is_staff"] is True

    def test_member_sees_is_staff_false(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        newsletter = NewsletterFactory(status=NewsletterStatus.SENT)
        response = client.get(
            reverse("frontend:communication:newsletter_detail", kwargs={"pk": newsletter.pk})
        )
        assert response.status_code == 200
        assert response.context["is_staff"] is False

