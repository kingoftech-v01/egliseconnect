"""Communication serializers."""
import bleach
from rest_framework import serializers
from .models import (
    Newsletter, NewsletterRecipient, Notification, NotificationPreference,
    SMSMessage, SMSTemplate, SMSOptOut, PushSubscription, EmailTemplate,
    Automation, AutomationStep, AutomationEnrollment, ABTest,
    DirectMessage, GroupChat, GroupChatMessage,
)
from .forms import ALLOWED_TAGS, ALLOWED_ATTRIBUTES


class NewsletterSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = Newsletter
        fields = '__all__'

    def validate_content(self, value):
        """Sanitize HTML to prevent XSS."""
        return bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,
        )


class NewsletterListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Newsletter
        fields = ['id', 'subject', 'status', 'status_display', 'sent_at', 'recipients_count', 'opened_count']


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['email_newsletter', 'email_events', 'email_birthdays', 'push_enabled', 'sms_enabled']


# ─── SMS ─────────────────────────────────────────────────────────────────────────


class SMSMessageSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SMSMessage
        fields = '__all__'
        read_only_fields = ['status', 'twilio_sid', 'sent_at', 'sent_by']


class SMSTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSTemplate
        fields = '__all__'


class SMSOptOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSOptOut
        fields = '__all__'


# ─── Push ────────────────────────────────────────────────────────────────────────


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'p256dh_key', 'auth_key', 'is_active']
        read_only_fields = ['id']


# ─── Email Template ─────────────────────────────────────────────────────────────


class EmailTemplateSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = EmailTemplate
        fields = '__all__'


# ─── Automation ──────────────────────────────────────────────────────────────────


class AutomationStepSerializer(serializers.ModelSerializer):
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = AutomationStep
        fields = '__all__'


class AutomationSerializer(serializers.ModelSerializer):
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    steps = AutomationStepSerializer(many=True, read_only=True)
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = Automation
        fields = '__all__'

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class AutomationEnrollmentSerializer(serializers.ModelSerializer):
    automation_name = serializers.CharField(source='automation.name', read_only=True)
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AutomationEnrollment
        fields = '__all__'


# ─── A/B Test ────────────────────────────────────────────────────────────────────


class ABTestSerializer(serializers.ModelSerializer):
    newsletter_subject = serializers.CharField(source='newsletter.subject', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ABTest
        fields = '__all__'


# ─── Messaging ───────────────────────────────────────────────────────────────────


class DirectMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = DirectMessage
        fields = '__all__'
        read_only_fields = ['sender', 'read_at']


class GroupChatSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = GroupChat
        fields = '__all__'

    def get_member_count(self, obj):
        return obj.members.count()


class GroupChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)

    class Meta:
        model = GroupChatMessage
        fields = '__all__'
        read_only_fields = ['sender', 'sent_at']
