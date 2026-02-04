"""
Core mixins - View mixins for ÉgliseConnect.

This module provides mixins for Django views that handle
permissions, context data, and common functionality.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .constants import Roles
from .permissions import get_user_role


# =============================================================================
# PERMISSION MIXINS
# =============================================================================

class MemberRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires the user to be an authenticated member.
    """
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not hasattr(request.user, 'member_profile'):
            messages.error(request, _("Vous devez avoir un profil membre pour accéder à cette page."))
            return redirect('frontend:members:member_create')

        return super().dispatch(request, *args, **kwargs)


class VolunteerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be a volunteer or higher.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user
        if user.is_staff:
            return True

        if hasattr(user, 'member_profile'):
            return user.member_profile.role in [
                Roles.VOLUNTEER,
                Roles.GROUP_LEADER,
                Roles.PASTOR,
                Roles.TREASURER,
                Roles.ADMIN,
            ]
        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être volontaire pour accéder à cette page."))
        if hasattr(self.request.user, 'member_profile'):
            return redirect('frontend:members:member_detail', pk=self.request.user.member_profile.pk)
        return redirect('/')


class GroupLeaderRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be a group leader or higher.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user
        if user.is_staff:
            return True

        if hasattr(user, 'member_profile'):
            return user.member_profile.role in [
                Roles.GROUP_LEADER,
                Roles.PASTOR,
                Roles.ADMIN,
            ]
        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être leader de groupe pour accéder à cette page."))
        return redirect('/')


class PastorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be a pastor or admin.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return True

        if hasattr(user, 'member_profile'):
            return user.member_profile.role in [
                Roles.PASTOR,
                Roles.ADMIN,
            ]
        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être pasteur pour accéder à cette page."))
        return redirect('/')


class TreasurerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be a treasurer or admin.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True

        if hasattr(user, 'member_profile'):
            return user.member_profile.role in [
                Roles.TREASURER,
                Roles.ADMIN,
            ]
        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être trésorier pour accéder à cette page."))
        return redirect('/')


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be an admin.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True

        if hasattr(user, 'member_profile'):
            return user.member_profile.role == Roles.ADMIN
        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être administrateur pour accéder à cette page."))
        return redirect('/')


class FinanceStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to have finance access (treasurer, pastor, admin).
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True

        if hasattr(user, 'member_profile'):
            return user.member_profile.role in [
                Roles.TREASURER,
                Roles.PASTOR,
                Roles.ADMIN,
            ]
        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas accès aux données financières."))
        return redirect('/')


# =============================================================================
# OWNERSHIP MIXINS
# =============================================================================

class OwnerOrStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be the owner of the object or staff.

    The view must implement get_object() and the object must have
    either a 'user' or 'member' attribute.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user

        # Staff can access anything
        if user.is_staff or user.is_superuser:
            return True

        # Check if user is pastor/admin
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in Roles.STAFF_ROLES:
                return True

        # Get the object and check ownership
        obj = self.get_object()

        if hasattr(obj, 'user'):
            return obj.user == user

        if hasattr(obj, 'member'):
            if hasattr(user, 'member_profile'):
                return obj.member == user.member_profile

        return False

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas la permission d'accéder à cette ressource."))
        return redirect('/')


# =============================================================================
# CONTEXT MIXINS
# =============================================================================

class ChurchContextMixin:
    """
    Mixin that adds church-related context data to views.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add user role
        if self.request.user.is_authenticated:
            context['current_user_role'] = get_user_role(self.request.user)

            if hasattr(self.request.user, 'member_profile'):
                context['current_member'] = self.request.user.member_profile
        else:
            context['current_user_role'] = None
            context['current_member'] = None

        # Add today's birthdays for staff
        if self.request.user.is_authenticated:
            role = context.get('current_user_role')
            if role in [Roles.PASTOR, Roles.ADMIN, Roles.GROUP_LEADER]:
                from .utils import get_today_birthdays
                context['today_birthdays'] = get_today_birthdays()[:5]

        return context


class PageTitleMixin:
    """
    Mixin that adds page title to context.

    Set page_title attribute on the view or override get_page_title().
    """
    page_title = None

    def get_page_title(self):
        """Return the page title."""
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        return context


class BreadcrumbMixin:
    """
    Mixin that adds breadcrumbs to context.

    Override get_breadcrumbs() to return a list of (label, url) tuples.
    """

    def get_breadcrumbs(self):
        """
        Return breadcrumbs as a list of (label, url) tuples.

        The last item should have url as None (current page).
        """
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


# =============================================================================
# FORM MIXINS
# =============================================================================

class FormMessageMixin:
    """
    Mixin that adds success/error messages for form views.
    """
    success_message = _("Opération réussie.")
    error_message = _("Une erreur s'est produite. Veuillez réessayer.")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class SetOwnerMixin:
    """
    Mixin that automatically sets the owner/member on create.

    Works with forms that have a 'member' field.
    """

    def form_valid(self, form):
        if hasattr(form.instance, 'member') and not form.instance.member_id:
            if hasattr(self.request.user, 'member_profile'):
                form.instance.member = self.request.user.member_profile

        if hasattr(form.instance, 'user') and not form.instance.user_id:
            form.instance.user = self.request.user

        if hasattr(form.instance, 'created_by') and not form.instance.created_by_id:
            if hasattr(self.request.user, 'member_profile'):
                form.instance.created_by = self.request.user.member_profile

        return super().form_valid(form)


# =============================================================================
# QUERYSET MIXINS
# =============================================================================

class FilterByMemberMixin:
    """
    Mixin that filters queryset to only show objects belonging to the current member.

    Staff members see all objects.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Staff see everything
        if user.is_staff or user.is_superuser:
            return queryset

        # Check if user is pastor/admin
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in Roles.STAFF_ROLES:
                return queryset

            # Filter by member
            if hasattr(queryset.model, 'member'):
                return queryset.filter(member=user.member_profile)

        return queryset.none()
