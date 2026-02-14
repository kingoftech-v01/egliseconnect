"""Celery tasks for the payments app."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_statement_email(statement_id):
    """Send a giving statement PDF to a member via email."""
    from apps.payments.models import GivingStatement
    from django.core.mail import EmailMessage
    from django.conf import settings
    from django.utils import timezone

    try:
        statement = GivingStatement.objects.get(pk=statement_id)
    except GivingStatement.DoesNotExist:
        logger.error(f'Statement not found: {statement_id}')
        return

    if not statement.pdf_file:
        logger.error(f'Statement {statement_id} has no PDF file')
        return

    church_name = getattr(settings, 'CHURCH_NAME', 'ÉgliseConnect')
    member = statement.member

    email = EmailMessage(
        subject=f'Votre relevé de dons - {church_name}',
        body=(
            f'Bonjour {member.full_name},\n\n'
            f'Veuillez trouver ci-joint votre relevé de dons '
            f'{statement.get_statement_type_display().lower()} '
            f'pour la période du {statement.period_start.strftime("%d/%m/%Y")} '
            f'au {statement.period_end.strftime("%d/%m/%Y")}.\n\n'
            f'Montant total: {statement.total_amount:.2f} CAD\n\n'
            f'Cordialement,\n{church_name}'
        ),
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@egliseconnect.com'),
        to=[member.email],
    )
    email.attach_file(statement.pdf_file.path)
    email.send()

    statement.sent_at = timezone.now()
    statement.save(update_fields=['sent_at', 'updated_at'])
    logger.info(f'Statement {statement_id} sent to {member.email}')


@shared_task
def send_bulk_statement_emails(statement_ids):
    """Send batch of giving statement emails."""
    for statement_id in statement_ids:
        send_statement_email.delay(statement_id)


@shared_task
def check_giving_goal_completion():
    """Monthly task to check if members have reached their giving goals."""
    from apps.payments.models import GivingGoal
    from apps.payments.services import PaymentService
    from apps.communication.models import Notification
    from django.utils import timezone

    current_year = timezone.now().year
    goals = GivingGoal.objects.filter(year=current_year, is_active=True)

    for goal in goals:
        progress = PaymentService.calculate_giving_goal_progress(goal.member, current_year)
        if progress and progress['percentage'] >= 100:
            # Check if notification already sent
            existing = Notification.objects.filter(
                member=goal.member,
                title='Objectif de don atteint!',
                created_at__year=current_year,
            ).exists()
            if not existing:
                Notification.objects.create(
                    member=goal.member,
                    title='Objectif de don atteint!',
                    message=(
                        f'Félicitations! Vous avez atteint votre objectif de don de '
                        f'{goal.target_amount:.2f} CAD pour {current_year}.'
                    ),
                    notification_type='donation',
                    link='/payments/history/',
                )
                logger.info(f'Goal completion notification sent to {goal.member.full_name}')


@shared_task
def payment_plan_reminder():
    """Celery task to send reminders for upcoming payment plan installments."""
    from apps.payments.models import PaymentPlan
    from apps.core.constants import PaymentPlanStatus
    from apps.communication.models import Notification
    from django.utils import timezone

    active_plans = PaymentPlan.objects.filter(
        status=PaymentPlanStatus.ACTIVE,
        is_active=True,
    )

    for plan in active_plans:
        # Send a reminder notification
        Notification.objects.create(
            member=plan.member,
            title='Rappel de plan de paiement',
            message=(
                f'Votre prochain versement de {plan.installment_amount:.2f} CAD '
                f'est prévu. Montant restant: {plan.remaining_amount:.2f} CAD.'
            ),
            notification_type='donation',
            link='/payments/plans/',
        )
        logger.info(f'Payment plan reminder sent to {plan.member.full_name}')


@shared_task
def tax_deadline_reminder():
    """Send tax-deadline reminder email before year-end."""
    from apps.members.models import Member
    from apps.communication.models import Notification
    from django.conf import settings

    church_name = getattr(settings, 'CHURCH_NAME', 'ÉgliseConnect')
    members = Member.objects.filter(is_active=True)

    for member in members:
        Notification.objects.create(
            member=member,
            title='Rappel - Date limite fiscale',
            message=(
                f'La date limite pour les dons déductibles d\'impôt pour cette année '
                f'approche! Faites votre don avant le 31 décembre pour recevoir '
                f'votre reçu fiscal de {church_name}.'
            ),
            notification_type='donation',
            link='/payments/donate/',
        )

    logger.info(f'Tax deadline reminders sent to {members.count()} members')


@shared_task
def year_end_giving_summary():
    """Send year-end giving summary email to each member."""
    from apps.payments.models import OnlinePayment, PaymentStatus
    from apps.communication.models import Notification
    from django.db.models import Sum
    from django.utils import timezone

    current_year = timezone.now().year

    # Get all members who donated this year
    member_ids = OnlinePayment.objects.filter(
        status=PaymentStatus.SUCCEEDED,
        created_at__year=current_year,
        is_active=True,
    ).values_list('member_id', flat=True).distinct()

    from apps.members.models import Member

    for member_id in member_ids:
        member = Member.objects.filter(pk=member_id).first()
        if not member:
            continue

        total = OnlinePayment.objects.filter(
            member=member,
            status=PaymentStatus.SUCCEEDED,
            created_at__year=current_year,
            is_active=True,
        ).aggregate(total=Sum('amount'))['total']

        Notification.objects.create(
            member=member,
            title=f'Résumé de vos dons {current_year}',
            message=(
                f'Merci pour votre générosité en {current_year}! '
                f'Votre total de dons cette année: {total:.2f} CAD. '
                f'Votre relevé fiscal sera bientôt disponible.'
            ),
            notification_type='donation',
            link='/payments/history/',
        )

    logger.info(f'Year-end summaries sent to {len(set(member_ids))} members')


@shared_task
def monthly_giving_summary():
    """Send monthly giving summary notification to each active donor."""
    from apps.payments.models import OnlinePayment, PaymentStatus
    from apps.communication.models import Notification
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = month_start - timedelta(seconds=1)
    prev_month_start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    member_ids = OnlinePayment.objects.filter(
        status=PaymentStatus.SUCCEEDED,
        created_at__gte=prev_month_start,
        created_at__lte=prev_month_end,
        is_active=True,
    ).values_list('member_id', flat=True).distinct()

    from apps.members.models import Member

    for member_id in member_ids:
        member = Member.objects.filter(pk=member_id).first()
        if not member:
            continue

        total = OnlinePayment.objects.filter(
            member=member,
            status=PaymentStatus.SUCCEEDED,
            created_at__gte=prev_month_start,
            created_at__lte=prev_month_end,
            is_active=True,
        ).aggregate(total=Sum('amount'))['total']

        month_name = prev_month_start.strftime('%B %Y')
        Notification.objects.create(
            member=member,
            title=f'Résumé mensuel - {month_name}',
            message=(
                f'Votre total de dons pour {month_name}: {total:.2f} CAD. '
                f'Merci pour votre fidélité!'
            ),
            notification_type='donation',
            link='/payments/history/',
        )

    logger.info(f'Monthly summaries sent to {len(set(member_ids))} members')
