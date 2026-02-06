"""View mixins for permissions, context, and form handling."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .constants import Roles
from .permissions import get_user_role


class MemberRequiredMixin(LoginRequiredMixin):
    """Requires user to have a member profile. Redirects to profile creation if missing."""
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not hasattr(request.user, 'member_profile'):
            messages.error(request, _("Vous devez avoir un profil membre pour accéder à cette page."))
            return redirect('frontend:members:member_create')

        return super().dispatch(request, *args, **kwargs)


class VolunteerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Requires volunteer role or higher (group_leader, pastor, treasurer, admin)."""
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
    """Requires group_leader role or higher."""
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
    """Requires pastor role or admin."""
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
    """Requires treasurer role or admin."""
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
    """Requires admin role or superuser."""
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
    """Requires finance access: treasurer, pastor, or admin."""
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


class OwnerOrStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Requires user to own the object or be staff.
    Object ownership checked via 'user' or 'member' attribute.
    """
    login_url = '/accounts/login/'

    def test_func(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return True

        if hasattr(user, 'member_profile'):
            if user.member_profile.role in Roles.STAFF_ROLES:
                return True

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


class ChurchContextMixin:
    """Adds current_user_role, current_member, and today_birthdays (for staff) to context."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['current_user_role'] = get_user_role(self.request.user)

            if hasattr(self.request.user, 'member_profile'):
                context['current_member'] = self.request.user.member_profile
        else:
            context['current_user_role'] = None
            context['current_member'] = None

        # Staff see today's birthdays in navbar
        if self.request.user.is_authenticated:
            role = context.get('current_user_role')
            if role in [Roles.PASTOR, Roles.ADMIN, Roles.GROUP_LEADER]:
                from .utils import get_today_birthdays
                context['today_birthdays'] = get_today_birthdays()[:5]

        return context


class PageTitleMixin:
    """Adds page_title to context. Set page_title attr or override get_page_title()."""
    page_title = None

    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        return context


class BreadcrumbMixin:
    """Adds breadcrumbs to context. Override get_breadcrumbs() -> [(label, url), ...]."""

    def get_breadcrumbs(self):
        """Return list of (label, url) tuples. Last item's url should be None."""
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


class FormMessageMixin:
    """Shows success/error messages on form submission."""
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
    """Auto-sets member/user/created_by on form save if not already set."""

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


class FilterByMemberMixin:
    """Filters queryset to current user's objects. Staff/admin see all."""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return queryset

        if hasattr(user, 'member_profile'):
            if user.member_profile.role in Roles.STAFF_ROLES:
                return queryset

            if hasattr(queryset.model, 'member'):
                return queryset.filter(member=user.member_profile)

        return queryset.none()
