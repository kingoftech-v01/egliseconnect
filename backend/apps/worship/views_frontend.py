"""Worship service planning frontend views."""
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.decorators.http import require_POST

from apps.core.constants import (
    Roles, WorshipServiceStatus, AssignmentStatus, ServiceSectionType,
    SermonStatus, SongRequestStatus, RehearsalAttendeeStatus,
)

from .models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
    Sermon, SermonSeries, Song, Setlist, SetlistSong,
    VolunteerPreference, LiveStream, Rehearsal, RehearsalAttendee,
    SongRequest, SongRequestVote,
)
from .forms import (
    WorshipServiceForm, ServiceSectionForm, ServiceAssignmentForm,
    EligibleMemberListForm, ServiceDateRangeFilterForm,
    SermonForm, SermonSeriesForm, SermonFilterForm,
    SongForm, SetlistForm, SetlistSongForm, SongSearchForm,
    VolunteerPreferenceForm, LiveStreamForm, RehearsalForm,
    SongRequestForm, SongRequestModerationForm,
)
from .services import (
    WorshipServiceManager, SongUsageTracker, SongRotationService,
    AutoScheduleService,
)


def _is_staff(member):
    return member.all_roles & set(Roles.STAFF_ROLES)


# ==================================================================
# Service CRUD (existing)
# ==================================================================


