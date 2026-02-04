"""
Donations Frontend Views - Template-based views for donation management.

This module provides template-based views for:
- Donation creation (online giving)
- Donation history
- Physical donation recording (treasurer)
- Campaign viewing
- Tax receipts

All views render HTML templates using Django's render().
"""
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, PaymentMethod
from apps.core.mixins import TreasurerRequiredMixin, FinanceStaffRequiredMixin

from .models import Donation, DonationCampaign, TaxReceipt
from .forms import (
    DonationForm,
    PhysicalDonationForm,
    DonationCampaignForm,
    DonationFilterForm,
)


# =============================================================================
# DONATION VIEWS
# =============================================================================

@login_required
def donation_create(request):
    """
    Create an online donation.

    Template: donations/donation_form.html
    """
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Vous devez avoir un profil membre pour faire un don."))
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.member = member
            donation.payment_method = PaymentMethod.ONLINE
            donation.save()

            messages.success(
                request,
                _('Merci pour votre don de %(amount)s$! Numéro: %(number)s') % {
                    'amount': donation.amount,
                    'number': donation.donation_number,
                }
            )
            return redirect('frontend:donations:donation_detail', pk=donation.pk)
    else:
        form = DonationForm()

    # Get active campaigns
    campaigns = DonationCampaign.objects.filter(is_active=True)

    context = {
        'form': form,
        'campaigns': campaigns,
        'form_title': _('Faire un don'),
        'submit_text': _('Donner'),
        'page_title': _('Faire un don'),
    }

    return render(request, 'donations/donation_form.html', context)


@login_required
def donation_detail(request, pk):
    """
    Display donation details.

    Template: donations/donation_detail.html
    """
    donation = get_object_or_404(Donation, pk=pk)

    # Check permissions
    can_view = False

    if request.user.is_staff:
        can_view = True
    elif hasattr(request.user, 'member_profile'):
        member = request.user.member_profile

        if donation.member == member:
            can_view = True
        elif member.role in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            can_view = True

    if not can_view:
        messages.error(request, _("Vous n'avez pas accès à ce don."))
        return redirect('/')

    context = {
        'donation': donation,
        'page_title': f'Don {donation.donation_number}',
    }

    return render(request, 'donations/donation_detail.html', context)


@login_required
def donation_history(request):
    """
    Display member's donation history.

    Template: donations/donation_history.html
    """
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Vous devez avoir un profil membre."))
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    year = request.GET.get('year')
    page = request.GET.get('page', 1)

    donations = Donation.objects.filter(member=member)

    if year:
        try:
            donations = donations.filter(date__year=int(year))
        except (ValueError, TypeError):
            pass

    donations = donations.order_by('-date')

    # Calculate totals
    total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Pagination
    paginator = Paginator(donations, 20)
    donations_page = paginator.get_page(page)

    # Get years for filter
    years = Donation.objects.filter(member=member).dates('date', 'year', order='DESC')

    context = {
        'donations': donations_page,
        'total': total,
        'selected_year': year,
        'years': years,
        'page_title': _('Historique des dons'),
    }

    return render(request, 'donations/donation_history.html', context)


# =============================================================================
# TREASURER VIEWS
# =============================================================================

