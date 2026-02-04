"""
Members Frontend Views - Template-based views for member management.

This module provides template-based views for human users:
- List views with filtering/pagination
- Detail views with related data
- Create/Update forms
- Birthday views
- Directory views

All views render HTML templates using Django's render().
Uses HTMX for dynamic interactions and Alpine.js for client-side reactivity.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
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

from .models import Member, Family, Group, GroupMembership, DirectoryPrivacy
from .forms import (
    MemberRegistrationForm,
    MemberProfileForm,
    MemberAdminForm,
    FamilyForm,
    GroupForm,
    DirectoryPrivacyForm,
    MemberSearchForm,
)


# =============================================================================
# MEMBER LIST VIEWS
# =============================================================================

@login_required
def member_list(request):
    """
    List all members with filtering, search, and pagination.

    Accessible by pastors and admins only.

    Template: members/member_list.html
    """
    # Check permissions
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Vous n'avez pas accès à la liste des membres."))
            return redirect('frontend:members:member_detail', pk=request.user.member_profile.pk)
    elif not request.user.is_staff:
        messages.error(request, _("Vous n'avez pas accès à la liste des membres."))
        return redirect('/')

    # Get query parameters
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

    # Base queryset
    members = Member.objects.all().select_related('family')

    # Apply search
    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(member_number__icontains=search) |
            Q(phone__icontains=search)
        )

    # Apply filters
    if role_filter:
        members = members.filter(role=role_filter)

    if family_status_filter:
        members = members.filter(family_status=family_status_filter)

    if group_filter:
        members = members.filter(group_memberships__group_id=group_filter)

    # Apply sorting
    if sort_by.startswith('-'):
        members = members.order_by(sort_by, 'last_name')
    else:
        members = members.order_by(sort_by)

    # Pagination
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


# =============================================================================
# MEMBER DETAIL VIEWS
# =============================================================================

@login_required
def member_detail(request, pk):
    """
    Display detailed information for a single member.

    Members can view their own profile.
    Staff can view any profile.

    Template: members/member_detail.html
    """
    member = get_object_or_404(
        Member.objects.select_related('family'),
        pk=pk
    )

    # Check permissions
    can_view = False
    can_edit = False

    if request.user.is_staff:
        can_view = True
        can_edit = True
    elif hasattr(request.user, 'member_profile'):
        current_member = request.user.member_profile

        # Own profile
        if current_member.id == member.id:
            can_view = True
            can_edit = True
        # Staff roles
        elif current_member.role in [Roles.PASTOR, Roles.ADMIN]:
            can_view = True
            can_edit = True
        # Group leader checking group member
        elif current_member.role == Roles.GROUP_LEADER:
            led_groups = current_member.led_groups.values_list('id', flat=True)
            is_group_member = member.group_memberships.filter(
                group_id__in=led_groups
            ).exists()
            can_view = is_group_member

    if not can_view:
        messages.error(request, _("Vous n'avez pas accès à ce profil."))
        return redirect('/')

    # Get related data
    groups = member.group_memberships.filter(is_active=True).select_related('group')
    family_members = []
    if member.family:
        family_members = member.family.members.exclude(id=member.id)

    context = {
        'member': member,
        'groups': groups,
        'family_members': family_members,
        'can_edit': can_edit,
        'page_title': member.full_name,
    }

    return render(request, 'members/member_detail.html', context)


# =============================================================================
# MEMBER CREATE/UPDATE VIEWS
# =============================================================================

def member_create(request):
    """
    Create a new member (public registration).

    Template: members/member_form.html
    """
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

            # Log in if account was created
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
    """
    Update an existing member profile.

    Template: members/member_form.html
    """
    member = get_object_or_404(Member, pk=pk)

    # Check permissions
    can_edit = False
    is_admin = False

    if request.user.is_staff:
        can_edit = True
        is_admin = True
    elif hasattr(request.user, 'member_profile'):
        current_member = request.user.member_profile

        if current_member.id == member.id:
            can_edit = True
        elif current_member.role in [Roles.PASTOR, Roles.ADMIN]:
            can_edit = True
            is_admin = True

    if not can_edit:
        messages.error(request, _("Vous n'avez pas la permission de modifier ce profil."))
        return redirect('frontend:members:member_detail', pk=pk)

    # Select appropriate form
    FormClass = MemberAdminForm if is_admin else MemberProfileForm

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
        'form_title': _('Modifier le profil'),
        'submit_text': _('Enregistrer'),
        'cancel_url': 'frontend:members:member_detail',
        'page_title': _('Modifier le profil'),
    }

    return render(request, 'members/member_form.html', context)


# =============================================================================
# BIRTHDAY VIEWS
# =============================================================================

@login_required
def birthday_list(request):
    """
    List birthdays for today, this week, or this month.

    Template: members/birthday_list.html
    """
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


# =============================================================================
# DIRECTORY VIEWS
# =============================================================================

@login_required
def directory(request):
    """
    Member directory with privacy settings applied.

    Template: members/directory.html
    """
    search = request.GET.get('search', '').strip()
    page = request.GET.get('page', 1)

    # Base queryset
    members = Member.objects.filter(is_active=True).select_related('privacy_settings')

    # Apply search
    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(member_number__icontains=search)
        )

    # Filter by privacy settings
    user = request.user
    if hasattr(user, 'member_profile'):
        current_member = user.member_profile

        # Staff sees everyone
        if current_member.role not in Roles.STAFF_ROLES and not user.is_staff:
            # Get user's groups
            user_groups = set(
                current_member.group_memberships.filter(is_active=True).values_list('group_id', flat=True)
            )

            # Filter by visibility
            members = members.filter(
                Q(privacy_settings__visibility='public') |
                Q(
                    privacy_settings__visibility='group',
                    group_memberships__group_id__in=user_groups
                ) |
                Q(id=current_member.id)
            ).distinct()
    elif not user.is_staff:
        # Users without member_profile and not staff see only public profiles
        members = members.filter(privacy_settings__visibility='public')

    members = members.order_by('last_name', 'first_name')

    # Pagination
    paginator = Paginator(members, 24)
    members_page = paginator.get_page(page)

    context = {
        'members': members_page,
        'search': search,
        'total_count': paginator.count,
        'page_title': _('Annuaire'),
    }

    return render(request, 'members/directory.html', context)


# =============================================================================
# PRIVACY SETTINGS VIEWS
# =============================================================================

@login_required
def privacy_settings(request):
    """
    Manage directory privacy settings.

    Template: members/privacy_settings.html
    """
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


# =============================================================================
# GROUP VIEWS
# =============================================================================

@login_required
def group_list(request):
    """
    List all groups.

    Template: members/group_list.html
    """
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
    """
    Display group details with members.

    Template: members/group_detail.html
    """
    group = get_object_or_404(Group.objects.select_related('leader'), pk=pk)
    memberships = group.memberships.filter(is_active=True).select_related('member')

    # Check if current user is leader
    is_leader = False
    if hasattr(request.user, 'member_profile'):
        is_leader = group.leader == request.user.member_profile

    context = {
        'group': group,
        'memberships': memberships,
        'is_leader': is_leader,
        'page_title': group.name,
    }

    return render(request, 'members/group_detail.html', context)


# =============================================================================
# FAMILY VIEWS
# =============================================================================

@login_required
def family_detail(request, pk):
    """
    Display family details with members.

    Template: members/family_detail.html
    """
    family = get_object_or_404(Family, pk=pk)
    members = family.members.filter(is_active=True)

    # Check if current user is family member
    is_family_member = False
    if hasattr(request.user, 'member_profile'):
        is_family_member = request.user.member_profile.family == family

    context = {
        'family': family,
        'members': members,
        'is_family_member': is_family_member,
        'page_title': family.name,
    }

    return render(request, 'members/family_detail.html', context)
