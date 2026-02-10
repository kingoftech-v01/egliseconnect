"""Worship service API serializers."""
from rest_framework import serializers
from .models import WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList


class WorshipServiceSerializer(serializers.ModelSerializer):
    """Serializer for WorshipService model."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    confirmation_rate = serializers.IntegerField(read_only=True)
    total_assignments = serializers.IntegerField(read_only=True)
    confirmed_assignments = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorshipService
        fields = '__all__'


class ServiceSectionSerializer(serializers.ModelSerializer):
    """Serializer for ServiceSection model."""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = ServiceSection
        fields = '__all__'


class ServiceAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ServiceAssignment model."""
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True, default=None)

    class Meta:
        model = ServiceAssignment
        fields = '__all__'


class EligibleMemberListSerializer(serializers.ModelSerializer):
    """Serializer for EligibleMemberList model."""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = EligibleMemberList
        fields = '__all__'

    def get_member_count(self, obj):
        return obj.members.count()
