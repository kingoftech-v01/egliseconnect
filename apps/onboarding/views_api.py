"""API views for onboarding."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.constants import MembershipStatus, Roles
from apps.core.permissions import IsPastorOrAdmin, IsMember
from .models import (
    TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview,
    MentorAssignment, MentorCheckIn,
    OnboardingFormField, OnboardingFormResponse,
    WelcomeSequence, WelcomeProgress,
    OnboardingDocument, DocumentSignature,
    VisitorFollowUp, OnboardingTrackModel,
    Achievement, MemberAchievement,
    Quiz, QuizAttempt,
)
from .serializers import (
    TrainingCourseSerializer,
    LessonSerializer,
    MemberTrainingSerializer,
    ScheduledLessonSerializer,
    InterviewSerializer,
    MentorAssignmentSerializer,
    MentorCheckInSerializer,
    OnboardingFormFieldSerializer,
    OnboardingFormResponseSerializer,
    WelcomeSequenceSerializer,
    WelcomeProgressSerializer,
    OnboardingDocumentSerializer,
    DocumentSignatureSerializer,
    VisitorFollowUpSerializer,
    OnboardingTrackSerializer,
    AchievementSerializer,
    MemberAchievementSerializer,
    QuizSerializer,
    QuizAttemptSerializer,
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
            'mentor_stats': OnboardingStats.mentor_stats(),
            'visitor_stats': OnboardingStats.visitor_stats(),
        })


# ─── P1: Mentor Assignment API ──────────────────────────────────────────────


class MentorAssignmentViewSet(viewsets.ModelViewSet):
    """API for mentor assignments."""
    serializer_class = MentorAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return MentorAssignment.objects.filter(is_active=True)
            # Show assignments where user is mentor or mentee
            return MentorAssignment.objects.filter(
                is_active=True
            ).filter(
                __import__('django.db.models', fromlist=['Q']).Q(mentor=user.member_profile) |
                __import__('django.db.models', fromlist=['Q']).Q(new_member=user.member_profile)
            )
        return MentorAssignment.objects.none()

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'member_profile'):
            return MentorAssignment.objects.none()
        from django.db.models import Q
        if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
            return MentorAssignment.objects.filter(is_active=True)
        return MentorAssignment.objects.filter(
            Q(mentor=user.member_profile) | Q(new_member=user.member_profile),
            is_active=True,
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        assignment = self.get_object()
        OnboardingService.complete_mentor_assignment(assignment)
        return Response({'status': 'completed'})

    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        assignment = self.get_object()
        notes = request.data.get('notes', '')
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'No profile'}, status=status.HTTP_400_BAD_REQUEST)
        OnboardingService.log_mentor_checkin(
            assignment=assignment,
            notes=notes,
            logged_by=request.user.member_profile,
        )
        return Response({'status': 'checkin_logged'})


# ─── P1: Custom Form Fields API ─────────────────────────────────────────────


class OnboardingFormFieldViewSet(viewsets.ModelViewSet):
    """Admin CRUD for custom form fields."""
    queryset = OnboardingFormField.objects.filter(is_active=True).order_by('order')
    serializer_class = OnboardingFormFieldSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


class OnboardingFormResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of form responses."""
    serializer_class = OnboardingFormResponseSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]

    def get_queryset(self):
        qs = OnboardingFormResponse.objects.select_related('member', 'field')
        member_pk = self.request.query_params.get('member')
        if member_pk:
            qs = qs.filter(member__pk=member_pk)
        return qs


# ─── P1: Welcome Sequence API ───────────────────────────────────────────────


class WelcomeSequenceViewSet(viewsets.ModelViewSet):
    """Admin CRUD for welcome sequences."""
    queryset = WelcomeSequence.objects.all()
    serializer_class = WelcomeSequenceSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


class WelcomeProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """Read progress of members through welcome sequences."""
    serializer_class = WelcomeProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return WelcomeProgress.objects.all()
            return WelcomeProgress.objects.filter(member=user.member_profile)
        return WelcomeProgress.objects.none()


