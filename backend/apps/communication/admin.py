"""Communication admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import (
    Newsletter, NewsletterRecipient, Notification, NotificationPreference,
    SMSMessage, SMSTemplate, SMSOptOut, PushSubscription, EmailTemplate,
    Automation, AutomationStep, AutomationEnrollment, ABTest,
    DirectMessage, GroupChat, GroupChatMessage,
)


@admin.register(Newsletter)
class NewsletterAdmin(BaseModelAdmin):
    list_display = ['subject', 'status', 'sent_at', 'recipients_count', 'opened_count']
    list_filter = ['status', 'sent_at']
    search_fields = ['subject']


@admin.register(NewsletterRecipient)
class NewsletterRecipientAdmin(BaseModelAdmin):
    list_display = ['newsletter', 'member', 'sent_at', 'opened_at', 'failed']
    list_filter = ['failed', 'newsletter']


@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    list_display = ['member', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['title', 'message']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(BaseModelAdmin):
    list_display = ['member', 'email_newsletter', 'email_events', 'push_enabled']


# ─── SMS ─────────────────────────────────────────────────────────────────────────


@admin.register(SMSMessage)
class SMSMessageAdmin(BaseModelAdmin):
    list_display = ['phone_number', 'recipient_member', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['phone_number', 'body']
    readonly_fields = ['id', 'created_at', 'updated_at', 'twilio_sid']


@admin.register(SMSTemplate)
class SMSTemplateAdmin(BaseModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'body_template']


@admin.register(SMSOptOut)
class SMSOptOutAdmin(BaseModelAdmin):
    list_display = ['phone_number', 'member', 'opted_out_at']
    search_fields = ['phone_number']


# ─── Push ────────────────────────────────────────────────────────────────────────


@admin.register(PushSubscription)
class PushSubscriptionAdmin(BaseModelAdmin):
    list_display = ['member', 'endpoint', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['member__first_name', 'member__last_name']


# ─── Email Templates ────────────────────────────────────────────────────────────


@admin.register(EmailTemplate)
class EmailTemplateAdmin(BaseModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'subject_template']


# ─── Automation ──────────────────────────────────────────────────────────────────


class AutomationStepInline(admin.TabularInline):
    model = AutomationStep
    extra = 1
    ordering = ['order']


@admin.register(Automation)
class AutomationAdmin(BaseModelAdmin):
    list_display = ['name', 'trigger_type', 'is_active', 'created_at']
    list_filter = ['trigger_type', 'is_active']
    search_fields = ['name']
    inlines = [AutomationStepInline]


@admin.register(AutomationStep)
class AutomationStepAdmin(BaseModelAdmin):
    list_display = ['automation', 'order', 'subject', 'channel', 'delay_days']
    list_filter = ['channel']
    search_fields = ['subject']


@admin.register(AutomationEnrollment)
class AutomationEnrollmentAdmin(BaseModelAdmin):
    list_display = ['member', 'automation', 'current_step', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'automation']
    search_fields = ['member__first_name', 'member__last_name']


# ─── A/B Test ────────────────────────────────────────────────────────────────────


@admin.register(ABTest)
class ABTestAdmin(BaseModelAdmin):
    list_display = ['newsletter', 'status', 'winner', 'test_size_pct']
    list_filter = ['status']


# ─── Messaging ───────────────────────────────────────────────────────────────────


@admin.register(DirectMessage)
class DirectMessageAdmin(BaseModelAdmin):
    list_display = ['sender', 'recipient', 'created_at', 'read_at']
    search_fields = ['sender__first_name', 'recipient__first_name', 'body']


@admin.register(GroupChat)
class GroupChatAdmin(BaseModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name']


@admin.register(GroupChatMessage)
class GroupChatMessageAdmin(BaseModelAdmin):
    list_display = ['chat', 'sender', 'sent_at']
    list_filter = ['chat']
    search_fields = ['body']
