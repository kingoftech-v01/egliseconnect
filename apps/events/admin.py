"""Events admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import Event, EventRSVP


@admin.register(Event)
class EventAdmin(BaseModelAdmin):
    list_display = ['title', 'event_type', 'start_datetime', 'location', 'is_published', 'is_cancelled']
    list_filter = ['event_type', 'is_published', 'is_cancelled', 'start_datetime']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'start_datetime'


@admin.register(EventRSVP)
class EventRSVPAdmin(BaseModelAdmin):
    list_display = ['event', 'member', 'status', 'guests', 'created_at']
    list_filter = ['status', 'event']
    autocomplete_fields = ['event', 'member']
