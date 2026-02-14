"""Template-based views for member management using HTMX and Alpine.js."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import (
    PastorRequiredMixin,
    MemberRequiredMixin,
    ChurchContextMixin,
    OwnerOrStaffRequiredMixin,
)
from apps.core.constants import Roles
from apps.core.utils import (
    get_today_birthdays,
    get_week_birthdays,
    get_month_birthdays,
)

from apps.core.export import export_queryset_csv, export_queryset_excel, export_queryset_pdf
from apps.core.constants import ApprovalStatus, CareStatus

from .models import (
    Member, Family, Group, GroupMembership, DirectoryPrivacy,
    Department, DepartmentMembership, DepartmentTaskType,
    DisciplinaryAction, ProfileModificationRequest,
    Child, PastoralCare, BackgroundCheck, ImportHistory,
    MemberMergeLog, CustomField, CustomFieldValue, MemberEngagementScore,
)
from .forms import (
    MemberRegistrationForm,
    MemberProfileForm,
    MemberAdminForm,
    MemberStaffForm,
    ProfileModificationRequestForm,
    FamilyForm,
    GroupForm,
    GroupMembershipForm,
    DirectoryPrivacyForm,
    MemberSearchForm,
    DepartmentForm,
    DepartmentTaskTypeForm,
    DepartmentMembershipForm,
    DisciplinaryActionForm,
    ChildForm,
    PastoralCareForm,
    BackgroundCheckForm,
    MemberImportForm,
    MemberImportMappingForm,
    CustomFieldForm,
    GroupFinderForm,
)
from .services import DisciplinaryService


@login_required
def member_list(request):
    """List all members with filtering, search, and pagination (pastors/admins only)."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Vous n'avez pas accès à la liste des membres."))
            return redirect('frontend:members:member_detail', pk=request.user.member_profile.pk)
    elif not request.user.is_staff:
        messages.error(request, _("Vous n'avez pas accès à la liste des membres."))
        return redirect('/')

    form = MemberSearchForm(request.GET)
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role')
    family_status_filter = request.GET.get('family_status')
    group_filter = request.GET.get('group')
    ALLOWED_SORT_FIELDS = {'last_name', '-last_name', 'first_name', '-first_name',
                           'created_at', '-created_at', 'birth_date', '-birth_date',
                           'role', '-role'}
    sort_by = request.GET.get('sort', 'last_name')
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = 'last_name'
    page = request.GET.get('page', 1)

    members = Member.objects.all().select_related('family')

    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(member_number__icontains=search) |
            Q(phone__icontains=search)
        )

    if role_filter:
        members = members.filter(role=role_filter)

    if family_status_filter:
        members = members.filter(family_status=family_status_filter)

    if group_filter:
        members = members.filter(group_memberships__group_id=group_filter)

    if sort_by.startswith('-'):
        members = members.order_by(sort_by, 'last_name')
    else:
        members = members.order_by(sort_by)

    paginator = Paginator(members, 20)
    members_page = paginator.get_page(page)

    context = {
        'members': members_page,
        'total_count': paginator.count,
        'form': form,
        'search': search,
        'role_filter': role_filter,
        'family_status_filter': family_status_filter,
        'group_filter': group_filter,
        'sort_by': sort_by,
        'page_title': _('Membres'),
    }

    return render(request, 'members/member_list.html', context)


@login_required
def member_detail(request, pk):
    """Display detailed member information with role-based access control."""
    member = get_object_or_404(
        Member.objects.select_related('family'),
        pk=pk
    )

    can_view = False
    is_own_profile = False
    can_edit_admin_fields = False

    current_member = getattr(request.user, 'member_profile', None)

    if request.user.is_staff:
        can_view = True
        can_edit_admin_fields = True
        if current_member and current_member.id == member.id:
            is_own_profile = True
    elif current_member:
        if current_member.id == member.id:
            can_view = True
            is_own_profile = True
        elif current_member.role in [Roles.PASTOR, Roles.ADMIN]:
            can_view = True
            can_edit_admin_fields = True
        elif current_member.role == Roles.DEACON:
            can_view = True
            can_edit_admin_fields = True
        elif current_member.role == Roles.GROUP_LEADER:
            led_groups = current_member.led_groups.values_list('id', flat=True)
            is_group_member = member.group_memberships.filter(
                group_id__in=led_groups
            ).exists()
            can_view = is_group_member

    if not can_view:
        messages.error(request, _("Vous n'avez pas accès à ce profil."))
        return redirect('/')

    groups = member.group_memberships.filter(is_active=True).select_related('group')
    family_members = []
    if member.family:
        family_members = member.family.members.exclude(id=member.id)

    # Department memberships
    department_memberships = member.department_memberships.filter(
        is_active=True
    ).select_related('department')

    # Engagement score
    engagement_score = None
    try:
        engagement_score = member.engagement_score
    except MemberEngagementScore.DoesNotExist:
        pass

    # Latest background check
    latest_background_check = member.background_checks.first()

    # Disciplinary history (staff only)
    disciplinary_actions = []
    is_staff_viewer = (
        request.user.is_staff
        or (current_member and current_member.role in Roles.STAFF_ROLES)
    )
    if is_staff_viewer:
        disciplinary_actions = member.disciplinary_actions.all()[:10]

    context = {
        'member': member,
        'groups': groups,
        'family_members': family_members,
        'department_memberships': department_memberships,
        'engagement_score': engagement_score,
        'latest_background_check': latest_background_check,
        'disciplinary_actions': disciplinary_actions,
        'is_own_profile': is_own_profile,
        'can_edit_admin_fields': can_edit_admin_fields and not is_own_profile,
        'page_title': member.full_name,
    }

    return render(request, 'members/member_detail.html', context)


