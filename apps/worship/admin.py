"""Worship admin configuration with enhanced list views and inlines."""
from django.contrib import admin
from .models import WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList


class ServiceSectionInline(admin.TabularInline):
    """Inline for sections within a service."""
    model = ServiceSection
    extra = 0
    fields = ['order', 'name', 'section_type', 'duration_minutes', 'department', 'notes']
    ordering = ['order']


class ServiceAssignmentInline(admin.TabularInline):
    """Inline for assignments within a section."""
    model = ServiceAssignment
    extra = 0
    fields = ['member', 'task_type', 'status', 'responded_at', 'notes']
    readonly_fields = ['responded_at']
    autocomplete_fields = ['member']


@admin.register(WorshipService)
class WorshipServiceAdmin(admin.ModelAdmin):
    """Admin for WorshipService with rich list display and filters."""
    list_display = [
        'date', 'start_time', 'theme', 'status',
        'total_assignments', 'confirmation_rate_display', 'created_by',
    ]
    list_filter = ['status', 'date']
    search_fields = ['theme', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ServiceSectionInline]
    ordering = ['-date', '-start_time']

    def confirmation_rate_display(self, obj):
        return f'{obj.confirmation_rate}%'
    confirmation_rate_display.short_description = 'Taux confirm.'

    def total_assignments(self, obj):
        return obj.total_assignments
    total_assignments.short_description = 'Assignations'


@admin.register(ServiceSection)
class ServiceSectionAdmin(admin.ModelAdmin):
    """Admin for ServiceSection with filters and inlines."""
    list_display = ['name', 'service', 'order', 'section_type', 'duration_minutes', 'department']
    list_filter = ['section_type', 'service__date']
    search_fields = ['name', 'notes', 'service__theme']
    ordering = ['service', 'order']
    inlines = [ServiceAssignmentInline]


@admin.register(ServiceAssignment)
class ServiceAssignmentAdmin(admin.ModelAdmin):
    """Admin for ServiceAssignment with filters and search."""
    list_display = ['member', 'section', 'status', 'task_type', 'responded_at']
    list_filter = ['status', 'section__service__date']
    search_fields = [
        'member__first_name', 'member__last_name',
        'section__name', 'notes',
    ]
    readonly_fields = ['responded_at', 'created_at', 'updated_at']
    autocomplete_fields = ['member']


@admin.register(EligibleMemberList)
class EligibleMemberListAdmin(admin.ModelAdmin):
    """Admin for EligibleMemberList with filters."""
    list_display = ['section_type', 'department', 'member_count']
    list_filter = ['section_type']
    filter_horizontal = ['members']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Membres'
