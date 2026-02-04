"""Events serializers."""
from rest_framework import serializers
from .models import Event, EventRSVP


class EventListSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    confirmed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'event_type', 'event_type_display', 'start_datetime', 'end_datetime', 'location', 'is_online', 'confirmed_count', 'max_attendees', 'is_published', 'is_cancelled']


class EventSerializer(serializers.ModelSerializer):
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
        fields = ['id', 'event', 'member', 'member_name', 'status', 'status_display', 'guests', 'notes', 'created_at']
