"""Template-based views for donation management."""
import csv
import io
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, PaymentMethod

from .models import Donation, DonationCampaign, TaxReceipt, FinanceDelegation
from .forms import (
    DonationForm,
    DonationEditForm,
    PhysicalDonationForm,
    DonationCampaignForm,
    DonationFilterForm,
)


def _is_finance_staff(user):
    """Check if user has finance access (treasurer, pastor, admin, or staff)."""
    if user.is_staff:
        return True
    if hasattr(user, 'member_profile'):
        return user.member_profile.role in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]
    return False


def _is_admin_user(user):
    """Check if user has admin-level access."""
    if user.is_staff:
        return True
    if hasattr(user, 'member_profile'):
        return user.member_profile.role == Roles.ADMIN
    return False


@login_required
def donation_create(request):
    """Create an online donation."""
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

            # Send donation confirmation notification
            try:
                from apps.communication.models import Notification
                Notification.objects.create(
                    member=member,
                    title='Confirmation de don',
                    message=(
                        f'Votre don de {donation.amount}$ a été enregistré avec succès. '
                        f'Numéro: {donation.donation_number}'
                    ),
                    notification_type='donation',
                    link=f'/donations/{donation.pk}/',
                )
            except Exception:
                pass

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
    """Display donation details."""
    donation = get_object_or_404(Donation, pk=pk)

    can_view = False
    is_finance = False

    if request.user.is_staff:
        can_view = True
        is_finance = True
    elif hasattr(request.user, 'member_profile'):
        member = request.user.member_profile

        if donation.member == member:
            can_view = True
        if member.role in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            can_view = True
            is_finance = True

    if not can_view:
        messages.error(request, _("Vous n'avez pas accès à ce don."))
        return redirect('/')

    context = {
        'donation': donation,
        'is_finance': is_finance,
        'page_title': f'Don {donation.donation_number}',
    }

    return render(request, 'donations/donation_detail.html', context)


@login_required
def donation_edit(request, pk):
    """Edit a donation - finance staff only."""
    if not _is_finance_staff(request.user):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('/')

    donation = get_object_or_404(Donation, pk=pk)

    if request.method == 'POST':
        form = DonationEditForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, _('Don mis à jour avec succès.'))
            return redirect('/donations/%s/' % donation.pk)
    else:
        form = DonationEditForm(instance=donation)

    context = {
        'form': form,
        'donation': donation,
        'form_title': _('Modifier le don'),
        'submit_text': _('Enregistrer'),
        'page_title': _('Modifier le don'),
    }

    return render(request, 'donations/donation_edit.html', context)


@login_required
def donation_delete(request, pk):
    """Delete a donation - admin only."""
    if not _is_admin_user(request.user):
        messages.error(request, _("Seul un administrateur peut supprimer un don."))
        return redirect('/')

    donation = get_object_or_404(Donation, pk=pk)

    if request.method == 'POST':
        donation_number = donation.donation_number
        donation.delete()
        messages.success(
            request,
            _('Don %(number)s supprimé.') % {'number': donation_number}
        )
        return redirect('/donations/admin/')

    context = {
        'donation': donation,
        'page_title': _('Supprimer le don'),
    }

    return render(request, 'donations/donation_delete.html', context)


@login_required
def donation_history(request):
    """Display member's donation history."""
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

    total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    paginator = Paginator(donations, 20)
    donations_page = paginator.get_page(page)

    years = Donation.objects.filter(member=member).dates('date', 'year', order='DESC')

    context = {
        'donations': donations_page,
        'total': total,
        'selected_year': year,
        'years': years,
        'page_title': _('Historique des dons'),
    }

    return render(request, 'donations/donation_history.html', context)


@login_required
def donation_admin_list(request):
    """List all donations - treasurer/admin view."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Vous n'avez pas accès à cette page."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('/')

    form = DonationFilterForm(request.GET)
    donations = Donation.objects.all().select_related('member', 'campaign')

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

    total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

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
def donation_export_csv(request):
    """Export donations to CSV - finance staff only."""
    if not _is_finance_staff(request.user):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('/')

    form = DonationFilterForm(request.GET)
    donations = Donation.objects.all().select_related('member', 'campaign')

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

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dons_export.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow([
        'Numéro', 'Membre', 'Date', 'Montant', 'Type', 'Mode de paiement',
        'Campagne', 'Notes', 'Reçu envoyé',
    ])

    for donation in donations:
        writer.writerow([
            donation.donation_number,
            donation.member.full_name,
            donation.date.isoformat(),
            str(donation.amount),
            donation.get_donation_type_display(),
            donation.get_payment_method_display(),
            donation.campaign.name if donation.campaign else '',
            donation.notes,
            'Oui' if donation.receipt_sent else 'Non',
        ])

    return response


@login_required
def donation_record(request):
    """Record a physical donation - treasurer only."""
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

            # Send donation confirmation notification
            try:
                from apps.communication.models import Notification
                Notification.objects.create(
                    member=donation.member,
                    title='Don enregistré',
                    message=(
                        f'Un don de {donation.amount}$ a été enregistré à votre nom. '
                        f'Numéro: {donation.donation_number}'
                    ),
                    notification_type='donation',
                    link=f'/donations/{donation.pk}/',
                )
            except Exception:
                pass

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


@login_required
def campaign_list(request):
    """List donation campaigns."""
    campaigns = DonationCampaign.objects.filter(is_active=True).order_by('-start_date')

    context = {
        'campaigns': campaigns,
        'page_title': _('Campagnes de dons'),
    }

    return render(request, 'donations/campaign_list.html', context)


@login_required
def campaign_detail(request, pk):
    """Display campaign details."""
    campaign = get_object_or_404(DonationCampaign, pk=pk)

    recent_donations = campaign.donations.filter(is_active=True).order_by('-date')[:10]

    context = {
        'campaign': campaign,
        'recent_donations': recent_donations,
        'page_title': campaign.name,
    }

    return render(request, 'donations/campaign_detail.html', context)


@login_required
def campaign_create(request):
    """Create a new donation campaign -- treasurer/admin/pastor only."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Accès refusé."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Accès refusé."))
        return redirect('/')

    if request.method == 'POST':
        form = DonationCampaignForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _('Campagne créée avec succès.'))
            return redirect('/donations/campaigns/')
    else:
        form = DonationCampaignForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle campagne'),
    }
    return render(request, 'donations/campaign_form.html', context)


