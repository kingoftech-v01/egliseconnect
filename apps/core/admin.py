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
