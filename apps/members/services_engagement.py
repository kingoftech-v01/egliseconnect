"""Member engagement score calculation service."""
from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class EngagementScoreService:
    """Calculates composite engagement scores for members."""

    # Weights for each component (must sum to 100)
    WEIGHTS = {
        'attendance': 30,
        'giving': 25,
        'volunteering': 25,
        'group': 20,
    }

    @classmethod
    def calculate_for_member(cls, member):
        """
        Calculate and save engagement score for a single member.

        Returns:
            MemberEngagementScore instance
        """
        from .models import MemberEngagementScore

        attendance = cls._attendance_score(member)
        giving = cls._giving_score(member)
        volunteering = cls._volunteering_score(member)
        group = cls._group_score(member)

        total = (
            attendance * cls.WEIGHTS['attendance'] / 100 +
            giving * cls.WEIGHTS['giving'] / 100 +
            volunteering * cls.WEIGHTS['volunteering'] / 100 +
            group * cls.WEIGHTS['group'] / 100
        )

        score, created = MemberEngagementScore.objects.update_or_create(
            member=member,
            defaults={
                'attendance_score': round(attendance, 1),
                'giving_score': round(giving, 1),
                'volunteering_score': round(volunteering, 1),
                'group_score': round(group, 1),
                'total_score': round(total, 1),
                'calculated_at': timezone.now(),
            }
        )

        return score

    @classmethod
    def calculate_for_all(cls):
        """Calculate engagement scores for all active members."""
        from .models import Member

        members = Member.objects.filter(is_active=True)
        scores = []
        for member in members:
            score = cls.calculate_for_member(member)
            scores.append(score)
        return scores

    @classmethod
    def _attendance_score(cls, member):
        """
        Calculate attendance score (0-100) based on last 90 days.
        Uses events app check-in data if available.
        """
        try:
            from apps.events.models import Attendance
            cutoff = timezone.now() - timedelta(days=90)
            total_services = 13  # ~1/week for 90 days
            attended = Attendance.objects.filter(
                member=member,
                checked_in_at__gte=cutoff,
            ).count()
            return min(100, (attended / max(total_services, 1)) * 100)
        except (ImportError, Exception):
            return 0

    @classmethod
    def _giving_score(cls, member):
        """
        Calculate giving score (0-100) based on donation regularity over 90 days.
        """
        try:
            from apps.donations.models import Donation
            cutoff = timezone.now() - timedelta(days=90)
            donations = Donation.objects.filter(
                member=member,
                date__gte=cutoff.date(),
            ).count()
            # Regular giving: at least once per month = 100
            return min(100, (donations / 3) * 100)
        except (ImportError, Exception):
            return 0

    @classmethod
    def _volunteering_score(cls, member):
        """
        Calculate volunteering score (0-100) based on volunteer activity.
        """
        try:
            from apps.volunteers.models import VolunteerSchedule
            cutoff = timezone.now() - timedelta(days=90)
            shifts = VolunteerSchedule.objects.filter(
                volunteer__member=member,
                date__gte=cutoff.date(),
                status='completed',
            ).count()
            return min(100, (shifts / 6) * 100)  # ~2/month = 100
        except (ImportError, Exception):
            return 0

    @classmethod
    def _group_score(cls, member):
        """
        Calculate group participation score (0-100).
        Based on active group memberships.
        """
        active_groups = member.group_memberships.filter(is_active=True).count()
        if active_groups >= 2:
            return 100
        elif active_groups == 1:
            return 60
        return 0

    @classmethod
    def get_at_risk_members(cls, threshold=30):
        """
        Get members with engagement scores below threshold.

        Returns:
            QuerySet of MemberEngagementScore
        """
        from .models import MemberEngagementScore
        return MemberEngagementScore.objects.filter(
            total_score__lt=threshold,
            member__is_active=True,
        ).select_related('member')
