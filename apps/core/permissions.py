"""DRF permission classes for role-based access control."""
from rest_framework import permissions

from .constants import Roles


class IsMember(permissions.BasePermission):
    """Allows any authenticated user."""
    message = "Vous devez être un membre pour accéder à cette ressource."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsVolunteer(permissions.BasePermission):
    """Requires volunteer role or higher."""
    message = "Vous devez être un volontaire pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = {
                Roles.VOLUNTEER, Roles.GROUP_LEADER, Roles.DEACON,
                Roles.PASTOR, Roles.TREASURER, Roles.ADMIN,
            }
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_staff


class IsGroupLeader(permissions.BasePermission):
    """Requires group_leader role or higher."""
    message = "Vous devez être un leader de groupe pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = {
                Roles.GROUP_LEADER, Roles.DEACON,
                Roles.PASTOR, Roles.ADMIN,
            }
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_staff


class IsDeacon(permissions.BasePermission):
    """Requires deacon role or higher."""
    message = "Vous devez être diacre pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = {Roles.DEACON, Roles.PASTOR, Roles.ADMIN}
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_staff


class IsPastor(permissions.BasePermission):
    """Requires pastor role or admin."""
    message = "Vous devez être un pasteur pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = {Roles.PASTOR, Roles.ADMIN}
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_staff


class IsTreasurer(permissions.BasePermission):
    """Requires treasurer role or admin."""
    message = "Vous devez être trésorier pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = {Roles.TREASURER, Roles.PASTOR, Roles.ADMIN}
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_staff


class IsAdmin(permissions.BasePermission):
    """Requires admin role, pastor role, or superuser."""
    message = "Vous devez être administrateur pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = {Roles.PASTOR, Roles.ADMIN}
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_superuser


class IsPastorOrAdmin(permissions.BasePermission):
    """Requires pastor or admin role."""
    message = "Vous devez être pasteur ou administrateur pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            allowed = set(Roles.STAFF_ROLES)
            return bool(request.user.member_profile.all_roles & allowed)

        return request.user.is_staff or request.user.is_superuser


class IsFinanceStaff(permissions.BasePermission):
    """Requires finance access: treasurer, pastor, admin, or delegated."""
    message = "Vous devez avoir accès aux finances pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            member = request.user.member_profile
            if bool(member.all_roles & set(Roles.FINANCE_ROLES)):
                return True
            # Check finance delegation
            from apps.donations.models import FinanceDelegation
            return FinanceDelegation.objects.filter(
                delegated_to=member, is_active=True, revoked_at__isnull=True
            ).exists()

        return request.user.is_staff


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Object-level: allows owner (via obj.user or obj.member) or staff.
    """
    message = "Vous n'avez pas la permission de modifier cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if hasattr(request.user, 'member_profile'):
            if bool(request.user.member_profile.all_roles & set(Roles.STAFF_ROLES)):
                return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'member'):
            if hasattr(request.user, 'member_profile'):
                return obj.member == request.user.member_profile

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level: read for all, write only for owner or staff."""
    message = "Vous n'avez pas la permission de modifier cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        if hasattr(request.user, 'member_profile'):
            if bool(request.user.member_profile.all_roles & set(Roles.STAFF_ROLES)):
                return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'member'):
            if hasattr(request.user, 'member_profile'):
                return obj.member == request.user.member_profile

        return False


class CanViewMember(permissions.BasePermission):
    """Object-level: checks privacy settings (public/group/private) for member profiles."""
    message = "Vous n'avez pas la permission de voir ce profil."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_staff:
            return True

        if not hasattr(user, 'member_profile'):
            return False

        member = user.member_profile

        if bool(member.all_roles & {Roles.PASTOR, Roles.ADMIN}):
            return True

        # Always allow viewing own profile
        if obj == member:
            return True

        if hasattr(obj, 'privacy_settings'):
            privacy = obj.privacy_settings

            if privacy.visibility == 'public':
                return True

            if privacy.visibility == 'group':
                # Allow if they share any group
                user_groups = set(member.groups.values_list('id', flat=True))
                obj_groups = set(obj.groups.values_list('id', flat=True))
                return bool(user_groups & obj_groups)

            # 'private' - staff only (handled above)
            return False

        # No privacy settings = public by default
        return True


def get_user_role(user):
    """Get primary role string for user. Superusers are ADMIN, staff without profile are PASTOR."""
    if user.is_superuser:
        return Roles.ADMIN

    if hasattr(user, 'member_profile'):
        return user.member_profile.role

    if user.is_staff:
        return Roles.PASTOR

    return None


def is_staff_member(user):
    """Check if user has staff-level access (deacon, pastor, or admin)."""
    if user.is_staff or user.is_superuser:
        return True

    if hasattr(user, 'member_profile'):
        return bool(user.member_profile.all_roles & set(Roles.STAFF_ROLES))

    return False


def can_manage_finances(user):
    """Check if user can access financial data."""
    if user.is_superuser:
        return True

    if hasattr(user, 'member_profile'):
        return bool(user.member_profile.all_roles & set(Roles.FINANCE_ROLES))

    return False
