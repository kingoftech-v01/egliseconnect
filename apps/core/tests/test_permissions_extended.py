"""Extended tests for core permissions - object-level permissions."""
import pytest
from unittest.mock import Mock
from apps.core.permissions import (
    IsOwnerOrStaff,
    IsOwnerOrReadOnly,
    CanViewMember,
    get_user_role,
    can_manage_finances,
)
from apps.core.constants import Roles


@pytest.fixture
def mock_request():
    request = Mock()
    request.user = Mock()
    request.user.is_staff = False
    request.user.is_superuser = False
    request.user.is_authenticated = True
    return request


@pytest.fixture
def mock_view():
    return Mock()


class TestIsOwnerOrStaff:
    """Tests for IsOwnerOrStaff permission."""

    def test_staff_can_access(self, mock_request, mock_view):
        """Staff can access any object."""
        mock_request.user.is_staff = True
        obj = Mock()
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_pastor_can_access(self, mock_request, mock_view):
        """Pastors can access any object."""
        mock_request.user.member_profile = Mock(role=Roles.PASTOR)
        obj = Mock(spec=[])
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_admin_can_access(self, mock_request, mock_view):
        """Admins can access any object."""
        mock_request.user.member_profile = Mock(role=Roles.ADMIN)
        obj = Mock(spec=[])
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_owner_via_user_attr(self, mock_request, mock_view):
        """Owner can access via obj.user attribute."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = mock_request.user
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_non_owner_via_user_attr(self, mock_request, mock_view):
        """Non-owner cannot access via obj.user attribute."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = Mock()
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_owner_via_member_attr(self, mock_request, mock_view):
        """Owner can access via obj.member attribute."""
        member = Mock(role=Roles.MEMBER)
        mock_request.user.member_profile = member
        obj = Mock(spec=['member'])
        obj.member = member
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_non_owner_via_member_attr(self, mock_request, mock_view):
        """Non-owner cannot access via obj.member attribute."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['member'])
        obj.member = Mock()
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_no_user_or_member_attr(self, mock_request, mock_view):
        """No access when object has no user or member attributes."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=[])
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_member_attr_but_no_member_profile(self, mock_request, mock_view):
        """No access when user lacks member_profile."""
        del mock_request.user.member_profile
        obj = Mock(spec=['member'])
        obj.member = Mock()
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False


class TestIsOwnerOrReadOnly:
    """Tests for IsOwnerOrReadOnly permission."""

    def test_safe_method_allowed(self, mock_request, mock_view):
        """GET requests are allowed."""
        mock_request.method = 'GET'
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_head_method_allowed(self, mock_request, mock_view):
        """HEAD requests are allowed."""
        mock_request.method = 'HEAD'
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_options_method_allowed(self, mock_request, mock_view):
        """OPTIONS requests are allowed."""
        mock_request.method = 'OPTIONS'
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_staff_can_write(self, mock_request, mock_view):
        """Staff can make write requests."""
        mock_request.method = 'PUT'
        mock_request.user.is_staff = True
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_pastor_can_write(self, mock_request, mock_view):
        """Pastors can make write requests."""
        mock_request.method = 'PUT'
        mock_request.user.member_profile = Mock(role=Roles.PASTOR)
        obj = Mock(spec=[])
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_owner_via_user_can_write(self, mock_request, mock_view):
        """Owner can make write requests via user attribute."""
        mock_request.method = 'PUT'
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = mock_request.user
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_owner_via_member_can_write(self, mock_request, mock_view):
        """Owner can make write requests via member attribute."""
        mock_request.method = 'PATCH'
        member = Mock(role=Roles.MEMBER)
        mock_request.user.member_profile = member
        obj = Mock(spec=['member'])
        obj.member = member
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_non_owner_cannot_write(self, mock_request, mock_view):
        """Non-owner cannot make write requests."""
        mock_request.method = 'DELETE'
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=[])
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_member_attr_no_member_profile_cannot_write(self, mock_request, mock_view):
        """Cannot write when user lacks member_profile."""
        mock_request.method = 'PUT'
        del mock_request.user.member_profile
        obj = Mock(spec=['member'])
        obj.member = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_user_attr_non_owner_cannot_write(self, mock_request, mock_view):
        """Non-owner cannot write via user attribute."""
        mock_request.method = 'PUT'
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False


class TestCanViewMember:
    """Tests for CanViewMember permission."""

    def test_staff_can_view(self, mock_request, mock_view):
        """Staff can view any member."""
        mock_request.user.is_staff = True
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_no_member_profile_denied(self, mock_request, mock_view):
        """Users without member_profile are denied."""
        del mock_request.user.member_profile
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_pastor_can_view(self, mock_request, mock_view):
        """Pastors can view any member."""
        mock_request.user.member_profile = Mock(role=Roles.PASTOR)
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_admin_can_view(self, mock_request, mock_view):
        """Admins can view any member."""
        mock_request.user.member_profile = Mock(role=Roles.ADMIN)
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_can_view_self(self, mock_request, mock_view):
        """Members can view themselves."""
        member = Mock(role=Roles.MEMBER)
        mock_request.user.member_profile = member
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, member) is True

    def test_public_profile_visible(self, mock_request, mock_view):
        """Public profiles are visible to all members."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock()
        obj.privacy_settings = Mock(visibility='public')
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_group_visibility_shared_group(self, mock_request, mock_view):
        """Group visibility allows members with shared groups."""
        member = Mock(role=Roles.MEMBER)
        member.groups = Mock()
        member.groups.values_list = Mock(return_value=[1, 2])
        mock_request.user.member_profile = member
        obj = Mock()
        obj.privacy_settings = Mock(visibility='group')
        obj.groups = Mock()
        obj.groups.values_list = Mock(return_value=[2, 3])
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_group_visibility_no_shared_group(self, mock_request, mock_view):
        """Group visibility denies members without shared groups."""
        member = Mock(role=Roles.MEMBER)
        member.groups = Mock()
        member.groups.values_list = Mock(return_value=[1, 2])
        mock_request.user.member_profile = member
        obj = Mock()
        obj.privacy_settings = Mock(visibility='group')
        obj.groups = Mock()
        obj.groups.values_list = Mock(return_value=[3, 4])
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_private_visibility_denied(self, mock_request, mock_view):
        """Private profiles are hidden from other members."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock()
        obj.privacy_settings = Mock(visibility='private')
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_no_privacy_settings_allowed(self, mock_request, mock_view):
        """Members without privacy_settings are visible."""
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=[])
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True


class TestGetUserRoleExtended:
    """Extended tests for get_user_role function."""

    def test_no_profile_no_staff(self):
        """Returns None when no profile and not staff."""
        user = Mock()
        user.is_superuser = False
        user.is_staff = False
        del user.member_profile
        assert get_user_role(user) is None


class TestCanManageFinancesExtended:
    """Extended tests for can_manage_finances function."""

    def test_superuser_can_manage(self):
        """Superusers can manage finances."""
        user = Mock()
        user.is_superuser = True
        assert can_manage_finances(user) is True

    def test_no_profile_cannot_manage(self):
        """Users without profile cannot manage finances."""
        user = Mock()
        user.is_superuser = False
        del user.member_profile
        assert can_manage_finances(user) is False
