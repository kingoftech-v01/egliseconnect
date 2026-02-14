"""Reports admin configuration."""
from django.contrib import admin
from .models import ReportSchedule, SavedReport


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'last_sent_at', 'next_run_at']
    list_filter = ['report_type', 'frequency', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['recipients']
    readonly_fields = ['last_sent_at', 'created_at', 'updated_at']


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'created_at']
    list_filter = ['report_type']
    search_fields = ['name']
    filter_horizontal = ['shared_with']
    readonly_fields = ['created_at', 'updated_at']
