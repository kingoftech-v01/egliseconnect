"""Tests for core permissions."""
import pytest
from django.contrib.auth import get_user_model
from unittest.mock import Mock, MagicMock, patch

from apps.core.permissions import (
    IsMember,
    IsVolunteer,
    IsGroupLeader,
    IsDeacon,
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


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = Mock()
    request.user = Mock()
    request.user.is_authenticated = True
    request.user.is_staff = False
    request.user.is_superuser = False
    return request


@pytest.fixture
def mock_view():
    """Mock view object."""
    return Mock()


@pytest.fixture
def create_member_profile():
    """Factory to create mock member profiles with specific roles."""
    def _create(role):
        profile = Mock()
        profile.role = role
        profile.all_roles = {role}
        return profile
    return _create


class TestIsMember:
    """Tests for IsMember permission."""

    def test_authenticated_user_allowed(self, mock_request, mock_view):
        """Authenticated users are allowed."""
        permission = IsMember()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_unauthenticated_user_denied(self, mock_request, mock_view):
        """Unauthenticated users are denied."""
        mock_request.user.is_authenticated = False
        permission = IsMember()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_no_user_denied(self, mock_view):
        """Requests without user are denied."""
        request = Mock()
        request.user = None
        permission = IsMember()
        assert permission.has_permission(request, mock_view) is False


class TestIsVolunteer:
    """Tests for IsVolunteer permission."""

    def test_volunteer_allowed(self, mock_request, mock_view, create_member_profile):
        """Volunteers are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_member_denied(self, mock_request, mock_view, create_member_profile):
        """Regular members are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_group_leader_allowed(self, mock_request, mock_view, create_member_profile):
        """Group leaders are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_deacon_allowed(self, mock_request, mock_view, create_member_profile):
        """Deacons are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.DEACON)
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_staff_allowed(self, mock_request, mock_view):
        """Staff users are allowed."""
        mock_request.user.is_staff = True
        delattr(mock_request.user, 'member_profile') if hasattr(mock_request.user, 'member_profile') else None
        permission = IsVolunteer()
        assert permission.has_permission(mock_request, mock_view) is True


class TestIsGroupLeader:
    """Tests for IsGroupLeader permission."""

    def test_group_leader_allowed(self, mock_request, mock_view, create_member_profile):
        """Group leaders are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_volunteer_denied(self, mock_request, mock_view, create_member_profile):
        """Volunteers are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_deacon_allowed(self, mock_request, mock_view, create_member_profile):
        """Deacons are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.DEACON)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsGroupLeader()
        assert permission.has_permission(mock_request, mock_view) is True


class TestIsDeacon:
    """Tests for IsDeacon permission."""

    def test_deacon_allowed(self, mock_request, mock_view, create_member_profile):
        """Deacons are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.DEACON)
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_group_leader_denied(self, mock_request, mock_view, create_member_profile):
        """Group leaders are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_volunteer_denied(self, mock_request, mock_view, create_member_profile):
        """Volunteers are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_member_denied(self, mock_request, mock_view, create_member_profile):
        """Regular members are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_unauthenticated_denied(self, mock_request, mock_view):
        """Unauthenticated users are denied."""
        mock_request.user.is_authenticated = False
        permission = IsDeacon()
        assert permission.has_permission(mock_request, mock_view) is False


class TestIsPastor:
    """Tests for IsPastor permission."""

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsPastor()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_group_leader_denied(self, mock_request, mock_view, create_member_profile):
        """Group leaders are denied."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsPastor()
        assert permission.has_permission(mock_request, mock_view) is False

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsPastor()
        assert permission.has_permission(mock_request, mock_view) is True


