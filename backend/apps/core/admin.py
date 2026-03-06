"""Base admin classes for all apps."""
from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """Base admin for models with common audit fields."""
    list_display = ['id', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self, request):
        """Include inactive objects in admin."""
        return self.model.all_objects.all()


class SoftDeleteModelAdmin(BaseModelAdmin):
    """Base admin for soft-deletable models with restore/hard-delete actions."""
    list_display = ['id', 'created_at', 'updated_at', 'is_active', 'deleted_at']
    list_filter = ['is_active', 'deleted_at', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

    actions = ['restore_selected', 'hard_delete_selected']

    def restore_selected(self, request, queryset):
        """Restore soft-deleted objects."""
        count = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                count += 1
        self.message_user(request, f'{count} objet(s) restauré(s).')

    restore_selected.short_description = "Restaurer les objets sélectionnés"

    def hard_delete_selected(self, request, queryset):
        """Permanently delete objects."""
        count = queryset.count()
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f'{count} objet(s) supprimé(s) définitivement.')

    hard_delete_selected.short_description = "Supprimer définitivement les objets sélectionnés"


from apps.core.audit import LoginAudit


@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    list_display = ['email_attempted', 'success', 'ip_address', 'method', 'created_at']
    list_filter = ['success', 'method', 'created_at']
    search_fields = ['email_attempted', 'ip_address']
    readonly_fields = ['user', 'email_attempted', 'ip_address', 'user_agent', 'success', 'failure_reason', 'method', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ─── Extended Core Models ────────────────────────────────────────────────────

from apps.core.models_extended import (
    ChurchBranding, WebhookEndpoint, WebhookDelivery, AuditLog, Campus,
)


@admin.register(ChurchBranding)
class ChurchBrandingAdmin(BaseModelAdmin):
    list_display = ['church_name', 'primary_color', 'email', 'is_active', 'created_at']
    search_fields = ['church_name', 'email']


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(BaseModelAdmin):
    list_display = ['name', 'url', 'is_active', 'max_retries', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['event', 'endpoint', 'status', 'response_code', 'attempts', 'created_at']
    list_filter = ['status', 'event', 'created_at']
    search_fields = ['event', 'endpoint__name']
    readonly_fields = [
        'id', 'endpoint', 'event', 'payload', 'status',
        'response_code', 'response_body', 'attempts',
        'last_attempt_at', 'error_message', 'created_at', 'updated_at',
    ]
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'ip_address', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['object_repr', 'model_name', 'user__username']
    readonly_fields = [
        'id', 'user', 'action', 'model_name', 'object_id',
        'object_repr', 'changes', 'ip_address', 'user_agent', 'created_at', 'updated_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Campus)
class CampusAdmin(BaseModelAdmin):
    list_display = ['name', 'city', 'pastor', 'is_main', 'is_active', 'created_at']
    list_filter = ['is_main', 'is_active', 'province']
    search_fields = ['name', 'city']
