"""Volunteers admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest


@admin.register(VolunteerPosition)
class VolunteerPositionAdmin(BaseModelAdmin):
    list_display = ['name', 'role_type', 'min_volunteers', 'max_volunteers', 'is_active']
    list_filter = ['role_type', 'is_active']
    search_fields = ['name']


@admin.register(VolunteerAvailability)
class VolunteerAvailabilityAdmin(BaseModelAdmin):
    list_display = ['member', 'position', 'is_available', 'frequency']
    list_filter = ['position', 'is_available', 'frequency']
    autocomplete_fields = ['member', 'position']


@admin.register(VolunteerSchedule)
class VolunteerScheduleAdmin(BaseModelAdmin):
    list_display = ['member', 'position', 'date', 'status', 'reminder_sent']
    list_filter = ['position', 'status', 'date']
    autocomplete_fields = ['member', 'position', 'event']
    date_hierarchy = 'date'


@admin.register(SwapRequest)
class SwapRequestAdmin(BaseModelAdmin):
    list_display = ['original_schedule', 'requested_by', 'swap_with', 'status']
    list_filter = ['status']
