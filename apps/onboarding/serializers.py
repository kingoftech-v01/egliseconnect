"""Serializers for onboarding models."""
from rest_framework import serializers
from .models import (
    TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview,
    InvitationCode, MentorAssignment, MentorCheckIn,
    OnboardingFormField, OnboardingFormResponse,
    WelcomeSequence, WelcomeStep, WelcomeProgress,
    OnboardingDocument, DocumentSignature,
    VisitorFollowUp, OnboardingTrackModel,
    Achievement, MemberAchievement,
    Quiz, QuizQuestion, QuizAnswer, QuizAttempt,
)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'order', 'title', 'description',
            'duration_minutes', 'materials_pdf', 'materials_notes',
            'video_url', 'created_at',
        ]


class TrainingCourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.ReadOnlyField()
    participants_count = serializers.ReadOnlyField()

    class Meta:
        model = TrainingCourse
        fields = [
            'id', 'name', 'description', 'total_lessons',
            'is_default', 'lesson_count', 'participants_count',
            'lessons', 'created_at',
        ]


class ScheduledLessonSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_order = serializers.IntegerField(source='lesson.order', read_only=True)

    class Meta:
        model = ScheduledLesson
        fields = [
            'id', 'lesson', 'lesson_title', 'lesson_order',
            'scheduled_date', 'location', 'status',
            'attended_at', 'is_makeup', 'notes',
            'video_completed', 'video_completed_at',
        ]


class MemberTrainingSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    completed_count = serializers.ReadOnlyField()
    total_count = serializers.ReadOnlyField()
    scheduled_lessons = ScheduledLessonSerializer(many=True, read_only=True)

    class Meta:
        model = MemberTraining
        fields = [
            'id', 'member', 'member_name', 'course', 'course_name',
            'assigned_at', 'is_completed', 'completed_at',
            'progress_percentage', 'completed_count', 'total_count',
            'scheduled_lessons',
        ]


class InterviewSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    final_date = serializers.ReadOnlyField()

    class Meta:
        model = Interview
        fields = [
            'id', 'member', 'member_name', 'status',
            'proposed_date', 'counter_proposed_date', 'confirmed_date',
            'final_date', 'location', 'interviewer', 'interviewer_name',
            'completed_at', 'result_notes',
        ]


# ─── Mentor serializers ──────────────────────────────────────────────────────


class MentorCheckInSerializer(serializers.ModelSerializer):
    logged_by_name = serializers.CharField(source='logged_by.full_name', read_only=True)

    class Meta:
        model = MentorCheckIn
        fields = ['id', 'assignment', 'date', 'notes', 'logged_by', 'logged_by_name', 'created_at']


class MentorAssignmentSerializer(serializers.ModelSerializer):
    new_member_name = serializers.CharField(source='new_member.full_name', read_only=True)
    mentor_name = serializers.CharField(source='mentor.full_name', read_only=True)
    check_ins = MentorCheckInSerializer(many=True, read_only=True)

    class Meta:
        model = MentorAssignment
        fields = [
            'id', 'new_member', 'new_member_name', 'mentor', 'mentor_name',
            'start_date', 'status', 'notes', 'check_in_count', 'check_ins',
            'created_at',
        ]


# ─── Custom form field serializers ───────────────────────────────────────────


class OnboardingFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingFormField
        fields = [
            'id', 'label', 'field_type', 'is_required', 'options', 'order',
            'conditional_field', 'conditional_value',
        ]


class OnboardingFormResponseSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source='field.label', read_only=True)

    class Meta:
        model = OnboardingFormResponse
        fields = ['id', 'member', 'field', 'field_label', 'value', 'file']


# ─── Welcome sequence serializers ────────────────────────────────────────────


class WelcomeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelcomeStep
        fields = ['id', 'sequence', 'day_offset', 'channel', 'subject', 'body', 'order']


class WelcomeSequenceSerializer(serializers.ModelSerializer):
    steps = WelcomeStepSerializer(many=True, read_only=True)

    class Meta:
        model = WelcomeSequence
        fields = ['id', 'name', 'description', 'is_active', 'steps']


class WelcomeProgressSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    sequence_name = serializers.CharField(source='sequence.name', read_only=True)

    class Meta:
        model = WelcomeProgress
        fields = [
            'id', 'member', 'member_name', 'sequence', 'sequence_name',
            'current_step', 'started_at', 'completed_at',
        ]


# ─── Document serializers ────────────────────────────────────────────────────


class OnboardingDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingDocument
        fields = ['id', 'title', 'content', 'requires_signature', 'document_type', 'created_at']


class DocumentSignatureSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = DocumentSignature
        fields = [
            'id', 'document', 'document_title', 'member', 'member_name',
            'signature_text', 'signed_at', 'ip_address',
        ]


# ─── Visitor follow-up serializers ───────────────────────────────────────────


class VisitorFollowUpSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True, default=None)

    class Meta:
        model = VisitorFollowUp
        fields = [
            'id', 'visitor_name', 'visitor_email', 'visitor_phone',
            'first_visit_date', 'assigned_to', 'assigned_to_name',
            'member', 'status', 'notes', 'converted_at', 'created_at',
        ]


# ─── Track serializers ───────────────────────────────────────────────────────


class OnboardingTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingTrackModel
        fields = ['id', 'name', 'track_type', 'description', 'courses', 'documents']


# ─── Gamification serializers ────────────────────────────────────────────────


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'icon', 'badge_image', 'points', 'trigger_type']


class MemberAchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='achievement.name', read_only=True)
    achievement_icon = serializers.CharField(source='achievement.icon', read_only=True)
    achievement_points = serializers.IntegerField(source='achievement.points', read_only=True)

    class Meta:
        model = MemberAchievement
        fields = [
            'id', 'member', 'achievement', 'achievement_name',
            'achievement_icon', 'achievement_points', 'earned_at',
        ]


# ─── Quiz serializers ────────────────────────────────────────────────────────


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id', 'question', 'text', 'is_correct']


class QuizQuestionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'quiz', 'text', 'order', 'answers']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'lesson', 'title', 'passing_score', 'questions']


class QuizAttemptSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'member', 'member_name', 'quiz', 'quiz_title',
            'score', 'passed', 'answers', 'completed_at',
        ]
