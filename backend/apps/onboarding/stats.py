"""Statistics and analytics for the onboarding pipeline."""
from datetime import timedelta

from django.db.models import Avg, Count, Q, F, Sum
from django.utils import timezone

from apps.core.constants import (
    MembershipStatus, InterviewStatus,
    MentorAssignmentStatus, VisitorFollowUpStatus,
)
from apps.members.models import Member
from apps.attendance.models import AttendanceRecord, AttendanceSession, AbsenceAlert
from .models import (
    MemberTraining, Interview,
    MentorAssignment, MentorCheckIn,
    VisitorFollowUp,
    OnboardingTrackModel, MemberAchievement,
)


class OnboardingStats:
    """Calculate statistics for the onboarding dashboard."""

    @staticmethod
    def pipeline_counts():
        """Count members at each stage of the pipeline."""
        return {
            'registered': Member.objects.filter(
                membership_status=MembershipStatus.REGISTERED
            ).count(),
            'form_pending': Member.objects.filter(
                membership_status=MembershipStatus.FORM_PENDING
            ).count(),
            'form_submitted': Member.objects.filter(
                membership_status=MembershipStatus.FORM_SUBMITTED
            ).count(),
            'in_review': Member.objects.filter(
                membership_status=MembershipStatus.IN_REVIEW
            ).count(),
            'in_training': Member.objects.filter(
                membership_status=MembershipStatus.IN_TRAINING
            ).count(),
            'interview_scheduled': Member.objects.filter(
                membership_status=MembershipStatus.INTERVIEW_SCHEDULED
            ).count(),
            'active': Member.objects.filter(
                membership_status=MembershipStatus.ACTIVE
            ).count(),
            'rejected': Member.objects.filter(
                membership_status=MembershipStatus.REJECTED
            ).count(),
            'expired': Member.objects.filter(
                membership_status=MembershipStatus.EXPIRED
            ).count(),
            'total_in_process': Member.objects.filter(
                membership_status__in=MembershipStatus.IN_PROCESS
            ).count(),
        }

    @staticmethod
    def success_rate():
        """Calculate the success rate (active / (active + rejected + expired))."""
        active = Member.objects.filter(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at__isnull=False,
        ).count()
        rejected = Member.objects.filter(
            membership_status=MembershipStatus.REJECTED
        ).count()
        expired = Member.objects.filter(
            membership_status=MembershipStatus.EXPIRED
        ).count()
        total = active + rejected + expired
        if total == 0:
            return 0
        return round((active / total) * 100, 1)

    @staticmethod
    def avg_completion_days():
        """Average days from registration to becoming active."""
        members = Member.objects.filter(
            membership_status=MembershipStatus.ACTIVE,
            registration_date__isnull=False,
            became_active_at__isnull=False,
        )
        if not members.exists():
            return 0

        total_days = 0
        count = 0
        for m in members:
            delta = m.became_active_at - m.registration_date
            total_days += delta.days
            count += 1

        return round(total_days / count, 1) if count > 0 else 0

    @staticmethod
    def training_stats():
        """Statistics about training courses."""
        total = MemberTraining.objects.count()
        completed = MemberTraining.objects.filter(is_completed=True).count()
        in_progress = MemberTraining.objects.filter(
            is_completed=False, is_active=True
        ).count()

        return {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'completion_rate': round((completed / total) * 100, 1) if total > 0 else 0,
        }

    @staticmethod
    def interview_stats():
        """Statistics about interviews."""
        total = Interview.objects.count()
        passed = Interview.objects.filter(status=InterviewStatus.COMPLETED_PASS).count()
        failed = Interview.objects.filter(status=InterviewStatus.COMPLETED_FAIL).count()
        no_show = Interview.objects.filter(status=InterviewStatus.NO_SHOW).count()
        pending = Interview.objects.filter(
            status__in=[InterviewStatus.PROPOSED, InterviewStatus.ACCEPTED,
                       InterviewStatus.COUNTER, InterviewStatus.CONFIRMED]
        ).count()

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'no_show': no_show,
            'pending': pending,
            'pass_rate': round((passed / (passed + failed + no_show)) * 100, 1) if (passed + failed + no_show) > 0 else 0,
        }

    @staticmethod
    def attendance_stats():
        """Attendance statistics for the last 30 days."""
        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        sessions = AttendanceSession.objects.filter(
            date__gte=thirty_days_ago
        )
        total_sessions = sessions.count()
        total_checkins = AttendanceRecord.objects.filter(
            session__date__gte=thirty_days_ago
        ).count()

        active_alerts = AbsenceAlert.objects.filter(
            alert_sent=False, is_active=True
        ).count()

        avg_attendance = round(total_checkins / total_sessions, 1) if total_sessions > 0 else 0

        return {
            'total_sessions': total_sessions,
            'total_checkins': total_checkins,
            'avg_attendance': avg_attendance,
            'active_alerts': active_alerts,
        }

    @staticmethod
    def recent_activity(limit=10):
        """Recent onboarding activity."""
        recent_members = Member.objects.filter(
            registration_date__isnull=False,
        ).order_by('-registration_date')[:limit]

        recent_completions = Member.objects.filter(
            became_active_at__isnull=False,
        ).order_by('-became_active_at')[:limit]

        return {
            'recent_registrations': recent_members,
            'recent_completions': recent_completions,
        }

    @staticmethod
    def monthly_registrations(months=6):
        """Count registrations per month for the last N months."""
        result = []
        now = timezone.now()
        for i in range(months - 1, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0)
            else:
                month_end = now

            count = Member.objects.filter(
                registration_date__gte=month_start,
                registration_date__lt=month_end,
            ).count()
            result.append({
                'month': month_start.strftime('%B %Y'),
                'count': count,
            })
        return result

    # ─── P1: Mentor Statistics ───────────────────────────────────────────

    @staticmethod
    def mentor_stats():
        """Statistics about mentor assignments."""
        total = MentorAssignment.objects.count()
        active = MentorAssignment.objects.filter(
            status=MentorAssignmentStatus.ACTIVE
        ).count()
        completed = MentorAssignment.objects.filter(
            status=MentorAssignmentStatus.COMPLETED
        ).count()
        total_checkins = MentorCheckIn.objects.count()

        avg_checkins = 0
        if total > 0:
            avg_checkins = round(total_checkins / total, 1)

        # Top mentors by assignment count
        top_mentors = (
            MentorAssignment.objects
            .values('mentor__first_name', 'mentor__last_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return {
            'total': total,
            'active': active,
            'completed': completed,
            'total_checkins': total_checkins,
            'avg_checkins': avg_checkins,
            'top_mentors': list(top_mentors),
        }

    # ─── P2: Visitor Statistics ──────────────────────────────────────────

    @staticmethod
    def visitor_stats():
        """Statistics about visitor follow-ups and conversion."""
        total = VisitorFollowUp.objects.count()
        converted = VisitorFollowUp.objects.filter(
            converted_at__isnull=False
        ).count()
        pending = VisitorFollowUp.objects.filter(
            status=VisitorFollowUpStatus.PENDING
        ).count()
        in_progress = VisitorFollowUp.objects.filter(
            status=VisitorFollowUpStatus.IN_PROGRESS
        ).count()

        # Monthly visitors
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_visitors = VisitorFollowUp.objects.filter(
            first_visit_date__gte=thirty_days_ago.date()
        ).count()

        return {
            'total': total,
            'converted': converted,
            'pending': pending,
            'in_progress': in_progress,
            'recent_visitors': recent_visitors,
            'conversion_rate': round((converted / total) * 100, 1) if total > 0 else 0,
        }

    # ─── P3: Track Comparison Analytics ──────────────────────────────────

    @staticmethod
    def track_comparison():
        """Compare onboarding tracks by completion rates and durations."""
        tracks = OnboardingTrackModel.objects.filter(is_active=True)
        result = []

        for track in tracks:
            enrollments = MemberTraining.objects.filter(track=track)
            total = enrollments.count()
            completed = enrollments.filter(is_completed=True).count()

            # Calculate average completion days for this track
            avg_days = 0
            completed_trainings = enrollments.filter(
                is_completed=True,
                completed_at__isnull=False,
            )
            if completed_trainings.exists():
                total_days = 0
                count = 0
                for t in completed_trainings:
                    if t.assigned_at:
                        delta = t.completed_at - t.assigned_at
                        total_days += delta.days
                        count += 1
                if count > 0:
                    avg_days = round(total_days / count, 1)

            result.append({
                'track': track,
                'total_enrollments': total,
                'completed': completed,
                'completion_rate': round((completed / total) * 100, 1) if total > 0 else 0,
                'avg_completion_days': avg_days,
                'courses_count': track.courses.count(),
                'documents_count': track.documents.count(),
            })

        return result

    # ─── P3: Gamification Stats ──────────────────────────────────────────

    @staticmethod
    def gamification_stats():
        """Statistics about achievement distribution."""
        total_earned = MemberAchievement.objects.count()
        unique_earners = MemberAchievement.objects.values('member').distinct().count()

        top_achievers = (
            MemberAchievement.objects
            .values('member__first_name', 'member__last_name')
            .annotate(
                total_points=Sum('achievement__points'),
                badge_count=Count('id'),
            )
            .order_by('-total_points')[:10]
        )

        return {
            'total_earned': total_earned,
            'unique_earners': unique_earners,
            'top_achievers': list(top_achievers),
        }
