"""Admin configuration for onboarding models."""
from django.contrib import admin
from .models import TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ['order']


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_lessons', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name']
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration_minutes']
    list_filter = ['course']
    ordering = ['course', 'order']


class ScheduledLessonInline(admin.TabularInline):
    model = ScheduledLesson
    extra = 0
    readonly_fields = ['attended_at', 'marked_by']


@admin.register(MemberTraining)
class MemberTrainingAdmin(admin.ModelAdmin):
    list_display = ['member', 'course', 'is_completed', 'assigned_at']
    list_filter = ['is_completed', 'course']
    search_fields = ['member__first_name', 'member__last_name']
    inlines = [ScheduledLessonInline]


@admin.register(ScheduledLesson)
class ScheduledLessonAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'training', 'scheduled_date', 'status', 'is_makeup']
    list_filter = ['status', 'is_makeup']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['member', 'status', 'proposed_date', 'confirmed_date', 'interviewer']
    list_filter = ['status']
    search_fields = ['member__first_name', 'member__last_name']
