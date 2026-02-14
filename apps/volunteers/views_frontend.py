"""Volunteers frontend views."""
from django.db.models import Count, Q, Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, ScheduleStatus, BackgroundCheckStatus

from .models import (
    VolunteerPosition, VolunteerSchedule, VolunteerAvailability,
    PlannedAbsence, SwapRequest, VolunteerHours, VolunteerBackgroundCheck,
    TeamAnnouncement, PositionChecklist, ChecklistProgress,
    Skill, VolunteerSkill, Milestone, MilestoneAchievement,
    AvailabilitySlot, CrossTraining,
)
from .forms import (
    VolunteerPositionForm, VolunteerScheduleForm, SwapRequestForm,
    VolunteerHoursForm, VolunteerHoursSelfForm,
    VolunteerBackgroundCheckForm, TeamAnnouncementForm,
    PositionChecklistForm, SkillForm, VolunteerSkillSelfForm,
    AvailabilitySlotForm, CrossTrainingForm,
)
from .services_hours import summarize_by_member, get_admin_report, export_report
from .services_skills import SkillMatchingService
from .services_recognition import RecognitionService


# ──────────────────────────────────────────────────────────────────────────────
# Existing: Position CRUD
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def position_list(request):
    """Display active volunteer positions with volunteer count annotation."""
    positions = VolunteerPosition.objects.filter(is_active=True).annotate(
        num_volunteers=Count(
            'available_volunteers', filter=Q(available_volunteers__is_available=True)
        )
    )
    context = {'positions': positions, 'page_title': _('Postes de benevolat')}
    return render(request, 'volunteers/position_list.html', context)


@login_required
def position_create(request):
    """Create a new volunteer position (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = VolunteerPositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Poste cree avec succes.'))
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
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    position = get_object_or_404(VolunteerPosition, pk=pk)

    if request.method == 'POST':
        form = VolunteerPositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, _('Poste modifie avec succes.'))
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
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    position = get_object_or_404(VolunteerPosition, pk=pk)

    if request.method == 'POST':
        position.delete()
        messages.success(request, _('Poste supprime.'))
        return redirect('/volunteers/positions/')

    context = {'position': position, 'page_title': _('Supprimer le poste')}
    return render(request, 'volunteers/position_delete.html', context)


@login_required
def position_detail(request, pk):
    """Display position detail with current volunteers assigned."""
    position = get_object_or_404(VolunteerPosition, pk=pk)

    # Current volunteers (those with active availability)
    volunteers = VolunteerAvailability.objects.filter(
        position=position, is_available=True, is_active=True
    ).select_related('member')

    # Upcoming schedules
    upcoming_schedules = VolunteerSchedule.objects.filter(
        position=position, date__gte=timezone.now().date(), is_active=True
    ).select_related('member').order_by('date')[:20]

    # Checklist items
    checklist_items = PositionChecklist.objects.filter(position=position, is_active=True)

    # Background check info
    bg_checks = VolunteerBackgroundCheck.objects.filter(
        position=position, is_active=True
    ).select_related('member')

    # Skill gap analysis
    skill_gap = SkillMatchingService.skill_gap_analysis(position)

    context = {
        'position': position,
        'volunteers': volunteers,
        'upcoming_schedules': upcoming_schedules,
        'checklist_items': checklist_items,
        'bg_checks': bg_checks,
        'skill_gap': skill_gap,
        'page_title': position.name,
    }
    return render(request, 'volunteers/position_detail.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Existing: Schedule CRUD
# ──────────────────────────────────────────────────────────────────────────────

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
        'page_title': _('Horaire des benevoles'),
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'volunteers/schedule_list.html', context)


@login_required
def my_schedule(request):
    """Display current user's volunteer schedule with confirm/decline buttons."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile

    # Handle confirm/decline actions
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        action = request.POST.get('action')
        if schedule_id and action:
            try:
                schedule = VolunteerSchedule.objects.get(pk=schedule_id, member=member)
                if action == 'confirm':
                    schedule.status = ScheduleStatus.CONFIRMED
                    schedule.save()
                    messages.success(request, _('Horaire confirme.'))
                elif action == 'decline':
                    schedule.status = ScheduleStatus.DECLINED
                    schedule.save()
                    messages.success(request, _('Horaire decline.'))
            except VolunteerSchedule.DoesNotExist:
                messages.error(request, _('Horaire introuvable.'))

    schedules = VolunteerSchedule.objects.filter(member=member).order_by('date')
    context = {'schedules': schedules, 'page_title': _('Mon horaire')}
    return render(request, 'volunteers/my_schedule.html', context)


