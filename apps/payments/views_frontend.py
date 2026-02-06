"""Frontend views for payments."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, DonationType
from .models import OnlinePayment, RecurringDonation


@login_required
def donate(request):
    """Donation page with Stripe Elements."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    from apps.donations.models import DonationCampaign
    campaigns = DonationCampaign.objects.filter(is_active=True)

    context = {
        'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'campaigns': campaigns,
        'donation_types': DonationType.CHOICES,
        'page_title': _('Faire un don'),
    }
    return render(request, 'payments/donate.html', context)


@login_required
def donation_success(request):
    """Payment confirmation page."""
    context = {
        'page_title': _('Don reçu - Merci!'),
    }
    return render(request, 'payments/donation_success.html', context)


@login_required
def payment_history(request):
    """View payment history."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    # Admin sees all, regular member sees own
    if member.role in [Roles.ADMIN, Roles.PASTOR, Roles.TREASURER]:
        payments = OnlinePayment.objects.all().order_by('-created_at')[:100]
    else:
        payments = OnlinePayment.objects.filter(
            member=member
        ).order_by('-created_at')

    context = {
        'payments': payments,
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
