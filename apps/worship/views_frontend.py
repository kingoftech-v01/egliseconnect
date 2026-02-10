"""Worship service planning frontend views."""
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.constants import (
    Roles, WorshipServiceStatus, AssignmentStatus, ServiceSectionType,
)

from .models import WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList
from .forms import (
    WorshipServiceForm, ServiceSectionForm, ServiceAssignmentForm,
    EligibleMemberListForm, ServiceDateRangeFilterForm,
)
from .services import WorshipServiceManager


def _is_staff(member):
    return member.all_roles & set(Roles.STAFF_ROLES)


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

    context = {
        'service': service,
        'sections': sections,
        'page_title': str(service),
        'is_staff': _is_staff(member),
    }
    return render(request, 'worship/service_detail.html', context)


@login_required
def service_create(request):
    """Create a new worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
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
            messages.success(request, 'Culte créé avec succès.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        form = WorshipServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Culte mis à jour.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Culte supprimé avec succès.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in WorshipServiceStatus.CHOICES]
        if new_status in valid_statuses:
            WorshipServiceManager.update_service_status(service, new_status)
            status_display = dict(WorshipServiceStatus.CHOICES).get(new_status, new_status)
            messages.success(request, f'Statut mis à jour: {status_display}')
        else:
            messages.error(request, 'Statut invalide.')

    return redirect(f'/worship/services/{service.pk}/')


@login_required
def service_print(request, pk):
    """Printable worship service program."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, 'Profil membre requis.')
        return redirect('/onboarding/dashboard/')

    service = get_object_or_404(WorshipService, pk=pk)
    sections = service.sections.prefetch_related(
        'assignments__member', 'assignments__task_type', 'department'
    ).order_by('order')

    context = {
        'service': service,
        'sections': sections,
        'page_title': f'Programme - {service}',
    }
    return render(request, 'worship/service_print.html', context)


@login_required
def service_duplicate(request, pk):
    """Duplicate a worship service by copying sections (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
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
            messages.success(request, f'Culte dupliqué avec {source_service.sections.count()} sections.')
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


@login_required
def section_manage(request, pk):
    """Add a section to a worship service (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    service = get_object_or_404(WorshipService, pk=pk)

    if request.method == 'POST':
        form = ServiceSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.service = service
            section.save()
            messages.success(request, f'Section "{section.name}" ajoutée.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    section = get_object_or_404(
        ServiceSection.objects.select_related('service'), pk=pk
    )
    service = section.service

    if request.method == 'POST':
        form = ServiceSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section "{section.name}" mise à jour.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    section = get_object_or_404(
        ServiceSection.objects.select_related('service'), pk=pk
    )
    service = section.service

    if request.method == 'POST':
        section_name = section.name
        section.delete()
        messages.success(request, f'Section "{section_name}" supprimée.')
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
        return JsonResponse({'error': 'Accès non autorisé.'}, status=403)

    service = get_object_or_404(WorshipService, pk=pk)

    try:
        data = json.loads(request.body)
        order_list = data.get('order', [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Données invalides.'}, status=400)

    if not order_list:
        return JsonResponse({'error': 'Liste d\'ordre vide.'}, status=400)

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


@login_required
def assign_members(request, section_pk):
    """Assign a member to a section (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
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
                messages.warning(request, f'{target_member.full_name} est déjà assigné(e) à cette section.')
            else:
                WorshipServiceManager.assign_member(
                    section=section,
                    member=target_member,
                    task_type=task_type,
                    notes=notes,
                )
                messages.success(request, f'{target_member.full_name} assigné(e) avec succès.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    assignment = get_object_or_404(
        ServiceAssignment.objects.select_related('section__service', 'member'), pk=pk
    )
    service = assignment.section.service

    if request.method == 'POST':
        member_name = assignment.member.full_name
        assignment.delete()
        messages.success(request, f'{member_name} retiré(e) de la section.')
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
            messages.success(request, 'Assignation confirmée!')
        elif action == 'decline':
            WorshipServiceManager.member_respond(assignment, accepted=False)
            messages.info(request, 'Assignation déclinée.')

    return redirect('/worship/my-assignments/')


@login_required
def eligible_list(request):
    """Manage eligible member lists for section types (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    eligible_lists = EligibleMemberList.objects.prefetch_related('members', 'department').all()

    context = {
        'eligible_lists': eligible_lists,
        'page_title': 'Listes d\'éligibilité',
        'section_type_choices': ServiceSectionType.CHOICES,
    }
    return render(request, 'worship/eligible_list.html', context)


@login_required
def eligible_list_edit(request, pk):
    """Edit an eligible member list (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    eligible = get_object_or_404(EligibleMemberList, pk=pk)

    if request.method == 'POST':
        form = EligibleMemberListForm(request.POST, instance=eligible)
        if form.is_valid():
            form.save()
            messages.success(request, 'Liste d\'éligibilité mise à jour.')
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
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    if request.method == 'POST':
        form = EligibleMemberListForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Liste d\'éligibilité créée.')
            return redirect('/worship/eligible/')
    else:
        form = EligibleMemberListForm()

    context = {
        'form': form,
        'page_title': 'Nouvelle liste d\'éligibilité',
    }
    return render(request, 'worship/eligible_list_form.html', context)


@login_required
def eligible_list_delete(request, pk):
    """Delete an eligible member list (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, 'Accès non autorisé.')
        return redirect('/worship/services/')

    eligible = get_object_or_404(EligibleMemberList, pk=pk)

    if request.method == 'POST':
        eligible.delete()
        messages.success(request, 'Liste d\'éligibilité supprimée.')
        return redirect('/worship/eligible/')

    context = {
        'eligible': eligible,
        'page_title': f'Supprimer: {eligible}',
    }
    return render(request, 'worship/eligible_list_delete.html', context)
