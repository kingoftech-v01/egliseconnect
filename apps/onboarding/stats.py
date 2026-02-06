"""Statistics and analytics for the onboarding pipeline."""
from datetime import timedelta

from django.db.models import Avg, Count, Q, F
from django.utils import timezone

from apps.core.constants import MembershipStatus, InterviewStatus
from apps.members.models import Member
from apps.attendance.models import AttendanceRecord, AttendanceSession, AbsenceAlert
from .models import MemberTraining, Interview


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
