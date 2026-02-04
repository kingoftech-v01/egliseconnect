"""
Tests for core mixins.

Tests all view mixins including permission mixins, context mixins,
form mixins, and queryset mixins. Uses Mock objects throughout to
avoid database dependencies where possible.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from apps.core.constants import Roles
from apps.core.mixins import (
    MemberRequiredMixin,
    VolunteerRequiredMixin,
    GroupLeaderRequiredMixin,
    PastorRequiredMixin,
    TreasurerRequiredMixin,
    AdminRequiredMixin,
    FinanceStaffRequiredMixin,
    OwnerOrStaffRequiredMixin,
    ChurchContextMixin,
    PageTitleMixin,
    BreadcrumbMixin,
    FormMessageMixin,
    SetOwnerMixin,
    FilterByMemberMixin,
)


# =============================================================================
# FAKE BASE CLASSES (provide super() targets for mixin testing)
# =============================================================================

class FakeContextView:
    """Fake view that provides get_context_data for context mixin tests."""
    def get_context_data(self, **kwargs):
        return kwargs.copy()


class FakeFormView:
    """Fake view that provides form_valid/form_invalid for form mixin tests."""
    def __init__(self):
        self._form_valid_response = Mock(name='form_valid_response')
        self._form_invalid_response = Mock(name='form_invalid_response')

    def form_valid(self, form):
        return self._form_valid_response

    def form_invalid(self, form):
        return self._form_invalid_response


class FakeListView:
    """Fake view that provides get_queryset for queryset mixin tests."""
    def __init__(self, queryset=None):
        self._queryset = queryset or Mock()

    def get_queryset(self):
        return self._queryset


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_request():
    """Create a mock request object with a mock user."""
    request = Mock()
    request.user = Mock()
    request.user.is_authenticated = True
    request.user.is_staff = False
    request.user.is_superuser = False
    return request


@pytest.fixture
def mock_request_no_profile():
    """Create a mock request where user has no member_profile attribute."""
    request = Mock()
    request.user = Mock(spec=['is_authenticated', 'is_staff', 'is_superuser'])
    request.user.is_authenticated = True
    request.user.is_staff = False
    request.user.is_superuser = False
    return request


@pytest.fixture
def create_member_profile():
    """Factory to create mock member profiles with specific roles."""
    def _create(role):
        profile = Mock()
        profile.role = role
        profile.pk = 1
        return profile
    return _create


def _make_mixin(mixin_class, request):
    """
    Helper to create a mixin instance with request set.

    Instantiates the mixin class and sets self.request so that
    test_func() and handle_no_permission() can access the user.
    """
    instance = mixin_class()
    instance.request = request
    return instance


# =============================================================================
# VOLUNTEER REQUIRED MIXIN TESTS
# =============================================================================

class TestVolunteerRequiredMixin:
    """Tests for VolunteerRequiredMixin."""

    # ---- test_func: allowed roles ----

    def test_staff_user_allowed(self, mock_request_no_profile):
        """Test that staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_volunteer_role_allowed(self, mock_request, create_member_profile):
        """Test that volunteer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_group_leader_role_allowed(self, mock_request, create_member_profile):
        """Test that group leader role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Test that pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_treasurer_role_allowed(self, mock_request, create_member_profile):
        """Test that treasurer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    # ---- test_func: denied roles ----

    def test_member_role_denied(self, mock_request, create_member_profile):
        """Test that regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """Test that user without member_profile and not staff fails."""
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_with_profile_redirects_to_member_detail(
        self, mock_messages, mock_redirect, mock_request, create_member_profile
    ):
        """Test handle_no_permission redirects to member detail when profile exists."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with(
            'frontend:members:member_detail', pk=profile.pk
        )

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_without_profile_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request_no_profile
    ):
        """Test handle_no_permission redirects to / when no profile."""
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request_no_profile)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# GROUP LEADER REQUIRED MIXIN TESTS
# =============================================================================

class TestGroupLeaderRequiredMixin:
    """Tests for GroupLeaderRequiredMixin."""

    # ---- test_func: allowed ----

    def test_staff_user_allowed(self, mock_request_no_profile):
        """Test that staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_group_leader_role_allowed(self, mock_request, create_member_profile):
        """Test that group leader role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Test that pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is True

    # ---- test_func: denied ----

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Test that volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Test that regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_treasurer_denied(self, mock_request, create_member_profile):
        """Test that treasurer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """Test that user without profile and not staff fails."""
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Test handle_no_permission redirects to /."""
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# PASTOR REQUIRED MIXIN TESTS
# =============================================================================

class TestPastorRequiredMixin:
    """Tests for PastorRequiredMixin."""

    # ---- test_func: allowed ----

    def test_staff_user_allowed(self, mock_request_no_profile):
        """Test that is_staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(PastorRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_superuser_allowed(self, mock_request_no_profile):
        """Test that superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(PastorRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Test that pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is True

    # ---- test_func: denied ----

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Test that volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Test that group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_treasurer_denied(self, mock_request, create_member_profile):
        """Test that treasurer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Test that regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """Test that user without profile and not staff/superuser fails."""
        mixin = _make_mixin(PastorRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Test handle_no_permission adds error message and redirects to /."""
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# TREASURER REQUIRED MIXIN TESTS
# =============================================================================

class TestTreasurerRequiredMixin:
    """Tests for TreasurerRequiredMixin."""

    # ---- test_func: allowed ----

    def test_superuser_allowed(self, mock_request_no_profile):
        """Test that superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_staff_user_allowed(self, mock_request_no_profile):
        """Test that is_staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_treasurer_role_allowed(self, mock_request, create_member_profile):
        """Test that treasurer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    # ---- test_func: denied ----

    def test_pastor_denied(self, mock_request, create_member_profile):
        """Test that pastor role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Test that volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Test that group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Test that regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """Test that user without profile and not staff/superuser fails."""
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Test handle_no_permission adds error message and redirects to /."""
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# ADMIN REQUIRED MIXIN TESTS
# =============================================================================

class TestAdminRequiredMixin:
    """Tests for AdminRequiredMixin."""

    # ---- test_func: allowed ----

    def test_superuser_allowed(self, mock_request_no_profile):
        """Test that superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(AdminRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is True

    # ---- test_func: denied ----

    def test_staff_user_without_admin_role_denied(self, mock_request_no_profile):
        """Test that is_staff without superuser or admin role fails."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(AdminRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    def test_pastor_denied(self, mock_request, create_member_profile):
        """Test that pastor role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_treasurer_denied(self, mock_request, create_member_profile):
        """Test that treasurer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Test that volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Test that group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Test that regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_superuser_denied(self, mock_request_no_profile):
        """Test that user without profile and not superuser fails."""
        mixin = _make_mixin(AdminRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Test handle_no_permission adds error message and redirects to /."""
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# FINANCE STAFF REQUIRED MIXIN TESTS
# =============================================================================

class TestFinanceStaffRequiredMixin:
    """Tests for FinanceStaffRequiredMixin."""

    # ---- test_func: allowed ----

    def test_superuser_allowed(self, mock_request_no_profile):
        """Test that superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_treasurer_role_allowed(self, mock_request, create_member_profile):
        """Test that treasurer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Test that pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is True

    # ---- test_func: denied ----

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Test that volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Test that group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Test that regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_superuser_denied(self, mock_request_no_profile):
        """Test that user without profile and not superuser fails."""
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Test handle_no_permission adds error message and redirects to /."""
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# MEMBER REQUIRED MIXIN TESTS
# =============================================================================

class TestMemberRequiredMixin:
    """Tests for MemberRequiredMixin."""

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_authenticated_user_without_profile_redirects_to_create(
        self, mock_messages, mock_redirect, mock_request_no_profile
    ):
        """Test that authenticated user without member_profile is redirected to create."""
        mixin = _make_mixin(MemberRequiredMixin, mock_request_no_profile)

        result = MemberRequiredMixin.dispatch(mixin, mock_request_no_profile)

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('frontend:members:member_create')

    def test_unauthenticated_user_gets_no_permission(self, mock_request):
        """Test that unauthenticated user triggers handle_no_permission."""
        mock_request.user.is_authenticated = False
        mixin = _make_mixin(MemberRequiredMixin, mock_request)
        mixin.handle_no_permission = Mock(return_value=Mock(name='redirect_response'))

        result = MemberRequiredMixin.dispatch(mixin, mock_request)

        mixin.handle_no_permission.assert_called_once()

    def test_login_url_is_set(self):
        """Test that login_url is configured."""
        assert MemberRequiredMixin.login_url == '/accounts/login/'

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_authenticated_user_with_profile_calls_super_dispatch(
        self, mock_messages, mock_redirect, mock_request, create_member_profile
    ):
        """Test that authenticated user with profile calls parent dispatch."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)

        # Create a concrete class that combines MemberRequiredMixin with a fake parent
        class FakeParentView:
            def dispatch(self, request, *args, **kwargs):
                return 'dispatched'

        class TestView(MemberRequiredMixin, FakeParentView):
            pass

        view = TestView()
        view.request = mock_request
        result = view.dispatch(mock_request)

        assert result == 'dispatched'
        # No error message should have been added
        mock_messages.error.assert_not_called()


# =============================================================================
# OWNER OR STAFF REQUIRED MIXIN TESTS
# =============================================================================

class TestOwnerOrStaffRequiredMixin:
    """Tests for OwnerOrStaffRequiredMixin."""

    def _make_owner_mixin(self, request, obj=None):
        """Helper that creates the mixin and stubs get_object()."""
        mixin = _make_mixin(OwnerOrStaffRequiredMixin, request)
        if obj is not None:
            mixin.get_object = Mock(return_value=obj)
        return mixin

    # ---- test_func: staff/superuser ----

    def test_staff_user_allowed(self, mock_request):
        """Test that is_staff users pass test_func."""
        mock_request.user.is_staff = True
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    def test_superuser_allowed(self, mock_request):
        """Test that superusers pass test_func."""
        mock_request.user.is_superuser = True
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    # ---- test_func: staff role ----

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Test that pastor role (in STAFF_ROLES) passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Test that admin role (in STAFF_ROLES) passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    # ---- test_func: ownership via user attribute ----

    def test_owner_via_user_attribute_allowed(self, mock_request, create_member_profile):
        """Test that owner of object (via obj.user) passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = mock_request.user  # Owner match
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is True

    def test_non_owner_via_user_attribute_denied(self, mock_request, create_member_profile):
        """Test that non-owner (via obj.user) fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = Mock()  # Different user
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is False

    # ---- test_func: ownership via member attribute ----

    def test_owner_via_member_attribute_allowed(self, mock_request, create_member_profile):
        """Test that owner of object (via obj.member) passes test_func."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile
        obj = Mock(spec=['member'])
        obj.member = profile  # Owner match
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is True

    def test_non_owner_via_member_attribute_denied(self, mock_request, create_member_profile):
        """Test that non-owner (via obj.member) fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=['member'])
        obj.member = Mock()  # Different member
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is False

    # ---- test_func: no ownership attributes ----

    def test_no_ownership_attributes_denied(self, mock_request, create_member_profile):
        """Test that object without user/member attributes fails."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=[])  # No user or member attribute
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is False

    # ---- test_func: no member profile, checking member ownership ----

    def test_no_profile_member_ownership_denied(self, mock_request_no_profile):
        """Test that user without member_profile fails member ownership check."""
        obj = Mock(spec=['member'])
        obj.member = Mock()
        mixin = _make_mixin(OwnerOrStaffRequiredMixin, mock_request_no_profile)
        mixin.get_object = Mock(return_value=obj)
        assert mixin.test_func() is False

    # ---- handle_no_permission ----

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Test handle_no_permission adds error message and redirects to /."""
        mixin = _make_mixin(OwnerOrStaffRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


# =============================================================================
# CHURCH CONTEXT MIXIN TESTS
# =============================================================================

# Concrete view classes for testing context mixins
class _ChurchContextTestView(ChurchContextMixin, FakeContextView):
    """Concrete test view combining ChurchContextMixin with a base view."""
    pass


class TestChurchContextMixin:
    """Tests for ChurchContextMixin."""

    @patch('apps.core.mixins.get_user_role')
    def test_authenticated_user_with_profile_gets_role_and_member(
        self, mock_get_role, mock_request, create_member_profile
    ):
        """Test that context includes role and member for authenticated user with profile."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile
        mock_get_role.return_value = Roles.MEMBER

        view = _ChurchContextTestView()
        view.request = mock_request
        context = view.get_context_data()

        assert context['current_user_role'] == Roles.MEMBER
        assert context['current_member'] == profile

    @patch('apps.core.mixins.get_user_role')
    def test_authenticated_user_without_profile(
        self, mock_get_role, mock_request_no_profile
    ):
        """Test that context has role but no member when user lacks profile."""
        mock_get_role.return_value = Roles.PASTOR

        view = _ChurchContextTestView()
        view.request = mock_request_no_profile
        context = view.get_context_data()

        assert context['current_user_role'] == Roles.PASTOR

    @patch('apps.core.mixins.get_user_role')
    def test_unauthenticated_user_gets_none_values(self, mock_get_role, mock_request):
        """Test that unauthenticated user gets None for role and member."""
        mock_request.user.is_authenticated = False

        view = _ChurchContextTestView()
        view.request = mock_request
        context = view.get_context_data()

        assert context['current_user_role'] is None
        assert context['current_member'] is None

    @patch('apps.core.mixins.get_user_role')
    def test_pastor_role_triggers_birthday_fetch(
        self, mock_get_role, mock_request, create_member_profile
    ):
        """Test that pastor role triggers birthday lookup in context."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mock_get_role.return_value = Roles.PASTOR

        view = _ChurchContextTestView()
        view.request = mock_request

        # Patch the deferred import of get_today_birthdays
        mock_birthdays = [Mock(), Mock()]
        with patch('apps.core.utils.get_today_birthdays', return_value=mock_birthdays):
            context = view.get_context_data()

        assert context['current_user_role'] == Roles.PASTOR
        # today_birthdays should be set for pastor role
        assert 'today_birthdays' in context

    @patch('apps.core.mixins.get_user_role')
    def test_admin_role_triggers_birthday_fetch(
        self, mock_get_role, mock_request, create_member_profile
    ):
        """Test that admin role triggers birthday lookup in context."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mock_get_role.return_value = Roles.ADMIN

        view = _ChurchContextTestView()
        view.request = mock_request

        mock_birthdays = [Mock()]
        with patch('apps.core.utils.get_today_birthdays', return_value=mock_birthdays):
            context = view.get_context_data()

        assert 'today_birthdays' in context

    @patch('apps.core.mixins.get_user_role')
    def test_member_role_does_not_get_birthdays(
        self, mock_get_role, mock_request, create_member_profile
    ):
        """Test that regular member role does not get birthday data."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mock_get_role.return_value = Roles.MEMBER

        view = _ChurchContextTestView()
        view.request = mock_request
        context = view.get_context_data()

        assert 'today_birthdays' not in context


# =============================================================================
# PAGE TITLE MIXIN TESTS
# =============================================================================

class _PageTitleTestView(PageTitleMixin, FakeContextView):
    """Concrete test view combining PageTitleMixin with a base view."""
    pass


class TestPageTitleMixin:
    """Tests for PageTitleMixin."""

    def test_default_page_title_is_none(self):
        """Test that default page_title is None."""
        mixin = PageTitleMixin()
        assert mixin.page_title is None

    def test_get_page_title_returns_set_title(self):
        """Test that get_page_title returns the configured title."""
        mixin = PageTitleMixin()
        mixin.page_title = 'Test Title'
        assert mixin.get_page_title() == 'Test Title'

    def test_get_context_data_includes_page_title(self):
        """Test that get_context_data includes page_title key."""
        view = _PageTitleTestView()
        view.page_title = 'My Page'
        context = view.get_context_data()

        assert context['page_title'] == 'My Page'

    def test_get_context_data_with_none_title(self):
        """Test that context includes None when page_title is not set."""
        view = _PageTitleTestView()
        context = view.get_context_data()

        assert context['page_title'] is None


# =============================================================================
# BREADCRUMB MIXIN TESTS
# =============================================================================

class _BreadcrumbTestView(BreadcrumbMixin, FakeContextView):
    """Concrete test view combining BreadcrumbMixin with a base view."""
    pass


class TestBreadcrumbMixin:
    """Tests for BreadcrumbMixin."""

    def test_default_breadcrumbs_is_empty_list(self):
        """Test that default breadcrumbs returns empty list."""
        mixin = BreadcrumbMixin()
        assert mixin.get_breadcrumbs() == []

    def test_get_context_data_includes_breadcrumbs(self):
        """Test that get_context_data includes breadcrumbs key."""
        view = _BreadcrumbTestView()
        context = view.get_context_data()

        assert context['breadcrumbs'] == []

    def test_custom_breadcrumbs_in_context(self):
        """Test that overridden breadcrumbs appear in context."""

        class CustomBreadcrumbView(BreadcrumbMixin, FakeContextView):
            def get_breadcrumbs(self):
                return [('Home', '/'), ('Members', '/members/'), ('Detail', None)]

        view = CustomBreadcrumbView()
        context = view.get_context_data()

        assert len(context['breadcrumbs']) == 3
        assert context['breadcrumbs'][0] == ('Home', '/')
        assert context['breadcrumbs'][2] == ('Detail', None)


# =============================================================================
# FORM MESSAGE MIXIN TESTS
# =============================================================================

class _FormMessageTestView(FormMessageMixin, FakeFormView):
    """Concrete test view combining FormMessageMixin with a base form view."""
    def __init__(self):
        FakeFormView.__init__(self)


class TestFormMessageMixin:
    """Tests for FormMessageMixin."""

    @patch('apps.core.mixins.messages')
    def test_form_valid_adds_success_message(self, mock_messages):
        """Test that form_valid adds a success message."""
        view = _FormMessageTestView()
        view.request = Mock()
        mock_form = Mock()

        result = view.form_valid(mock_form)

        mock_messages.success.assert_called_once_with(
            view.request, view.success_message
        )
        assert result == view._form_valid_response

    @patch('apps.core.mixins.messages')
    def test_form_invalid_adds_error_message(self, mock_messages):
        """Test that form_invalid adds an error message."""
        view = _FormMessageTestView()
        view.request = Mock()
        mock_form = Mock()

        result = view.form_invalid(mock_form)

        mock_messages.error.assert_called_once_with(
            view.request, view.error_message
        )
        assert result == view._form_invalid_response

    def test_default_success_message_is_set(self):
        """Test that default success_message is set."""
        mixin = FormMessageMixin()
        assert mixin.success_message is not None

    def test_default_error_message_is_set(self):
        """Test that default error_message is set."""
        mixin = FormMessageMixin()
        assert mixin.error_message is not None


# =============================================================================
# SET OWNER MIXIN TESTS
# =============================================================================

class _SetOwnerTestView(SetOwnerMixin, FakeFormView):
    """Concrete test view combining SetOwnerMixin with a base form view."""
    def __init__(self):
        FakeFormView.__init__(self)


class TestSetOwnerMixin:
    """Tests for SetOwnerMixin."""

    def test_sets_member_on_form_instance(self, mock_request, create_member_profile):
        """Test that form_valid sets member on the form instance."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile

        view = _SetOwnerTestView()
        view.request = mock_request

        mock_form = Mock()
        mock_form.instance.member_id = None
        mock_form.instance.user_id = None
        mock_form.instance.created_by_id = None

        view.form_valid(mock_form)

        assert mock_form.instance.member == profile
        assert mock_form.instance.user == mock_request.user
        assert mock_form.instance.created_by == profile

    def test_does_not_overwrite_existing_member(self, mock_request, create_member_profile):
        """Test that form_valid does not overwrite existing member_id."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile

        view = _SetOwnerTestView()
        view.request = mock_request

        # Set existing IDs that should not be overwritten
        existing_member = Mock()
        existing_user = Mock()
        existing_created_by = Mock()

        mock_form = Mock()
        mock_form.instance.member = existing_member
        mock_form.instance.member_id = 999
        mock_form.instance.user = existing_user
        mock_form.instance.user_id = 999
        mock_form.instance.created_by = existing_created_by
        mock_form.instance.created_by_id = 999

        view.form_valid(mock_form)

        # Should not have been reassigned because IDs were already set
        assert mock_form.instance.member == existing_member
        assert mock_form.instance.user == existing_user
        assert mock_form.instance.created_by == existing_created_by

    def test_sets_user_when_no_member_profile(self, mock_request_no_profile):
        """Test that form_valid sets user even without member_profile."""
        view = _SetOwnerTestView()
        view.request = mock_request_no_profile

        # Instance with only user attribute (no member or created_by)
        mock_form = Mock()
        mock_form.instance = Mock(spec=['user', 'user_id'])
        mock_form.instance.user_id = None

        view.form_valid(mock_form)

        assert mock_form.instance.user == mock_request_no_profile.user


# =============================================================================
# FILTER BY MEMBER MIXIN TESTS
# =============================================================================

def _make_filter_view(request, queryset):
    """Create a concrete FilterByMemberMixin view with a given queryset."""

    class _FilterTestView(FilterByMemberMixin, FakeListView):
        def __init__(self, qs):
            FakeListView.__init__(self, qs)

    view = _FilterTestView(queryset)
    view.request = request
    return view


class TestFilterByMemberMixin:
    """Tests for FilterByMemberMixin."""

    def test_staff_user_sees_all(self, mock_request):
        """Test that is_staff users see all objects."""
        mock_request.user.is_staff = True
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_superuser_sees_all(self, mock_request):
        """Test that superusers see all objects."""
        mock_request.user.is_superuser = True
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_pastor_role_sees_all(self, mock_request, create_member_profile):
        """Test that pastor (STAFF_ROLES) sees all objects."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_admin_role_sees_all(self, mock_request, create_member_profile):
        """Test that admin (STAFF_ROLES) sees all objects."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_member_role_filters_by_own_member(self, mock_request, create_member_profile):
        """Test that regular member only sees own objects."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile

        mock_qs = Mock()
        mock_qs.model = Mock()
        mock_qs.model.member = True  # Simulate model has 'member' attribute
        mock_qs.filter = Mock(return_value=Mock(name='filtered_qs'))

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        mock_qs.filter.assert_called_once_with(member=profile)

    def test_no_profile_gets_empty_queryset(self, mock_request_no_profile):
        """Test that user without profile gets empty queryset."""
        mock_qs = Mock()
        mock_empty = Mock(name='empty_qs')
        mock_qs.none = Mock(return_value=mock_empty)

        view = _make_filter_view(mock_request_no_profile, mock_qs)
        result = view.get_queryset()

        mock_qs.none.assert_called_once()
        assert result == mock_empty

    def test_model_without_member_attribute_returns_empty(
        self, mock_request, create_member_profile
    ):
        """Test that when model lacks 'member' field, queryset.none() is returned."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)

        mock_qs = Mock()
        mock_qs.model = Mock(spec=[])  # No 'member' attribute on model
        mock_empty = Mock(name='empty_qs')
        mock_qs.none = Mock(return_value=mock_empty)

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        mock_qs.none.assert_called_once()
        assert result == mock_empty


# =============================================================================
# LOGIN URL CONFIGURATION TESTS
# =============================================================================

class TestLoginUrlConfiguration:
    """Test that all permission mixins have the correct login_url."""

    def test_member_required_login_url(self):
        assert MemberRequiredMixin.login_url == '/accounts/login/'

    def test_volunteer_required_login_url(self):
        assert VolunteerRequiredMixin.login_url == '/accounts/login/'

    def test_group_leader_required_login_url(self):
        assert GroupLeaderRequiredMixin.login_url == '/accounts/login/'

    def test_pastor_required_login_url(self):
        assert PastorRequiredMixin.login_url == '/accounts/login/'

    def test_treasurer_required_login_url(self):
        assert TreasurerRequiredMixin.login_url == '/accounts/login/'

    def test_admin_required_login_url(self):
        assert AdminRequiredMixin.login_url == '/accounts/login/'

    def test_finance_staff_required_login_url(self):
        assert FinanceStaffRequiredMixin.login_url == '/accounts/login/'

    def test_owner_or_staff_required_login_url(self):
        assert OwnerOrStaffRequiredMixin.login_url == '/accounts/login/'
