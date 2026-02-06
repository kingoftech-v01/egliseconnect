"""Volunteers frontend views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from .models import VolunteerPosition, VolunteerSchedule, VolunteerAvailability


@login_required
def position_list(request):
    """Display active volunteer positions."""
    positions = VolunteerPosition.objects.filter(is_active=True)
    context = {'positions': positions, 'page_title': _('Postes de bénévolat')}
    return render(request, 'volunteers/position_list.html', context)


@login_required
def schedule_list(request):
    """Display all volunteer schedules."""
    schedules = VolunteerSchedule.objects.filter(is_active=True).select_related('member', 'position').order_by('date')
    context = {'schedules': schedules, 'page_title': _('Horaire des bénévoles')}
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
