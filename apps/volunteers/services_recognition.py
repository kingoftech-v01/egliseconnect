"""Service for volunteer recognition: milestone checking and notifications."""
import logging
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.core.constants import MilestoneType

logger = logging.getLogger(__name__)


class RecognitionService:
    """Check milestones and trigger notifications for volunteer achievements."""

    @staticmethod
    def check_milestones(member):
        """
        Check if a member has achieved any new milestones.

        Checks both hours-based and years-based milestones.

        Returns:
            list of newly achieved MilestoneAchievement instances
        """
        from .models import Milestone, MilestoneAchievement, VolunteerHours

        now = timezone.now()
        new_achievements = []

        # Get all milestones not yet achieved by this member
        achieved_ids = MilestoneAchievement.objects.filter(
            member=member
        ).values_list('milestone_id', flat=True)

        pending_milestones = Milestone.objects.exclude(id__in=achieved_ids)

        # Calculate total volunteer hours
        total_hours = VolunteerHours.objects.filter(
            member=member
        ).aggregate(total=Sum('hours_worked'))['total'] or Decimal('0')

        # Calculate years of service (based on first volunteer hour entry)
        first_entry = VolunteerHours.objects.filter(
            member=member
        ).order_by('date').first()

        years_of_service = 0
        if first_entry:
            delta = now.date() - first_entry.date
            years_of_service = delta.days // 365

        for milestone in pending_milestones:
            achieved = False

            if milestone.milestone_type == MilestoneType.HOURS:
                achieved = total_hours >= Decimal(str(milestone.threshold))
            elif milestone.milestone_type == MilestoneType.YEARS:
                achieved = years_of_service >= milestone.threshold

            if achieved:
                achievement = MilestoneAchievement.objects.create(
                    member=member,
                    milestone=milestone,
                    achieved_at=now,
                    notified=False,
                )
                new_achievements.append(achievement)
                logger.info(
                    f'Milestone achieved: {member.full_name} - {milestone.name}'
                )

        return new_achievements

    @staticmethod
    def trigger_notification(achievement):
        """
        Send a notification for a milestone achievement.

        Args:
            achievement: MilestoneAchievement instance
        """
        from apps.communication.models import Notification

        if achievement.notified:
            return

        Notification.objects.create(
            member=achievement.member,
            title='Jalon atteint!',
            message=(
                f'Felicitations! Vous avez atteint le jalon '
                f'"{achievement.milestone.name}". '
                f'Merci pour votre service devoue!'
            ),
            notification_type='volunteer',
            link='/volunteers/milestones/',
        )

        achievement.notified = True
        achievement.save(update_fields=['notified', 'updated_at'])

    @staticmethod
    def get_leaderboard(limit=10):
        """
        Get top volunteers by total hours.

        Returns:
            list of dicts: [{member, total_hours}, ...]
        """
        from .models import VolunteerHours
        from django.db.models import F

        return list(
            VolunteerHours.objects.values(
                mem_id=F('member__id'),
                member_name=F('member__first_name'),
                member_last=F('member__last_name'),
            ).annotate(
                total_hours=Sum('hours_worked'),
            ).order_by('-total_hours')[:limit]
        )
