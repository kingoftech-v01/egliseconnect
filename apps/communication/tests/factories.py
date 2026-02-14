"""Test factories for communication app."""
import factory
from factory.django import DjangoModelFactory
from apps.communication.models import (
    Newsletter, Notification, NotificationPreference,
    SMSMessage, SMSTemplate, SMSOptOut, PushSubscription, EmailTemplate,
    Automation, AutomationStep, AutomationEnrollment, ABTest,
    DirectMessage, GroupChat, GroupChatMessage,
)
from apps.members.tests.factories import MemberFactory
from apps.core.constants import (
    NewsletterStatus, NotificationType, SMSStatus, AutomationTrigger,
    AutomationStepChannel, AutomationStatus, ABTestStatus,
    EmailTemplateCategory,
)


class NewsletterFactory(DjangoModelFactory):
    """Creates test newsletters with draft status by default."""

    class Meta:
        model = Newsletter

    subject = factory.Sequence(lambda n: f'Newsletter {n}')
    content = factory.Faker('paragraph')
    content_plain = factory.Faker('paragraph')
    created_by = factory.SubFactory(MemberFactory)
    status = NewsletterStatus.DRAFT
    send_to_all = True


class NotificationFactory(DjangoModelFactory):
    """Creates test notifications for members."""

    class Meta:
        model = Notification

    member = factory.SubFactory(MemberFactory)
    title = factory.Sequence(lambda n: f'Notification {n}')
    message = factory.Faker('paragraph')
    notification_type = NotificationType.GENERAL
    is_read = False


class NotificationPreferenceFactory(DjangoModelFactory):
    """Creates test notification preferences with all channels enabled."""

    class Meta:
        model = NotificationPreference

    member = factory.SubFactory(MemberFactory)
    email_newsletter = True
    email_events = True
    email_birthdays = True
    push_enabled = True
    sms_enabled = False


# ─── SMS ─────────────────────────────────────────────────────────────────────────


class SMSTemplateFactory(DjangoModelFactory):
    """Creates test SMS templates."""

    class Meta:
        model = SMSTemplate

    name = factory.Sequence(lambda n: f'Modele SMS {n}')
    body_template = factory.Faker('sentence')
    is_active = True


class SMSMessageFactory(DjangoModelFactory):
    """Creates test SMS messages."""

    class Meta:
        model = SMSMessage

    recipient_member = factory.SubFactory(MemberFactory)
    phone_number = factory.Faker('phone_number')
    body = factory.Faker('sentence')
    status = SMSStatus.PENDING


class SMSOptOutFactory(DjangoModelFactory):
    """Creates test SMS opt-outs."""

    class Meta:
        model = SMSOptOut

    member = factory.SubFactory(MemberFactory)
    phone_number = factory.Sequence(lambda n: f'+1555000{n:04d}')


# ─── Push ────────────────────────────────────────────────────────────────────────


class PushSubscriptionFactory(DjangoModelFactory):
    """Creates test push subscriptions."""

    class Meta:
        model = PushSubscription

    member = factory.SubFactory(MemberFactory)
    endpoint = factory.Sequence(lambda n: f'https://push.example.com/sub/{n}')
    p256dh_key = factory.Faker('sha256')
    auth_key = factory.Faker('sha1')
    is_active = True


# ─── Email Template ─────────────────────────────────────────────────────────────


class EmailTemplateFactory(DjangoModelFactory):
    """Creates test email templates."""

    class Meta:
        model = EmailTemplate

    name = factory.Sequence(lambda n: f'Modele Courriel {n}')
    subject_template = 'Bienvenue {{member_name}}'
    body_html_template = '<p>Bonjour {{member_name}}</p>'
    category = EmailTemplateCategory.GENERAL
    is_active = True


# ─── Automation ──────────────────────────────────────────────────────────────────


class AutomationFactory(DjangoModelFactory):
    """Creates test automations."""

    class Meta:
        model = Automation

    name = factory.Sequence(lambda n: f'Automatisation {n}')
    description = factory.Faker('paragraph')
    trigger_type = AutomationTrigger.MEMBER_CREATED
    is_active = True
    created_by = factory.SubFactory(MemberFactory)


class AutomationStepFactory(DjangoModelFactory):
    """Creates test automation steps."""

    class Meta:
        model = AutomationStep

    automation = factory.SubFactory(AutomationFactory)
    order = factory.Sequence(lambda n: n)
    delay_days = 1
    subject = factory.Sequence(lambda n: f'Step {n} Subject')
    body = factory.Faker('paragraph')
    channel = AutomationStepChannel.EMAIL


class AutomationEnrollmentFactory(DjangoModelFactory):
    """Creates test automation enrollments."""

    class Meta:
        model = AutomationEnrollment

    automation = factory.SubFactory(AutomationFactory)
    member = factory.SubFactory(MemberFactory)
    current_step = 0
    status = AutomationStatus.ACTIVE


# ─── A/B Test ────────────────────────────────────────────────────────────────────


class ABTestFactory(DjangoModelFactory):
    """Creates test A/B tests."""

    class Meta:
        model = ABTest

    newsletter = factory.SubFactory(NewsletterFactory)
    variant_a_subject = 'Subject A'
    variant_b_subject = 'Subject B'
    test_size_pct = 20
    status = ABTestStatus.DRAFT


# ─── Messaging ───────────────────────────────────────────────────────────────────


class DirectMessageFactory(DjangoModelFactory):
    """Creates test direct messages."""

    class Meta:
        model = DirectMessage

    sender = factory.SubFactory(MemberFactory)
    recipient = factory.SubFactory(MemberFactory)
    body = factory.Faker('paragraph')


class GroupChatFactory(DjangoModelFactory):
    """Creates test group chats."""

    class Meta:
        model = GroupChat

    name = factory.Sequence(lambda n: f'Discussion {n}')
    created_by = factory.SubFactory(MemberFactory)


class GroupChatMessageFactory(DjangoModelFactory):
    """Creates test group chat messages."""

    class Meta:
        model = GroupChatMessage

    chat = factory.SubFactory(GroupChatFactory)
    sender = factory.SubFactory(MemberFactory)
    body = factory.Faker('paragraph')