class TestIsTreasurer:
    """Tests for IsTreasurer permission."""

    def test_treasurer_allowed(self, mock_request, mock_view, create_member_profile):
        """Treasurers are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        permission = IsTreasurer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Pastors are allowed (treasurer resources accessible to pastors)."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsTreasurer()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsTreasurer()
        assert permission.has_permission(mock_request, mock_view) is True


class TestIsAdmin:
    """Tests for IsAdmin permission."""

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsAdmin()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Pastors are allowed (admin access includes pastors)."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsAdmin()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_superuser_allowed(self, mock_request, mock_view):
        """Superusers are allowed."""
        mock_request.user.is_superuser = True
        mock_request.user.configure_mock(**{'member_profile': Mock(spec=[])})
        del mock_request.user.member_profile
        permission = IsAdmin()
        assert permission.has_permission(mock_request, mock_view) is True


class TestIsFinanceStaff:
    """Tests for IsFinanceStaff permission."""

    def test_treasurer_allowed(self, mock_request, mock_view, create_member_profile):
        """Treasurers are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_pastor_allowed(self, mock_request, mock_view, create_member_profile):
        """Pastors are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is True

    def test_admin_allowed(self, mock_request, mock_view, create_member_profile):
        """Admins are allowed."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is True

    @patch('apps.donations.models.FinanceDelegation.objects')
    def test_group_leader_denied(self, mock_fd_objects, mock_request, mock_view, create_member_profile):
        """Group leaders are denied."""
        mock_fd_objects.filter.return_value.exists.return_value = False
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        permission = IsFinanceStaff()
        assert permission.has_permission(mock_request, mock_view) is False


class TestGetUserRole:
    """Tests for get_user_role function."""

    def test_superuser_returns_admin(self):
        """Superusers return admin role."""
        user = Mock()
        user.is_superuser = True
        assert get_user_role(user) == Roles.ADMIN

    def test_staff_returns_pastor(self):
        """Staff without profile returns pastor role."""
        user = Mock()
        user.is_superuser = False
        user.is_staff = True
        user.member_profile = None
        del user.member_profile
        assert get_user_role(user) == Roles.PASTOR

    def test_member_profile_returns_role(self, create_member_profile):
        """Member profile role is returned."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.VOLUNTEER)
        assert get_user_role(user) == Roles.VOLUNTEER


class TestIsStaffMember:
    """Tests for is_staff_member function."""

    def test_django_staff_is_staff(self):
        """Django staff are considered staff."""
        user = Mock()
        user.is_staff = True
        user.is_superuser = False
        assert is_staff_member(user) is True

    def test_pastor_is_staff(self, create_member_profile):
        """Pastors are considered staff."""
        user = Mock()
        user.is_staff = False
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.PASTOR)
        assert is_staff_member(user) is True

    def test_deacon_is_staff(self, create_member_profile):
        """Deacons are considered staff."""
        user = Mock()
        user.is_staff = False
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.DEACON)
        assert is_staff_member(user) is True

    def test_volunteer_is_not_staff(self, create_member_profile):
        """Volunteers are not considered staff."""
        user = Mock()
        user.is_staff = False
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.VOLUNTEER)
        assert is_staff_member(user) is False


class TestCanManageFinances:
    """Tests for can_manage_finances function."""

    def test_treasurer_can_manage(self, create_member_profile):
        """Treasurers can manage finances."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.TREASURER)
        assert can_manage_finances(user) is True

    def test_admin_can_manage(self, create_member_profile):
        """Admins can manage finances."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.ADMIN)
        assert can_manage_finances(user) is True

    def test_pastor_can_manage(self, create_member_profile):
        """Pastors can manage finances (PASTOR in FINANCE_ROLES)."""
        user = Mock()
        user.is_superuser = False
        user.member_profile = create_member_profile(Roles.PASTOR)
        assert can_manage_finances(user) is True


# ==============================================================================
# Tests for unauthenticated checks and is_staff fallback paths
# ==============================================================================

from apps.core.permissions import CanViewMember


def _make_user_no_profile(is_staff=False, is_superuser=False, is_authenticated=True):
    """Create a mock user with no member_profile attribute."""
    user = Mock(spec=['is_authenticated', 'is_staff', 'is_superuser'])
    user.is_authenticated = is_authenticated
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    return user


class TestIsVolunteerUnauthenticated:
    """Tests for IsVolunteer unauthenticated check (line 21)."""

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied by IsVolunteer."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        permission = IsVolunteer()
        assert permission.has_permission(request, None) is False

    def test_no_user_denied(self):
        """Request with no user should be denied by IsVolunteer."""
        request = Mock()
        request.user = None
        permission = IsVolunteer()
        assert permission.has_permission(request, None) is False


class TestIsGroupLeaderStaffFallback:
    """Tests for IsGroupLeader unauthenticated (line 41) and staff fallback (line 50)."""

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        permission = IsGroupLeader()
        assert permission.has_permission(request, None) is False

    def test_staff_user_no_profile_allowed(self):
        """Staff user without member_profile should be allowed (is_staff fallback)."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=True)
        permission = IsGroupLeader()
        assert permission.has_permission(request, None) is True

    def test_non_staff_user_no_profile_denied(self):
        """Non-staff user without member_profile should be denied."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=False)
        permission = IsGroupLeader()
        assert permission.has_permission(request, None) is False


class TestIsPastorStaffFallback:
    """Tests for IsPastor unauthenticated (line 59) and staff fallback (line 67)."""

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        permission = IsPastor()
        assert permission.has_permission(request, None) is False

    def test_staff_user_no_profile_allowed(self):
        """Staff user without member_profile should be allowed."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=True)
        permission = IsPastor()
        assert permission.has_permission(request, None) is True

    def test_non_staff_user_no_profile_denied(self):
        """Non-staff user without member_profile should be denied."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=False)
        permission = IsPastor()
        assert permission.has_permission(request, None) is False


class TestIsTreasurerStaffFallback:
    """Tests for IsTreasurer unauthenticated (line 76) and staff fallback (line 84)."""

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        permission = IsTreasurer()
        assert permission.has_permission(request, None) is False

    def test_staff_user_no_profile_allowed(self):
        """Staff user without member_profile should be allowed."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=True)
        permission = IsTreasurer()
        assert permission.has_permission(request, None) is True

    def test_non_staff_user_no_profile_denied(self):
        """Non-staff user without member_profile should be denied."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=False)
        permission = IsTreasurer()
        assert permission.has_permission(request, None) is False


class TestIsAdminUnauthenticated:
    """Tests for IsAdmin unauthenticated check (line 93)."""

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        permission = IsAdmin()
        assert permission.has_permission(request, None) is False

    def test_no_user_denied(self):
        """Request with no user should be denied."""
        request = Mock()
        request.user = None
        permission = IsAdmin()
        assert permission.has_permission(request, None) is False

    def test_non_superuser_no_profile_denied(self):
        """Non-superuser without member_profile should be denied (is_superuser fallback)."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=True, is_superuser=False)
        permission = IsAdmin()
        assert permission.has_permission(request, None) is False


