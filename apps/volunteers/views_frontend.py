"""Volunteers frontend views."""
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles

from .models import VolunteerPosition, VolunteerSchedule, VolunteerAvailability, PlannedAbsence, SwapRequest
from .forms import VolunteerPositionForm, VolunteerScheduleForm, SwapRequestForm


@login_required
def position_list(request):
    """Display active volunteer positions with volunteer count annotation."""
    positions = VolunteerPosition.objects.filter(is_active=True).annotate(
        num_volunteers=Count(
            'available_volunteers', filter=Q(available_volunteers__is_available=True)
        )
    )
    context = {'positions': positions, 'page_title': _('Postes de bénévolat')}
    return render(request, 'volunteers/position_list.html', context)


@login_required
def schedule_list(request):
    """Display all volunteer schedules with optional date range filter."""
    schedules = VolunteerSchedule.objects.filter(
        is_active=True
    ).select_related('member', 'position').order_by('date')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        schedules = schedules.filter(date__gte=date_from)
    if date_to:
        schedules = schedules.filter(date__lte=date_to)

    context = {
        'schedules': schedules,
        'page_title': _('Horaire des bénévoles'),
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'volunteers/schedule_list.html', context)


@login_required
def my_schedule(request):
    """Display current user's volunteer schedule."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')
    schedules = VolunteerSchedule.objects.filter(member=request.user.member_profile).order_by('date')
    context = {'schedules': schedules, 'page_title': _('Mon horaire')}
    return render(request, 'volunteers/my_schedule.html', context)


@login_required
def availability_update(request):
    """Allow users to update their availability for each position."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    availabilities = VolunteerAvailability.objects.filter(member=member)
    positions = VolunteerPosition.objects.filter(is_active=True)

    if request.method == 'POST':
        for position in positions:
            is_available = request.POST.get(f'position_{position.id}') == 'on'
            frequency = request.POST.get(f'frequency_{position.id}', 'monthly')

            VolunteerAvailability.objects.update_or_create(
                member=member,
                position=position,
                defaults={'is_available': is_available, 'frequency': frequency}
            )
        messages.success(request, _('Disponibilités mises à jour.'))
        return redirect('frontend:volunteers:my_schedule')

    context = {
        'availabilities': {a.position_id: a for a in availabilities},
        'positions': positions,
        'page_title': _('Mes disponibilités'),
    }
    return render(request, 'volunteers/availability_update.html', context)


