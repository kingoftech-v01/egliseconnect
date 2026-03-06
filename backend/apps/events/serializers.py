"""Event serializers — events, RSVP, rooms, bookings, templates, waitlist,
volunteer needs, photos, surveys."""
from rest_framework import serializers
from .models import (
    Event, EventRSVP, Room, RoomBooking, EventTemplate,
    RegistrationForm, RegistrationEntry,
    EventWaitlist, EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)


# ──────────────────────────────────────────────────────────────────────────────
# Event
# ──────────────────────────────────────────────────────────────────────────────

class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event listings."""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    confirmed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'event_type_display',
            'start_datetime', 'end_datetime', 'location',
            'is_online', 'confirmed_count', 'max_attendees',
            'is_published', 'is_cancelled', 'campus',
        ]


class EventSerializer(serializers.ModelSerializer):
    """Full event serializer with all fields."""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True, allow_null=True)
    confirmed_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EventRSVPSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EventRSVP
        fields = [
            'id', 'event', 'member', 'member_name', 'status',
            'status_display', 'guests', 'notes', 'created_at',
        ]


# ──────────────────────────────────────────────────────────────────────────────
# Room / Booking
# ──────────────────────────────────────────────────────────────────────────────

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class RoomBookingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    booked_by_name = serializers.CharField(source='booked_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = RoomBooking
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ──────────────────────────────────────────────────────────────────────────────
# Template
# ──────────────────────────────────────────────────────────────────────────────

class EventTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ──────────────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────────────

class RegistrationFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationForm
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class RegistrationEntrySerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = RegistrationEntry
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'submitted_at']


# ──────────────────────────────────────────────────────────────────────────────
# Waitlist
# ──────────────────────────────────────────────────────────────────────────────

class EventWaitlistSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = EventWaitlist
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'added_at']


# ──────────────────────────────────────────────────────────────────────────────
# Volunteer Needs
# ──────────────────────────────────────────────────────────────────────────────

class EventVolunteerNeedSerializer(serializers.ModelSerializer):
    filled_count = serializers.IntegerField(read_only=True)
    is_filled = serializers.BooleanField(read_only=True)
    remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = EventVolunteerNeed
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EventVolunteerSignupSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = EventVolunteerSignup
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ──────────────────────────────────────────────────────────────────────────────
# Photo
# ──────────────────────────────────────────────────────────────────────────────

class EventPhotoSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = EventPhoto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ──────────────────────────────────────────────────────────────────────────────
# Survey
# ──────────────────────────────────────────────────────────────────────────────

class EventSurveySerializer(serializers.ModelSerializer):
    response_count = serializers.SerializerMethodField()

    class Meta:
        model = EventSurvey
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_response_count(self, obj):
        return obj.responses.count()


class SurveyResponseSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = SurveyResponse
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'submitted_at']
