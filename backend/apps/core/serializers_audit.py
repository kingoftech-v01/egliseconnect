"""Serializers for audit models."""
from rest_framework import serializers
from .audit import LoginAudit


class LoginAuditSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = LoginAudit
        fields = [
            'id', 'user', 'username', 'email_attempted',
            'ip_address', 'user_agent', 'success', 'failure_reason',
            'method', 'created_at',
        ]
