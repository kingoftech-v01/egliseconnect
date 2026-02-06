"""Tests for reports frontend views."""
import pytest
from datetime import date
from django.test import Client
from django.urls import NoReverseMatch

from apps.members.tests.factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    TreasurerFactory,
    AdminMemberFactory,
)
from apps.donations.tests.factories import DonationFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def pastor_user(db):
    """Pastor with user account."""
    user = UserFactory()
    member = PastorFactory(user=user)
    return user, member


@pytest.fixture
def admin_user(db):
    """Admin with user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def treasurer_user(db):
    """Treasurer with user account."""
    user = UserFactory()
    member = TreasurerFactory(user=user)
    return user, member


@pytest.fixture
def regular_member_user(db):
    """Regular member with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='member')
    return user, member


@pytest.fixture
def volunteer_user(db):
    """Volunteer with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='volunteer')
    return user, member


@pytest.fixture
def user_without_profile(db):
    """User without member profile."""
    return UserFactory()


@pytest.mark.django_db
class TestDashboardView:
    """Tests for the dashboard frontend view."""

    url = '/reports/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_can_access(self, client, treasurer_user):
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_volunteer_denied(self, client, volunteer_user):
        user, member = volunteer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        """User without profile triggers NoReverseMatch due to pk='' fallback."""
        client.force_login(user_without_profile)
        with pytest.raises(NoReverseMatch):
            client.get(self.url)

    def test_dashboard_context_contains_summary(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'summary' in response.context


@pytest.mark.django_db
class TestMemberStatsView:
    """Tests for the member_stats frontend view."""

    url = '/reports/members/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_denied(self, client, treasurer_user):
        """Treasurers cannot access member stats (only pastor/admin)."""
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_context_contains_stats(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'stats' in response.context


@pytest.mark.django_db
class TestDonationReportView:
    """Tests for the donation_report frontend view."""

    url = '/reports/donations/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_can_access(self, client, treasurer_user):
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_year(self, client, pastor_user):
        """No year param defaults to current year."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context['current_year'] == date.today().year

    def test_with_valid_year_param(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': '2024'})
        assert response.status_code == 200
        assert response.context['current_year'] == 2024

    def test_with_invalid_year_param(self, client, pastor_user):
        """Invalid year falls back to current year."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': 'invalid'})
        assert response.status_code == 200
        assert response.context['current_year'] == date.today().year

    def test_context_contains_report_and_stats(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'report' in response.context
        assert 'stats' in response.context
        assert 'current_year' in response.context
        assert 'available_years' in response.context

    def test_available_years_range(self, client, pastor_user):
        """Available years covers 5-year range backwards from current year."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        available_years = list(response.context['available_years'])
        current_year = date.today().year
        assert available_years[0] == current_year
        assert len(available_years) == 5

    def test_with_donations_present(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        DonationFactory()
        response = client.get(self.url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAttendanceReportView:
    """Tests for the attendance_report frontend view."""

    url = '/reports/attendance/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_denied(self, client, treasurer_user):
        """Treasurers cannot access attendance report (only pastor/admin)."""
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_without_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'report' in response.context
        assert 'event_stats' in response.context

    def test_with_valid_start_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': '2025-01-01'})
        assert response.status_code == 200

    def test_with_valid_end_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': '2025-12-31'})
        assert response.status_code == 200

    def test_with_both_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        })
        assert response.status_code == 200

    def test_with_invalid_start_date(self, client, pastor_user):
        """Invalid start_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': 'not-a-date'})
        assert response.status_code == 200

    def test_with_invalid_end_date(self, client, pastor_user):
        """Invalid end_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': 'bad-date'})
        assert response.status_code == 200

    def test_with_both_invalid_dates(self, client, pastor_user):
        """Both invalid dates fall back to defaults."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': 'invalid',
            'end_date': 'invalid',
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestVolunteerReportView:
    """Tests for the volunteer_report frontend view."""

    url = '/reports/volunteers/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_denied(self, client, treasurer_user):
        """Treasurers cannot access volunteer report (only pastor/admin)."""
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_without_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'report' in response.context
        assert 'volunteer_stats' in response.context

    def test_with_valid_start_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': '2025-06-01'})
        assert response.status_code == 200

    def test_with_valid_end_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': '2025-06-30'})
        assert response.status_code == 200

    def test_with_both_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2025-01-01',
            'end_date': '2025-06-30',
        })
        assert response.status_code == 200

    def test_with_invalid_start_date(self, client, pastor_user):
        """Invalid start_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': 'xyz'})
        assert response.status_code == 200

    def test_with_invalid_end_date(self, client, pastor_user):
        """Invalid end_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': 'xyz'})
        assert response.status_code == 200

    def test_with_both_invalid_dates(self, client, pastor_user):
        """Both invalid dates fall back to defaults."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': 'bad',
            'end_date': 'bad',
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestBirthdayReportView:
    """Tests for the birthday_report frontend view."""

    url = '/reports/birthdays/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_any_member_can_access(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_days(self, client, pastor_user):
        """Default days is 30 when not specified."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context['days'] == 30

    def test_with_custom_days(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'days': '60'})
        assert response.status_code == 200
        assert response.context['days'] == 60

    def test_with_invalid_days(self, client, pastor_user):
        """Invalid days parameter falls back to default 30."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'days': 'abc'})
        assert response.status_code == 200
        assert response.context['days'] == 30

    def test_context_contains_birthdays(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'birthdays' in response.context
        assert 'days' in response.context


@pytest.mark.django_db
class TestFrontendRedirects:
    """Tests for unauthorized user redirect destinations."""

    def test_dashboard_regular_member_redirect_target(self, client, regular_member_user):
        """Dashboard redirects regular member to their member_detail page."""
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/')
        assert response.status_code == 302
        assert str(member.pk) in response.url

    def test_member_stats_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/members/')
        assert response.status_code == 302

    def test_donation_report_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/donations/')
        assert response.status_code == 302

    def test_attendance_report_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/attendance/')
        assert response.status_code == 302

    def test_volunteer_report_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/volunteers/')
        assert response.status_code == 302

    def test_birthday_report_no_profile_redirects_to_member_list(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get('/reports/birthdays/')
        assert response.status_code == 302
