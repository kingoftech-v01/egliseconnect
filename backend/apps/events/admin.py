"""Events admin — all event-related models."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import (
    Event, EventRSVP, Room, RoomBooking, EventTemplate,
    RegistrationForm, RegistrationEntry,
    EventWaitlist, EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)


@admin.register(Event)
class EventAdmin(BaseModelAdmin):
    list_display = [
        'title', 'event_type', 'start_datetime', 'location',
        'is_published', 'is_cancelled', 'is_recurring', 'campus',
    ]
    list_filter = [
        'event_type', 'is_published', 'is_cancelled',
        'is_recurring', 'start_datetime',
    ]
    search_fields = ['title', 'description', 'location', 'campus']
    date_hierarchy = 'start_datetime'


@admin.register(EventRSVP)
class EventRSVPAdmin(BaseModelAdmin):
    list_display = ['event', 'member', 'status', 'guests', 'created_at']
    list_filter = ['status', 'event']
    autocomplete_fields = ['event', 'member']


@admin.register(Room)
class RoomAdmin(BaseModelAdmin):
    list_display = ['name', 'capacity', 'location', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'location']


@admin.register(RoomBooking)
class RoomBookingAdmin(BaseModelAdmin):
    list_display = [
        'room', 'event', 'booked_by', 'start_datetime',
        'end_datetime', 'status',
    ]
    list_filter = ['status', 'room']
    autocomplete_fields = ['room', 'event', 'booked_by']
    date_hierarchy = 'start_datetime'


@admin.register(EventTemplate)
class EventTemplateAdmin(BaseModelAdmin):
    list_display = ['name', 'event_type', 'default_capacity', 'is_active']
    list_filter = ['event_type', 'is_active']
    search_fields = ['name']


@admin.register(RegistrationForm)
class RegistrationFormAdmin(BaseModelAdmin):
    list_display = ['title', 'event', 'is_active']
    list_filter = ['is_active']
    autocomplete_fields = ['event']


@admin.register(RegistrationEntry)
class RegistrationEntryAdmin(BaseModelAdmin):
    list_display = ['form', 'member', 'submitted_at']
    autocomplete_fields = ['form', 'member']


@admin.register(EventWaitlist)
class EventWaitlistAdmin(BaseModelAdmin):
    list_display = ['event', 'member', 'position', 'added_at', 'promoted_at']
    list_filter = ['event']
    autocomplete_fields = ['event', 'member']


@admin.register(EventVolunteerNeed)
class EventVolunteerNeedAdmin(BaseModelAdmin):
    list_display = ['event', 'position_name', 'required_count', 'is_active']
    list_filter = ['event']
    autocomplete_fields = ['event']


@admin.register(EventVolunteerSignup)
class EventVolunteerSignupAdmin(BaseModelAdmin):
    list_display = ['need', 'member', 'status']
    list_filter = ['status']
    autocomplete_fields = ['need', 'member']


@admin.register(EventPhoto)
class EventPhotoAdmin(BaseModelAdmin):
    list_display = ['event', 'caption', 'uploaded_by', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'event']
    autocomplete_fields = ['event', 'uploaded_by']


@admin.register(EventSurvey)
class EventSurveyAdmin(BaseModelAdmin):
    list_display = ['title', 'event', 'send_after_hours', 'survey_sent', 'is_active']
    list_filter = ['survey_sent', 'is_active']
    autocomplete_fields = ['event']


@admin.register(SurveyResponse)
class SurveyResponseAdmin(BaseModelAdmin):
    list_display = ['survey', 'member', 'submitted_at']
    autocomplete_fields = ['survey', 'member']