def member_create(request):
    """Public registration form for new members."""
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            messages.success(
                request,
                _('Inscription réussie! Votre numéro de membre est: %(number)s') % {
                    'number': member.member_number
                }
            )

            if form.cleaned_data.get('create_account') and member.user:
                from django.contrib.auth import login
                login(request, member.user)
                return redirect('frontend:members:member_detail', pk=member.pk)

            return redirect('frontend:members:member_detail', pk=member.pk)
    else:
        form = MemberRegistrationForm()

    context = {
        'form': form,
        'form_title': _('Inscription'),
        'submit_text': _("S'inscrire"),
        'page_title': _('Inscription'),
    }

    return render(request, 'members/member_form.html', context)


@login_required
def member_update(request, pk):
    """Update member profile. Own profile: personal fields. Other member: admin fields only."""
    member = get_object_or_404(Member, pk=pk)

    can_edit = False
    is_own_profile = False
    is_staff_editing = False

    current_member = getattr(request.user, 'member_profile', None)

    if current_member and current_member.id == member.id:
        can_edit = True
        is_own_profile = True
    elif request.user.is_staff:
        can_edit = True
        is_staff_editing = True
    elif current_member and current_member.role in Roles.STAFF_ROLES:
        can_edit = True
        is_staff_editing = True

    if not can_edit:
        messages.error(request, _("Vous n'avez pas la permission de modifier ce profil."))
        return redirect('frontend:members:member_detail', pk=pk)

    if is_own_profile:
        FormClass = MemberProfileForm
        form_title = _('Modifier mon profil')
    else:
        FormClass = MemberStaffForm
        form_title = _('Modifier les champs administratifs')

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil mis à jour avec succès.'))
            return redirect('frontend:members:member_detail', pk=member.pk)
    else:
        form = FormClass(instance=member)

    context = {
        'form': form,
        'member': member,
        'form_title': form_title,
        'submit_text': _('Enregistrer'),
        'cancel_url': 'frontend:members:member_detail',
        'page_title': form_title,
    }

    return render(request, 'members/member_form.html', context)


@login_required
def birthday_list(request):
    """List birthdays filtered by period (today/week/month)."""
    period = request.GET.get('period', 'week')
    month = request.GET.get('month')

    if period == 'today':
        members = get_today_birthdays()
        title = _("Anniversaires aujourd'hui")
    elif period == 'month':
        month_names = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        if month:
            try:
                month_int = int(month)
                if 1 <= month_int <= 12:
                    members = get_month_birthdays(month_int)
                    title = _("Anniversaires en %(month)s") % {'month': month_names[month_int - 1]}
                else:
                    members = get_month_birthdays()
                    title = _("Anniversaires ce mois")
            except (ValueError, TypeError):
                members = get_month_birthdays()
                title = _("Anniversaires ce mois")
        else:
            members = get_month_birthdays()
            title = _("Anniversaires ce mois")
    else:
        members = get_week_birthdays()
        title = _("Anniversaires cette semaine")

    context = {
        'members': members,
        'period': period,
        'selected_month': month,
        'title': title,
        'page_title': title,
    }

    return render(request, 'members/birthday_list.html', context)


@login_required
def directory(request):
    """Member directory with privacy settings applied."""
    search = request.GET.get('search', '').strip()
    page = request.GET.get('page', 1)

    members = Member.objects.filter(is_active=True).select_related('privacy_settings')

    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(member_number__icontains=search)
        )

    user = request.user
    if hasattr(user, 'member_profile'):
        current_member = user.member_profile

        if current_member.role not in Roles.STAFF_ROLES and not user.is_staff:
            user_groups = set(
                current_member.group_memberships.filter(is_active=True).values_list('group_id', flat=True)
            )

            # Filter by visibility: public, same group, or self
            members = members.filter(
                Q(privacy_settings__visibility='public') |
                Q(
                    privacy_settings__visibility='group',
                    group_memberships__group_id__in=user_groups
                ) |
                Q(id=current_member.id)
            ).distinct()
    elif not user.is_staff:
        members = members.filter(privacy_settings__visibility='public')

    members = members.order_by('last_name', 'first_name')

    paginator = Paginator(members, 24)
    members_page = paginator.get_page(page)

    context = {
        'members': members_page,
        'search': search,
        'total_count': paginator.count,
        'page_title': _('Annuaire'),
    }

    return render(request, 'members/directory.html', context)


@login_required
def privacy_settings(request):
    """Manage directory privacy settings."""
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Vous devez avoir un profil membre."))
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    try:
        privacy = member.privacy_settings
    except DirectoryPrivacy.DoesNotExist:
        privacy = DirectoryPrivacy.objects.create(member=member)

    if request.method == 'POST':
        form = DirectoryPrivacyForm(request.POST, instance=privacy)
        if form.is_valid():
            form.save()
            messages.success(request, _('Paramètres de confidentialité mis à jour.'))
            return redirect('frontend:members:member_detail', pk=member.pk)
    else:
        form = DirectoryPrivacyForm(instance=privacy)

    context = {
        'form': form,
        'page_title': _('Paramètres de confidentialité'),
    }

    return render(request, 'members/privacy_settings.html', context)


@login_required
def group_list(request):
    """List all active groups."""
    groups = Group.objects.filter(is_active=True).select_related('leader')

    group_type = request.GET.get('type')
    if group_type:
        groups = groups.filter(group_type=group_type)

    context = {
        'groups': groups,
        'group_type_filter': group_type,
        'page_title': _('Groupes'),
    }

    return render(request, 'members/group_list.html', context)


@login_required
def group_detail(request, pk):
    """Display group details with members."""
    group = get_object_or_404(Group.objects.select_related('leader'), pk=pk)
    memberships = group.memberships.filter(is_active=True).select_related('member')

    is_leader = False
    is_staff_user = False
    if hasattr(request.user, 'member_profile'):
        current_member = request.user.member_profile
        is_leader = group.leader == current_member
        is_staff_user = current_member.role in Roles.STAFF_ROLES

    context = {
        'group': group,
        'memberships': memberships,
        'is_leader': is_leader,
        'is_staff_user': is_staff_user,
        'page_title': group.name,
    }

    return render(request, 'members/group_detail.html', context)


