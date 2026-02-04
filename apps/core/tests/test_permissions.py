"""
Tests for core permissions.
"""
import pytest
from django.contrib.auth import get_user_model
from unittest.mock import Mock, MagicMock

from apps.core.permissions import (
    IsMember,
    IsVolunteer,
    IsGroupLeader,
    IsPastor,
    IsTreasurer,
    IsAdmin,
    IsPastorOrAdmin,
    IsFinanceStaff,
    IsOwnerOrStaff,
    IsOwnerOrReadOnly,
    get_user_role,
    is_staff_member,
    can_manage_finances,
)
from apps.core.constants import Roles

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = Mock()
    request.user = Mock()
    request.user.is_authenticated = True
    request.user.is_staff = False
    request.user.is_superuser = False
    return request


@pytest.fixture
def mock_view():
    """Create a mock view object."""
    return Mock()


@pytest.fixture
def create_member_profile():
    """Factory to create mock member profiles with specific roles."""
    def _create(role):
        profile = Mock()
        profile.role = role
        return profile
    return _create


# =============================================================================
# IS MEMBER TESTS
# =============================================================================

class TestIsMember:
    """Tests for IsMember permission."""

    def test_authenticated_user_allowed(self, mock_request, mock_view):
        """Test that authenticated users are allowed."""
        permission = IsMember()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_unauthenticated_user_denied(self, mock_request, mock_view):
        """Test that unauthenticated users are denied."""
        mock_request.user.is_authenticated = False
        permission = IsMember()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_no_user_denied(self, mock_view):
        """Test that requests without user are denied."""
        request = Mock()
        request.user = None
        permission = IsMember()
        assert permission.has_permission(request, mock_view) is False


# =============================================================================
# IS VOLUNTEER TESTS
# =============================================================================

class TestIsVolunteer:
    """Tests for IsVolunteer permission."""

    def test_volunteer_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that volunteers are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_member_denied(self, mock_request, mock_view, create_member_profile):
        """Test that regular members are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_group_leader_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that group leaders are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_staff_allowed(self, mock_request, mock_view):
        """Test that staff users are allowed."""
        mock_request.user.is_staff = True
        delattr(mock_request.user, 'member_profile') if hasattr(mock_request.user, 'member_profile') else None
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True


# =============================================================================
# IS GROUP LEADER TESTS
# =============================================================================

class TestIsGroupLeader:
    """Tests for IsGroupLeader permission."""

    def test_group_leader_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that group leaders are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_volunteer_denied(self, mock_request, mock_view, create_member_profile):
        """Test that volunteers are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is True


# =============================================================================
# IS PASTOR TESTS
# =============================================================================

class TestIsPastor:
    """Tests for IsPastor permission."""

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsPastor()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_group_leader_denied(self, mock_request, mock_view, create_member_profile):
        """Test that group leaders are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsPastor()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsPastor()
        assert permission.has_permission(mock_request, mock_view) is True


# =============================================================================
# IS TREASURER TESTS
# =============================================================================

class TestIsTreasurer:
    """Tests for IsTreasurer permission."""

    def test_treasurer_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that treasurers are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        permission = IsTreasurer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_denied(self, mock_request, mock_view, create_member_profile):
        """Test that pastors are denied (for treasurer-only resources)."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsTreasurer()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsTreasurer()
        assert permission.has_permission(mock_request, mock_view) is True


# =============================================================================
# IS ADMIN TESTS
# =============================================================================

class TestIsAdmin:
    """Tests for IsAdmin permission."""

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsAdmin()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_denied(self, mock_request, mock_view, create_member_profile):
        """Test that pastors are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsAdmin()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_superuser_allowed(self, mock_request, mock_view):
        """Test that superusers are allowed."""
        mock_request.user.is_superuser = True
        # Remove member_profile so IsAdmin falls through to is_superuser check
        mock_request.user.configure_mock(**{'member_profile': Mock(spec=[])})
        del mock_request.user.member_profile
        permission = IsAdmin()
        assert permission.has_permission(mock_request, mock_view) is True


# =============================================================================
# IS FINANCE STAFF TESTS
# =============================================================================

class TestIsFinanceStaff:
    """Tests for IsFinanceStaff permission."""

    def test_treasurer_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that treasurers are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Test that admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_group_leader_denied(self, mock_request, mock_view, create_member_profile):
        """Test that group leaders are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is False


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestGetUserRole:
    """Tests for get_user_role function."""

    def test_superuser_returns_admin(self):
        """Test that superusers return admin role."""
        user = Mock()
        user.is_superuser = True
        assert get_user_role(user) == Roles.ADMIN

    def test_staff_returns_pastor(self):
        """Test that staff without profile returns pastor role."""
        user = Mock()
        user.is_superuser = False
        user.is_staff = True
        user.member_profile = None
        # Remove member_profile attribute
        del user.member_profile
        assert get_user_role(user) == Roles.PASTOR

    def test_member_profile_returns_role(self, create_member_profile):
        """Test that member profile role is returned."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.VOLUNTEER)
        assert get_user_role(user) == Roles.VOLUNTEER


class TestIsStaffMember:
    """Tests for is_staff_member function."""

    def test_django_staff_is_staff(self):
        """Test that Django staff are considered staff."""
        user = Mock()
        user.is_staff = True
        user.is_superuser = False
        assert is_staff_member(user) is True

    def test_pastor_is_staff(self, create_member_profile):
        """Test that pastors are considered staff."""
        user = Mock()
        user.is_staff = False
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.PASTOR)
        assert is_staff_member(user) is True

    def test_volunteer_is_not_staff(self, create_member_profile):
        """Test that volunteers are not considered staff."""
        user = Mock()
        user.is_staff = False
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.VOLUNTEER)
        assert is_staff_member(user) is False


class TestCanManageFinances:
    """Tests for can_manage_finances function."""

    def test_treasurer_can_manage(self, create_member_profile):
        """Test that treasurers can manage finances."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.TREASURER)
        assert can_manage_finances(user) is True

    def test_admin_can_manage(self, create_member_profile):
        """Test that admins can manage finances."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.ADMIN)
        assert can_manage_finances(user) is True

    def test_pastor_cannot_manage(self, create_member_profile):
        """Test that pastors cannot manage finances (unless in FINANCE_ROLES)."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.PASTOR)
        # Pastor is not in FINANCE_ROLES (only TREASURER and ADMIN)
        assert can_manage_finances(user) is False
