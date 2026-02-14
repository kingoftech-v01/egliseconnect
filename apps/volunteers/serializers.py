"""Volunteer serializers."""
from rest_framework import serializers
from .models import (
    VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest,
    VolunteerHours, VolunteerBackgroundCheck, TeamAnnouncement,
    PositionChecklist, ChecklistProgress, Skill, VolunteerSkill,
    Milestone, MilestoneAchievement, AvailabilitySlot, CrossTraining,
)


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


class VolunteerHoursSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)

    class Meta:
        model = VolunteerHours
        fields = '__all__'


class VolunteerBackgroundCheckSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VolunteerBackgroundCheck
        fields = '__all__'


class TeamAnnouncementSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)

    class Meta:
        model = TeamAnnouncement
        fields = '__all__'


class PositionChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = PositionChecklist
        fields = '__all__'


class ChecklistProgressSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = ChecklistProgress
        fields = '__all__'


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class VolunteerSkillSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    proficiency_display = serializers.CharField(source='get_proficiency_level_display', read_only=True)

    class Meta:
        model = VolunteerSkill
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'


class MilestoneAchievementSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    milestone_name = serializers.CharField(source='milestone.name', read_only=True)

    class Meta:
        model = MilestoneAchievement
        fields = '__all__'


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = AvailabilitySlot
        fields = '__all__'


class CrossTrainingSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    original_position_name = serializers.CharField(source='original_position.name', read_only=True)
    trained_position_name = serializers.CharField(source='trained_position.name', read_only=True)

    class Meta:
        model = CrossTraining
        fields = '__all__'