@login_required
def campaign_update(request, pk):
    """Edit a donation campaign -- treasurer/admin/pastor only."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Accès refusé."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Accès refusé."))
        return redirect('/')

    campaign = get_object_or_404(DonationCampaign, pk=pk)

    if request.method == 'POST':
        form = DonationCampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, _('Campagne mise à jour.'))
            return redirect('/donations/campaigns/%s/' % campaign.pk)
    else:
        form = DonationCampaignForm(instance=campaign)

    context = {
        'form': form,
        'campaign': campaign,
        'page_title': _('Modifier la campagne'),
    }
    return render(request, 'donations/campaign_form.html', context)


@login_required
def campaign_delete(request, pk):
    """Delete a donation campaign -- treasurer/admin/pastor only."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Accès refusé."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Accès refusé."))
        return redirect('/')

    campaign = get_object_or_404(DonationCampaign, pk=pk)

    if request.method == 'POST':
        campaign.delete()
        messages.success(request, _('Campagne supprimée.'))
        return redirect('/donations/campaigns/')

    context = {
        'campaign': campaign,
        'page_title': _('Supprimer la campagne'),
    }
    return render(request, 'donations/campaign_delete.html', context)


@login_required
def receipt_list(request):
    """List tax receipts."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Vous devez avoir un profil membre."))
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    is_finance = member.role in [Roles.TREASURER, Roles.ADMIN] or request.user.is_staff

    if is_finance:
        receipts = TaxReceipt.objects.all().select_related('member')
    else:
        receipts = TaxReceipt.objects.filter(member=member)

    receipts = receipts.order_by('-year', '-generated_at')

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
    """Display tax receipt details."""
    receipt = get_object_or_404(TaxReceipt, pk=pk)

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


@login_required
def receipt_download_pdf(request, pk):
    """Download a tax receipt as PDF using xhtml2pdf."""
    receipt = get_object_or_404(TaxReceipt, pk=pk)

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

    # Get donations for this receipt's year
    donations = Donation.objects.filter(
        member=receipt.member,
        date__year=receipt.year,
        is_active=True,
    ).order_by('date')

    html_string = render_to_string('donations/receipt_pdf.html', {
        'receipt': receipt,
        'donations': donations,
        'church_name': getattr(settings, 'CHURCH_NAME', 'EgliseConnect'),
        'church_address': getattr(settings, 'CHURCH_ADDRESS', ''),
        'church_registration': getattr(settings, 'CHURCH_REGISTRATION', ''),
    })

    try:
        from xhtml2pdf import pisa
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="recu_{receipt.receipt_number}.pdf"'
        )
        pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=response)
        if pisa_status.err:
            return HttpResponse('Erreur de génération PDF', status=500)
        return response
    except ImportError:
        messages.error(request, _("Le module de génération PDF n'est pas installé."))
        return redirect(f'/donations/receipts/{pk}/')


@login_required
def receipt_batch_email(request):
    """Batch send tax receipts by email - finance staff only."""
    if not _is_finance_staff(request.user):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('/')

    if request.method == 'POST':
        receipt_ids = request.POST.getlist('receipt_ids')
        if not receipt_ids:
            messages.warning(request, _('Aucun reçu sélectionné.'))
            return redirect('/donations/receipts/')

        receipts = TaxReceipt.objects.filter(pk__in=receipt_ids, email_sent=False)
        count = 0
        for receipt in receipts:
            receipt.email_sent = True
            receipt.email_sent_date = timezone.now()
            receipt.save(update_fields=['email_sent', 'email_sent_date', 'updated_at'])
            count += 1

        messages.success(
            request,
            _('%(count)d reçu(s) marqué(s) comme envoyé(s).') % {'count': count}
        )

    return redirect('/donations/receipts/')


@login_required
def donation_monthly_report(request):
    """Display monthly donation report - finance staff only."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Vous n'avez pas accès aux rapports."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Vous n'avez pas accès aux rapports."))
        return redirect('/')

    # Support date range picker
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from and date_to:
        # Date range mode
        try:
            from datetime import date as dt_date
            parts_from = date_from.split('-')
            parts_to = date_to.split('-')
            date_from_obj = dt_date(int(parts_from[0]), int(parts_from[1]), int(parts_from[2]))
            date_to_obj = dt_date(int(parts_to[0]), int(parts_to[1]), int(parts_to[2]))
        except (ValueError, IndexError):
            date_from_obj = None
            date_to_obj = None

        if date_from_obj and date_to_obj:
            donations = Donation.objects.filter(
                date__gte=date_from_obj,
                date__lte=date_to_obj,
                is_active=True
            ).select_related('member')

            year = date_from_obj.year
            month = date_from_obj.month
        else:
            year = timezone.now().year
            month = timezone.now().month
            donations = Donation.objects.filter(
                date__year=year,
                date__month=month,
                is_active=True
            ).select_related('member')
    else:
        try:
            year = int(request.GET.get('year', timezone.now().year))
        except (ValueError, TypeError):
            year = timezone.now().year
        try:
            month = int(request.GET.get('month', timezone.now().month))
        except (ValueError, TypeError):
            month = timezone.now().month

        donations = Donation.objects.filter(
            date__year=year,
            date__month=month,
            is_active=True
        ).select_related('member')

    total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    count = donations.count()

    by_type = donations.values('donation_type').annotate(
        total=Sum('amount')
    ).order_by('-total')

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
        'date_from': date_from or '',
        'date_to': date_to or '',
        'page_title': _('Rapport mensuel'),
    }

    return render(request, 'donations/monthly_report.html', context)


