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


# =============================================================================
# IsOwnerOrStaff TESTS
# =============================================================================

class TestIsOwnerOrStaff:
    def test_staff_can_access(self, mock_request, mock_view):
        mock_request.user.is_staff = True
        obj = Mock()
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_pastor_can_access(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.PASTOR)
        obj = Mock(spec=[])
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_admin_can_access(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.ADMIN)
        obj = Mock(spec=[])
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_owner_via_user_attr(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = mock_request.user
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_non_owner_via_user_attr(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = Mock()  # Different user
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_owner_via_member_attr(self, mock_request, mock_view):
        member = Mock(role=Roles.MEMBER)
        mock_request.user.member_profile = member
        obj = Mock(spec=['member'])
        obj.member = member
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_non_owner_via_member_attr(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['member'])
        obj.member = Mock()  # Different member
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_no_user_or_member_attr(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=[])  # No user or member attrs
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_member_attr_but_no_member_profile(self, mock_request, mock_view):
        del mock_request.user.member_profile
        obj = Mock(spec=['member'])
        obj.member = Mock()
        perm = IsOwnerOrStaff()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False


# =============================================================================
# IsOwnerOrReadOnly TESTS
# =============================================================================

class TestIsOwnerOrReadOnly:
    def test_safe_method_allowed(self, mock_request, mock_view):
        mock_request.method = 'GET'
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_head_method_allowed(self, mock_request, mock_view):
        mock_request.method = 'HEAD'
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_options_method_allowed(self, mock_request, mock_view):
        mock_request.method = 'OPTIONS'
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_staff_can_write(self, mock_request, mock_view):
        mock_request.method = 'PUT'
        mock_request.user.is_staff = True
        obj = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_pastor_can_write(self, mock_request, mock_view):
        mock_request.method = 'PUT'
        mock_request.user.member_profile = Mock(role=Roles.PASTOR)
        obj = Mock(spec=[])
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_owner_via_user_can_write(self, mock_request, mock_view):
        mock_request.method = 'PUT'
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = mock_request.user
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_owner_via_member_can_write(self, mock_request, mock_view):
        mock_request.method = 'PATCH'
        member = Mock(role=Roles.MEMBER)
        mock_request.user.member_profile = member
        obj = Mock(spec=['member'])
        obj.member = member
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_non_owner_cannot_write(self, mock_request, mock_view):
        mock_request.method = 'DELETE'
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=[])
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_member_attr_no_member_profile_cannot_write(self, mock_request, mock_view):
        mock_request.method = 'PUT'
        del mock_request.user.member_profile
        obj = Mock(spec=['member'])
        obj.member = Mock()
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_user_attr_non_owner_cannot_write(self, mock_request, mock_view):
        mock_request.method = 'PUT'
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = Mock()  # Different user
        perm = IsOwnerOrReadOnly()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False


# =============================================================================
# CanViewMember TESTS
# =============================================================================

class TestCanViewMember:
    def test_staff_can_view(self, mock_request, mock_view):
        mock_request.user.is_staff = True
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_no_member_profile_denied(self, mock_request, mock_view):
        del mock_request.user.member_profile
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_pastor_can_view(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.PASTOR)
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_admin_can_view(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.ADMIN)
        obj = Mock()
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_can_view_self(self, mock_request, mock_view):
        member = Mock(role=Roles.MEMBER)
        mock_request.user.member_profile = member
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, member) is True

    def test_public_profile_visible(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock()
        obj.privacy_settings = Mock(visibility='public')
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True

    def test_group_visibility_shared_group(self, mock_request, mock_view):
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
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock()
        obj.privacy_settings = Mock(visibility='private')
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is False

    def test_no_privacy_settings_allowed(self, mock_request, mock_view):
        mock_request.user.member_profile = Mock(role=Roles.MEMBER)
        obj = Mock(spec=[])  # No privacy_settings attribute
        perm = CanViewMember()
        assert perm.has_object_permission(mock_request, mock_view, obj) is True


# =============================================================================
# Additional utility function tests
# =============================================================================

class TestGetUserRoleExtended:
    def test_no_profile_no_staff(self):
        user = Mock()
        user.is_superuser = False
        user.is_staff = False
        del user.member_profile
        assert get_user_role(user) is None


class TestCanManageFinancesExtended:
    def test_superuser_can_manage(self):
        user = Mock()
        user.is_superuser = True
        assert can_manage_finances(user) is True

    def test_no_profile_cannot_manage(self):
        user = Mock()
        user.is_superuser = False
        del user.member_profile
        assert can_manage_finances(user) is False
