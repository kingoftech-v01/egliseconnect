"""Help Requests admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import HelpRequest, HelpRequestCategory, HelpRequestComment


@admin.register(HelpRequestCategory)
class HelpRequestCategoryAdmin(BaseModelAdmin):
    list_display = ['name', 'name_fr', 'icon', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'name_fr']
    ordering = ['order', 'name']


class HelpRequestCommentInline(admin.TabularInline):
    model = HelpRequestComment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(HelpRequest)
class HelpRequestAdmin(BaseModelAdmin):
    list_display = [
        'request_number', 'title', 'member', 'category',
        'urgency', 'status', 'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'urgency', 'category', 'is_confidential', 'created_at']
    search_fields = ['request_number', 'title', 'description', 'member__first_name', 'member__last_name']
    readonly_fields = ['request_number', 'created_at', 'updated_at', 'resolved_at']
    raw_id_fields = ['member', 'assigned_to']
    inlines = [HelpRequestCommentInline]

    fieldsets = (
        (None, {
            'fields': ('request_number', 'member', 'category', 'title', 'description')
        }),
        ('Status', {
            'fields': ('status', 'urgency', 'assigned_to', 'is_confidential')
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HelpRequestComment)
class HelpRequestCommentAdmin(BaseModelAdmin):
    list_display = ['help_request', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['content', 'help_request__request_number']
    raw_id_fields = ['help_request', 'author']
