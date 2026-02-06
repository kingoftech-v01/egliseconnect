"""API views for onboarding."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.constants import MembershipStatus, Roles
from apps.core.permissions import IsPastorOrAdmin
from .models import TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview
from .serializers import (
    TrainingCourseSerializer,
    LessonSerializer,
    MemberTrainingSerializer,
    ScheduledLessonSerializer,
    InterviewSerializer,
)
from .services import OnboardingService


class TrainingCourseViewSet(viewsets.ModelViewSet):
    queryset = TrainingCourse.objects.filter(is_active=True)
    serializer_class = TrainingCourseSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.filter(is_active=True)
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    filterset_fields = ['course']


class MemberTrainingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MemberTrainingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return MemberTraining.objects.filter(is_active=True)
            return MemberTraining.objects.filter(
                member=user.member_profile, is_active=True
            )
        return MemberTraining.objects.none()


class InterviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return Interview.objects.filter(is_active=True)
            return Interview.objects.filter(
                member=user.member_profile, is_active=True
            )
        return Interview.objects.none()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        interview = self.get_object()
        OnboardingService.member_accept_interview(interview)
        return Response({'status': 'accepted'})

    @action(detail=True, methods=['post'])
    def counter_propose(self, request, pk=None):
        interview = self.get_object()
        new_date = request.data.get('counter_proposed_date')
        if not new_date:
            return Response(
                {'error': 'counter_proposed_date required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        from django.utils.dateparse import parse_datetime
        parsed = parse_datetime(new_date)
        if not parsed:
            return Response(
                {'error': 'Invalid date format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        OnboardingService.member_counter_propose(interview, parsed)
        return Response({'status': 'counter_proposed'})


class OnboardingStatusView(viewsets.ViewSet):
    """API endpoint for checking onboarding status."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        if not hasattr(request.user, 'member_profile'):
            return Response({'status': 'no_profile'})

        member = request.user.member_profile
        data = {
            'membership_status': member.membership_status,
            'has_full_access': member.has_full_access,
            'can_use_qr': member.can_use_qr,
            'days_remaining_for_form': member.days_remaining_for_form,
            'is_form_expired': member.is_form_expired,
        }

        # Add training progress if in training
        if member.membership_status == MembershipStatus.IN_TRAINING:
            training = MemberTraining.objects.filter(
                member=member, is_active=True
            ).first()
            if training:
                data['training'] = {
                    'course_name': training.course.name,
                    'progress': training.progress_percentage,
                    'completed': training.completed_count,
                    'total': training.total_count,
                }

        return Response(data)


class OnboardingStatsView(viewsets.ViewSet):
    """API endpoint for onboarding statistics (admin only)."""
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]

    def list(self, request):
        from .stats import OnboardingStats

        return Response({
            'pipeline': OnboardingStats.pipeline_counts(),
            'success_rate': OnboardingStats.success_rate(),
            'avg_completion_days': OnboardingStats.avg_completion_days(),
            'training': OnboardingStats.training_stats(),
            'interviews': OnboardingStats.interview_stats(),
            'attendance': OnboardingStats.attendance_stats(),
            'monthly_registrations': OnboardingStats.monthly_registrations(),
        })