@login_required
def family_detail(request, pk):
    """Display family details with members and children."""
    family = get_object_or_404(Family, pk=pk)
    members = family.members.filter(is_active=True)
    children = family.children.filter(is_active=True)

    is_family_member = False
    if hasattr(request.user, 'member_profile'):
        is_family_member = request.user.member_profile.family == family

    context = {
        'family': family,
        'members': members,
        'children': children,
        'is_family_member': is_family_member,
        'page_title': family.name,
    }

    return render(request, 'members/family_detail.html', context)


# ==============================================================================
# Department views
# ==============================================================================


@login_required
def department_list(request):
    """List all departments."""
    departments = Department.objects.filter(is_active=True).select_related('leader')
    context = {
        'departments': departments,
        'page_title': _('Départements'),
    }
    return render(request, 'departments/department_list.html', context)


@login_required
def department_detail(request, pk):
    """View department details with members and task types."""
    department = get_object_or_404(Department, pk=pk)
    memberships = department.memberships.filter(
        is_active=True
    ).select_related('member')
    task_types = department.task_types.filter(is_active=True)

    context = {
        'department': department,
        'memberships': memberships,
        'task_types': task_types,
        'page_title': department.name,
    }
    return render(request, 'departments/department_detail.html', context)


@login_required
def department_create(request):
    """Create a new department (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/departments/')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Département créé avec succès.'))
            return redirect('/departments/')
    else:
        form = DepartmentForm()

    context = {
        'form': form,
        'page_title': _('Nouveau département'),
    }
    return render(request, 'departments/department_form.html', context)


@login_required
def department_edit(request, pk):
    """Edit a department (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/departments/')

    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, _('Département modifié avec succès.'))
            return redirect(f'/departments/{department.pk}/')
    else:
        form = DepartmentForm(instance=department)

    context = {
        'form': form,
        'department': department,
        'page_title': _('Modifier ') + department.name,
    }
    return render(request, 'departments/department_form.html', context)


@login_required
def department_add_member(request, pk):
    """Add a member to a department (admin/pastor/dept leader only)."""
    department = get_object_or_404(Department, pk=pk)

    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    is_dept_leader = department.leader == member
    if member.role not in [Roles.ADMIN, Roles.PASTOR] and not is_dept_leader:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/departments/{pk}/')

    if request.method == 'POST':
        form = DepartmentMembershipForm(request.POST, department=department)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.department = department
            membership.save()
            messages.success(request, _('Membre ajouté au département.'))
            return redirect(f'/departments/{pk}/')
    else:
        form = DepartmentMembershipForm(department=department)

    context = {
        'form': form,
        'department': department,
        'page_title': _('Ajouter un membre'),
    }
    return render(request, 'departments/department_add_member.html', context)


@login_required
def department_task_types(request, pk):
    """Manage task types for a department."""
    department = get_object_or_404(Department, pk=pk)

    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    is_dept_leader = department.leader == member
    if member.role not in [Roles.ADMIN, Roles.PASTOR] and not is_dept_leader:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/departments/{pk}/')

    if request.method == 'POST':
        form = DepartmentTaskTypeForm(request.POST)
        if form.is_valid():
            task_type = form.save(commit=False)
            task_type.department = department
            task_type.save()
            messages.success(request, _('Type de tâche ajouté.'))
            return redirect(f'/departments/{pk}/task-types/')
    else:
        form = DepartmentTaskTypeForm()

    task_types = department.task_types.filter(is_active=True)
    context = {
        'form': form,
        'department': department,
        'task_types': task_types,
        'page_title': _('Types de tâches - ') + department.name,
    }
    return render(request, 'departments/department_task_types.html', context)


# ==============================================================================
# Disciplinary action views
# ==============================================================================


def _is_staff(member):
    return member.role in Roles.STAFF_ROLES


@login_required
def disciplinary_list(request):
    """List all disciplinary actions (staff only) with date range filtering."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    actions = DisciplinaryAction.objects.select_related(
        'member', 'created_by', 'approved_by'
    )

    status_filter = request.GET.get('status')
    if status_filter:
        actions = actions.filter(approval_status=status_filter)

    type_filter = request.GET.get('type')
    if type_filter:
        actions = actions.filter(action_type=type_filter)

    # Date range filtering
    start_date_from = request.GET.get('start_date_from')
    start_date_to = request.GET.get('start_date_to')
    if start_date_from:
        actions = actions.filter(start_date__gte=start_date_from)
    if start_date_to:
        actions = actions.filter(start_date__lte=start_date_to)

    paginator = Paginator(actions, 20)
    page = request.GET.get('page', 1)
    actions_page = paginator.get_page(page)

    context = {
        'actions': actions_page,
        'page_title': _('Actions disciplinaires'),
        'is_pastor_or_admin': member.role in [Roles.PASTOR, Roles.ADMIN],
        'start_date_from': start_date_from or '',
        'start_date_to': start_date_to or '',
    }
    return render(request, 'members/disciplinary_list.html', context)


@login_required
def disciplinary_create(request):
    """Create a new disciplinary action (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    if request.method == 'POST':
        form = DisciplinaryActionForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data['member']
            try:
                action = DisciplinaryService.create_action(
                    actor=member,
                    target=target,
                    action_type=form.cleaned_data['action_type'],
                    reason=form.cleaned_data['reason'],
                    start_date=form.cleaned_data['start_date'],
                    end_date=form.cleaned_data.get('end_date'),
                    notes=form.cleaned_data.get('notes', ''),
                    auto_suspend=form.cleaned_data.get('auto_suspend_membership', True),
                )
                messages.success(request, _('Action disciplinaire créée. En attente d\'approbation.'))
                return redirect(f'/members/disciplinary/{action.pk}/')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = DisciplinaryActionForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle action disciplinaire'),
    }
    return render(request, 'members/disciplinary_form.html', context)


