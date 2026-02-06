"""Tests for TwoFactorEnforcementMiddleware and MembershipAccessMiddleware."""
import pytest
from datetime import timedelta
from django.http import HttpResponse
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.core.middleware import (
    TwoFactorEnforcementMiddleware,
    MembershipAccessMiddleware,
    TWO_FACTOR_EXEMPT_PATHS,
    MFA_SETUP_URL,
)
from apps.core.constants import Roles, MembershipStatus
from apps.members.tests.factories import MemberFactory, UserFactory


def ok_response(request):
    """Simple pass-through view for middleware testing."""
    return HttpResponse('OK')


@pytest.mark.django_db
class TestTwoFactorEnforcementMiddleware:
    """Tests for the TwoFactorEnforcementMiddleware."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.middleware = TwoFactorEnforcementMiddleware(ok_response)

    def _make_request(self, path='/', user=None):
        request = self.factory.get(path)
        request.user = user if user else AnonymousUser()
        return request

    def test_anonymous_user_passes_through(self):
        request = self._make_request('/')
        response = self.middleware(request)
        assert response.status_code == 200
        assert response.content == b'OK'

    def test_authenticated_user_without_member_passes(self):
        user = UserFactory()
        request = self._make_request('/dashboard/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_user_with_2fa_enabled_passes(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=True,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/dashboard/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_user_without_2fa_no_deadline_passes(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=None,
            registration_date=None,
        )
        request = self._make_request('/dashboard/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_user_with_future_deadline_passes(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() + timedelta(days=7),
            registration_date=None,
        )
        request = self._make_request('/dashboard/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_overdue_2fa_redirects_to_setup(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/dashboard/', user)
        response = self.middleware(request)
        assert response.status_code == 302
        assert response['Location'] == MFA_SETUP_URL

    def test_overdue_2fa_redirects_from_members_page(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 302
        assert response['Location'] == MFA_SETUP_URL

    def test_exempt_path_accounts_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/accounts/login/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_exempt_path_api_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/api/v1/members/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_exempt_path_static_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/static/css/style.css', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_exempt_path_media_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/media/photos/test.jpg', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_exempt_path_admin_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request('/admin/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_mfa_setup_url_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request(MFA_SETUP_URL, user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_mfa_setup_subpath_not_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        request = self._make_request(f'{MFA_SETUP_URL}totp/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_all_exempt_paths_covered(self):
        """Ensure all paths in TWO_FACTOR_EXEMPT_PATHS pass."""
        user = UserFactory()
        MemberFactory(
            user=user,
            two_factor_enabled=False,
            two_factor_deadline=timezone.now() - timedelta(days=1),
            registration_date=None,
        )
        for exempt_path in TWO_FACTOR_EXEMPT_PATHS:
            request = self._make_request(exempt_path + 'test/', user)
            response = self.middleware(request)
            assert response.status_code == 200, f'{exempt_path} should be exempt'


@pytest.mark.django_db
class TestMembershipAccessMiddleware:
    """Tests for the MembershipAccessMiddleware."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.middleware = MembershipAccessMiddleware(ok_response)

    def _make_request(self, path='/', user=None):
        request = self.factory.get(path)
        request.user = user if user else AnonymousUser()
        return request

    def test_anonymous_passes_through(self):
        request = self._make_request('/members/')
        response = self.middleware(request)
        assert response.status_code == 200

    def test_user_without_member_passes(self):
        user = UserFactory()
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_active_member_accesses_all(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.ACTIVE,
        )
        for path in MembershipAccessMiddleware.MEMBERS_ONLY:
            request = self._make_request(path, user)
            response = self.middleware(request)
            assert response.status_code == 200, f'Active member blocked from {path}'

    def test_registered_member_blocked_from_members(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 302
        assert 'onboarding' in response['Location']

    def test_registered_member_blocked_from_donations(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/donations/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_registered_member_blocked_from_events(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/events/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_registered_member_blocked_from_volunteers(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/volunteers/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_registered_member_blocked_from_communication(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/communication/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_registered_member_blocked_from_help_requests(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/help-requests/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_registered_member_blocked_from_reports(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/reports/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_registered_member_allowed_onboarding(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/onboarding/dashboard/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_accounts(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/accounts/settings/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_attendance_qr(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/attendance/my-qr/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_attendance_history(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/attendance/my-history/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_api(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/api/v1/onboarding/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_payments(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/payments/donate/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_audit(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/audit/logins/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_registered_member_allowed_pwa_paths(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        for path in ['/sw.js', '/manifest.json', '/offline/']:
            request = self._make_request(path, user)
            response = self.middleware(request)
            assert response.status_code == 200, f'Registered member blocked from {path}'

    def test_admin_bypasses_restrictions(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            role=Roles.ADMIN,
            registration_date=None,
        )
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_pastor_bypasses_restrictions(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            role=Roles.PASTOR,
            registration_date=None,
        )
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_in_training_member_blocked_from_members_only(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.IN_TRAINING,
            registration_date=None,
        )
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_form_pending_member_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.FORM_PENDING,
            registration_date=None,
        )
        request = self._make_request('/donations/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_all_always_allowed_paths(self):
        """Ensure all ALWAYS_ALLOWED paths pass for non-active members."""
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        for path in MembershipAccessMiddleware.ALWAYS_ALLOWED:
            request = self._make_request(path, user)
            response = self.middleware(request)
            assert response.status_code == 200, f'{path} should always be allowed'

    def test_non_listed_path_passes_for_non_active(self):
        """Paths not in MEMBERS_ONLY and not in ALWAYS_ALLOWED should pass."""
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        request = self._make_request('/some-random-path/', user)
        response = self.middleware(request)
        assert response.status_code == 200

    def test_suspended_member_blocked(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.SUSPENDED,
            registration_date=None,
        )
        request = self._make_request('/members/', user)
        response = self.middleware(request)
        assert response.status_code == 302

    def test_static_and_media_always_allowed(self):
        user = UserFactory()
        MemberFactory(
            user=user,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=None,
        )
        for path in ['/static/js/app.js', '/media/photos/img.jpg']:
            request = self._make_request(path, user)
            response = self.middleware(request)
            assert response.status_code == 200
