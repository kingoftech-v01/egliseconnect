"""Communication serializers."""
import bleach
from rest_framework import serializers
from .models import Newsletter, NewsletterRecipient, Notification, NotificationPreference
from .forms import ALLOWED_TAGS, ALLOWED_ATTRIBUTES


class NewsletterSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = Newsletter
        fields = '__all__'

    def validate_content(self, value):
        """Sanitize HTML content to prevent XSS."""
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
