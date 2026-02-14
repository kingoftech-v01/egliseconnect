"""Frontend views for payments."""
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, DonationType, PaymentPlanStatus
from .models import (
    OnlinePayment,
    RecurringDonation,
    GivingStatement,
    GivingGoal,
    PaymentPlan,
    EmployerMatch,
    GivingCampaign,
    KioskSession,
    CurrencyChoices,
)
from .forms import (
    GivingGoalForm,
    BulkStatementForm,
    EditRecurringForm,
    PaymentPlanForm,
    EmployerMatchForm,
    GivingCampaignForm,
)
from .services import PaymentService


@login_required
def donate(request):
    """Donation page with Stripe Elements."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    from apps.donations.models import DonationCampaign
    campaigns = DonationCampaign.objects.filter(is_active=True)

    # Pre-select campaign from query param
    selected_campaign = request.GET.get('campaign', '')

    # Suggested amounts
    suggested_amounts = [25, 50, 100]

    # Giving goal progress
    member = request.user.member_profile
    current_year = timezone.now().year
    goal_progress = PaymentService.calculate_giving_goal_progress(member, current_year)

    context = {
        'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'campaigns': campaigns,
        'donation_types': DonationType.CHOICES,
        'selected_campaign': selected_campaign,
        'suggested_amounts': suggested_amounts,
        'goal_progress': goal_progress,
        'currencies': CurrencyChoices.CHOICES,
        'page_title': _('Faire un don'),
    }
    return render(request, 'payments/donate.html', context)


@login_required
def donation_success(request):
    """Payment confirmation page with receipt details."""
    payment_id = request.GET.get('payment_id', '')
    payment = None
    if payment_id:
        payment = OnlinePayment.objects.filter(pk=payment_id).first()

    context = {
        'payment': payment,
        'page_title': _('Don reçu - Merci!'),
    }
    return render(request, 'payments/donation_success.html', context)


@login_required
def payment_history(request):
    """View payment history with pagination."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    # Admin sees all, regular member sees own
    if member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        payments = OnlinePayment.objects.all().order_by('-created_at')
    else:
        payments = OnlinePayment.objects.filter(
            member=member
        ).order_by('-created_at')

    # Statements for this member
    statements = GivingStatement.objects.filter(member=member, is_active=True)

    paginator = Paginator(payments, 25)
    page = request.GET.get('page', 1)
    payments_page = paginator.get_page(page)

    context = {
        'payments': payments_page,
        'statements': statements,
        'page_title': _('Historique des paiements'),
    }
    return render(request, 'payments/payment_history.html', context)


@login_required
def recurring_manage(request):
    """Manage recurring donations."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    recurring = RecurringDonation.objects.filter(
        member=member, is_active_subscription=True
    )
    cancelled = RecurringDonation.objects.filter(
        member=member, is_active_subscription=False
    ).order_by('-cancelled_at')[:10]

    context = {
        'recurring': recurring,
        'cancelled': cancelled,
        'page_title': _('Mes dons récurrents'),
    }
    return render(request, 'payments/recurring_manage.html', context)


@login_required
def cancel_recurring(request, pk):
    """Cancel a recurring donation with confirmation."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    recurring = get_object_or_404(
        RecurringDonation,
        pk=pk,
        member=member,
        is_active_subscription=True,
    )

    if request.method == 'POST':
        recurring.is_active_subscription = False
        recurring.cancelled_at = timezone.now()
        recurring.save(update_fields=['is_active_subscription', 'cancelled_at', 'updated_at'])

        messages.success(
            request,
            _('Don récurrent de %(amount)s annulé.') % {'amount': recurring.amount_display}
        )
        return redirect('/payments/recurring/')

    context = {
        'recurring': recurring,
        'page_title': _('Annuler le don récurrent'),
    }
    return render(request, 'payments/cancel_recurring.html', context)


# ─── P1: Edit Recurring ──────────────────────────────────────────────────────


