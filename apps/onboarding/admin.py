"""Admin configuration for onboarding models."""
from django.contrib import admin
from .models import (
    TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview,
    InvitationCode,
    MentorAssignment, MentorCheckIn,
    OnboardingFormField, OnboardingFormResponse,
    WelcomeSequence, WelcomeStep, WelcomeProgress,
    OnboardingDocument, DocumentSignature,
    VisitorFollowUp,
    OnboardingTrackModel,
    Achievement, MemberAchievement,
    Quiz, QuizQuestion, QuizAnswer, QuizAttempt,
)


# ─── Training Course Admin ──────────────────────────────────────────────────


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
    list_display = ['title', 'course', 'order', 'duration_minutes', 'video_url']
    list_filter = ['course']
    ordering = ['course', 'order']
    search_fields = ['title']


class ScheduledLessonInline(admin.TabularInline):
    model = ScheduledLesson
    extra = 0
    readonly_fields = ['attended_at', 'marked_by']


@admin.register(MemberTraining)
class MemberTrainingAdmin(admin.ModelAdmin):
    list_display = ['member', 'course', 'is_completed', 'assigned_at', 'track']
    list_filter = ['is_completed', 'course', 'track']
    search_fields = ['member__first_name', 'member__last_name']
    inlines = [ScheduledLessonInline]


@admin.register(ScheduledLesson)
class ScheduledLessonAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'training', 'scheduled_date', 'status', 'is_makeup', 'video_completed']
    list_filter = ['status', 'is_makeup', 'video_completed']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['member', 'status', 'proposed_date', 'confirmed_date', 'interviewer']
    list_filter = ['status']
    search_fields = ['member__first_name', 'member__last_name']


# ─── Invitation Code Admin ──────────────────────────────────────────────────


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'role', 'created_by', 'used_by', 'expires_at', 'use_count', 'max_uses', 'is_active']
    list_filter = ['role', 'is_active', 'skip_onboarding']
    search_fields = ['code', 'note']
    readonly_fields = ['code', 'use_count', 'used_by', 'used_at']


# ─── P1: Mentor Assignment Admin ────────────────────────────────────────────


class MentorCheckInInline(admin.TabularInline):
    model = MentorCheckIn
    extra = 0
    readonly_fields = ['logged_by', 'date']


@admin.register(MentorAssignment)
class MentorAssignmentAdmin(admin.ModelAdmin):
    list_display = ['new_member', 'mentor', 'status', 'start_date', 'check_in_count', 'created_at']
    list_filter = ['status']
    search_fields = [
        'new_member__first_name', 'new_member__last_name',
        'mentor__first_name', 'mentor__last_name',
    ]
    inlines = [MentorCheckInInline]


@admin.register(MentorCheckIn)
class MentorCheckInAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'date', 'logged_by', 'created_at']
    list_filter = ['date']


# ─── P1: Custom Form Fields Admin ───────────────────────────────────────────


@admin.register(OnboardingFormField)
class OnboardingFormFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'field_type', 'is_required', 'order', 'is_active']
    list_filter = ['field_type', 'is_required', 'is_active']
    ordering = ['order']


@admin.register(OnboardingFormResponse)
class OnboardingFormResponseAdmin(admin.ModelAdmin):
    list_display = ['member', 'field', 'value', 'created_at']
    list_filter = ['field']
    search_fields = ['member__first_name', 'member__last_name']


# ─── P1: Welcome Sequence Admin ─────────────────────────────────────────────


class WelcomeStepInline(admin.TabularInline):
    model = WelcomeStep
    extra = 1
    ordering = ['order']


@admin.register(WelcomeSequence)
class WelcomeSequenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    inlines = [WelcomeStepInline]


@admin.register(WelcomeStep)
class WelcomeStepAdmin(admin.ModelAdmin):
    list_display = ['sequence', 'day_offset', 'channel', 'subject', 'order']
    list_filter = ['channel', 'sequence']
    ordering = ['sequence', 'order']


@admin.register(WelcomeProgress)
class WelcomeProgressAdmin(admin.ModelAdmin):
    list_display = ['member', 'sequence', 'current_step', 'started_at', 'completed_at']
    list_filter = ['sequence']
    search_fields = ['member__first_name', 'member__last_name']


# ─── P2: Document Signing Admin ─────────────────────────────────────────────


@admin.register(OnboardingDocument)
class OnboardingDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'requires_signature', 'is_active', 'created_at']
    list_filter = ['document_type', 'requires_signature', 'is_active']
    search_fields = ['title']


@admin.register(DocumentSignature)
class DocumentSignatureAdmin(admin.ModelAdmin):
    list_display = ['document', 'member', 'signature_text', 'signed_at', 'ip_address']
    list_filter = ['document']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['signed_at', 'ip_address']


# ─── P2: Visitor Follow-Up Admin ────────────────────────────────────────────


@admin.register(VisitorFollowUp)
class VisitorFollowUpAdmin(admin.ModelAdmin):
    list_display = ['visitor_name', 'visitor_email', 'first_visit_date', 'status', 'assigned_to', 'converted_at']
    list_filter = ['status']
    search_fields = ['visitor_name', 'visitor_email']


# ─── P3: Multi-Track Admin ──────────────────────────────────────────────────


@admin.register(OnboardingTrackModel)
class OnboardingTrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'track_type', 'is_active', 'created_at']
    list_filter = ['track_type', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['courses', 'documents']


# ─── P3: Gamification Admin ─────────────────────────────────────────────────


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'points', 'trigger_type', 'is_active']
    list_filter = ['trigger_type', 'is_active']
    search_fields = ['name']


@admin.register(MemberAchievement)
class MemberAchievementAdmin(admin.ModelAdmin):
    list_display = ['member', 'achievement', 'earned_at']
    list_filter = ['achievement']
    search_fields = ['member__first_name', 'member__last_name']


# ─── P3: Quiz Admin ─────────────────────────────────────────────────────────


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    ordering = ['order']


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 2


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'passing_score', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title']
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'text', 'order']
    list_filter = ['quiz']
    ordering = ['quiz', 'order']
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'text', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['member', 'quiz', 'score', 'passed', 'completed_at']
    list_filter = ['passed', 'quiz']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['completed_at']