@login_required
def schedule_create(request):
    """Create a new volunteer schedule entry (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = VolunteerScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)

            # Block scheduling for expired background checks
            bg_check = VolunteerBackgroundCheck.objects.filter(
                member=schedule.member,
                is_active=True,
            ).exclude(status=BackgroundCheckStatus.NOT_REQUIRED).first()

            if bg_check and not bg_check.is_valid:
                messages.error(request, _(
                    'Ce benevole a une verification des antecedents expiree ou en attente. '
                    'Impossible de planifier.'
                ))
            else:
                # Block scheduling if onboarding checklist not complete
                required_items = PositionChecklist.objects.filter(
                    position=schedule.position, is_required=True, is_active=True
                )
                if required_items.exists():
                    completed = ChecklistProgress.objects.filter(
                        member=schedule.member,
                        checklist_item__in=required_items,
                        completed_at__isnull=False,
                    ).count()
                    if completed < required_items.count():
                        messages.error(request, _(
                            'Ce benevole n\'a pas complete la checklist d\'integration '
                            'requise pour ce poste.'
                        ))
                        context = {'form': form, 'page_title': _('Nouvel horaire')}
                        return render(request, 'volunteers/schedule_form.html', context)

                schedule.save()
                # Send notification for new schedule assignment
                _notify_schedule_assignment(schedule)
                messages.success(request, _('Horaire cree avec succes.'))
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
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    schedule = get_object_or_404(VolunteerSchedule, pk=pk)

    if request.method == 'POST':
        form = VolunteerScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, _('Horaire modifie avec succes.'))
            return redirect('/volunteers/schedule/')
    else:
        form = VolunteerScheduleForm(instance=schedule)

    context = {'form': form, 'schedule': schedule, 'page_title': _("Modifier l'horaire")}
    return render(request, 'volunteers/schedule_form.html', context)


@login_required
def schedule_delete(request, pk):
    """Delete a volunteer schedule entry (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    schedule = get_object_or_404(VolunteerSchedule, pk=pk)

    if request.method == 'POST':
        schedule.delete()
        messages.success(request, _('Horaire supprime.'))
        return redirect('/volunteers/schedule/')

    context = {'schedule': schedule, 'page_title': _("Supprimer l'horaire")}
    return render(request, 'volunteers/schedule_delete.html', context)


@login_required
def schedule_bulk_action(request):
    """Bulk actions on schedule list (assign multiple members at once)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/volunteers/schedule/')

    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        schedule_ids = request.POST.getlist('schedule_ids')

        if not schedule_ids:
            messages.error(request, _('Aucun horaire selectionne.'))
            return redirect('/volunteers/schedule/')

        schedules = VolunteerSchedule.objects.filter(pk__in=schedule_ids)

        if action == 'confirm':
            schedules.update(status=ScheduleStatus.CONFIRMED)
            messages.success(request, _('Horaires confirmes.'))
        elif action == 'delete':
            schedules.delete()
            messages.success(request, _('Horaires supprimes.'))

    return redirect('/volunteers/schedule/')


# ──────────────────────────────────────────────────────────────────────────────
# Existing: Availability
# ──────────────────────────────────────────────────────────────────────────────

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
        messages.success(request, _('Disponibilites mises a jour.'))
        return redirect('frontend:volunteers:my_schedule')

    context = {
        'availabilities': {a.position_id: a for a in availabilities},
        'positions': positions,
        'page_title': _('Mes disponibilites'),
    }
    return render(request, 'volunteers/availability_update.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Existing: Planned Absences
# ──────────────────────────────────────────────────────────────────────────────

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
        'page_title': _('Absences prevues'),
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
            messages.error(request, _('Les dates de debut et de fin sont requises.'))
        elif start_date > end_date:
            messages.error(request, _('La date de fin doit etre apres la date de debut.'))
        else:
            PlannedAbsence.objects.create(
                member=member,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            messages.success(request, _('Absence prevue enregistree.'))
            return redirect('/volunteers/planned-absences/')

    context = {'page_title': _('Declarer une absence')}
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
        messages.error(request, _('Acces refuse.'))
        return redirect('/volunteers/planned-absences/')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '')

        if not start_date or not end_date:
            messages.error(request, _('Les dates de debut et de fin sont requises.'))
        elif start_date > end_date:
            messages.error(request, _('La date de fin doit etre apres la date de debut.'))
        else:
            absence.start_date = start_date
            absence.end_date = end_date
            absence.reason = reason
            absence.save()
            messages.success(request, _('Absence modifiee avec succes.'))
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
        messages.error(request, _('Acces refuse.'))
        return redirect('/volunteers/planned-absences/')

    if request.method == 'POST':
        absence.delete()
        messages.success(request, _('Absence supprimee.'))
        return redirect('/volunteers/planned-absences/')

    context = {
        'absence': absence,
        'page_title': _("Supprimer l'absence"),
    }
    return render(request, 'volunteers/planned_absence_delete.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Existing + P1: Swap Request Frontend Views
# ──────────────────────────────────────────────────────────────────────────────

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
        'page_title': _("Demandes d'echange"),
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
            messages.success(request, _("Demande d'echange envoyee."))
            return redirect('/volunteers/swap-requests/')
    else:
        form = SwapRequestForm(member=member)

    context = {
        'form': form,
        'page_title': _("Nouvelle demande d'echange"),
    }
    return render(request, 'volunteers/swap_request_form.html', context)


@login_required
def swap_request_detail(request, pk):
    """View details of a swap request."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    swap_req = get_object_or_404(SwapRequest, pk=pk)
    member = request.user.member_profile

    # Only involved parties or staff can view
    if (swap_req.requested_by != member and swap_req.swap_with != member
            and member.role not in Roles.STAFF_ROLES):
        messages.error(request, _('Acces refuse.'))
        return redirect('/volunteers/swap-requests/')

    # Handle approve/decline by staff
    if request.method == 'POST' and member.role in Roles.STAFF_ROLES:
        action = request.POST.get('action')
        if action == 'approve':
            swap_req.status = 'approved'
            swap_req.save()
            messages.success(request, _('Demande approuvee.'))
        elif action == 'decline':
            swap_req.status = 'declined'
            swap_req.save()
            messages.success(request, _('Demande refusee.'))
        return redirect('/volunteers/swap-requests/')

    context = {
        'swap_request': swap_req,
        'page_title': _("Detail de la demande d'echange"),
    }
    return render(request, 'volunteers/swap_request_detail.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P1: Volunteer Hour Tracking
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def hours_log(request):
    """Log volunteer hours. Staff can log for anyone; volunteers for themselves."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    is_staff = member.role in Roles.STAFF_ROLES

    if request.method == 'POST':
        if is_staff:
            form = VolunteerHoursForm(request.POST)
        else:
            form = VolunteerHoursSelfForm(request.POST)

        if form.is_valid():
            entry = form.save(commit=False)
            if not is_staff:
                entry.member = member
            entry.save()
            messages.success(request, _('Heures enregistrees avec succes.'))
            return redirect('/volunteers/hours/my-summary/')
    else:
        if is_staff:
            form = VolunteerHoursForm()
        else:
            form = VolunteerHoursSelfForm()

    context = {
        'form': form,
        'page_title': _('Enregistrer des heures'),
        'is_staff': is_staff,
    }
    return render(request, 'volunteers/hours_log.html', context)


@login_required
def hours_my_summary(request):
    """Display volunteer hour summary for the current user."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    summary = summarize_by_member(member, date_from=date_from, date_to=date_to)

    # Get recent entries
    recent = VolunteerHours.objects.filter(member=member).select_related('position')[:20]

    context = {
        'summary': summary,
        'recent_hours': recent,
        'page_title': _('Mes heures de benevolat'),
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'volunteers/hours_my_summary.html', context)


@login_required
def hours_admin_report(request):
    """Admin report view for all volunteer hours."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    position_id = request.GET.get('position')

    position = None
    if position_id:
        try:
            position = VolunteerPosition.objects.get(pk=position_id)
        except VolunteerPosition.DoesNotExist:
            pass

    hours_qs = get_admin_report(date_from=date_from, date_to=date_to, position=position)

    # Handle CSV export
    if request.GET.get('export') == 'csv':
        return export_report(hours_qs)

    # Aggregate stats
    total_hours = hours_qs.aggregate(total=Sum('hours_worked'))['total'] or 0

    positions = VolunteerPosition.objects.filter(is_active=True)

    context = {
        'hours': hours_qs[:100],
        'total_hours': total_hours,
        'positions': positions,
        'page_title': _('Rapport des heures'),
        'date_from': date_from or '',
        'date_to': date_to or '',
        'selected_position': position_id or '',
    }
    return render(request, 'volunteers/hours_admin_report.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P1: Background Check Status
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def background_check_list(request):
    """List all background checks (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    checks = VolunteerBackgroundCheck.objects.filter(
        is_active=True
    ).select_related('member', 'position')

    context = {
        'checks': checks,
        'page_title': _('Verifications des antecedents'),
    }
    return render(request, 'volunteers/background_check_list.html', context)


@login_required
def background_check_create(request):
    """Create a background check record (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = VolunteerBackgroundCheckForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Verification creee avec succes.'))
            return redirect('/volunteers/background-checks/')
    else:
        form = VolunteerBackgroundCheckForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle verification'),
    }
    return render(request, 'volunteers/background_check_form.html', context)


@login_required
def background_check_update(request, pk):
    """Update a background check record (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    check = get_object_or_404(VolunteerBackgroundCheck, pk=pk)

    if request.method == 'POST':
        form = VolunteerBackgroundCheckForm(request.POST, instance=check)
        if form.is_valid():
            form.save()
            messages.success(request, _('Verification modifiee avec succes.'))
            return redirect('/volunteers/background-checks/')
    else:
        form = VolunteerBackgroundCheckForm(instance=check)

    context = {
        'form': form,
        'check': check,
        'page_title': _('Modifier la verification'),
    }
    return render(request, 'volunteers/background_check_form.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P1: Team Communication
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def announcement_list(request):
    """List team announcements. Filter by position if provided."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    position_id = request.GET.get('position')
    announcements = TeamAnnouncement.objects.filter(
        is_active=True
    ).select_related('position', 'author')

    if position_id:
        announcements = announcements.filter(position_id=position_id)

    positions = VolunteerPosition.objects.filter(is_active=True)

    context = {
        'announcements': announcements,
        'positions': positions,
        'page_title': _("Annonces d'equipe"),
        'selected_position': position_id or '',
    }
    return render(request, 'volunteers/announcement_list.html', context)


@login_required
def announcement_create(request):
    """Create a team announcement (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    member = request.user.member_profile

    if request.method == 'POST':
        form = TeamAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = member
            announcement.sent_at = timezone.now()
            announcement.save()

            # Notify all volunteers in the position
            _notify_team_announcement(announcement)

            messages.success(request, _('Annonce envoyee avec succes.'))
            return redirect('/volunteers/announcements/')
    else:
        form = TeamAnnouncementForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle annonce'),
    }
    return render(request, 'volunteers/announcement_form.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P2: Onboarding Checklist
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def checklist_manage(request, position_pk):
    """Manage checklist items for a position (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    position = get_object_or_404(VolunteerPosition, pk=position_pk)
    items = PositionChecklist.objects.filter(position=position, is_active=True)

    if request.method == 'POST':
        form = PositionChecklistForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.position = position
            item.save()
            messages.success(request, _('Element ajoute a la checklist.'))
            return redirect(f'/volunteers/positions/{position_pk}/checklist/')
    else:
        form = PositionChecklistForm(initial={'position': position})

    context = {
        'position': position,
        'items': items,
        'form': form,
        'page_title': _('Checklist - ') + position.name,
    }
    return render(request, 'volunteers/checklist_manage.html', context)


@login_required
def onboarding_checklist(request, position_pk):
    """View and complete onboarding checklist for a position (for volunteers)."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    position = get_object_or_404(VolunteerPosition, pk=position_pk)
    items = PositionChecklist.objects.filter(position=position, is_active=True)

    # Get completion status for each item
    progress_map = {}
    progress_records = ChecklistProgress.objects.filter(
        member=member, checklist_item__in=items
    )
    for p in progress_records:
        progress_map[p.checklist_item_id] = p

    # Handle marking items complete
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        if item_id:
            try:
                item = PositionChecklist.objects.get(pk=item_id, position=position)
                ChecklistProgress.objects.update_or_create(
                    member=member,
                    checklist_item=item,
                    defaults={'completed_at': timezone.now()},
                )
                messages.success(request, _('Element complete.'))
            except PositionChecklist.DoesNotExist:
                messages.error(request, _('Element introuvable.'))
        return redirect(f'/volunteers/onboarding/{position_pk}/')

    checklist_data = []
    for item in items:
        progress = progress_map.get(item.id)
        checklist_data.append({
            'item': item,
            'completed': progress.is_completed if progress else False,
            'completed_at': progress.completed_at if progress else None,
        })

    total = items.count()
    completed_count = sum(1 for d in checklist_data if d['completed'])

    context = {
        'position': position,
        'checklist_data': checklist_data,
        'total': total,
        'completed_count': completed_count,
        'page_title': _('Integration - ') + position.name,
    }
    return render(request, 'volunteers/onboarding_checklist.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P2: Skills Profile
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def skills_profile(request):
    """View and manage the current user's skills profile."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    skills = VolunteerSkill.objects.filter(
        member=member, is_active=True
    ).select_related('skill')

    if request.method == 'POST':
        form = VolunteerSkillSelfForm(request.POST)
        if form.is_valid():
            vs = form.save(commit=False)
            vs.member = member
            vs.save()
            messages.success(request, _('Competence ajoutee.'))
            return redirect('/volunteers/skills/profile/')
    else:
        form = VolunteerSkillSelfForm()

    context = {
        'skills': skills,
        'form': form,
        'page_title': _('Mon profil de competences'),
    }
    return render(request, 'volunteers/skills_profile.html', context)


@login_required
def skills_list(request):
    """List all available skills (admin view)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    skills = Skill.objects.filter(is_active=True)

    if request.method == 'POST' and request.user.member_profile.role in Roles.STAFF_ROLES:
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Competence creee.'))
            return redirect('/volunteers/skills/')
    else:
        form = SkillForm()

    context = {
        'skills': skills,
        'form': form,
        'page_title': _('Competences'),
        'is_staff': request.user.member_profile.role in Roles.STAFF_ROLES,
    }
    return render(request, 'volunteers/skills_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P2: Volunteer Recognition
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def milestones_page(request):
    """Appreciation page showing leaderboard and milestones achieved."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    leaderboard = RecognitionService.get_leaderboard(limit=10)
    milestones = Milestone.objects.filter(is_active=True)

    # Recent achievements
    recent_achievements = MilestoneAchievement.objects.filter(
        is_active=True
    ).select_related('member', 'milestone').order_by('-achieved_at')[:20]

    # Current user's achievements
    member = request.user.member_profile
    my_achievements = MilestoneAchievement.objects.filter(
        member=member, is_active=True
    ).select_related('milestone')

    context = {
        'leaderboard': leaderboard,
        'milestones': milestones,
        'recent_achievements': recent_achievements,
        'my_achievements': my_achievements,
        'page_title': _('Reconnaissance des benevoles'),
    }
    return render(request, 'volunteers/milestones_page.html', context)


@login_required
def volunteer_of_month(request):
    """Volunteer of the month/quarter view. Staff can nominate."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    # Top volunteer by hours this month
    now = timezone.now()
    first_of_month = now.replace(day=1).date()

    top_this_month = (
        VolunteerHours.objects.filter(
            date__gte=first_of_month
        ).values(
            'member__id', 'member__first_name', 'member__last_name'
        ).annotate(
            total_hours=Sum('hours_worked')
        ).order_by('-total_hours').first()
    )

    context = {
        'top_volunteer': top_this_month,
        'page_title': _('Benevole du mois'),
    }
    return render(request, 'volunteers/volunteer_of_month.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P3: Availability Heatmap
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def availability_slots(request):
    """Submit availability time slots for the current user."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    slots = AvailabilitySlot.objects.filter(member=member, is_active=True)

    if request.method == 'POST':
        form = AvailabilitySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.member = member
            slot.save()
            messages.success(request, _('Plage de disponibilite ajoutee.'))
            return redirect('/volunteers/availability-slots/')
    else:
        form = AvailabilitySlotForm()

    context = {
        'slots': slots,
        'form': form,
        'page_title': _('Mes plages de disponibilite'),
    }
    return render(request, 'volunteers/availability_slots.html', context)


@login_required
def availability_heatmap(request):
    """Visual heatmap calendar showing team availability (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    from apps.core.constants import DayOfWeek

    # Build heatmap data: count of available volunteers per day/time
    slots = AvailabilitySlot.objects.filter(is_available=True, is_active=True)

    heatmap = {}
    for day_val, day_label in DayOfWeek.CHOICES:
        day_slots = slots.filter(day_of_week=day_val)
        heatmap[day_label] = day_slots.count()

    context = {
        'heatmap': heatmap,
        'page_title': _('Heatmap de disponibilite'),
    }
    return render(request, 'volunteers/availability_heatmap.html', context)


@login_required
def availability_calendar(request):
    """Volunteer availability calendar view."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    slots = AvailabilitySlot.objects.filter(member=member, is_active=True).order_by('day_of_week', 'time_start')

    context = {
        'slots': slots,
        'page_title': _('Calendrier de disponibilite'),
    }
    return render(request, 'volunteers/availability_calendar.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P3: Cross-Training
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def cross_training_list(request):
    """List cross-training records."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile

    if member.role in Roles.STAFF_ROLES:
        trainings = CrossTraining.objects.filter(is_active=True).select_related(
            'member', 'original_position', 'trained_position'
        )
    else:
        trainings = CrossTraining.objects.filter(
            member=member, is_active=True
        ).select_related('original_position', 'trained_position')

    context = {
        'trainings': trainings,
        'page_title': _('Formations croisees'),
    }
    return render(request, 'volunteers/cross_training_list.html', context)


@login_required
def cross_training_create(request):
    """Record a cross-training entry (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = CrossTrainingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Formation croisee enregistree.'))
            return redirect('/volunteers/cross-training/')
    else:
        form = CrossTrainingForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle formation croisee'),
    }
    return render(request, 'volunteers/cross_training_form.html', context)


@login_required
def cross_training_suggestions(request):
    """Suggest cross-trained volunteers for unfilled shifts (staff only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in Roles.STAFF_ROLES:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    # Find positions with scheduled gaps (upcoming dates with no confirmed volunteer)
    today = timezone.now().date()
    positions = VolunteerPosition.objects.filter(is_active=True)

    suggestions = []
    for position in positions:
        # Get cross-trained volunteers for this position
        cross_trained = CrossTraining.objects.filter(
            trained_position=position,
            certified_at__isnull=False,
            is_active=True,
        ).select_related('member')

        if cross_trained.exists():
            suggestions.append({
                'position': position,
                'cross_trained_volunteers': cross_trained,
            })

    context = {
        'suggestions': suggestions,
        'page_title': _('Suggestions de benevoles formes'),
    }
    return render(request, 'volunteers/cross_training_suggestions.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# P3: Mobile-Optimized Schedule View
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def mobile_schedule(request):
    """Mobile-optimized schedule view with day-by-day navigation."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('/')

    member = request.user.member_profile
    from datetime import timedelta

    selected_date = request.GET.get('date')
    if selected_date:
        try:
            from datetime import datetime
            current_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    schedules = VolunteerSchedule.objects.filter(
        member=member,
        date=current_date,
    ).select_related('position')

    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)

    context = {
        'schedules': schedules,
        'current_date': current_date,
        'prev_date': prev_date.isoformat(),
        'next_date': next_date.isoformat(),
        'page_title': _('Mon planning mobile'),
    }
    return render(request, 'volunteers/mobile_schedule.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────

def _notify_schedule_assignment(schedule):
    """Send notification when a new schedule is assigned."""
    from apps.communication.models import Notification
    Notification.objects.create(
        member=schedule.member,
        title=_('Nouvel horaire assigne'),
        message=_(
            f'Vous avez ete assigne au poste "{schedule.position.name}" '
            f'le {schedule.date:%d/%m/%Y}.'
        ),
        notification_type='volunteer',
        link='/volunteers/my-schedule/',
    )


def _notify_team_announcement(announcement):
    """Send notification to all volunteers in a position about a team announcement."""
    from apps.communication.models import Notification

    volunteers = VolunteerAvailability.objects.filter(
        position=announcement.position,
        is_available=True,
        is_active=True,
    ).select_related('member')

    for avail in volunteers:
        Notification.objects.create(
            member=avail.member,
            title=f'Annonce: {announcement.title}',
            message=announcement.body[:200],
            notification_type='volunteer',
            link='/volunteers/announcements/',
        )