class TestIsFinanceStaffStaffFallback:
    """Tests for IsFinanceStaff staff fallback (line 130)."""

    def test_staff_user_no_profile_allowed(self):
        """Staff user without member_profile should be allowed."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=True)
        permission = IsFinanceStaff()
        assert permission.has_permission(request, None) is True

    def test_non_staff_user_no_profile_denied(self):
        """Non-staff user without member_profile should be denied."""
        request = Mock()
        request.user = _make_user_no_profile(is_staff=False)
        permission = IsFinanceStaff()
        assert permission.has_permission(request, None) is False

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        permission = IsFinanceStaff()
        assert permission.has_permission(request, None) is False


class TestIsStaffMemberNoProfile:
    """Tests for is_staff_member fallback (line 247) when user has no member_profile."""

    def test_no_profile_non_staff_returns_false(self):
        """User without member_profile and not staff should return False."""
        user = _make_user_no_profile(is_staff=False, is_superuser=False)
        assert is_staff_member(user) is False

    def test_no_profile_staff_returns_true(self):
        """Staff user without member_profile should return True."""
        user = _make_user_no_profile(is_staff=True, is_superuser=False)
        assert is_staff_member(user) is True

    def test_no_profile_superuser_returns_true(self):
        """Superuser without member_profile should return True."""
        user = _make_user_no_profile(is_staff=False, is_superuser=True)
        assert is_staff_member(user) is True


class TestCanManageFinancesNoProfile:
    """Tests for can_manage_finances fallback when user has no member_profile."""

    def test_no_profile_non_superuser_returns_false(self):
        """Non-superuser without member_profile should return False."""
        user = _make_user_no_profile(is_staff=True, is_superuser=False)
        assert can_manage_finances(user) is False

    def test_no_profile_superuser_returns_true(self):
        """Superuser without member_profile should return True."""
        user = _make_user_no_profile(is_staff=False, is_superuser=True)
        assert can_manage_finances(user) is True
