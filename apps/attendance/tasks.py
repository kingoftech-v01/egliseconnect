"""Celery tasks for attendance-based inactivity tracking."""
import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from apps.core.constants import MembershipStatus, AttendanceSessionType, Roles

logger = logging.getLogger(__name__)


@shared_task
def check_member_inactivity():
    """
    Check member inactivity based on attendance records.
    - 2 months without any attendance → INACTIVE
    - 6 months inactive → EXPIRED (must redo onboarding, account conserved)
    """
    from apps.members.models import Member
    from apps.attendance.models import AttendanceRecord

    now = timezone.now()
    two_months_ago = now - timedelta(days=60)
    six_months_ago = now - timedelta(days=180)

    total_inactive = 0
    total_expired = 0

    # Step 1: Active members with no attendance in 2 months → INACTIVE
    active_members = Member.objects.filter(
        membership_status=MembershipStatus.ACTIVE,
        is_active=True,
    )

    for member in active_members:
        last_attendance = AttendanceRecord.objects.filter(
            member=member,
            checked_in_at__gte=two_months_ago,
        ).exists()

        if not last_attendance:
            # Check they have at least some attendance history (not brand new)
            has_any_attendance = AttendanceRecord.objects.filter(
                member=member,
            ).exists()
            if has_any_attendance:
                member.membership_status = MembershipStatus.INACTIVE
                member.save(update_fields=['membership_status', 'updated_at'])
                total_inactive += 1
                logger.info(
                    f'Member marked INACTIVE: {member.full_name} '
                    f'({member.member_number})'
                )

    # Step 2: Inactive members for 6+ months → EXPIRED
    inactive_members = Member.objects.filter(
        membership_status=MembershipStatus.INACTIVE,
    )

    for member in inactive_members:
        last_attendance = AttendanceRecord.objects.filter(
            member=member,
            checked_in_at__gte=six_months_ago,
        ).exists()

        if not last_attendance:
            member.membership_status = MembershipStatus.EXPIRED
            member.is_active = False
            member.save(update_fields=[
                'membership_status', 'is_active', 'updated_at'
            ])
            total_expired += 1
            logger.info(
                f'Member marked EXPIRED: {member.full_name} '
                f'({member.member_number})'
            )

    logger.info(
        f'Inactivity check: {total_inactive} marked inactive, '
        f'{total_expired} marked expired.'
    )
    return {'inactive': total_inactive, 'expired': total_expired}


@shared_task
def check_absence_alerts():
    """
    Check for members who missed 3+ worship sessions in the last 30 days.
    Creates AbsenceAlert records and notifies leaders/admins.
    """
    from apps.members.models import Member
    from apps.attendance.models import AttendanceSession, AttendanceRecord, AbsenceAlert
    from apps.communication.models import Notification

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Get all worship sessions in the last 30 days
    recent_sessions = AttendanceSession.objects.filter(
        session_type=AttendanceSessionType.WORSHIP,
        date__gte=thirty_days_ago.date(),
        date__lte=now.date(),
    )
    session_count = recent_sessions.count()

    if session_count == 0:
        return 0

    total_alerts = 0

    # Check active members
    active_members = Member.objects.filter(
        membership_status=MembershipStatus.ACTIVE,
        is_active=True,
    )

    for member in active_members:
        # Count sessions this member attended
        attended = AttendanceRecord.objects.filter(
            member=member,
            session__in=recent_sessions,
        ).count()

        missed = session_count - attended
        if missed < 3:
            continue

        # Check if an unacknowledged alert already exists
        existing_alert = AbsenceAlert.objects.filter(
            member=member,
            acknowledged_by__isnull=True,
        ).first()

        if existing_alert:
            # Update consecutive count if it increased
            if missed > existing_alert.consecutive_absences:
                existing_alert.consecutive_absences = missed
                existing_alert.save(update_fields=['consecutive_absences', 'updated_at'])
            continue

        # Get last attendance date
        last_record = AttendanceRecord.objects.filter(
            member=member,
        ).order_by('-checked_in_at').first()

        last_date = last_record.checked_in_at.date() if last_record else None

        # Create alert
        AbsenceAlert.objects.create(
            member=member,
            consecutive_absences=missed,
            last_attendance_date=last_date,
            alert_sent=True,
            alert_sent_at=now,
        )

        # Notify admins and pastors
        leaders = Member.objects.filter(
            role__in=[Roles.ADMIN, Roles.PASTOR],
            is_active=True,
        )
        for leader in leaders:
            Notification.objects.create(
                member=leader,
                title=f"Alerte d'absence: {member.full_name}",
                message=(
                    f'{member.full_name} a manqué {missed} cultes '
                    f'au cours des 30 derniers jours.'
                ),
                notification_type='attendance',
                link='/attendance/sessions/',
            )

        total_alerts += 1
        logger.info(
            f'Absence alert created for {member.full_name}: '
            f'{missed} missed sessions'
        )

    return total_alerts