@login_required
def edit_recurring(request, pk):
    """Edit amount/frequency for a recurring donation."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    recurring = get_object_or_404(
        RecurringDonation,
        pk=pk,
        member=member,
        is_active_subscription=True,
    )

    if request.method == 'POST':
        form = EditRecurringForm(request.POST)
        if form.is_valid():
            new_amount = form.cleaned_data['amount']
            new_frequency = form.cleaned_data['frequency']
            PaymentService.update_recurring_donation(recurring, new_amount, new_frequency)
            messages.success(request, _('Don récurrent mis à jour.'))
            return redirect('/payments/recurring/')
    else:
        form = EditRecurringForm(initial={
            'amount': recurring.amount,
            'frequency': recurring.frequency,
        })

    context = {
        'form': form,
        'recurring': recurring,
        'page_title': _('Modifier le don récurrent'),
    }
    return render(request, 'payments/edit_recurring.html', context)


# ─── P1: Giving Statements ───────────────────────────────────────────────────


@login_required
def bulk_generate_statements(request):
    """Admin view to generate statements for all donors in a period."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        form = BulkStatementForm(request.POST)
        if form.is_valid():
            statements = PaymentService.generate_bulk_statements(
                period_start=form.cleaned_data['period_start'],
                period_end=form.cleaned_data['period_end'],
                statement_type=form.cleaned_data['statement_type'],
            )
            messages.success(
                request,
                _('%(count)d relevés générés.') % {'count': len(statements)}
            )
            return redirect('/payments/statements/')
    else:
        form = BulkStatementForm()

    context = {
        'form': form,
        'page_title': _('Générer des relevés'),
    }
    return render(request, 'payments/bulk_statements.html', context)


@login_required
def statement_list(request):
    """View generated statements (admin sees all, member sees own)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        statements = GivingStatement.objects.all()
    else:
        statements = GivingStatement.objects.filter(member=member)

    paginator = Paginator(statements, 25)
    page = request.GET.get('page', 1)
    statements_page = paginator.get_page(page)

    context = {
        'statements': statements_page,
        'is_admin': member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER],
        'page_title': _('Relevés de dons'),
    }
    return render(request, 'payments/statement_list.html', context)


@login_required
def statement_download(request, pk):
    """Download a statement PDF."""
    if not hasattr(request.user, 'member_profile'):
        raise Http404

    member = request.user.member_profile
    if member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        statement = get_object_or_404(GivingStatement, pk=pk)
    else:
        statement = get_object_or_404(GivingStatement, pk=pk, member=member)

    if not statement.pdf_file:
        raise Http404

    return FileResponse(
        statement.pdf_file.open('rb'),
        as_attachment=True,
        filename=f'releve_{statement.period_start}_{statement.period_end}.pdf'
    )


# ─── P1: Giving Goals ────────────────────────────────────────────────────────


@login_required
def giving_goal_manage(request):
    """Create or update giving goal for current year."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    current_year = timezone.now().year
    goal = GivingGoal.objects.filter(member=member, year=current_year).first()

    if request.method == 'POST':
        form = GivingGoalForm(request.POST, instance=goal, member=member)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.member = member
            obj.save()
            messages.success(request, _('Objectif de don enregistré.'))
            return redirect('/payments/goals/')
    else:
        form = GivingGoalForm(instance=goal, member=member)

    progress = PaymentService.calculate_giving_goal_progress(member, current_year)

    context = {
        'form': form,
        'goal': goal,
        'progress': progress,
        'current_year': current_year,
        'page_title': _('Objectif de don'),
    }
    return render(request, 'payments/giving_goal.html', context)


@login_required
def giving_goal_summary(request):
    """Finance staff view: total pledged vs received."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    summary = PaymentService.get_giving_goal_summary()
    goals = GivingGoal.objects.filter(year=timezone.now().year, is_active=True).select_related('member')

    context = {
        'summary': summary,
        'goals': goals,
        'page_title': _('Résumé des objectifs de don'),
    }
    return render(request, 'payments/giving_goal_summary.html', context)


# ─── P2: Giving Kiosk ────────────────────────────────────────────────────────


@login_required
def kiosk_donate(request):
    """Standalone kiosk UI for in-person donations."""
    stripe_public_key = getattr(settings, 'STRIPE_PUBLIC_KEY', '')
    suggested_amounts = [10, 25, 50, 100, 250, 500]

    context = {
        'stripe_public_key': stripe_public_key,
        'suggested_amounts': suggested_amounts,
        'page_title': _('Kiosque de dons'),
    }
    return render(request, 'payments/kiosk_donate.html', context)


@login_required
def kiosk_reconciliation(request):
    """Daily reconciliation view for kiosk sessions."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    sessions = KioskSession.objects.all()[:30]

    context = {
        'sessions': sessions,
        'page_title': _('Réconciliation kiosque'),
    }
    return render(request, 'payments/kiosk_reconciliation.html', context)


# ─── P3: Payment Plans ───────────────────────────────────────────────────────


