"""Tests for core mixins."""
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
    W3CRMFormMixin,
)


class FakeContextView:
    """Provides get_context_data for context mixin tests."""
    def get_context_data(self, **kwargs):
        return kwargs.copy()


class FakeFormView:
    """Provides form_valid/form_invalid for form mixin tests."""
    def __init__(self):
        self._form_valid_response = Mock(name='form_valid_response')
        self._form_invalid_response = Mock(name='form_invalid_response')

    def form_valid(self, form):
        return self._form_valid_response

    def form_invalid(self, form):
        return self._form_invalid_response


class FakeListView:
    """Provides get_queryset for queryset mixin tests."""
    def __init__(self, queryset=None):
        self._queryset = queryset or Mock()

    def get_queryset(self):
        return self._queryset


@pytest.fixture
def mock_request():
    """Mock request object with a mock user."""
    request = Mock()
    request.user = Mock()
    request.user.is_authenticated = True
    request.user.is_staff = False
    request.user.is_superuser = False
    return request


@pytest.fixture
def mock_request_no_profile():
    """Mock request where user has no member_profile attribute."""
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
    """Create a mixin instance with request set."""
    instance = mixin_class()
    instance.request = request
    return instance


class TestVolunteerRequiredMixin:
    """Tests for VolunteerRequiredMixin."""

    def test_staff_user_allowed(self, mock_request_no_profile):
        """Staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_volunteer_role_allowed(self, mock_request, create_member_profile):
        """Volunteer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_group_leader_role_allowed(self, mock_request, create_member_profile):
        """Group leader role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_treasurer_role_allowed(self, mock_request, create_member_profile):
        """Treasurer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_member_role_denied(self, mock_request, create_member_profile):
        """Regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """User without member_profile and not staff fails."""
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_with_profile_redirects_to_member_detail(
        self, mock_messages, mock_redirect, mock_request, create_member_profile
    ):
        """Redirects to member detail when profile exists."""
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
        """Redirects to / when no profile."""
        mixin = _make_mixin(VolunteerRequiredMixin, mock_request_no_profile)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class TestGroupLeaderRequiredMixin:
    """Tests for GroupLeaderRequiredMixin."""

    def test_staff_user_allowed(self, mock_request_no_profile):
        """Staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_group_leader_role_allowed(self, mock_request, create_member_profile):
        """Group leader role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_treasurer_denied(self, mock_request, create_member_profile):
        """Treasurer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """User without profile and not staff fails."""
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Redirects to /."""
        mixin = _make_mixin(GroupLeaderRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class TestPastorRequiredMixin:
    """Tests for PastorRequiredMixin."""

    def test_staff_user_allowed(self, mock_request_no_profile):
        """is_staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(PastorRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_superuser_allowed(self, mock_request_no_profile):
        """Superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(PastorRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_treasurer_denied(self, mock_request, create_member_profile):
        """Treasurer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """User without profile and not staff/superuser fails."""
        mixin = _make_mixin(PastorRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Adds error message and redirects to /."""
        mixin = _make_mixin(PastorRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class TestTreasurerRequiredMixin:
    """Tests for TreasurerRequiredMixin."""

    def test_superuser_allowed(self, mock_request_no_profile):
        """Superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_staff_user_allowed(self, mock_request_no_profile):
        """is_staff users pass test_func."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_treasurer_role_allowed(self, mock_request, create_member_profile):
        """Treasurer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_denied(self, mock_request, create_member_profile):
        """Pastor role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_staff_denied(self, mock_request_no_profile):
        """User without profile and not staff/superuser fails."""
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Adds error message and redirects to /."""
        mixin = _make_mixin(TreasurerRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class TestAdminRequiredMixin:
    """Tests for AdminRequiredMixin."""

    def test_superuser_allowed(self, mock_request_no_profile):
        """Superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(AdminRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_staff_user_without_admin_role_denied(self, mock_request_no_profile):
        """is_staff without superuser or admin role fails."""
        mock_request_no_profile.user.is_staff = True
        mixin = _make_mixin(AdminRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    def test_pastor_denied(self, mock_request, create_member_profile):
        """Pastor role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_treasurer_denied(self, mock_request, create_member_profile):
        """Treasurer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_superuser_denied(self, mock_request_no_profile):
        """User without profile and not superuser fails."""
        mixin = _make_mixin(AdminRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Adds error message and redirects to /."""
        mixin = _make_mixin(AdminRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class TestFinanceStaffRequiredMixin:
    """Tests for FinanceStaffRequiredMixin."""

    def test_superuser_allowed(self, mock_request_no_profile):
        """Superusers pass test_func."""
        mock_request_no_profile.user.is_superuser = True
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is True

    def test_treasurer_role_allowed(self, mock_request, create_member_profile):
        """Treasurer role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.TREASURER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Pastor role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is True

    def test_volunteer_denied(self, mock_request, create_member_profile):
        """Volunteer role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_group_leader_denied(self, mock_request, create_member_profile):
        """Group leader role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.GROUP_LEADER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_member_denied(self, mock_request, create_member_profile):
        """Regular member role fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        assert mixin.test_func() is False

    def test_no_profile_not_superuser_denied(self, mock_request_no_profile):
        """User without profile and not superuser fails."""
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request_no_profile)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Adds error message and redirects to /."""
        mixin = _make_mixin(FinanceStaffRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class TestMemberRequiredMixin:
    """Tests for MemberRequiredMixin."""

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_authenticated_user_without_profile_redirects_to_create(
        self, mock_messages, mock_redirect, mock_request_no_profile
    ):
        """Authenticated user without member_profile is redirected to create."""
        mixin = _make_mixin(MemberRequiredMixin, mock_request_no_profile)

        result = MemberRequiredMixin.dispatch(mixin, mock_request_no_profile)

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('frontend:members:member_create')

    def test_unauthenticated_user_gets_no_permission(self, mock_request):
        """Unauthenticated user triggers handle_no_permission."""
        mock_request.user.is_authenticated = False
        mixin = _make_mixin(MemberRequiredMixin, mock_request)
        mixin.handle_no_permission = Mock(return_value=Mock(name='redirect_response'))

        result = MemberRequiredMixin.dispatch(mixin, mock_request)

        mixin.handle_no_permission.assert_called_once()

    def test_login_url_is_set(self):
        """login_url is configured."""
        assert MemberRequiredMixin.login_url == '/accounts/login/'

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_authenticated_user_with_profile_calls_super_dispatch(
        self, mock_messages, mock_redirect, mock_request, create_member_profile
    ):
        """Authenticated user with profile calls parent dispatch."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)

        class FakeParentView:
            def dispatch(self, request, *args, **kwargs):
                return 'dispatched'

        class TestView(MemberRequiredMixin, FakeParentView):
            pass

        view = TestView()
        view.request = mock_request
        result = view.dispatch(mock_request)

        assert result == 'dispatched'
        mock_messages.error.assert_not_called()


class TestOwnerOrStaffRequiredMixin:
    """Tests for OwnerOrStaffRequiredMixin."""

    def _make_owner_mixin(self, request, obj=None):
        """Create the mixin and stub get_object()."""
        mixin = _make_mixin(OwnerOrStaffRequiredMixin, request)
        if obj is not None:
            mixin.get_object = Mock(return_value=obj)
        return mixin

    def test_staff_user_allowed(self, mock_request):
        """is_staff users pass test_func."""
        mock_request.user.is_staff = True
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    def test_superuser_allowed(self, mock_request):
        """Superusers pass test_func."""
        mock_request.user.is_superuser = True
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    def test_pastor_role_allowed(self, mock_request, create_member_profile):
        """Pastor role (in STAFF_ROLES) passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    def test_admin_role_allowed(self, mock_request, create_member_profile):
        """Admin role (in STAFF_ROLES) passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mixin = self._make_owner_mixin(mock_request)
        assert mixin.test_func() is True

    def test_owner_via_user_attribute_allowed(self, mock_request, create_member_profile):
        """Owner of object (via obj.user) passes test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = mock_request.user
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is True

    def test_non_owner_via_user_attribute_denied(self, mock_request, create_member_profile):
        """Non-owner (via obj.user) fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=['user'])
        obj.user = Mock()
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is False

    def test_owner_via_member_attribute_allowed(self, mock_request, create_member_profile):
        """Owner of object (via obj.member) passes test_func."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile
        obj = Mock(spec=['member'])
        obj.member = profile
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is True

    def test_non_owner_via_member_attribute_denied(self, mock_request, create_member_profile):
        """Non-owner (via obj.member) fails test_func."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=['member'])
        obj.member = Mock()
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is False

    def test_no_ownership_attributes_denied(self, mock_request, create_member_profile):
        """Object without user/member attributes fails."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        obj = Mock(spec=[])
        mixin = self._make_owner_mixin(mock_request, obj)
        assert mixin.test_func() is False

    def test_no_profile_member_ownership_denied(self, mock_request_no_profile):
        """User without member_profile fails member ownership check."""
        obj = Mock(spec=['member'])
        obj.member = Mock()
        mixin = _make_mixin(OwnerOrStaffRequiredMixin, mock_request_no_profile)
        mixin.get_object = Mock(return_value=obj)
        assert mixin.test_func() is False

    @patch('apps.core.mixins.redirect')
    @patch('apps.core.mixins.messages')
    def test_handle_no_permission_redirects_to_root(
        self, mock_messages, mock_redirect, mock_request
    ):
        """Adds error message and redirects to /."""
        mixin = _make_mixin(OwnerOrStaffRequiredMixin, mock_request)
        mixin.handle_no_permission()

        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once_with('/')


class _ChurchContextTestView(ChurchContextMixin, FakeContextView):
    """Concrete test view combining ChurchContextMixin with a base view."""
    pass


class TestChurchContextMixin:
    """Tests for ChurchContextMixin."""

    @patch('apps.core.mixins.get_user_role')
    def test_authenticated_user_with_profile_gets_role_and_member(
        self, mock_get_role, mock_request, create_member_profile
    ):
        """Context includes role and member for authenticated user with profile."""
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
        """Context has role but no member when user lacks profile."""
        mock_get_role.return_value = Roles.PASTOR

        view = _ChurchContextTestView()
        view.request = mock_request_no_profile
        context = view.get_context_data()

        assert context['current_user_role'] == Roles.PASTOR

    @patch('apps.core.mixins.get_user_role')
    def test_unauthenticated_user_gets_none_values(self, mock_get_role, mock_request):
        """Unauthenticated user gets None for role and member."""
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
        """Pastor role triggers birthday lookup in context."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mock_get_role.return_value = Roles.PASTOR

        view = _ChurchContextTestView()
        view.request = mock_request

        mock_birthdays = [Mock(), Mock()]
        with patch('apps.core.utils.get_today_birthdays', return_value=mock_birthdays):
            context = view.get_context_data()

        assert context['current_user_role'] == Roles.PASTOR
        assert 'today_birthdays' in context

    @patch('apps.core.mixins.get_user_role')
    def test_admin_role_triggers_birthday_fetch(
        self, mock_get_role, mock_request, create_member_profile
    ):
        """Admin role triggers birthday lookup in context."""
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
        """Regular member role does not get birthday data."""
        mock_request.user.member_profile = create_member_profile(Roles.MEMBER)
        mock_get_role.return_value = Roles.MEMBER

        view = _ChurchContextTestView()
        view.request = mock_request
        context = view.get_context_data()

        assert 'today_birthdays' not in context


class _PageTitleTestView(PageTitleMixin, FakeContextView):
    """Concrete test view combining PageTitleMixin with a base view."""
    pass


class TestPageTitleMixin:
    """Tests for PageTitleMixin."""

    def test_default_page_title_is_none(self):
        """Default page_title is None."""
        mixin = PageTitleMixin()
        assert mixin.page_title is None

    def test_get_page_title_returns_set_title(self):
        """get_page_title returns the configured title."""
        mixin = PageTitleMixin()
        mixin.page_title = 'Test Title'
        assert mixin.get_page_title() == 'Test Title'

    def test_get_context_data_includes_page_title(self):
        """get_context_data includes page_title key."""
        view = _PageTitleTestView()
        view.page_title = 'My Page'
        context = view.get_context_data()

        assert context['page_title'] == 'My Page'

    def test_get_context_data_with_none_title(self):
        """Context includes None when page_title is not set."""
        view = _PageTitleTestView()
        context = view.get_context_data()

        assert context['page_title'] is None


class _BreadcrumbTestView(BreadcrumbMixin, FakeContextView):
    """Concrete test view combining BreadcrumbMixin with a base view."""
    pass


class TestBreadcrumbMixin:
    """Tests for BreadcrumbMixin."""

    def test_default_breadcrumbs_is_empty_list(self):
        """Default breadcrumbs returns empty list."""
        mixin = BreadcrumbMixin()
        assert mixin.get_breadcrumbs() == []

    def test_get_context_data_includes_breadcrumbs(self):
        """get_context_data includes breadcrumbs key."""
        view = _BreadcrumbTestView()
        context = view.get_context_data()

        assert context['breadcrumbs'] == []

    def test_custom_breadcrumbs_in_context(self):
        """Overridden breadcrumbs appear in context."""

        class CustomBreadcrumbView(BreadcrumbMixin, FakeContextView):
            def get_breadcrumbs(self):
                return [('Home', '/'), ('Members', '/members/'), ('Detail', None)]

        view = CustomBreadcrumbView()
        context = view.get_context_data()

        assert len(context['breadcrumbs']) == 3
        assert context['breadcrumbs'][0] == ('Home', '/')
        assert context['breadcrumbs'][2] == ('Detail', None)


class _FormMessageTestView(FormMessageMixin, FakeFormView):
    """Concrete test view combining FormMessageMixin with a base form view."""
    def __init__(self):
        FakeFormView.__init__(self)


class TestFormMessageMixin:
    """Tests for FormMessageMixin."""

    @patch('apps.core.mixins.messages')
    def test_form_valid_adds_success_message(self, mock_messages):
        """form_valid adds a success message."""
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
        """form_invalid adds an error message."""
        view = _FormMessageTestView()
        view.request = Mock()
        mock_form = Mock()

        result = view.form_invalid(mock_form)

        mock_messages.error.assert_called_once_with(
            view.request, view.error_message
        )
        assert result == view._form_invalid_response

    def test_default_success_message_is_set(self):
        """Default success_message is set."""
        mixin = FormMessageMixin()
        assert mixin.success_message is not None

    def test_default_error_message_is_set(self):
        """Default error_message is set."""
        mixin = FormMessageMixin()
        assert mixin.error_message is not None


class _SetOwnerTestView(SetOwnerMixin, FakeFormView):
    """Concrete test view combining SetOwnerMixin with a base form view."""
    def __init__(self):
        FakeFormView.__init__(self)


class TestSetOwnerMixin:
    """Tests for SetOwnerMixin."""

    def test_sets_member_on_form_instance(self, mock_request, create_member_profile):
        """form_valid sets member on the form instance."""
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
        """form_valid does not overwrite existing member_id."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile

        view = _SetOwnerTestView()
        view.request = mock_request

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

        assert mock_form.instance.member == existing_member
        assert mock_form.instance.user == existing_user
        assert mock_form.instance.created_by == existing_created_by

    def test_sets_user_when_no_member_profile(self, mock_request_no_profile):
        """form_valid sets user even without member_profile."""
        view = _SetOwnerTestView()
        view.request = mock_request_no_profile

        mock_form = Mock()
        mock_form.instance = Mock(spec=['user', 'user_id'])
        mock_form.instance.user_id = None

        view.form_valid(mock_form)

        assert mock_form.instance.user == mock_request_no_profile.user


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
        """is_staff users see all objects."""
        mock_request.user.is_staff = True
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_superuser_sees_all(self, mock_request):
        """Superusers see all objects."""
        mock_request.user.is_superuser = True
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_pastor_role_sees_all(self, mock_request, create_member_profile):
        """Pastor (STAFF_ROLES) sees all objects."""
        mock_request.user.member_profile = create_member_profile(Roles.PASTOR)
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_admin_role_sees_all(self, mock_request, create_member_profile):
        """Admin (STAFF_ROLES) sees all objects."""
        mock_request.user.member_profile = create_member_profile(Roles.ADMIN)
        mock_qs = Mock()

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        assert result == mock_qs

    def test_member_role_filters_by_own_member(self, mock_request, create_member_profile):
        """Regular member only sees own objects."""
        profile = create_member_profile(Roles.MEMBER)
        mock_request.user.member_profile = profile

        mock_qs = Mock()
        mock_qs.model = Mock()
        mock_qs.model.member = True
        mock_qs.filter = Mock(return_value=Mock(name='filtered_qs'))

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        mock_qs.filter.assert_called_once_with(member=profile)

    def test_no_profile_gets_empty_queryset(self, mock_request_no_profile):
        """User without profile gets empty queryset."""
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
        """When model lacks 'member' field, queryset.none() is returned."""
        mock_request.user.member_profile = create_member_profile(Roles.VOLUNTEER)

        mock_qs = Mock()
        mock_qs.model = Mock(spec=[])
        mock_empty = Mock(name='empty_qs')
        mock_qs.none = Mock(return_value=mock_empty)

        view = _make_filter_view(mock_request, mock_qs)
        result = view.get_queryset()

        mock_qs.none.assert_called_once()
        assert result == mock_empty


class TestLoginUrlConfiguration:
    """Tests that all permission mixins have correct login_url."""

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


class TestW3CRMFormMixin:
    """Tests for W3CRMFormMixin."""

    def test_text_input_gets_form_control(self):
        """TextInput widget gets form-control class."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            name = forms.CharField()

        form = TestForm()
        assert 'form-control' in form.fields['name'].widget.attrs.get('class', '')

    def test_select_gets_form_select(self):
        """Select widget gets form-select class."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            choice = forms.ChoiceField(choices=[('a', 'A'), ('b', 'B')])

        form = TestForm()
        assert 'form-select' in form.fields['choice'].widget.attrs.get('class', '')

    def test_checkbox_gets_form_check_input(self):
        """CheckboxInput widget gets form-check-input class."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            active = forms.BooleanField(required=False)

        form = TestForm()
        assert 'form-check-input' in form.fields['active'].widget.attrs.get('class', '')

    def test_textarea_gets_form_control(self):
        """Textarea widget gets form-control class."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            notes = forms.CharField(widget=forms.Textarea)

        form = TestForm()
        assert 'form-control' in form.fields['notes'].widget.attrs.get('class', '')

    def test_email_input_gets_form_control(self):
        """EmailInput widget gets form-control class."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            email = forms.EmailField()

        form = TestForm()
        assert 'form-control' in form.fields['email'].widget.attrs.get('class', '')

    def test_date_input_gets_form_control(self):
        """DateInput widget gets form-control class."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            date = forms.DateField(widget=forms.DateInput)

        form = TestForm()
        attrs = form.fields['date'].widget.attrs
        assert 'form-control' in attrs.get('class', '')

    def test_preserves_existing_attrs(self):
        """Mixin preserves existing widget attributes like placeholder, rows, etc."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter notes'}))

        form = TestForm()
        attrs = form.fields['notes'].widget.attrs
        assert 'form-control' in attrs.get('class', '')
        assert attrs.get('rows') == 3
        assert attrs.get('placeholder') == 'Enter notes'

    def test_preserves_existing_css_classes(self):
        """Mixin preserves existing CSS classes and adds new ones."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={'class': 'my-custom'}))

        form = TestForm()
        css = form.fields['name'].widget.attrs.get('class', '')
        assert 'my-custom' in css
        assert 'form-control' in css

    def test_no_duplicate_classes(self):
        """Mixin does not add duplicate CSS classes."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

        form = TestForm()
        css = form.fields['name'].widget.attrs.get('class', '')
        assert css.count('form-control') == 1

    def test_works_with_model_form(self):
        """Mixin works correctly with ModelForm subclasses."""
        from django import forms
        from apps.help_requests.forms import HelpRequestResolveForm

        form = HelpRequestResolveForm()
        assert 'form-control' in form.fields['resolution_notes'].widget.attrs.get('class', '')

    def test_works_with_form_that_has_custom_init(self):
        """Mixin cooperates with forms that have custom __init__."""
        from django import forms

        class TestForm(W3CRMFormMixin, forms.Form):
            name = forms.CharField()
            role = forms.ChoiceField(choices=[('a', 'A')])

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['role'].choices = [('b', 'B'), ('c', 'C')]

        form = TestForm()
        assert 'form-control' in form.fields['name'].widget.attrs.get('class', '')
        assert 'form-select' in form.fields['role'].widget.attrs.get('class', '')