@login_required
def disciplinary_detail(request, pk):
    """View disciplinary action details (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    action = get_object_or_404(
        DisciplinaryAction.objects.select_related(
            'member', 'created_by', 'approved_by'
        ),
        pk=pk,
    )

    can_approve = (
        action.approval_status == ApprovalStatus.PENDING
        and DisciplinaryService.can_approve(member, action)
    )

    context = {
        'action': action,
        'can_approve': can_approve,
        'page_title': str(action),
    }
    return render(request, 'members/disciplinary_detail.html', context)


@login_required
def disciplinary_approve(request, pk):
    """Approve or reject a disciplinary action (pastor/admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/disciplinary/')

    action = get_object_or_404(DisciplinaryAction, pk=pk)

    if request.method == 'POST':
        decision = request.POST.get('decision')
        try:
            if decision == 'approve':
                DisciplinaryService.approve_action(member, action)
                messages.success(request, _('Action disciplinaire approuvée.'))
            elif decision == 'reject':
                DisciplinaryService.reject_action(member, action)
                messages.info(request, _('Action disciplinaire rejetée.'))
            elif decision == 'lift':
                DisciplinaryService.lift_suspension(member, action)
                messages.success(request, _('Suspension levée.'))
        except ValueError as e:
            messages.error(request, str(e))

    return redirect(f'/members/disciplinary/{action.pk}/')


# ── Profile & Modification Requests ──


@login_required
def my_profile(request):
    """Self-service profile page where user edits their own information."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        from django.http import Http404
        raise Http404

    if request.method == 'POST':
        form = MemberProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil mis à jour avec succès.'))
            return redirect('frontend:members:my_profile')
    else:
        form = MemberProfileForm(instance=member)

    pending_requests = member.modification_requests.filter(status='pending')

    context = {
        'member': member,
        'form': form,
        'pending_requests': pending_requests,
        'page_title': _('Mon profil'),
    }

    return render(request, 'members/my_profile.html', context)


@login_required
def request_modification(request, pk):
    """Staff sends a modification request to a member."""
    current_member = getattr(request.user, 'member_profile', None)
    if not current_member:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/')

    if not (request.user.is_staff or current_member.role in Roles.STAFF_ROLES):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('frontend:members:member_detail', pk=pk)

    target_member = get_object_or_404(Member, pk=pk)

    if request.method == 'POST':
        form = ProfileModificationRequestForm(request.POST)
        if form.is_valid():
            mod_request = form.save(commit=False)
            mod_request.target_member = target_member
            mod_request.requested_by = current_member
            mod_request.save()
            messages.success(
                request,
                _('Demande de modification envoyée à %(name)s.') % {
                    'name': target_member.full_name
                }
            )
            return redirect('frontend:members:member_detail', pk=pk)
    else:
        form = ProfileModificationRequestForm()

    context = {
        'form': form,
        'target_member': target_member,
        'page_title': _('Demander une modification'),
    }

    return render(request, 'members/request_modification.html', context)


@login_required
def complete_modification_request(request, pk):
    """Mark a modification request as completed (target member only)."""
    mod_request = get_object_or_404(ProfileModificationRequest, pk=pk)
    member = getattr(request.user, 'member_profile', None)

    if not member or member.id != mod_request.target_member_id:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/')

    if request.method == 'POST':
        mod_request.status = 'completed'
        mod_request.completed_at = timezone.now()
        mod_request.save()
        messages.success(request, _('Demande marquée comme complétée.'))

    return redirect('frontend:members:my_profile')



# ==============================================================================
# Group CRUD views
# ==============================================================================


@login_required
def group_create(request):
    """Create a new group (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/groups/')

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Groupe créé avec succès.'))
            return redirect('/members/groups/')
    else:
        form = GroupForm()

    context = {
        'form': form,
        'page_title': _('Nouveau groupe'),
    }
    return render(request, 'members/group_form.html', context)


@login_required
def group_edit(request, pk):
    """Edit an existing group (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/groups/')

    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, _('Groupe modifié avec succès.'))
            return redirect(f'/members/groups/{group.pk}/')
    else:
        form = GroupForm(instance=group)

    context = {
        'form': form,
        'group': group,
        'page_title': _('Modifier ') + group.name,
    }
    return render(request, 'members/group_form.html', context)


@login_required
def group_delete(request, pk):
    """Delete a group (staff only, POST confirmation)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/groups/')

    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        group.delete()
        messages.success(request, _('Groupe supprimé avec succès.'))
        return redirect('/members/groups/')

    context = {
        'group': group,
        'page_title': _('Supprimer le groupe'),
    }
    return render(request, 'members/group_delete.html', context)


@login_required
def group_add_member(request, pk):
    """Add a member to a group (staff or group leader)."""
    group = get_object_or_404(Group, pk=pk)

    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/groups/{pk}/')

    is_leader = group.leader == member
    if not _is_staff(member) and not is_leader:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/groups/{pk}/')

    if request.method == 'POST':
        form = GroupMembershipForm(request.POST, group=group)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.group = group
            membership.save()
            messages.success(request, _('Membre ajouté au groupe.'))
            return redirect(f'/members/groups/{pk}/')
    else:
        form = GroupMembershipForm(group=group)

    context = {
        'form': form,
        'group': group,
        'page_title': _('Ajouter un membre'),
    }
    return render(request, 'members/group_add_member.html', context)


@login_required
@require_POST
def group_remove_member(request, pk, membership_pk):
    """Remove a member from a group (staff or group leader, POST only)."""
    group = get_object_or_404(Group, pk=pk)

    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/groups/{pk}/')

    is_leader = group.leader == member
    if not _is_staff(member) and not is_leader:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/groups/{pk}/')

    membership = get_object_or_404(GroupMembership, pk=membership_pk, group=group)
    membership.delete()
    messages.success(request, _('Membre retiré du groupe.'))
    return redirect(f'/members/groups/{pk}/')



# ==============================================================================
# Family CRUD views
# ==============================================================================


@login_required
def family_list(request):
    """List all families."""
    families = Family.objects.all().order_by('name')
    search = request.GET.get('search', '').strip()

    if search:
        families = families.filter(
            Q(name__icontains=search) |
            Q(city__icontains=search)
        )

    context = {
        'families': families,
        'search': search,
        'page_title': _('Familles'),
    }
    return render(request, 'members/family_list.html', context)


@login_required
def family_create(request):
    """Create a new family (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/families/')

    if request.method == 'POST':
        form = FamilyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Famille créée avec succès.'))
            return redirect('/members/families/')
    else:
        form = FamilyForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle famille'),
    }
    return render(request, 'members/family_form.html', context)


@login_required
def family_edit(request, pk):
    """Edit an existing family (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/families/')

    family = get_object_or_404(Family, pk=pk)

    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, _('Famille modifiée avec succès.'))
            return redirect(f'/members/families/{family.pk}/')
    else:
        form = FamilyForm(instance=family)

    context = {
        'form': form,
        'family': family,
        'page_title': _('Modifier ') + family.name,
    }
    return render(request, 'members/family_form.html', context)


@login_required
def family_delete(request, pk):
    """Delete a family (staff only, POST confirmation)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/families/')

    family = get_object_or_404(Family, pk=pk)

    if request.method == 'POST':
        family.delete()
        messages.success(request, _('Famille supprimée avec succès.'))
        return redirect('/members/families/')

    context = {
        'family': family,
        'page_title': _('Supprimer la famille'),
    }
    return render(request, 'members/family_delete.html', context)



# ==============================================================================
# Department delete & remove member views
# ==============================================================================


@login_required
def department_delete(request, pk):
    """Delete a department (admin/pastor only, POST confirmation)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/departments/')

    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        department.delete()
        messages.success(request, _('Département supprimé avec succès.'))
        return redirect('/members/departments/')

    context = {
        'department': department,
        'page_title': _('Supprimer le département'),
    }
    return render(request, 'members/department_delete.html', context)


@login_required
@require_POST
def department_remove_member(request, pk, membership_pk):
    """Remove a member from a department (admin/pastor/dept leader, POST only)."""
    department = get_object_or_404(Department, pk=pk)

    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/departments/{pk}/')

    is_dept_leader = department.leader == member
    if member.role not in [Roles.ADMIN, Roles.PASTOR] and not is_dept_leader:
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/departments/{pk}/')

    membership = get_object_or_404(DepartmentMembership, pk=membership_pk, department=department)
    membership.delete()
    messages.success(request, _('Membre retiré du département.'))
    return redirect(f'/members/departments/{pk}/')


# ==============================================================================
# Modification request list & Member export
# ==============================================================================


@login_required
def modification_request_list(request):
    """List all pending profile modification requests (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    status_filter = request.GET.get('status', 'pending')
    requests_qs = ProfileModificationRequest.objects.select_related(
        'target_member', 'requested_by'
    ).order_by('-created_at')

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    paginator = Paginator(requests_qs, 20)
    page = request.GET.get('page', 1)
    requests_page = paginator.get_page(page)

    context = {
        'requests': requests_page,
        'status_filter': status_filter,
        'page_title': _('Demandes de modification'),
    }
    return render(request, 'members/modification_request_list.html', context)


@login_required
def member_list_export(request):
    """Export member list to CSV/Excel/PDF (pastor/admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    members = Member.objects.filter(is_active=True).order_by('last_name', 'first_name')

    fields = [
        'member_number',
        'first_name',
        'last_name',
        'email',
        'phone',
        'birth_date',
        'role',
        'family_status',
        'address',
        'city',
        'province',
        'postal_code',
        'joined_date',
        'membership_status',
    ]

    headers = [
        'Numéro de membre',
        'Prénom',
        'Nom',
        'Courriel',
        'Téléphone',
        'Date de naissance',
        'Rôle',
        'État civil',
        'Adresse',
        'Ville',
        'Province',
        'Code postal',
        "Date d'adhésion",
        'Statut',
    ]

    export_format = request.GET.get('format', 'csv')

    if export_format == 'excel':
        return export_queryset_excel(members, fields, 'membres', headers=headers)
    elif export_format == 'pdf':
        return export_queryset_pdf(members, fields, 'membres', headers=headers)

    return export_queryset_csv(members, fields, 'membres', headers=headers)


# ==============================================================================
# Child / Dependent CRUD views
# ==============================================================================


@login_required
def child_list(request, family_pk):
    """List children for a family."""
    family = get_object_or_404(Family, pk=family_pk)
    children = family.children.filter(is_active=True)

    context = {
        'family': family,
        'children': children,
        'page_title': _('Enfants - ') + family.name,
    }
    return render(request, 'members/child_list.html', context)


@login_required
def child_create(request, family_pk):
    """Create a new child profile in a family."""
    family = get_object_or_404(Family, pk=family_pk)

    member = getattr(request.user, 'member_profile', None)
    if not member or (not _is_staff(member) and member.family != family):
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/families/{family_pk}/')

    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            child.family = family
            child.save()
            messages.success(request, _('Enfant ajouté avec succès.'))
            return redirect(f'/members/families/{family_pk}/')
    else:
        form = ChildForm(initial={'family': family})

    context = {
        'form': form,
        'family': family,
        'page_title': _('Ajouter un enfant'),
    }
    return render(request, 'members/child_form.html', context)


@login_required
def child_edit(request, pk):
    """Edit a child profile."""
    child = get_object_or_404(Child, pk=pk)

    member = getattr(request.user, 'member_profile', None)
    if not member or (not _is_staff(member) and member.family != child.family):
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/families/{child.family_id}/')

    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil enfant modifié avec succès.'))
            return redirect(f'/members/families/{child.family_id}/')
    else:
        form = ChildForm(instance=child)

    context = {
        'form': form,
        'child': child,
        'page_title': _('Modifier ') + child.full_name,
    }
    return render(request, 'members/child_form.html', context)


@login_required
def child_delete(request, pk):
    """Delete a child profile (POST confirmation)."""
    child = get_object_or_404(Child, pk=pk)

    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/families/{child.family_id}/')

    if request.method == 'POST':
        family_pk = child.family_id
        child.delete()
        messages.success(request, _('Enfant supprimé.'))
        return redirect(f'/members/families/{family_pk}/')

    context = {
        'child': child,
        'page_title': _('Supprimer l\'enfant'),
    }
    return render(request, 'members/child_delete.html', context)


# ==============================================================================
# Pastoral Care CRUD views
# ==============================================================================


@login_required
def care_list(request):
    """List all pastoral care records (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    cares = PastoralCare.objects.filter(is_active=True).select_related(
        'member', 'assigned_to'
    )

    status_filter = request.GET.get('status')
    if status_filter:
        cares = cares.filter(status=status_filter)

    care_type_filter = request.GET.get('care_type')
    if care_type_filter:
        cares = cares.filter(care_type=care_type_filter)

    paginator = Paginator(cares, 20)
    page = request.GET.get('page', 1)
    cares_page = paginator.get_page(page)

    context = {
        'cares': cares_page,
        'status_filter': status_filter or '',
        'care_type_filter': care_type_filter or '',
        'page_title': _('Soins pastoraux'),
    }
    return render(request, 'members/care_list.html', context)


@login_required
def care_create(request):
    """Create a new pastoral care record (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    if request.method == 'POST':
        form = PastoralCareForm(request.POST)
        if form.is_valid():
            care = form.save(commit=False)
            if not care.assigned_to:
                care.assigned_to = member
            care.save()
            messages.success(request, _('Soin pastoral créé.'))
            return redirect(f'/members/care/{care.pk}/')
    else:
        form = PastoralCareForm(initial={
            'assigned_to': member,
            'date': timezone.now().date(),
        })

    context = {
        'form': form,
        'page_title': _('Nouveau soin pastoral'),
    }
    return render(request, 'members/care_form.html', context)


@login_required
def care_detail(request, pk):
    """View pastoral care record details (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    care = get_object_or_404(
        PastoralCare.objects.select_related('member', 'assigned_to'),
        pk=pk
    )

    context = {
        'care': care,
        'page_title': str(care),
    }
    return render(request, 'members/care_detail.html', context)


@login_required
def care_edit(request, pk):
    """Edit a pastoral care record (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    care = get_object_or_404(PastoralCare, pk=pk)

    if request.method == 'POST':
        form = PastoralCareForm(request.POST, instance=care)
        if form.is_valid():
            form.save()
            messages.success(request, _('Soin pastoral modifié.'))
            return redirect(f'/members/care/{care.pk}/')
    else:
        form = PastoralCareForm(instance=care)

    context = {
        'form': form,
        'care': care,
        'page_title': _('Modifier le soin pastoral'),
    }
    return render(request, 'members/care_form.html', context)


@login_required
def care_dashboard(request):
    """Pastoral care dashboard for pastors."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    from datetime import date

    open_cares = PastoralCare.objects.filter(
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
        is_active=True,
    ).select_related('member', 'assigned_to')

    overdue = open_cares.filter(follow_up_date__lt=date.today())
    recent = PastoralCare.objects.filter(is_active=True).select_related(
        'member', 'assigned_to'
    ).order_by('-date')[:10]

    my_cares = open_cares.filter(assigned_to=member)

    context = {
        'open_count': open_cares.count(),
        'overdue_cares': overdue,
        'recent_cares': recent,
        'my_cares': my_cares,
        'page_title': _('Tableau de bord pastoral'),
    }
    return render(request, 'members/care_dashboard.html', context)


# ==============================================================================
# Background Check views
# ==============================================================================


@login_required
def background_check_list(request):
    """List all background checks (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    checks = BackgroundCheck.objects.filter(is_active=True).select_related('member')

    status_filter = request.GET.get('status')
    if status_filter:
        checks = checks.filter(status=status_filter)

    paginator = Paginator(checks, 20)
    page = request.GET.get('page', 1)
    checks_page = paginator.get_page(page)

    context = {
        'checks': checks_page,
        'status_filter': status_filter or '',
        'page_title': _('Vérifications des antécédents'),
    }
    return render(request, 'members/background_check_list.html', context)


@login_required
def background_check_create(request):
    """Create a new background check record (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    if request.method == 'POST':
        form = BackgroundCheckForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Vérification créée.'))
            return redirect('/members/background-checks/')
    else:
        form = BackgroundCheckForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle vérification'),
    }
    return render(request, 'members/background_check_form.html', context)


@login_required
def background_check_detail(request, pk):
    """View background check details (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    check = get_object_or_404(BackgroundCheck.objects.select_related('member'), pk=pk)

    context = {
        'check': check,
        'page_title': str(check),
    }
    return render(request, 'members/background_check_detail.html', context)


@login_required
def background_check_edit(request, pk):
    """Edit a background check record (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    check = get_object_or_404(BackgroundCheck, pk=pk)

    if request.method == 'POST':
        form = BackgroundCheckForm(request.POST, instance=check)
        if form.is_valid():
            form.save()
            messages.success(request, _('Vérification modifiée.'))
            return redirect(f'/members/background-checks/{check.pk}/')
    else:
        form = BackgroundCheckForm(instance=check)

    context = {
        'form': form,
        'check': check,
        'page_title': _('Modifier la vérification'),
    }
    return render(request, 'members/background_check_form.html', context)


# ==============================================================================
# Member Import Wizard views
# ==============================================================================


@login_required
def import_upload(request):
    """Step 1: Upload CSV/Excel file for member import."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    if request.method == 'POST':
        form = MemberImportForm(request.POST, request.FILES)
        if form.is_valid():
            from .services_import import MemberImportService
            try:
                uploaded_file = request.FILES['file']
                headers, rows = MemberImportService.parse_file(uploaded_file)
                request.session['import_headers'] = headers
                request.session['import_rows'] = rows
                request.session['import_filename'] = uploaded_file.name
                return redirect('/members/import/map/')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = MemberImportForm()

    context = {
        'form': form,
        'page_title': _('Importer des membres - Étape 1'),
    }
    return render(request, 'members/import_upload.html', context)


@login_required
def import_map(request):
    """Step 2: Map CSV columns to member fields."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    headers = request.session.get('import_headers')
    if not headers:
        messages.error(request, _('Aucun fichier à importer.'))
        return redirect('/members/import/')

    if request.method == 'POST':
        form = MemberImportMappingForm(request.POST, csv_columns=headers)
        if form.is_valid():
            mapping = {}
            for col in headers:
                field_key = f'col_{col}'
                if field_key in form.cleaned_data:
                    mapping[col] = form.cleaned_data[field_key]
            request.session['import_mapping'] = mapping
            return redirect('/members/import/preview/')
    else:
        form = MemberImportMappingForm(csv_columns=headers)

    context = {
        'form': form,
        'headers': headers,
        'page_title': _('Importer des membres - Étape 2'),
    }
    return render(request, 'members/import_map.html', context)


@login_required
def import_preview(request):
    """Step 3: Preview import results and confirm."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    rows = request.session.get('import_rows')
    mapping = request.session.get('import_mapping')
    if not rows or not mapping:
        messages.error(request, _('Données manquantes.'))
        return redirect('/members/import/')

    from .services_import import MemberImportService
    preview = MemberImportService.validate_preview(rows, mapping)
    valid_count = sum(1 for r in preview if r['valid'])
    error_count = sum(1 for r in preview if not r['valid'])

    if request.method == 'POST':
        # Execute import
        history = MemberImportService.execute_import(preview, imported_by=member)
        history.filename = request.session.get('import_filename', 'import')
        history.save()

        # Clean up session
        for key in ['import_headers', 'import_rows', 'import_mapping', 'import_filename']:
            request.session.pop(key, None)

        messages.success(
            request,
            _('Importation terminée: %(success)d réussis, %(errors)d erreurs.') % {
                'success': history.success_count,
                'errors': history.error_count,
            }
        )
        return redirect('/members/import/history/')

    context = {
        'preview': preview[:50],  # Show first 50 rows
        'valid_count': valid_count,
        'error_count': error_count,
        'total': len(preview),
        'page_title': _('Importer des membres - Aperçu'),
    }
    return render(request, 'members/import_preview.html', context)


@login_required
def import_history(request):
    """View import history."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    history = ImportHistory.objects.filter(is_active=True).select_related(
        'imported_by'
    ).order_by('-created_at')

    context = {
        'history': history,
        'page_title': _('Historique d\'importation'),
    }
    return render(request, 'members/import_history.html', context)


# ==============================================================================
# Member Merge & Dedup views
# ==============================================================================


@login_required
def merge_find_duplicates(request):
    """Find potential duplicate members (admin/pastor only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    from .services_merge import MemberMergeService
    duplicates = MemberMergeService.find_duplicates()

    context = {
        'duplicates': duplicates,
        'page_title': _('Doublons potentiels'),
    }
    return render(request, 'members/merge_duplicates.html', context)


@login_required
def merge_wizard(request, pk_a, pk_b):
    """Merge wizard: select primary record and confirm merge."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    member_a = get_object_or_404(Member, pk=pk_a)
    member_b = get_object_or_404(Member, pk=pk_b)

    if request.method == 'POST':
        primary_pk = request.POST.get('primary')
        if str(primary_pk) == str(pk_a):
            primary, secondary = member_a, member_b
        else:
            primary, secondary = member_b, member_a

        from .services_merge import MemberMergeService
        log = MemberMergeService.merge_members(primary, secondary, merged_by=member)
        messages.success(
            request,
            _('Fusion réussie. %(secondary)s a été fusionné dans %(primary)s.') % {
                'primary': primary.full_name,
                'secondary': secondary.full_name,
            }
        )
        return redirect(f'/members/{primary.pk}/')

    context = {
        'member_a': member_a,
        'member_b': member_b,
        'page_title': _('Fusionner des membres'),
    }
    return render(request, 'members/merge_wizard.html', context)


@login_required
def merge_history(request):
    """View merge audit trail."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/')

    logs = MemberMergeLog.objects.filter(is_active=True).select_related(
        'primary_member', 'merged_by'
    ).order_by('-created_at')

    context = {
        'logs': logs,
        'page_title': _('Historique de fusion'),
    }
    return render(request, 'members/merge_history.html', context)


# ==============================================================================
# Group Finder & Lifecycle views
# ==============================================================================


@login_required
def group_finder(request):
    """Public group finder for members to search for groups."""
    form = GroupFinderForm(request.GET)

    groups = Group.objects.filter(
        is_active=True,
        lifecycle_stage__in=['launching', 'active'],
    ).select_related('leader')

    search = request.GET.get('search', '').strip()
    if search:
        groups = groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    group_type = request.GET.get('group_type')
    if group_type:
        groups = groups.filter(group_type=group_type)

    meeting_day = request.GET.get('meeting_day', '').strip()
    if meeting_day:
        groups = groups.filter(meeting_day__icontains=meeting_day)

    context = {
        'groups': groups,
        'form': form,
        'search': search,
        'page_title': _('Trouver un groupe'),
    }
    return render(request, 'members/group_finder.html', context)


# ==============================================================================
# Custom Fields management views
# ==============================================================================


@login_required
def custom_field_list(request):
    """Manage custom member fields (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role != Roles.ADMIN:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    fields = CustomField.objects.filter(is_active=True)

    context = {
        'custom_fields': fields,
        'page_title': _('Champs personnalisés'),
    }
    return render(request, 'members/custom_field_list.html', context)


@login_required
def custom_field_create(request):
    """Create a new custom field (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role != Roles.ADMIN:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    if request.method == 'POST':
        form = CustomFieldForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Champ personnalisé créé.'))
            return redirect('/members/custom-fields/')
    else:
        form = CustomFieldForm()

    context = {
        'form': form,
        'page_title': _('Nouveau champ personnalisé'),
    }
    return render(request, 'members/custom_field_form.html', context)


@login_required
def custom_field_edit(request, pk):
    """Edit a custom field (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role != Roles.ADMIN:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    field = get_object_or_404(CustomField, pk=pk)

    if request.method == 'POST':
        form = CustomFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, _('Champ personnalisé modifié.'))
            return redirect('/members/custom-fields/')
    else:
        form = CustomFieldForm(instance=field)

    context = {
        'form': form,
        'field': field,
        'page_title': _('Modifier le champ personnalisé'),
    }
    return render(request, 'members/custom_field_form.html', context)


@login_required
@require_POST
def custom_field_delete(request, pk):
    """Delete a custom field (admin only, POST)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role != Roles.ADMIN:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    field = get_object_or_404(CustomField, pk=pk)
    field.is_active = False
    field.save()
    messages.success(request, _('Champ personnalisé supprimé.'))
    return redirect('/members/custom-fields/')


# ==============================================================================
# Member Engagement Score views
# ==============================================================================


@login_required
def engagement_dashboard(request):
    """View engagement scores for all members (staff only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/reports/')

    scores = MemberEngagementScore.objects.filter(
        member__is_active=True
    ).select_related('member').order_by('-total_score')

    # At-risk members (score < 30)
    at_risk = scores.filter(total_score__lt=30)

    paginator = Paginator(scores, 20)
    page = request.GET.get('page', 1)
    scores_page = paginator.get_page(page)

    context = {
        'scores': scores_page,
        'at_risk_count': at_risk.count(),
        'total_count': scores.count(),
        'page_title': _('Scores d\'engagement'),
    }
    return render(request, 'members/engagement_dashboard.html', context)


@login_required
def engagement_recalculate(request):
    """Trigger recalculation of engagement scores (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/engagement/')

    if request.method == 'POST':
        from .services_engagement import EngagementScoreService
        scores = EngagementScoreService.calculate_for_all()
        messages.success(
            request,
            _('%(count)d scores recalculés.') % {'count': len(scores)}
        )

    return redirect('/members/engagement/')


# ==============================================================================
# Church Directory (opt-in public)
# ==============================================================================


@login_required
def directory_public(request):
    """Opt-in public directory with photo grid view."""
    search = request.GET.get('search', '').strip()
    view_mode = request.GET.get('view', 'grid')
    group_filter = request.GET.get('group')
    page = request.GET.get('page', 1)

    members = Member.objects.filter(
        is_active=True,
        privacy_settings__visibility='public',
        privacy_settings__show_photo=True,
    ).select_related('privacy_settings')

    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    if group_filter:
        members = members.filter(group_memberships__group_id=group_filter)

    members = members.order_by('last_name', 'first_name')

    paginator = Paginator(members, 24)
    members_page = paginator.get_page(page)

    context = {
        'members': members_page,
        'search': search,
        'view_mode': view_mode,
        'groups': Group.objects.filter(is_active=True),
        'page_title': _('Annuaire public'),
    }
    return render(request, 'members/directory_public.html', context)


@login_required
def directory_export_pdf(request):
    """Export public directory to PDF."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/directory/')

    members = Member.objects.filter(
        is_active=True,
    ).order_by('last_name', 'first_name')

    fields = ['first_name', 'last_name', 'email', 'phone']
    headers = ['Prénom', 'Nom', 'Courriel', 'Téléphone']

    return export_queryset_pdf(members, fields, 'annuaire', headers=headers)


# ==============================================================================
# Family Dashboard & Merge
# ==============================================================================


@login_required
def family_dashboard(request, pk):
    """Family dashboard showing members, giving summary, attendance."""
    family = get_object_or_404(Family, pk=pk)
    members = family.members.filter(is_active=True)
    children = family.children.filter(is_active=True)

    context = {
        'family': family,
        'members': members,
        'children': children,
        'page_title': _('Tableau de bord - ') + family.name,
    }
    return render(request, 'members/family_dashboard.html', context)


@login_required
def family_merge(request):
    """Merge two families (admin/pastor only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in [Roles.PASTOR, Roles.ADMIN]:
        messages.error(request, _('Accès non autorisé.'))
        return redirect('/members/families/')

    if request.method == 'POST':
        family_a_pk = request.POST.get('family_a')
        family_b_pk = request.POST.get('family_b')

        if family_a_pk and family_b_pk and family_a_pk != family_b_pk:
            family_a = get_object_or_404(Family, pk=family_a_pk)
            family_b = get_object_or_404(Family, pk=family_b_pk)

            # Move all members from family_b to family_a
            family_b.members.update(family=family_a)
            # Move children
            family_b.children.update(family=family_a)

            # Merge address if family_a has none
            if not family_a.address and family_b.address:
                family_a.address = family_b.address
                family_a.city = family_b.city
                family_a.province = family_b.province
                family_a.postal_code = family_b.postal_code
                family_a.save()

            # Deactivate family_b
            family_b.is_active = False
            family_b.save()

            messages.success(
                request,
                _('%(b)s a été fusionnée dans %(a)s.') % {
                    'a': family_a.name, 'b': family_b.name,
                }
            )
            return redirect(f'/members/families/{family_a.pk}/')
        else:
            messages.error(request, _('Veuillez sélectionner deux familles différentes.'))

    families = Family.objects.filter(is_active=True)

    context = {
        'families': families,
        'page_title': _('Fusionner des familles'),
    }
    return render(request, 'members/family_merge.html', context)


@login_required
def family_sync_address(request, pk):
    """Sync family address to all member addresses."""
    member = getattr(request.user, 'member_profile', None)
    if not member or not _is_staff(member):
        messages.error(request, _('Accès non autorisé.'))
        return redirect(f'/members/families/{pk}/')

    family = get_object_or_404(Family, pk=pk)

    if request.method == 'POST':
        family.members.filter(is_active=True).update(
            address=family.address,
            city=family.city,
            province=family.province,
            postal_code=family.postal_code,
        )
        messages.success(request, _('Adresse synchronisée pour tous les membres.'))

    return redirect(f'/members/families/{pk}/')