@login_required
def payment_plan_create(request):
    """Create a payment plan for installment giving."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile

    if request.method == 'POST':
        form = PaymentPlanForm(request.POST)
        if form.is_valid():
            plan = PaymentService.create_payment_plan(
                member=member,
                total_amount=form.cleaned_data['total_amount'],
                installment_amount=form.cleaned_data['installment_amount'],
                frequency=form.cleaned_data['frequency'],
                start_date=form.cleaned_data['start_date'],
                donation_type=form.cleaned_data['donation_type'],
            )
            messages.success(request, _('Plan de paiement créé.'))
            return redirect('/payments/plans/')
    else:
        form = PaymentPlanForm()

    context = {
        'form': form,
        'page_title': _('Créer un plan de paiement'),
    }
    return render(request, 'payments/payment_plan_create.html', context)


@login_required
def payment_plan_list(request):
    """List payment plans for a member."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        plans = PaymentPlan.objects.all()
    else:
        plans = PaymentPlan.objects.filter(member=member)

    context = {
        'plans': plans,
        'page_title': _('Plans de paiement'),
    }
    return render(request, 'payments/payment_plan_list.html', context)


@login_required
def payment_plan_complete(request, pk):
    """Complete a payment plan early."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    plan = get_object_or_404(PaymentPlan, pk=pk, member=member, status=PaymentPlanStatus.ACTIVE)

    if request.method == 'POST':
        PaymentService.complete_plan_early(plan)
        messages.success(request, _('Plan de paiement complété.'))
        return redirect('/payments/plans/')

    context = {
        'plan': plan,
        'page_title': _('Compléter le plan de paiement'),
    }
    return render(request, 'payments/payment_plan_complete.html', context)


# ─── P3: Employer Matching ───────────────────────────────────────────────────


@login_required
def employer_match_create(request):
    """Submit employer matching info."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile

    if request.method == 'POST':
        form = EmployerMatchForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.member = member
            match.save()
            messages.success(request, _('Demande de jumelage soumise.'))
            return redirect('/payments/employer-match/')
    else:
        form = EmployerMatchForm()

    matches = EmployerMatch.objects.filter(member=member)

    context = {
        'form': form,
        'matches': matches,
        'page_title': _('Jumelage employeur'),
    }
    return render(request, 'payments/employer_match.html', context)


# ─── P3: Giving Campaigns ────────────────────────────────────────────────────


@login_required
def giving_campaign_list(request):
    """List active giving campaigns."""
    campaigns = GivingCampaign.objects.filter(is_active=True)

    context = {
        'campaigns': campaigns,
        'page_title': _('Campagnes de dons'),
    }
    return render(request, 'payments/giving_campaign_list.html', context)


@login_required
def giving_campaign_detail(request, pk):
    """Campaign detail page with progress bar and countdown."""
    campaign = get_object_or_404(GivingCampaign, pk=pk)

    context = {
        'campaign': campaign,
        'page_title': campaign.name,
    }
    return render(request, 'payments/giving_campaign_detail.html', context)


@login_required
def giving_campaign_create(request):
    """Create a giving campaign (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        form = GivingCampaignForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _('Campagne créée.'))
            return redirect('/payments/campaigns/')
    else:
        form = GivingCampaignForm()

    context = {
        'form': form,
        'page_title': _('Créer une campagne'),
    }
    return render(request, 'payments/giving_campaign_create.html', context)


# ─── P3: Crypto Donations ────────────────────────────────────────────────────


@login_required
def crypto_donate(request):
    """Cryptocurrency donation page."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    supported_cryptos = PaymentService.get_supported_cryptos()

    context = {
        'supported_cryptos': supported_cryptos,
        'page_title': _('Don en cryptomonnaie'),
    }
    return render(request, 'payments/crypto_donate.html', context)


# ─── P3: Webhook Error Admin ─────────────────────────────────────────────────


@login_required
def webhook_errors(request):
    """Admin view for recent Stripe webhook errors."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    # Show recent failed payments as proxy for webhook issues
    failed_payments = OnlinePayment.objects.filter(
        status='failed'
    ).order_by('-created_at')[:50]

    context = {
        'failed_payments': failed_payments,
        'page_title': _('Erreurs webhook Stripe'),
    }
    return render(request, 'payments/webhook_errors.html', context)


# ─── P1: Payment Confirmation ────────────────────────────────────────────────


@login_required
def payment_confirmation(request, pk):
    """Payment confirmation page with receipt details."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    if member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        payment = get_object_or_404(OnlinePayment, pk=pk)
    else:
        payment = get_object_or_404(OnlinePayment, pk=pk, member=member)

    context = {
        'payment': payment,
        'page_title': _('Confirmation de paiement'),
    }
    return render(request, 'payments/payment_confirmation.html', context)
