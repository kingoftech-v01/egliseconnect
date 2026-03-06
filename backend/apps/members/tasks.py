"""Celery tasks for member management."""
from celery import shared_task


@shared_task
def send_care_follow_up_reminders():
    """
    Check for overdue pastoral care follow-ups and notify assigned pastors.
    Should run daily.
    """
    from datetime import date
    from apps.members.models import PastoralCare
    from apps.core.constants import CareStatus

    overdue = PastoralCare.objects.filter(
        follow_up_date__lte=date.today(),
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
        is_active=True,
    ).select_related('member', 'assigned_to')

    count = 0
    for care in overdue:
        if care.assigned_to:
            try:
                from apps.communication.models import Notification
                Notification.objects.create(
                    member=care.assigned_to,
                    title='Suivi pastoral en retard',
                    message=(
                        f'Le suivi pour {care.member.full_name} '
                        f'({care.get_care_type_display()}) était prévu le {care.follow_up_date}.'
                    ),
                    notification_type='general',
                    link=f'/members/care/{care.pk}/',
                )
                count += 1
            except Exception:
                pass

    return f'{count} rappels de suivi envoyés'


@shared_task
def check_background_check_expiry():
    """
    Check for background checks expiring within 30 days and notify admins.
    Should run daily.
    """
    from datetime import date, timedelta
    from apps.members.models import BackgroundCheck, Member
    from apps.core.constants import BackgroundCheckStatus, Roles

    threshold = date.today() + timedelta(days=30)

    expiring = BackgroundCheck.objects.filter(
        expiry_date__lte=threshold,
        expiry_date__gte=date.today(),
        status=BackgroundCheckStatus.APPROVED,
        is_active=True,
    ).select_related('member')

    if not expiring.exists():
        return '0 vérifications expirantes'

    # Get admin/pastor members to notify
    admins = Member.objects.filter(
        role__in=[Roles.ADMIN, Roles.PASTOR],
        is_active=True,
    )

    count = 0
    for check in expiring:
        for admin in admins:
            try:
                from apps.communication.models import Notification
                Notification.objects.create(
                    member=admin,
                    title='Vérification des antécédents bientôt expirée',
                    message=(
                        f'La vérification de {check.member.full_name} '
                        f'expire le {check.expiry_date}.'
                    ),
                    notification_type='general',
                    link=f'/members/background-checks/{check.pk}/',
                )
                count += 1
            except Exception:
                pass

    # Also mark expired checks
    BackgroundCheck.objects.filter(
        expiry_date__lt=date.today(),
        status=BackgroundCheckStatus.APPROVED,
    ).update(status=BackgroundCheckStatus.EXPIRED)

    return f'{count} alertes d\'expiration envoyées'


@shared_task
def calculate_all_engagement_scores():
    """
    Recalculate engagement scores for all active members.
    Should run weekly.
    """
    from apps.members.services_engagement import EngagementScoreService

    scores = EngagementScoreService.calculate_for_all()
    return f'{len(scores)} scores calculés'
