"""Audit logging service for tracking model changes."""
import json
import logging

from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating audit log entries.

    Usage:
        AuditService.log_create(request, instance)
        AuditService.log_update(request, instance, old_data)
        AuditService.log_delete(request, instance)
    """

    @classmethod
    def log(cls, user, action, instance, changes=None, request=None):
        """Create an audit log entry."""
        from apps.core.models_extended import AuditLog

        ip_address = None
        user_agent = ''

        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk) if instance.pk else '',
            object_repr=str(instance)[:500],
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def log_create(cls, request, instance):
        """Log a create action."""
        user = request.user if request and hasattr(request, 'user') else None
        cls.log(user, 'create', instance, request=request)

    @classmethod
    def log_update(cls, request, instance, old_data=None):
        """Log an update action with changes diff."""
        user = request.user if request and hasattr(request, 'user') else None
        changes = {}

        if old_data:
            new_data = cls._serialize_instance(instance)
            for key in old_data:
                if key in new_data and old_data[key] != new_data[key]:
                    changes[key] = {
                        'old': str(old_data[key]),
                        'new': str(new_data[key]),
                    }

        cls.log(user, 'update', instance, changes=changes, request=request)

    @classmethod
    def log_delete(cls, request, instance):
        """Log a delete action."""
        user = request.user if request and hasattr(request, 'user') else None
        cls.log(user, 'delete', instance, request=request)

    @classmethod
    def log_export(cls, request, model_name, count):
        """Log a data export action."""
        from apps.core.models_extended import AuditLog

        ip_address = None
        user_agent = ''
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        AuditLog.objects.create(
            user=request.user if request else None,
            action='export',
            model_name=model_name,
            object_repr=f'Export de {count} enregistrements',
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def _serialize_instance(cls, instance):
        """Safely serialize model instance to dict."""
        try:
            data = model_to_dict(instance)
            # Convert non-serializable values to strings
            return {k: str(v) for k, v in data.items()}
        except Exception:
            return {}

    @classmethod
    def _get_client_ip(cls, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
