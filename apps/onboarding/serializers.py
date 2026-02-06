"""Serializers for onboarding models."""
from rest_framework import serializers
from .models import TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'order', 'title', 'description',
            'duration_minutes', 'materials_pdf', 'materials_notes',
            'created_at',
        ]


class TrainingCourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.ReadOnlyField()

    class Meta:
        model = TrainingCourse
        fields = [
            'id', 'name', 'description', 'total_lessons',
            'is_default', 'lesson_count', 'lessons', 'created_at',
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