# ==============================================================================
# Finance delegation views
# ==============================================================================


@login_required
def finance_delegations(request):
    """List all finance delegations (pastor/admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès réservé aux pasteurs et administrateurs.'))
        return redirect('/donations/history/')

    delegations = FinanceDelegation.objects.select_related(
        'delegated_to', 'delegated_by'
    ).order_by('-granted_at')

    active_delegations = delegations.filter(revoked_at__isnull=True)
    revoked_delegations = delegations.filter(revoked_at__isnull=False)

    from apps.members.models import Member
    eligible_members = Member.objects.filter(
        is_active=True,
    ).exclude(
        role__in=[Roles.TREASURER, Roles.ADMIN],
    ).exclude(
        pk__in=active_delegations.values_list('delegated_to_id', flat=True),
    )

    context = {
        'active_delegations': active_delegations,
        'revoked_delegations': revoked_delegations,
        'eligible_members': eligible_members,
        'page_title': _('Délégations financières'),
    }
    return render(request, 'donations/finance_delegations.html', context)


@login_required
def delegate_finance_access(request):
    """Grant finance access to a member (pastor/admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès réservé aux pasteurs et administrateurs.'))
        return redirect('/donations/history/')

    if request.method == 'POST':
        from apps.members.models import Member
        target_pk = request.POST.get('member')
        reason = request.POST.get('reason', '')

        try:
            target = Member.objects.get(pk=target_pk, is_active=True)
        except (Member.DoesNotExist, ValueError, TypeError, Exception):
            messages.error(request, _('Membre invalide.'))
            return redirect('/donations/delegations/')

        # Check no active delegation exists
        if FinanceDelegation.objects.filter(
            delegated_to=target, revoked_at__isnull=True
        ).exists():
            messages.warning(request, _('Ce membre a déjà un accès financier délégué.'))
            return redirect('/donations/delegations/')

        FinanceDelegation.objects.create(
            delegated_to=target,
            delegated_by=member,
            reason=reason,
        )

        from apps.communication.models import Notification
        Notification.objects.create(
            member=target,
            title='Accès financier accordé',
            message=(
                f'{member.full_name} vous a accordé un accès aux données financières.'
            ),
            notification_type='general',
            link='/donations/admin/',
        )

        messages.success(
            request,
            _('Accès financier accordé à %(name)s.') % {'name': target.full_name}
        )

    return redirect('/donations/delegations/')


@login_required
def revoke_finance_access(request, pk):
    """Revoke a finance delegation (pastor/admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès réservé aux pasteurs et administrateurs.'))
        return redirect('/donations/history/')

    delegation = get_object_or_404(FinanceDelegation, pk=pk, revoked_at__isnull=True)

    if request.method == 'POST':
        delegation.revoked_at = timezone.now()
        delegation.save(update_fields=['revoked_at', 'updated_at'])

        from apps.communication.models import Notification
        Notification.objects.create(
            member=delegation.delegated_to,
            title='Accès financier révoqué',
            message=(
                f'Votre accès aux données financières a été révoqué par '
                f'{member.full_name}.'
            ),
            notification_type='general',
        )

        messages.success(
            request,
            _('Accès financier révoqué pour %(name)s.') % {
                'name': delegation.delegated_to.full_name
            }
        )

    return redirect('/donations/delegations/')