@login_required
def planned_absence_list(request):
    """Display planned absences for the current member (or all for leaders)."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    if member.role in ('admin', 'pastor', 'deacon', 'group_leader'):
        absences = PlannedAbsence.objects.filter(is_active=True).select_related('member', 'approved_by')
    else:
        absences = PlannedAbsence.objects.filter(member=member, is_active=True)

    context = {
        'absences': absences,
        'page_title': _('Absences prévues'),
    }
    return render(request, 'volunteers/planned_absence_list.html', context)


@login_required
def planned_absence_create(request):
    """Create a planned absence for a member."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '')

        if not start_date or not end_date:
            messages.error(request, _('Les dates de début et de fin sont requises.'))
        elif start_date > end_date:
            messages.error(request, _('La date de fin doit être après la date de début.'))
        else:
            PlannedAbsence.objects.create(
                member=member,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            messages.success(request, _('Absence prévue enregistrée.'))
            return redirect('/volunteers/planned-absences/')

    context = {'page_title': _('Déclarer une absence')}
    return render(request, 'volunteers/planned_absence_form.html', context)




@login_required
def planned_absence_edit(request, pk):
    """Edit a planned absence (owner or staff)."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    absence = get_object_or_404(PlannedAbsence, pk=pk)
    member = request.user.member_profile

    # Only the owner or staff can edit
    if absence.member != member and member.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Accès refusé.'))
        return redirect('/volunteers/planned-absences/')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '')

        if not start_date or not end_date:
            messages.error(request, _('Les dates de début et de fin sont requises.'))
        elif start_date > end_date:
            messages.error(request, _('La date de fin doit être après la date de début.'))
        else:
            absence.start_date = start_date
            absence.end_date = end_date
            absence.reason = reason
            absence.save()
            messages.success(request, _('Absence modifiée avec succès.'))
            return redirect('/volunteers/planned-absences/')

    context = {
        'page_title': _("Modifier l'absence"),
        'absence': absence,
        'editing': True,
    }
    return render(request, 'volunteers/planned_absence_form.html', context)


@login_required
def planned_absence_delete(request, pk):
    """Delete a planned absence (owner or staff)."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    absence = get_object_or_404(PlannedAbsence, pk=pk)
    member = request.user.member_profile

    # Only the owner or staff can delete
    if absence.member != member and member.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Accès refusé.'))
        return redirect('/volunteers/planned-absences/')

    if request.method == 'POST':
        absence.delete()
        messages.success(request, _('Absence supprimée.'))
        return redirect('/volunteers/planned-absences/')

    context = {
        'absence': absence,
        'page_title': _("Supprimer l'absence"),
    }
    return render(request, 'volunteers/planned_absence_delete.html', context)


@login_required
def swap_request_list(request):
    """List swap requests for the current member. Staff sees all."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile

    if member.role in Roles.STAFF_ROLES:
        swap_requests = SwapRequest.objects.filter(
            is_active=True
        ).select_related(
            'original_schedule__position', 'original_schedule__member',
            'requested_by', 'swap_with',
        ).order_by('-created_at')
    else:
        swap_requests = SwapRequest.objects.filter(
            Q(requested_by=member) | Q(swap_with=member),
            is_active=True,
        ).select_related(
            'original_schedule__position', 'original_schedule__member',
            'requested_by', 'swap_with',
        ).order_by('-created_at')

    context = {
        'swap_requests': swap_requests,
        'page_title': _("Demandes d'échange"),
    }
    return render(request, 'volunteers/swap_request_list.html', context)


@login_required
def swap_request_create(request):
    """Create a swap request."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile

    if request.method == 'POST':
        form = SwapRequestForm(request.POST, member=member)
        if form.is_valid():
            form.save()
            messages.success(request, _("Demande d'échange envoyée."))
            return redirect('/volunteers/swap-requests/')
    else:
        form = SwapRequestForm(member=member)

    context = {
        'form': form,
        'page_title': _("Nouvelle demande d'échange"),
    }
    return render(request, 'volunteers/swap_request_form.html', context)

@login_required
def position_create(request):
    """Create a new volunteer position (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        form = VolunteerPositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Poste créé avec succès.'))
            return redirect('/volunteers/positions/')
    else:
        form = VolunteerPositionForm()

    context = {'form': form, 'page_title': _('Nouveau poste')}
    return render(request, 'volunteers/position_form.html', context)


@login_required
def position_update(request, pk):
    """Update a volunteer position (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    position = get_object_or_404(VolunteerPosition, pk=pk)

    if request.method == 'POST':
        form = VolunteerPositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, _('Poste modifié avec succès.'))
            return redirect('/volunteers/positions/')
    else:
        form = VolunteerPositionForm(instance=position)

    context = {'form': form, 'position': position, 'page_title': _('Modifier le poste')}
    return render(request, 'volunteers/position_form.html', context)


@login_required
def position_delete(request, pk):
    """Delete a volunteer position (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    position = get_object_or_404(VolunteerPosition, pk=pk)

    if request.method == 'POST':
        position.delete()
        messages.success(request, _('Poste supprimé.'))
        return redirect('/volunteers/positions/')

    context = {'position': position, 'page_title': _('Supprimer le poste')}
    return render(request, 'volunteers/position_delete.html', context)


@login_required
def schedule_create(request):
    """Create a new volunteer schedule entry (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        form = VolunteerScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Horaire créé avec succès.'))
            return redirect('/volunteers/schedule/')
    else:
        form = VolunteerScheduleForm()

    context = {'form': form, 'page_title': _('Nouvel horaire')}
    return render(request, 'volunteers/schedule_form.html', context)


@login_required
def schedule_update(request, pk):
    """Update a volunteer schedule entry (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    schedule = get_object_or_404(VolunteerSchedule, pk=pk)

    if request.method == 'POST':
        form = VolunteerScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, _('Horaire modifié avec succès.'))
            return redirect('/volunteers/schedule/')
    else:
        form = VolunteerScheduleForm(instance=schedule)

    context = {'form': form, 'schedule': schedule, 'page_title': _('Modifier l\'horaire')}
    return render(request, 'volunteers/schedule_form.html', context)


@login_required
def schedule_delete(request, pk):
    """Delete a volunteer schedule entry (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    schedule = get_object_or_404(VolunteerSchedule, pk=pk)

    if request.method == 'POST':
        schedule.delete()
        messages.success(request, _('Horaire supprimé.'))
        return redirect('/volunteers/schedule/')

    context = {'schedule': schedule, 'page_title': _('Supprimer l\'horaire')}
    return render(request, 'volunteers/schedule_delete.html', context)
