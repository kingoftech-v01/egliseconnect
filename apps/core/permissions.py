"""
Core permissions - Permission classes for ÉgliseConnect.

This module provides permission classes used across the application
for both DRF API views and Django views.
"""
from rest_framework import permissions

from .constants import Roles


# =============================================================================
# BASE PERMISSION CLASSES
# =============================================================================

class IsMember(permissions.BasePermission):
    """
    Permission class that allows access to any authenticated member.
    """
    message = "Vous devez être un membre pour accéder à cette ressource."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsVolunteer(permissions.BasePermission):
    """
    Permission class that allows access to volunteers and above.
    """
    message = "Vous devez être un volontaire pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a member profile with volunteer+ role
        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role in [
                Roles.VOLUNTEER,
                Roles.GROUP_LEADER,
                Roles.PASTOR,
                Roles.TREASURER,
                Roles.ADMIN,
            ]

        return request.user.is_staff


class IsGroupLeader(permissions.BasePermission):
    """
    Permission class that allows access to group leaders and above.
    """
    message = "Vous devez être un leader de groupe pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role in [
                Roles.GROUP_LEADER,
                Roles.PASTOR,
                Roles.ADMIN,
            ]

        return request.user.is_staff


class IsPastor(permissions.BasePermission):
    """
    Permission class that allows access to pastors and admins only.
    """
    message = "Vous devez être un pasteur pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role in [
                Roles.PASTOR,
                Roles.ADMIN,
            ]

        return request.user.is_staff


class IsTreasurer(permissions.BasePermission):
    """
    Permission class that allows access to treasurers and admins only.
    """
    message = "Vous devez être trésorier pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role in [
                Roles.TREASURER,
                Roles.ADMIN,
            ]

        return request.user.is_staff


class IsAdmin(permissions.BasePermission):
    """
    Permission class that allows access to admins only.
    """
    message = "Vous devez être administrateur pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role == Roles.ADMIN

        return request.user.is_superuser


class IsPastorOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to pastors and admins.
    """
    message = "Vous devez être pasteur ou administrateur pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role in Roles.STAFF_ROLES

        return request.user.is_staff or request.user.is_superuser


class IsFinanceStaff(permissions.BasePermission):
    """
    Permission class that allows access to finance staff (treasurer, pastor, admin).
    """
    message = "Vous devez avoir accès aux finances pour accéder à cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'member_profile'):
            return request.user.member_profile.role in [
                Roles.TREASURER,
                Roles.PASTOR,
                Roles.ADMIN,
            ]

        return request.user.is_staff


# =============================================================================
# OBJECT-LEVEL PERMISSION CLASSES
# =============================================================================

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Object-level permission to only allow owners or staff to access/modify.

    Assumes the model instance has an `user` or `member` attribute.
    """
    message = "Vous n'avez pas la permission de modifier cette ressource."

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True

        # Check if user is pastor/admin
        if hasattr(request.user, 'member_profile'):
            if request.user.member_profile.role in Roles.STAFF_ROLES:
                return True

        # Check ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'member'):
            if hasattr(request.user, 'member_profile'):
                return obj.member == request.user.member_profile

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit.
    Read access is allowed for all authenticated users.
    """
    message = "Vous n'avez pas la permission de modifier cette ressource."

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff can do anything
        if request.user.is_staff:
            return True

        # Check if user is pastor/admin
        if hasattr(request.user, 'member_profile'):
            if request.user.member_profile.role in Roles.STAFF_ROLES:
                return True

        # Check ownership for write permissions
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'member'):
            if hasattr(request.user, 'member_profile'):
                return obj.member == request.user.member_profile

        return False


class CanViewMember(permissions.BasePermission):
    """
    Permission to view member details based on privacy settings and role.
    """
    message = "Vous n'avez pas la permission de voir ce profil."

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Staff can see everything
        if user.is_staff:
            return True

        # Check if user has member profile
        if not hasattr(user, 'member_profile'):
            return False

        member = user.member_profile

        # Admins and pastors can see everyone
        if member.role in [Roles.PASTOR, Roles.ADMIN]:
            return True

        # User can see their own profile
        if obj == member:
            return True

        # Check privacy settings if they exist
        if hasattr(obj, 'privacy_settings'):
            privacy = obj.privacy_settings

            # Public profiles are visible to all members
            if privacy.visibility == 'public':
                return True

            # Group-level visibility
            if privacy.visibility == 'group':
                # Check if they share any groups
                user_groups = set(member.groups.values_list('id', flat=True))
                obj_groups = set(obj.groups.values_list('id', flat=True))
                return bool(user_groups & obj_groups)

            # Private profiles are only visible to staff (handled above)
            return False

        # Default: allow viewing if no privacy settings
        return True


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_user_role(user):
    """
    Get the role of a user.

    Args:
        user: Django User instance

    Returns:
        str: Role string or None if no member profile
    """
    if user.is_superuser:
        return Roles.ADMIN

    if hasattr(user, 'member_profile'):
        return user.member_profile.role

    if user.is_staff:
        return Roles.PASTOR

    return None


def is_staff_member(user):
    """
    Check if a user is a staff member (pastor, treasurer, or admin).

    Args:
        user: Django User instance

    Returns:
        bool: True if user is staff
    """
    if user.is_staff or user.is_superuser:
        return True

    if hasattr(user, 'member_profile'):
        return user.member_profile.role in [
            Roles.PASTOR,
            Roles.TREASURER,
            Roles.ADMIN,
        ]

    return False


def can_manage_finances(user):
    """
    Check if a user can manage finances.

    Args:
        user: Django User instance

    Returns:
        bool: True if user can manage finances
    """
    if user.is_superuser:
        return True

    if hasattr(user, 'member_profile'):
        return user.member_profile.role in Roles.FINANCE_ROLES

    return False
