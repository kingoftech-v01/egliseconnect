"""Volunteers admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import (
    VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest,
    PlannedAbsence, VolunteerHours, VolunteerBackgroundCheck, TeamAnnouncement,
    PositionChecklist, ChecklistProgress, Skill, VolunteerSkill,
    Milestone, MilestoneAchievement, AvailabilitySlot, CrossTraining,
)


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


@admin.register(PlannedAbsence)
class PlannedAbsenceAdmin(BaseModelAdmin):
    list_display = ['member', 'start_date', 'end_date', 'approved_by']
    list_filter = ['start_date']
    autocomplete_fields = ['member', 'approved_by']
    date_hierarchy = 'start_date'


@admin.register(SwapRequest)
class SwapRequestAdmin(BaseModelAdmin):
    list_display = ['original_schedule', 'requested_by', 'swap_with', 'status']
    list_filter = ['status']


@admin.register(VolunteerHours)
class VolunteerHoursAdmin(BaseModelAdmin):
    list_display = ['member', 'position', 'date', 'hours_worked', 'approved_by']
    list_filter = ['position', 'date']
    autocomplete_fields = ['member', 'position', 'approved_by']
    date_hierarchy = 'date'
    search_fields = ['member__first_name', 'member__last_name']


@admin.register(VolunteerBackgroundCheck)
class VolunteerBackgroundCheckAdmin(BaseModelAdmin):
    list_display = ['member', 'position', 'status', 'check_date', 'expiry_date']
    list_filter = ['status', 'check_date']
    autocomplete_fields = ['member', 'position']
    search_fields = ['member__first_name', 'member__last_name']


@admin.register(TeamAnnouncement)
class TeamAnnouncementAdmin(BaseModelAdmin):
    list_display = ['title', 'position', 'author', 'sent_at']
    list_filter = ['position', 'sent_at']
    autocomplete_fields = ['position', 'author']
    search_fields = ['title']


@admin.register(PositionChecklist)
class PositionChecklistAdmin(BaseModelAdmin):
    list_display = ['title', 'position', 'order', 'is_required']
    list_filter = ['position', 'is_required']
    autocomplete_fields = ['position']


@admin.register(ChecklistProgress)
class ChecklistProgressAdmin(BaseModelAdmin):
    list_display = ['member', 'checklist_item', 'completed_at', 'verified_by']
    list_filter = ['completed_at']
    autocomplete_fields = ['member', 'checklist_item', 'verified_by']


@admin.register(Skill)
class SkillAdmin(BaseModelAdmin):
    list_display = ['name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category']


@admin.register(VolunteerSkill)
class VolunteerSkillAdmin(BaseModelAdmin):
    list_display = ['member', 'skill', 'proficiency_level', 'certified_at', 'verified_by']
    list_filter = ['proficiency_level', 'skill']
    autocomplete_fields = ['member', 'skill', 'verified_by']


@admin.register(Milestone)
class MilestoneAdmin(BaseModelAdmin):
    list_display = ['name', 'milestone_type', 'threshold', 'badge_icon']
    list_filter = ['milestone_type']


@admin.register(MilestoneAchievement)
class MilestoneAchievementAdmin(BaseModelAdmin):
    list_display = ['member', 'milestone', 'achieved_at', 'notified']
    list_filter = ['notified', 'achieved_at']
    autocomplete_fields = ['member', 'milestone']


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(BaseModelAdmin):
    list_display = ['member', 'day_of_week', 'time_start', 'time_end', 'is_available']
    list_filter = ['day_of_week', 'is_available']
    autocomplete_fields = ['member']


@admin.register(CrossTraining)
class CrossTrainingAdmin(BaseModelAdmin):
    list_display = ['member', 'original_position', 'trained_position', 'certified_at']
    list_filter = ['original_position', 'trained_position']
    autocomplete_fields = ['member', 'original_position', 'trained_position']
