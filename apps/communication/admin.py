"""Communication admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import Newsletter, NewsletterRecipient, Notification, NotificationPreference


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
