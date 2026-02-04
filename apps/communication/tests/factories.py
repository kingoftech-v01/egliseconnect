"""Communication test factories."""
import factory
from factory.django import DjangoModelFactory
from apps.communication.models import Newsletter, Notification, NotificationPreference
from apps.members.tests.factories import MemberFactory
from apps.core.constants import NewsletterStatus, NotificationType


class NewsletterFactory(DjangoModelFactory):
    """Factory for Newsletter model."""

    class Meta:
        model = Newsletter

    subject = factory.Sequence(lambda n: f'Newsletter {n}')
    content = factory.Faker('paragraph')
    content_plain = factory.Faker('paragraph')
    created_by = factory.SubFactory(MemberFactory)
    status = NewsletterStatus.DRAFT
    send_to_all = True


class NotificationFactory(DjangoModelFactory):
    """Factory for Notification model."""

    class Meta:
        model = Notification

    member = factory.SubFactory(MemberFactory)
    title = factory.Sequence(lambda n: f'Notification {n}')
    message = factory.Faker('paragraph')
    notification_type = NotificationType.GENERAL
    is_read = False


class NotificationPreferenceFactory(DjangoModelFactory):
    """Factory for NotificationPreference model."""

    class Meta:
        model = NotificationPreference

    member = factory.SubFactory(MemberFactory)
    email_newsletter = True
    email_events = True
    email_birthdays = True
    push_enabled = True
    sms_enabled = False