@login_required
def donation_admin_list(request):
    """
    List all donations (treasurer/admin view).

    Template: donations/donation_admin_list.html
    """
    # Check permissions
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Vous n'avez pas accès à cette page."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('/')

    form = DonationFilterForm(request.GET)
    donations = Donation.objects.all().select_related('member', 'campaign')

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('date_from'):
            donations = donations.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            donations = donations.filter(date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('donation_type'):
            donations = donations.filter(donation_type=form.cleaned_data['donation_type'])
        if form.cleaned_data.get('payment_method'):
            donations = donations.filter(payment_method=form.cleaned_data['payment_method'])
        if form.cleaned_data.get('campaign'):
            donations = donations.filter(campaign=form.cleaned_data['campaign'])
        if form.cleaned_data.get('member'):
            search = form.cleaned_data['member']
            donations = donations.filter(
                Q(member__first_name__icontains=search) |
                Q(member__last_name__icontains=search) |
                Q(member__member_number__icontains=search)
            )

    donations = donations.order_by('-date', '-created_at')

    # Calculate totals
    total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Pagination
    paginator = Paginator(donations, 50)
    page = request.GET.get('page', 1)
    donations_page = paginator.get_page(page)

    context = {
        'donations': donations_page,
        'total': total,
        'total_count': paginator.count,
        'form': form,
        'page_title': _('Gestion des dons'),
    }

    return render(request, 'donations/donation_admin_list.html', context)


@login_required
def donation_record(request):
    """
    Record a physical donation (treasurer).

    Template: donations/donation_record.html
    """
    # Check permissions
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.ADMIN]:
            messages.error(request, _("Seul le trésorier peut enregistrer des dons."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Seul le trésorier peut enregistrer des dons."))
        return redirect('/')

    if request.method == 'POST':
        form = PhysicalDonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.recorded_by = request.user.member_profile
            donation.save()

            messages.success(
                request,
                _('Don enregistré: %(number)s - %(amount)s$') % {
                    'number': donation.donation_number,
                    'amount': donation.amount,
                }
            )
            return redirect('frontend:donations:donation_admin_list')
    else:
        form = PhysicalDonationForm()

    context = {
        'form': form,
        'form_title': _('Enregistrer un don'),
        'submit_text': _('Enregistrer'),
        'page_title': _('Enregistrer un don'),
    }

    return render(request, 'donations/donation_record.html', context)


# =============================================================================
# CAMPAIGN VIEWS
# =============================================================================

@login_required
def campaign_list(request):
    """
    List donation campaigns.

    Template: donations/campaign_list.html
    """
    campaigns = DonationCampaign.objects.filter(is_active=True).order_by('-start_date')

    context = {
        'campaigns': campaigns,
        'page_title': _('Campagnes de dons'),
    }

    return render(request, 'donations/campaign_list.html', context)


@login_required
def campaign_detail(request, pk):
    """
    Display campaign details.

    Template: donations/campaign_detail.html
    """
    campaign = get_object_or_404(DonationCampaign, pk=pk)

    # Get recent donations for this campaign
    recent_donations = campaign.donations.filter(is_active=True).order_by('-date')[:10]

    context = {
        'campaign': campaign,
        'recent_donations': recent_donations,
        'page_title': campaign.name,
    }

    return render(request, 'donations/campaign_detail.html', context)


# =============================================================================
# TAX RECEIPT VIEWS
# =============================================================================

@login_required
def receipt_list(request):
    """
    List member's tax receipts.

    Template: donations/receipt_list.html
    """
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Vous devez avoir un profil membre."))
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    # Check if user is finance staff
    is_finance = member.role in [Roles.TREASURER, Roles.ADMIN] or request.user.is_staff

    if is_finance:
        receipts = TaxReceipt.objects.all().select_related('member')
    else:
        receipts = TaxReceipt.objects.filter(member=member)

    receipts = receipts.order_by('-year', '-generated_at')

    # Pagination
    paginator = Paginator(receipts, 20)
    page = request.GET.get('page', 1)
    receipts_page = paginator.get_page(page)

    context = {
        'receipts': receipts_page,
        'is_finance': is_finance,
        'page_title': _('Reçus fiscaux'),
    }

    return render(request, 'donations/receipt_list.html', context)


@login_required
def receipt_detail(request, pk):
    """
    Display tax receipt details.

    Template: donations/receipt_detail.html
    """
    receipt = get_object_or_404(TaxReceipt, pk=pk)

    # Check permissions
    can_view = False

    if request.user.is_staff:
        can_view = True
    elif hasattr(request.user, 'member_profile'):
        member = request.user.member_profile

        if receipt.member == member:
            can_view = True
        elif member.role in [Roles.TREASURER, Roles.ADMIN]:
            can_view = True

    if not can_view:
        messages.error(request, _("Vous n'avez pas accès à ce reçu."))
        return redirect('/')

    context = {
        'receipt': receipt,
        'page_title': f'Reçu {receipt.receipt_number}',
    }

    return render(request, 'donations/receipt_detail.html', context)


# =============================================================================
# REPORT VIEWS
# =============================================================================

@login_required
def donation_monthly_report(request):
    """
    Display monthly donation report.

    Template: donations/monthly_report.html
    """
    # Check permissions
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Vous n'avez pas accès aux rapports."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Vous n'avez pas accès aux rapports."))
        return redirect('/')

    # Get year and month from request
    try:
        year = int(request.GET.get('year', timezone.now().year))
    except (ValueError, TypeError):
        year = timezone.now().year
    try:
        month = int(request.GET.get('month', timezone.now().month))
    except (ValueError, TypeError):
        month = timezone.now().month

    # Get donations for the period
    donations = Donation.objects.filter(
        date__year=year,
        date__month=month,
        is_active=True
    ).select_related('member')

    # Calculate stats
    total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    count = donations.count()

    # By type
    by_type = donations.values('donation_type').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # By payment method
    by_method = donations.values('payment_method').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'donations': donations,
        'total': total,
        'count': count,
        'by_type': by_type,
        'by_method': by_method,
        'year': year,
        'month': month,
        'page_title': _('Rapport mensuel'),
    }

    return render(request, 'donations/monthly_report.html', context)
