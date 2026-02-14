"""Serializers for extended core models: audit, webhooks, branding, campus."""
from rest_framework import serializers

from .models_extended import AuditLog, WebhookEndpoint, WebhookDelivery, ChurchBranding, Campus


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action', 'action_display',
            'model_name', 'object_id', 'object_repr', 'changes',
            'ip_address', 'created_at',
        ]
        read_only_fields = fields


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = [
            'id', 'name', 'url', 'secret', 'events', 'headers',
            'max_retries', 'is_active', 'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'secret': {'write_only': True},
        }


class WebhookDeliverySerializer(serializers.ModelSerializer):
    endpoint_name = serializers.CharField(source='endpoint.name', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'endpoint', 'endpoint_name', 'event', 'payload',
            'status', 'response_code', 'response_body', 'attempts',
            'last_attempt_at', 'error_message', 'created_at',
        ]
        read_only_fields = fields


class ChurchBrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChurchBranding
        fields = [
            'id', 'church_name', 'logo', 'favicon',
            'primary_color', 'secondary_color', 'accent_color',
            'address', 'phone', 'email', 'website',
            'is_active', 'created_at', 'updated_at',
        ]


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = [
            'id', 'name', 'address', 'city', 'province', 'postal_code',
            'phone', 'email', 'pastor', 'is_main',
            'is_active', 'created_at', 'updated_at',
        ]
