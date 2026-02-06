"""Volunteer serializers."""
from rest_framework import serializers
from .models import VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest


class VolunteerPositionSerializer(serializers.ModelSerializer):
    role_type_display = serializers.CharField(source='get_role_type_display', read_only=True)

    class Meta:
        model = VolunteerPosition
        fields = '__all__'


class VolunteerAvailabilitySerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)

    class Meta:
        model = VolunteerAvailability
        fields = '__all__'


class VolunteerScheduleSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VolunteerSchedule
        fields = '__all__'


class SwapRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)

    class Meta:
        model = SwapRequest
        fields = '__all__'