# ─── P2: Document API ───────────────────────────────────────────────────────


class OnboardingDocumentViewSet(viewsets.ModelViewSet):
    """Admin CRUD for onboarding documents."""
    queryset = OnboardingDocument.objects.filter(is_active=True)
    serializer_class = OnboardingDocumentSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


class DocumentSignatureViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of document signatures."""
    serializer_class = DocumentSignatureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return DocumentSignature.objects.all()
            return DocumentSignature.objects.filter(member=user.member_profile)
        return DocumentSignature.objects.none()

    @action(detail=False, methods=['post'])
    def sign(self, request):
        """Sign a document via API."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'No profile'}, status=status.HTTP_400_BAD_REQUEST)

        document_pk = request.data.get('document')
        signature_text = request.data.get('signature_text')

        if not document_pk or not signature_text:
            return Response(
                {'error': 'document and signature_text required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = OnboardingDocument.objects.get(pk=document_pk)
        except OnboardingDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ip_address = request.META.get('REMOTE_ADDR')
        signature, created = OnboardingService.sign_document(
            document=document,
            member=request.user.member_profile,
            signature_text=signature_text,
            ip_address=ip_address,
        )

        if created:
            return Response({'status': 'signed'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already_signed'})


# ─── P2: Visitor Follow-Up API ──────────────────────────────────────────────


class VisitorFollowUpViewSet(viewsets.ModelViewSet):
    """Admin CRUD for visitor follow-ups."""
    queryset = VisitorFollowUp.objects.select_related('assigned_to', 'member')
    serializer_class = VisitorFollowUpSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


# ─── P3: Multi-Track API ────────────────────────────────────────────────────


class OnboardingTrackViewSet(viewsets.ModelViewSet):
    """Admin CRUD for onboarding tracks."""
    queryset = OnboardingTrackModel.objects.filter(is_active=True)
    serializer_class = OnboardingTrackSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


# ─── P3: Gamification API ───────────────────────────────────────────────────


class AchievementViewSet(viewsets.ModelViewSet):
    """Admin CRUD for achievements."""
    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]


class MemberAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of member achievements."""
    serializer_class = MemberAchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return MemberAchievement.objects.all()
            return MemberAchievement.objects.filter(member=user.member_profile)
        return MemberAchievement.objects.none()


# ─── P3: Quiz API ───────────────────────────────────────────────────────────


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of quizzes."""
    queryset = Quiz.objects.filter(is_active=True)
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]


class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """View and create quiz attempts."""
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]:
                return QuizAttempt.objects.all()
            return QuizAttempt.objects.filter(member=user.member_profile)
        return QuizAttempt.objects.none()

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """Submit a quiz attempt."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'No profile'}, status=status.HTTP_400_BAD_REQUEST)

        quiz_pk = request.data.get('quiz')
        answers_data = request.data.get('answers', {})

        if not quiz_pk:
            return Response(
                {'error': 'quiz required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quiz = Quiz.objects.get(pk=quiz_pk)
        except Quiz.DoesNotExist:
            return Response(
                {'error': 'Quiz not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate score
        from .models import QuizQuestion, QuizAnswer
        questions = quiz.questions.filter(is_active=True)
        total = questions.count()
        correct = 0

        for question in questions:
            answer_id = answers_data.get(str(question.pk))
            if answer_id:
                try:
                    answer = QuizAnswer.objects.get(pk=answer_id, question=question)
                    if answer.is_correct:
                        correct += 1
                except QuizAnswer.DoesNotExist:
                    pass

        score = int((correct / total) * 100) if total > 0 else 0
        passed = score >= quiz.passing_score

        attempt = QuizAttempt.objects.create(
            member=request.user.member_profile,
            quiz=quiz,
            score=score,
            passed=passed,
            answers=answers_data,
        )

        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