@login_required
def service_list(request):
    """List all worship services with date range and status filters."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    services = WorshipService.objects.all()

    status_filter = request.GET.get('status')
    if status_filter:
        services = services.filter(status=status_filter)

    upcoming = request.GET.get('upcoming')
    if upcoming:
        services = services.filter(date__gte=timezone.now().date())

    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        services = services.filter(date__gte=date_from)
    if date_to:
        services = services.filter(date__lte=date_to)

    date_filter_form = ServiceDateRangeFilterForm(request.GET or None)

    paginator = Paginator(services, 20)
    page = request.GET.get('page', 1)
    services_page = paginator.get_page(page)

    context = {
        'services': services_page,
        'page_title': 'Cultes',
        'is_staff': _is_staff(member),
        'status_choices': WorshipServiceStatus.CHOICES,
        'date_filter_form': date_filter_form,
    }
    return render(request, 'worship/service_list.html', context)


@login_required
def service_detail(request, pk):
    """View a worship service with its sections and assignments."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    service = get_object_or_404(WorshipService, pk=pk)
    sections = service.sections.prefetch_related(
        'assignments__member', 'assignments__task_type', 'department'
    ).order_by('order')

    # Get setlist if exists
    setlist = getattr(service, 'setlist', None)
    setlist_songs = []
    if setlist:
        setlist_songs = setlist.songs.select_related('song').order_by('order')

    # Get livestreams
    livestreams = service.livestreams.all()

    # Get rehearsals
    rehearsals = service.rehearsals.all()

    context = {
        'service': service,
        'sections': sections,
        'setlist': setlist,
        'setlist_songs': setlist_songs,
        'livestreams': livestreams,
        'rehearsals': rehearsals,
        'page_title': str(service),
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/service_detail.html', context)


@login_required
def service_create(request):
    """Create a new worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    if request.method == 'POST':
        form = WorshipServiceForm(request.POST)
        if form.is_valid():
            service = WorshipServiceManager.create_service(
                date=form.cleaned_data['date'],
                start_time=form.cleaned_data['start_time'],
                end_time=form.cleaned_data.get('end_time'),
                duration_minutes=form.cleaned_data.get('duration_minutes', 120),
                theme=form.cleaned_data.get('theme', ''),
                notes=form.cleaned_data.get('notes', ''),
                created_by=member,
            )
            messages.success(request, 'Culte cree avec succes.')
            return redirect(f'/worship/services/{service.pk}/')
    else:
        form = WorshipServiceForm()

    context = {
        'form': form,
        'page_title': 'Nouveau culte',
    }
    return render(request, 'worship/service_form.html', context)


@login_required
def service_edit(request, pk):
    """Edit an existing worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        form = WorshipServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Culte mis a jour.')
            return redirect(f'/worship/services/{service.pk}/')
    else:
        form = WorshipServiceForm(instance=service)

    context = {
        'form': form,
        'service': service,
        'page_title': f'Modifier: {service}',
    }
    return render(request, 'worship/service_form.html', context)


@login_required
def service_delete(request, pk):
    """Delete a worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Culte supprime avec succes.')
        return redirect('/worship/services/')

    context = {
        'service': service,
        'page_title': f'Supprimer: {service}',
    }
    return render(request, 'worship/service_delete.html', context)


@login_required
def service_publish(request, pk):
    """Publish/finalize a worship service status (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in WorshipServiceStatus.CHOICES]
        if new_status in valid_statuses:
            old_status = service.status
            WorshipServiceManager.update_service_status(service, new_status)
            status_display = dict(WorshipServiceStatus.CHOICES).get(new_status, new_status)
            messages.success(request, f'Statut mis a jour: {status_display}')

            # Track song usage when service is completed
            if new_status == WorshipServiceStatus.COMPLETED and old_status != WorshipServiceStatus.COMPLETED:
                count = SongUsageTracker.record_service_songs(service)
                if count:
                    messages.info(request, f'{count} chant(s) mis a jour dans les statistiques.')
        else:
            messages.error(request, 'Statut invalide.')

    return redirect(f'/worship/services/{service.pk}/')


@login_required
def service_print(request, pk):
    """Printable worship service program with setlist songs/chords."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    service = get_object_or_404(WorshipService, pk=pk)
    sections = service.sections.prefetch_related(
        'assignments__member', 'assignments__task_type', 'department'
    ).order_by('order')

    # Get setlist for enhanced print view
    setlist = getattr(service, 'setlist', None)
    setlist_songs = []
    if setlist:
        setlist_songs = setlist.songs.select_related('song').order_by('order')

    context = {
        'service': service,
        'sections': sections,
        'setlist': setlist,
        'setlist_songs': setlist_songs,
        'page_title': f'Programme - {service}',
    }
    return render(request, 'worship/service_print.html', context)


@login_required
def service_duplicate(request, pk):
    """Duplicate a worship service by copying sections (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    source_service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        form = WorshipServiceForm(request.POST)
        if form.is_valid():
            new_service = WorshipServiceManager.create_service(
                date=form.cleaned_data['date'],
                start_time=form.cleaned_data['start_time'],
                end_time=form.cleaned_data.get('end_time'),
                duration_minutes=form.cleaned_data.get('duration_minutes', 120),
                theme=form.cleaned_data.get('theme', ''),
                notes=form.cleaned_data.get('notes', ''),
                created_by=member,
            )
            # Copy sections from source
            for section in source_service.sections.order_by('order'):
                ServiceSection.objects.create(
                    service=new_service,
                    name=section.name,
                    order=section.order,
                    section_type=section.section_type,
                    duration_minutes=section.duration_minutes,
                    department=section.department,
                    notes=section.notes,
                )
            messages.success(request, f'Culte duplique avec {source_service.sections.count()} sections.')
            return redirect(f'/worship/services/{new_service.pk}/')
    else:
        form = WorshipServiceForm(initial={
            'start_time': source_service.start_time,
            'end_time': source_service.end_time,
            'duration_minutes': source_service.duration_minutes,
            'theme': source_service.theme,
        })

    context = {
        'form': form,
        'source_service': source_service,
        'page_title': f'Dupliquer: {source_service}',
    }
    return render(request, 'worship/service_duplicate.html', context)


# ==================================================================
# Section CRUD (existing)
# ==================================================================


@login_required
def section_manage(request, pk):
    """Add a section to a worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        form = ServiceSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.service = service
            section.save()
            messages.success(request, f'Section "{section.name}" ajoutee.')
            return redirect(f'/worship/services/{service.pk}/')
    else:
        next_order = service.sections.count() + 1
        form = ServiceSectionForm(initial={'order': next_order})

    context = {
        'form': form,
        'service': service,
        'page_title': f'Ajouter une section - {service}',
    }
    return render(request, 'worship/section_form.html', context)


@login_required
def section_edit(request, pk):
    """Edit an existing section (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    section = get_object_or_404(
        ServiceSection.objects.select_related('service'), pk=pk
    )
    service = section.service

    if request.method == 'POST':
        form = ServiceSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section "{section.name}" mise a jour.')
            return redirect(f'/worship/services/{service.pk}/')
    else:
        form = ServiceSectionForm(instance=section)

    context = {
        'form': form,
        'section': section,
        'service': service,
        'page_title': f'Modifier: {section.name}',
    }
    return render(request, 'worship/section_edit.html', context)


@login_required
def section_delete(request, pk):
    """Delete a section (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    section = get_object_or_404(
        ServiceSection.objects.select_related('service'), pk=pk
    )
    service = section.service

    if request.method == 'POST':
        section_name = section.name
        section.delete()
        messages.success(request, f'Section "{section_name}" supprimee.')
        return redirect(f'/worship/services/{service.pk}/')

    context = {
        'section': section,
        'service': service,
        'page_title': f'Supprimer: {section.name}',
    }
    return render(request, 'worship/section_delete.html', context)


@login_required
@require_POST
def section_reorder(request, pk):
    """Reorder sections of a service via AJAX (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        return JsonResponse({'error': 'Acces non autorise.'}, status=403)

    service = get_object_or_404(WorshipService, pk=pk)

    try:
        data = json.loads(request.body)
        order_list = data.get('order', [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Donnees invalides.'}, status=400)

    if not order_list:
        return JsonResponse({'error': "Liste d'ordre vide."}, status=400)

    # Validate all section IDs belong to this service
    section_ids = [str(s.pk) for s in service.sections.all()]
    for item in order_list:
        if str(item) not in section_ids:
            return JsonResponse({'error': 'Section invalide.'}, status=400)

    # Temporarily clear unique constraint by setting high orders
    for i, section_id in enumerate(order_list):
        ServiceSection.objects.filter(pk=section_id, service=service).update(
            order=1000 + i
        )

    # Then set the real orders
    for i, section_id in enumerate(order_list):
        ServiceSection.objects.filter(pk=section_id, service=service).update(
            order=i + 1
        )

    return JsonResponse({'status': 'ok'})


# ==================================================================
# Assignment Management (existing)
# ==================================================================


@login_required
def assign_members(request, section_pk):
    """Assign a member to a section (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    section = get_object_or_404(
        ServiceSection.objects.select_related('service'), pk=section_pk
    )
    service = section.service

    if request.method == 'POST':
        form = ServiceAssignmentForm(request.POST, section=section)
        if form.is_valid():
            target_member = form.cleaned_data['member']
            task_type = form.cleaned_data.get('task_type')
            notes = form.cleaned_data.get('notes', '')

            # Check for duplicate
            if ServiceAssignment.objects.filter(section=section, member=target_member).exists():
                messages.warning(request, f'{target_member.full_name} est deja assigne(e) a cette section.')
            else:
                WorshipServiceManager.assign_member(
                    section=section,
                    member=target_member,
                    task_type=task_type,
                    notes=notes,
                )
                messages.success(request, f'{target_member.full_name} assigne(e) avec succes.')
            return redirect(f'/worship/services/{service.pk}/')
    else:
        form = ServiceAssignmentForm(section=section)

    existing_assignments = section.assignments.select_related('member', 'task_type')

    context = {
        'form': form,
        'section': section,
        'service': service,
        'existing_assignments': existing_assignments,
        'page_title': f'Assigner - {section.name}',
    }
    return render(request, 'worship/assign_members.html', context)


@login_required
def assignment_remove(request, pk):
    """Remove/unassign a member from a section (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    assignment = get_object_or_404(
        ServiceAssignment.objects.select_related('section__service', 'member'), pk=pk
    )
    service = assignment.section.service

    if request.method == 'POST':
        member_name = assignment.member.full_name
        assignment.delete()
        messages.success(request, f'{member_name} retire(e) de la section.')
        return redirect(f'/worship/services/{service.pk}/')

    context = {
        'assignment': assignment,
        'service': service,
        'page_title': f'Retirer: {assignment.member.full_name}',
    }
    return render(request, 'worship/assignment_remove.html', context)


@login_required
def my_assignments(request):
    """View current user's worship service assignments."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    assignments = ServiceAssignment.objects.filter(
        member=member,
        section__service__date__gte=timezone.now().date(),
    ).select_related(
        'section__service', 'task_type'
    ).order_by('section__service__date')

    past_assignments = ServiceAssignment.objects.filter(
        member=member,
        section__service__date__lt=timezone.now().date(),
    ).select_related(
        'section__service', 'task_type'
    ).order_by('-section__service__date')[:10]

    context = {
        'assignments': assignments,
        'past_assignments': past_assignments,
        'page_title': 'Mes assignations de culte',
    }
    return render(request, 'worship/my_assignments.html', context)


@login_required
def assignment_respond(request, pk):
    """Member confirms or declines an assignment."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    assignment = get_object_or_404(ServiceAssignment, pk=pk, member=member)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            WorshipServiceManager.member_respond(assignment, accepted=True)
            messages.success(request, 'Assignation confirmee!')
        elif action == 'decline':
            WorshipServiceManager.member_respond(assignment, accepted=False)
            messages.info(request, 'Assignation declinee.')

    return redirect('/worship/my-assignments/')


# ==================================================================
# Eligible List Management (existing)
# ==================================================================


@login_required
def eligible_list(request):
    """Manage eligible member lists for section types (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    eligible_lists = EligibleMemberList.objects.prefetch_related('members', 'department').all()

    context = {
        'eligible_lists': eligible_lists,
        'page_title': "Listes d'eligibilite",
        'section_type_choices': ServiceSectionType.CHOICES,
    }
    return render(request, 'worship/eligible_list.html', context)


@login_required
def eligible_list_edit(request, pk):
    """Edit an eligible member list (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    eligible = get_object_or_404(EligibleMemberList, pk=pk)

    if request.method == 'POST':
        form = EligibleMemberListForm(request.POST, instance=eligible)
        if form.is_valid():
            form.save()
            messages.success(request, "Liste d'eligibilite mise a jour.")
            return redirect('/worship/eligible/')
    else:
        form = EligibleMemberListForm(instance=eligible)

    context = {
        'form': form,
        'eligible': eligible,
        'page_title': f'Modifier: {eligible}',
    }
    return render(request, 'worship/eligible_list_form.html', context)


@login_required
def eligible_list_create(request):
    """Create a new eligible member list (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    if request.method == 'POST':
        form = EligibleMemberListForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Liste d'eligibilite creee.")
            return redirect('/worship/eligible/')
    else:
        form = EligibleMemberListForm()

    context = {
        'form': form,
        'page_title': "Nouvelle liste d'eligibilite",
    }
    return render(request, 'worship/eligible_list_form.html', context)


@login_required
def eligible_list_delete(request, pk):
    """Delete an eligible member list (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    eligible = get_object_or_404(EligibleMemberList, pk=pk)

    if request.method == 'POST':
        eligible.delete()
        messages.success(request, "Liste d'eligibilite supprimee.")
        return redirect('/worship/eligible/')

    context = {
        'eligible': eligible,
        'page_title': f'Supprimer: {eligible}',
    }
    return render(request, 'worship/eligible_list_delete.html', context)


# ==================================================================
# P1: Sermon CRUD
# ==================================================================


@login_required
def sermon_list(request):
    """List sermons (published for members, all for staff)."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    is_staff = _is_staff(member)
    sermons = Sermon.objects.select_related('speaker', 'series')

    if not is_staff:
        sermons = sermons.filter(status=SermonStatus.PUBLISHED)

    # Search
    q = request.GET.get('q', '')
    if q:
        sermons = sermons.filter(
            Q(title__icontains=q) | Q(scripture_reference__icontains=q)
        )

    paginator = Paginator(sermons, 20)
    page = request.GET.get('page', 1)
    sermons_page = paginator.get_page(page)

    context = {
        'sermons': sermons_page,
        'page_title': 'Predications',
        'is_staff': is_staff,
        'q': q,
    }
    return render(request, 'worship/sermon_list.html', context)


@login_required
def sermon_create(request):
    """Create a new sermon (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/sermons/')

    if request.method == 'POST':
        form = SermonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Predication creee avec succes.')
            return redirect('/worship/sermons/')
    else:
        form = SermonForm()

    context = {
        'form': form,
        'page_title': 'Nouvelle predication',
    }
    return render(request, 'worship/sermon_form.html', context)


@login_required
def sermon_detail(request, pk):
    """View a sermon detail."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    sermon = get_object_or_404(Sermon.objects.select_related('speaker', 'series', 'service'), pk=pk)

    # Non-staff can only see published sermons
    if not _is_staff(member) and sermon.status != SermonStatus.PUBLISHED:
        messages.error(request, 'Predication non disponible.')
        return redirect('/worship/sermons/')

    context = {
        'sermon': sermon,
        'page_title': sermon.title,
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/sermon_detail.html', context)


@login_required
def sermon_edit(request, pk):
    """Edit a sermon (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/sermons/')

    sermon = get_object_or_404(Sermon, pk=pk)

    if request.method == 'POST':
        form = SermonForm(request.POST, instance=sermon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Predication mise a jour.')
            return redirect(f'/worship/sermons/{sermon.pk}/')
    else:
        form = SermonForm(instance=sermon)

    context = {
        'form': form,
        'sermon': sermon,
        'page_title': f'Modifier: {sermon.title}',
    }
    return render(request, 'worship/sermon_form.html', context)


@login_required
def sermon_delete(request, pk):
    """Delete a sermon (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/sermons/')

    sermon = get_object_or_404(Sermon, pk=pk)

    if request.method == 'POST':
        sermon.delete()
        messages.success(request, 'Predication supprimee.')
        return redirect('/worship/sermons/')

    context = {
        'sermon': sermon,
        'page_title': f'Supprimer: {sermon.title}',
    }
    return render(request, 'worship/sermon_delete.html', context)


@login_required
def sermon_archive(request):
    """Searchable, filterable sermon archive."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    sermons = Sermon.objects.filter(
        status__in=[SermonStatus.PUBLISHED, SermonStatus.ARCHIVED]
    ).select_related('speaker', 'series')

    filter_form = SermonFilterForm(request.GET or None)

    speaker = request.GET.get('speaker')
    if speaker:
        sermons = sermons.filter(speaker_id=speaker)

    series = request.GET.get('series')
    if series:
        sermons = sermons.filter(series_id=series)

    date_from = request.GET.get('date_from')
    if date_from:
        sermons = sermons.filter(date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        sermons = sermons.filter(date__lte=date_to)

    q = request.GET.get('q', '')
    if q:
        sermons = sermons.filter(
            Q(title__icontains=q) | Q(scripture_reference__icontains=q) | Q(notes__icontains=q)
        )

    paginator = Paginator(sermons, 20)
    page = request.GET.get('page', 1)
    sermons_page = paginator.get_page(page)

    context = {
        'sermons': sermons_page,
        'filter_form': filter_form,
        'page_title': 'Archives des predications',
        'is_staff': _is_staff(member),
        'q': q,
    }
    return render(request, 'worship/sermon_archive.html', context)


# ==================================================================
# P1: Sermon RSS Feed
# ==================================================================


class SermonRssFeed(Feed):
    """RSS feed for published sermons (podcast distribution)."""
    title = "Predications - EgliseConnect"
    link = "/worship/sermons/"
    description = "Les dernieres predications de notre eglise."
    feed_type = Rss201rev2Feed

    def items(self):
        return Sermon.objects.filter(
            status=SermonStatus.PUBLISHED
        ).order_by('-date')[:50]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        desc = f'{item.scripture_reference}' if item.scripture_reference else ''
        if item.speaker:
            desc += f' - {item.speaker.full_name}'
        if item.notes:
            desc += f'\n\n{item.notes[:500]}'
        return desc

    def item_link(self, item):
        return f'/worship/sermons/{item.pk}/'

    def item_pubdate(self, item):
        return timezone.make_aware(
            timezone.datetime.combine(item.date, timezone.datetime.min.time())
        )

    def item_enclosures(self, item):
        enclosures = []
        if item.audio_url:
            from django.utils.feedgenerator import Enclosure
            enclosures.append(Enclosure(item.audio_url, '0', 'audio/mpeg'))
        return enclosures


# ==================================================================
# P1: Song CRUD
# ==================================================================


@login_required
def song_list(request):
    """List all songs with search."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    songs = Song.objects.all()

    q = request.GET.get('q', '')
    if q:
        songs = songs.filter(
            Q(title__icontains=q) | Q(artist__icontains=q) | Q(tags__icontains=q)
        )

    song_key = request.GET.get('song_key', '')
    if song_key:
        songs = songs.filter(song_key=song_key)

    search_form = SongSearchForm(request.GET or None)

    paginator = Paginator(songs, 20)
    page = request.GET.get('page', 1)
    songs_page = paginator.get_page(page)

    context = {
        'songs': songs_page,
        'search_form': search_form,
        'page_title': 'Base de chants',
        'is_staff': _is_staff(member),
        'q': q,
    }
    return render(request, 'worship/song_list.html', context)


@login_required
def song_create(request):
    """Create a new song (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/songs/')

    if request.method == 'POST':
        form = SongForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chant cree avec succes.')
            return redirect('/worship/songs/')
    else:
        form = SongForm()

    context = {
        'form': form,
        'page_title': 'Nouveau chant',
    }
    return render(request, 'worship/song_form.html', context)


@login_required
def song_detail(request, pk):
    """View a song detail with chord chart."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    song = get_object_or_404(Song, pk=pk)

    context = {
        'song': song,
        'page_title': song.title,
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/song_detail.html', context)


@login_required
def song_edit(request, pk):
    """Edit a song (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/songs/')

    song = get_object_or_404(Song, pk=pk)

    if request.method == 'POST':
        form = SongForm(request.POST, instance=song)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chant mis a jour.')
            return redirect(f'/worship/songs/{song.pk}/')
    else:
        form = SongForm(instance=song)

    context = {
        'form': form,
        'song': song,
        'page_title': f'Modifier: {song.title}',
    }
    return render(request, 'worship/song_form.html', context)


@login_required
def song_delete(request, pk):
    """Delete a song (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/songs/')

    song = get_object_or_404(Song, pk=pk)

    if request.method == 'POST':
        song.delete()
        messages.success(request, 'Chant supprime.')
        return redirect('/worship/songs/')

    context = {
        'song': song,
        'page_title': f'Supprimer: {song.title}',
    }
    return render(request, 'worship/song_delete.html', context)


@login_required
def chord_chart_view(request, pk):
    """Display chord chart for a song in performance mode."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    song = get_object_or_404(Song, pk=pk)

    context = {
        'song': song,
        'page_title': f'Grille - {song.title}',
    }
    return render(request, 'worship/chord_chart.html', context)


@login_required
def chord_chart_print(request, pk):
    """Print-friendly chord chart layout."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    song = get_object_or_404(Song, pk=pk)

    context = {
        'song': song,
        'page_title': f'Impression - {song.title}',
    }
    return render(request, 'worship/chord_chart_print.html', context)


# ==================================================================
# P1: Setlist Builder
# ==================================================================


@login_required
def setlist_builder(request, service_pk):
    """Build/edit a setlist for a worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=service_pk)

    # Get or create setlist
    setlist, created = Setlist.objects.get_or_create(service=service)

    if request.method == 'POST':
        form = SetlistSongForm(request.POST)
        if form.is_valid():
            setlist_song = form.save(commit=False)
            setlist_song.setlist = setlist
            setlist_song.save()
            messages.success(request, f'Chant "{setlist_song.song.title}" ajoute.')
            return redirect(f'/worship/services/{service.pk}/setlist/')
    else:
        next_order = setlist.songs.count() + 1
        form = SetlistSongForm(initial={'order': next_order})

    setlist_songs = setlist.songs.select_related('song').order_by('order')
    all_songs = Song.objects.all().order_by('title')

    context = {
        'service': service,
        'setlist': setlist,
        'setlist_songs': setlist_songs,
        'form': form,
        'all_songs': all_songs,
        'page_title': f'Liste de chants - {service}',
    }
    return render(request, 'worship/setlist_builder.html', context)


@login_required
def setlist_song_remove(request, pk):
    """Remove a song from a setlist (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    setlist_song = get_object_or_404(
        SetlistSong.objects.select_related('setlist__service'), pk=pk
    )
    service_pk = setlist_song.setlist.service.pk

    if request.method == 'POST':
        setlist_song.delete()
        messages.success(request, 'Chant retire de la liste.')

    return redirect(f'/worship/services/{service_pk}/setlist/')


@login_required
@require_POST
def setlist_reorder(request, service_pk):
    """Reorder setlist songs via AJAX (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        return JsonResponse({'error': 'Acces non autorise.'}, status=403)

    service = get_object_or_404(WorshipService, pk=service_pk)

    try:
        setlist = Setlist.objects.get(service=service)
    except Setlist.DoesNotExist:
        return JsonResponse({'error': 'Setlist introuvable.'}, status=404)

    try:
        data = json.loads(request.body)
        order_list = data.get('order', [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Donnees invalides.'}, status=400)

    if not order_list:
        return JsonResponse({'error': "Liste d'ordre vide."}, status=400)

    # Temporarily set high orders
    for i, song_id in enumerate(order_list):
        SetlistSong.objects.filter(pk=song_id, setlist=setlist).update(order=1000 + i)

    # Set real orders
    for i, song_id in enumerate(order_list):
        SetlistSong.objects.filter(pk=song_id, setlist=setlist).update(order=i + 1)

    return JsonResponse({'status': 'ok'})


# ==================================================================
# P1: CCLI Song Usage Report
# ==================================================================


@login_required
def ccli_report(request):
    """CCLI song usage reporting view."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    songs = Song.objects.filter(ccli_number__gt='').order_by('-play_count')

    # Get usage in date range if filters provided
    usage_data = []
    for song in songs:
        appearances = SetlistSong.objects.filter(song=song)
        if date_from:
            appearances = appearances.filter(setlist__service__date__gte=date_from)
        if date_to:
            appearances = appearances.filter(setlist__service__date__lte=date_to)
        play_count = appearances.count()
        if play_count > 0:
            dates = list(appearances.values_list(
                'setlist__service__date', flat=True
            ).order_by('setlist__service__date'))
            usage_data.append({
                'song': song,
                'play_count': play_count,
                'dates': dates,
            })

    usage_data.sort(key=lambda x: x['play_count'], reverse=True)

    context = {
        'usage_data': usage_data,
        'page_title': 'Rapport CCLI',
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'worship/ccli_report.html', context)


# ==================================================================
# P2: Calendar Views
# ==================================================================


@login_required
def calendar_view(request):
    """Month/week calendar view for worship services."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    context = {
        'page_title': 'Calendrier des cultes',
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/calendar.html', context)


@login_required
def calendar_data(request):
    """Return services as JSON events for FullCalendar."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        return JsonResponse([], safe=False)

    start = request.GET.get('start', '')
    end = request.GET.get('end', '')

    services = WorshipService.objects.all()
    if start:
        services = services.filter(date__gte=start)
    if end:
        services = services.filter(date__lte=end)

    STATUS_COLORS = {
        'draft': '#6c757d',
        'planned': '#17a2b8',
        'confirmed': '#28a745',
        'completed': '#007bff',
        'cancelled': '#dc3545',
    }

    events = []
    for s in services:
        events.append({
            'id': str(s.pk),
            'title': s.theme or f'Culte {s.start_time:%H:%M}',
            'start': f'{s.date.isoformat()}T{s.start_time.isoformat()}',
            'url': f'/worship/services/{s.pk}/',
            'color': STATUS_COLORS.get(s.status, '#6c757d'),
        })

    return JsonResponse(events, safe=False)


@login_required
def planning_timeline(request, pk):
    """Service planning timeline view."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    service = get_object_or_404(WorshipService, pk=pk)
    checklist = service.planning_checklist

    context = {
        'service': service,
        'checklist': checklist,
        'page_title': f'Planification - {service}',
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/planning_timeline.html', context)


# ==================================================================
# P2: Song Usage Analytics
# ==================================================================


@login_required
def most_played_songs(request):
    """Most-played songs report."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    limit = int(request.GET.get('limit', 20))
    songs = Song.objects.filter(play_count__gt=0).order_by('-play_count')[:limit]

    context = {
        'songs': songs,
        'page_title': 'Chants les plus joues',
        'limit': limit,
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/most_played_songs.html', context)


@login_required
def song_rotation(request):
    """Song rotation suggestions (songs not played recently)."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    weeks = int(request.GET.get('weeks', 6))
    suggestions = SongRotationService.get_rotation_suggestions(weeks=weeks)

    context = {
        'suggestions': suggestions,
        'page_title': 'Suggestions de rotation',
        'weeks': weeks,
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/song_rotation.html', context)


# ==================================================================
# P2: Auto-Scheduling
# ==================================================================


@login_required
def auto_schedule_preview(request, pk):
    """Preview auto-generated schedule before publishing (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        created = AutoScheduleService.generate_schedule(service)
        if created:
            messages.success(request, f'{len(created)} assignation(s) creee(s) automatiquement.')
        else:
            messages.info(request, 'Aucune assignation creee (toutes les sections sont deja remplies ou pas de membres eligibles).')
        return redirect(f'/worship/services/{service.pk}/')

    conflicts = AutoScheduleService.detect_conflicts(service)

    context = {
        'service': service,
        'conflicts': conflicts,
        'page_title': f'Auto-planification - {service}',
    }
    return render(request, 'worship/auto_schedule_preview.html', context)


# ==================================================================
# P3: Live Streaming
# ==================================================================


@login_required
def livestream_manage(request, service_pk):
    """Manage live stream for a service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=service_pk)

    if request.method == 'POST':
        form = LiveStreamForm(request.POST)
        if form.is_valid():
            livestream = form.save(commit=False)
            livestream.service = service
            livestream.save()
            messages.success(request, 'Diffusion en direct configuree.')
            return redirect(f'/worship/services/{service.pk}/')
    else:
        form = LiveStreamForm(initial={'service': service})

    livestreams = service.livestreams.all()

    context = {
        'service': service,
        'form': form,
        'livestreams': livestreams,
        'page_title': f'Diffusion en direct - {service}',
    }
    return render(request, 'worship/livestream_manage.html', context)


@login_required
def livestream_delete(request, pk):
    """Delete a livestream (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    livestream = get_object_or_404(
        LiveStream.objects.select_related('service'), pk=pk
    )
    service_pk = livestream.service.pk

    if request.method == 'POST':
        livestream.delete()
        messages.success(request, 'Diffusion supprimee.')
        return redirect(f'/worship/services/{service_pk}/')

    context = {
        'livestream': livestream,
        'page_title': f'Supprimer la diffusion',
    }
    return render(request, 'worship/livestream_delete.html', context)


# ==================================================================
# P3: Rehearsal CRUD
# ==================================================================


@login_required
def rehearsal_list(request):
    """List all rehearsals."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    rehearsals = Rehearsal.objects.select_related('service').all()

    upcoming = request.GET.get('upcoming')
    if upcoming:
        rehearsals = rehearsals.filter(date__gte=timezone.now().date())

    paginator = Paginator(rehearsals, 20)
    page = request.GET.get('page', 1)
    rehearsals_page = paginator.get_page(page)

    context = {
        'rehearsals': rehearsals_page,
        'page_title': 'Repetitions',
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/rehearsal_list.html', context)


@login_required
def rehearsal_create(request):
    """Create a rehearsal (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/rehearsals/')

    if request.method == 'POST':
        form = RehearsalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Repetition creee avec succes.')
            return redirect('/worship/rehearsals/')
    else:
        form = RehearsalForm()

    context = {
        'form': form,
        'page_title': 'Nouvelle repetition',
    }
    return render(request, 'worship/rehearsal_form.html', context)


@login_required
def rehearsal_detail(request, pk):
    """View a rehearsal with attendees."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    rehearsal = get_object_or_404(
        Rehearsal.objects.select_related('service'), pk=pk
    )
    attendees = rehearsal.attendees.select_related('member').all()

    # Check if current member has RSVP
    user_rsvp = rehearsal.attendees.filter(member=member).first()

    # Get setlist from associated service if available
    setlist = None
    if rehearsal.service:
        setlist = getattr(rehearsal.service, 'setlist', None)

    context = {
        'rehearsal': rehearsal,
        'attendees': attendees,
        'user_rsvp': user_rsvp,
        'setlist': setlist,
        'page_title': str(rehearsal),
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/rehearsal_detail.html', context)


@login_required
def rehearsal_edit(request, pk):
    """Edit a rehearsal (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/rehearsals/')

    rehearsal = get_object_or_404(Rehearsal, pk=pk)

    if request.method == 'POST':
        form = RehearsalForm(request.POST, instance=rehearsal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Repetition mise a jour.')
            return redirect(f'/worship/rehearsals/{rehearsal.pk}/')
    else:
        form = RehearsalForm(instance=rehearsal)

    context = {
        'form': form,
        'rehearsal': rehearsal,
        'page_title': f'Modifier: {rehearsal}',
    }
    return render(request, 'worship/rehearsal_form.html', context)


@login_required
def rehearsal_delete(request, pk):
    """Delete a rehearsal (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/rehearsals/')

    rehearsal = get_object_or_404(Rehearsal, pk=pk)

    if request.method == 'POST':
        rehearsal.delete()
        messages.success(request, 'Repetition supprimee.')
        return redirect('/worship/rehearsals/')

    context = {
        'rehearsal': rehearsal,
        'page_title': f'Supprimer: {rehearsal}',
    }
    return render(request, 'worship/rehearsal_delete.html', context)


@login_required
@require_POST
def rehearsal_rsvp(request, pk):
    """RSVP to a rehearsal."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    rehearsal = get_object_or_404(Rehearsal, pk=pk)
    action = request.POST.get('action')

    attendee, created = RehearsalAttendee.objects.get_or_create(
        rehearsal=rehearsal, member=member,
        defaults={'status': RehearsalAttendeeStatus.INVITED},
    )

    if action == 'confirm':
        attendee.status = RehearsalAttendeeStatus.CONFIRMED
        attendee.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Presence confirmee.')
    elif action == 'decline':
        attendee.status = RehearsalAttendeeStatus.DECLINED
        attendee.save(update_fields=['status', 'updated_at'])
        messages.info(request, 'Absence signalee.')

    return redirect(f'/worship/rehearsals/{rehearsal.pk}/')


# ==================================================================
# P3: Song Requests
# ==================================================================


@login_required
def song_request_list(request):
    """View song requests."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    requests_qs = SongRequest.objects.select_related('requested_by').all()

    status_filter = request.GET.get('status')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    context = {
        'song_requests': requests_qs,
        'page_title': 'Demandes de chants',
        'is_staff': _is_staff(member),
        'status_choices': SongRequestStatus.CHOICES,
    }
    return render(request, 'worship/song_request_list.html', context)


@login_required
def song_request_create(request):
    """Submit a new song request."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    if request.method == 'POST':
        form = SongRequestForm(request.POST)
        if form.is_valid():
            song_request = form.save(commit=False)
            song_request.requested_by = member
            song_request.save()
            messages.success(request, 'Demande de chant soumise!')
            return redirect('/worship/song-requests/')
    else:
        form = SongRequestForm()

    context = {
        'form': form,
        'page_title': 'Demander un chant',
    }
    return render(request, 'worship/song_request_form.html', context)


@login_required
@require_POST
def song_request_vote(request, pk):
    """Vote for a song request (one per member)."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        return JsonResponse({'error': 'Profil requis'}, status=403)

    song_request = get_object_or_404(SongRequest, pk=pk)

    # Check if already voted
    if SongRequestVote.objects.filter(song_request=song_request, member=member).exists():
        return JsonResponse({'error': 'Vous avez deja vote.'}, status=400)

    SongRequestVote.objects.create(song_request=song_request, member=member)
    song_request.votes += 1
    song_request.save(update_fields=['votes', 'updated_at'])

    return JsonResponse({'votes': song_request.votes})


@login_required
def song_request_moderate(request, pk):
    """Moderate a song request (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/song-requests/')

    song_request = get_object_or_404(SongRequest, pk=pk)

    if request.method == 'POST':
        form = SongRequestModerationForm(request.POST)
        if form.is_valid():
            song_request.status = form.cleaned_data['status']
            if form.cleaned_data.get('scheduled_date'):
                song_request.scheduled_date = form.cleaned_data['scheduled_date']
            song_request.save(update_fields=['status', 'scheduled_date', 'updated_at'])
            messages.success(request, 'Statut de la demande mis a jour.')
            return redirect('/worship/song-requests/')
    else:
        form = SongRequestModerationForm(initial={
            'status': song_request.status,
            'scheduled_date': song_request.scheduled_date,
        })

    context = {
        'form': form,
        'song_request': song_request,
        'page_title': f'Moderer: {song_request.song_title}',
    }
    return render(request, 'worship/song_request_moderate.html', context)


# ==================================================================
# P3: ProPresenter / EasyWorship Exports
# ==================================================================


@login_required
def propresenter_export(request, pk):
    """Export service plan as ProPresenter-compatible XML."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)
    setlist = getattr(service, 'setlist', None)

    root = ET.Element('RVPresentationDocument')
    root.set('width', '1920')
    root.set('height', '1080')

    if setlist:
        for setlist_song in setlist.songs.select_related('song').order_by('order'):
            song = setlist_song.song
            slide_group = ET.SubElement(root, 'RVSlideGrouping')
            slide_group.set('name', song.title)
            slide_group.set('color', '0 0 0 1')

            if song.lyrics:
                # Split lyrics into slides by blank lines
                sections = song.lyrics.split('\n\n')
                for idx, section_text in enumerate(sections):
                    slide = ET.SubElement(slide_group, 'RVDisplaySlide')
                    text_elem = ET.SubElement(slide, 'RVTextElement')
                    text_elem.text = section_text.strip()

    xml_string = ET.tostring(root, encoding='unicode', xml_declaration=True)
    try:
        pretty = parseString(xml_string).toprettyxml(indent='  ')
    except Exception:
        pretty = xml_string

    response = HttpResponse(pretty, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="service_{service.date}.pro6.xml"'
    return response


@login_required
def easyworship_export(request, pk):
    """Export service plan as EasyWorship schedule file (simplified XML)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Acces non autorise.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)
    sections = service.sections.prefetch_related('assignments__member').order_by('order')
    setlist = getattr(service, 'setlist', None)

    root = ET.Element('EasyWorshipSchedule')
    root.set('title', str(service))
    root.set('date', service.date.isoformat())

    for section in sections:
        item = ET.SubElement(root, 'ScheduleItem')
        item.set('type', section.section_type)
        item.set('title', section.name)
        item.set('duration', str(section.duration_minutes))

    if setlist:
        songs_group = ET.SubElement(root, 'Songs')
        for ss in setlist.songs.select_related('song').order_by('order'):
            song_elem = ET.SubElement(songs_group, 'Song')
            song_elem.set('title', ss.song.title)
            song_elem.set('artist', ss.song.artist)
            song_elem.set('key', ss.key_override or ss.song.song_key)
            if ss.song.ccli_number:
                song_elem.set('ccli', ss.song.ccli_number)
            if ss.song.lyrics:
                lyrics_elem = ET.SubElement(song_elem, 'Lyrics')
                lyrics_elem.text = ss.song.lyrics

    xml_string = ET.tostring(root, encoding='unicode', xml_declaration=True)

    response = HttpResponse(xml_string, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="service_{service.date}_ew.xml"'
    return response
