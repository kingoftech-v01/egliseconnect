"""Tests for reports API views."""
import pytest
from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.members.tests.factories import MemberFactory, UserFactory, TreasurerFactory
from apps.reports.views_api import ReportViewSet, TreasurerDonationReportView


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def pastor_user():
    user = UserFactory()
    member = MemberFactory(user=user, role='pastor')
    return user, member


@pytest.fixture
def member_user():
    user = UserFactory()
    member = MemberFactory(user=user, role='member')
    return user, member


@pytest.mark.django_db
class TestDashboardAPI:
    """Tests for Dashboard API endpoints."""

    def test_dashboard_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_dashboard_requires_pastor_role(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_accessible_by_pastor(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'members' in response.data
        assert 'donations' in response.data

    def test_member_stats_endpoint(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/members/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'active' in response.data

    def test_donation_stats_endpoint(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_amount' in response.data

    def test_donation_stats_with_year(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/donations/?year=2025')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2025

    def test_birthdays_endpoint(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/birthdays/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestReportAPI:
    """Tests for Report API endpoints."""

    def test_attendance_report(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/attendance/')
        assert response.status_code == status.HTTP_200_OK
        assert 'events' in response.data

    def test_donation_report(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/donations/2026/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2026

    def test_volunteer_report(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/volunteers/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_shifts' in response.data


@pytest.mark.django_db
class TestTreasurerAccess:
    """Tests for treasurer-specific API access."""

    def test_treasurer_can_access_donation_report(self, api_client):
        user = UserFactory()
        member = MemberFactory(user=user, role='treasurer')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_200_OK

    def test_member_cannot_access_treasurer_reports(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDashboardEventsAPI:
    """Tests for Dashboard events endpoint."""

    def test_events_endpoint(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/events/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_events' in response.data
        assert 'upcoming' in response.data
        assert 'cancelled' in response.data
        assert 'year' in response.data

    def test_events_with_year_param(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/events/?year=2025')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2025

    def test_events_with_invalid_year_param(self, api_client, pastor_user):
        """Invalid year falls back to current year."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/events/?year=notayear')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year

    def test_events_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/dashboard/events/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_events_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/events/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDashboardVolunteersAPI:
    """Tests for Dashboard volunteers endpoint."""

    def test_volunteers_endpoint(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/volunteers/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_positions' in response.data
        assert 'upcoming_schedules' in response.data

    def test_volunteers_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/dashboard/volunteers/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_volunteers_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/volunteers/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDashboardHelpRequestsAPI:
    """Tests for Dashboard help_requests endpoint."""

    def test_help_requests_endpoint(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/help_requests/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'open' in response.data
        assert 'resolved_this_month' in response.data

    def test_help_requests_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/dashboard/help_requests/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_help_requests_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/help_requests/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationStatsEdgeCases:
    """Tests for donation stats edge cases."""

    def test_donation_stats_with_invalid_year(self, api_client, pastor_user):
        """Invalid year falls back to current year."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/donations/?year=abc')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year

    def test_donation_stats_without_year(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year


@pytest.mark.django_db
class TestBirthdaysEdgeCases:
    """Tests for birthdays endpoint edge cases."""

    def test_birthdays_with_custom_days(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/birthdays/?days=30')
        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_with_invalid_days(self, api_client, pastor_user):
        """Invalid days falls back to default."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/birthdays/?days=notanumber')
        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/dashboard/birthdays/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_birthdays_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/birthdays/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestReportAttendanceEdgeCases:
    """Tests for attendance report edge cases."""

    def test_attendance_with_valid_dates(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/attendance/?start_date=2025-01-01&end_date=2025-12-31'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['start_date'] == '2025-01-01'
        assert response.data['end_date'] == '2025-12-31'

    def test_attendance_with_invalid_start_date(self, api_client, pastor_user):
        """Invalid start_date falls back to None."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/attendance/?start_date=invalid'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_with_invalid_end_date(self, api_client, pastor_user):
        """Invalid end_date falls back to None."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/attendance/?end_date=invalid'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_with_both_invalid_dates(self, api_client, pastor_user):
        """Both invalid dates fall back to defaults."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/attendance/?start_date=bad&end_date=bad'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_with_only_start_date(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/attendance/?start_date=2025-06-01'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_with_only_end_date(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/attendance/?end_date=2025-06-30'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/reports/attendance/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_attendance_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/attendance/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestReportDonationEdgeCases:
    """Tests for donation report edge cases with different years."""

    def test_donation_report_2025(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/donations/2025/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2025

    def test_donation_report_2024(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/donations/2024/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2024

    def test_donation_report_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/reports/donations/2026/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_donation_report_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/donations/2026/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_donation_report_response_fields(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/donations/2026/')
        assert response.status_code == status.HTTP_200_OK
        assert 'year' in response.data
        assert 'total' in response.data
        assert 'total_count' in response.data
        assert 'unique_donors' in response.data
        assert 'monthly' in response.data
        assert 'top_donors' in response.data
        assert 'campaigns' in response.data


@pytest.mark.django_db
class TestReportVolunteerEdgeCases:
    """Tests for volunteer report edge cases."""

    def test_volunteer_report_with_valid_dates(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/volunteers/?start_date=2025-01-01&end_date=2025-12-31'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['start_date'] == '2025-01-01'
        assert response.data['end_date'] == '2025-12-31'

    def test_volunteer_report_with_invalid_start_date(self, api_client, pastor_user):
        """Invalid start_date falls back to None."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/volunteers/?start_date=invalid'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_volunteer_report_with_invalid_end_date(self, api_client, pastor_user):
        """Invalid end_date falls back to None."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/volunteers/?end_date=invalid'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_volunteer_report_with_both_invalid_dates(self, api_client, pastor_user):
        """Both invalid dates fall back to defaults."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get(
            '/api/v1/reports/reports/volunteers/?start_date=bad&end_date=bad'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_volunteer_report_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/reports/volunteers/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_volunteer_report_denied_for_regular_member(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/volunteers/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_volunteer_report_response_fields(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/volunteers/')
        assert response.status_code == status.HTTP_200_OK
        assert 'start_date' in response.data
        assert 'end_date' in response.data
        assert 'total_shifts' in response.data
        assert 'completed' in response.data
        assert 'no_shows' in response.data
        assert 'by_position' in response.data
        assert 'top_volunteers' in response.data


@pytest.mark.django_db
class TestTreasurerDonationReportEdgeCases:
    """Tests for treasurer donation report edge cases."""

    def test_treasurer_report_with_year(self, api_client):
        user = UserFactory()
        TreasurerFactory(user=user)
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/2025/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2025

    def test_treasurer_report_without_year_uses_current(self, api_client):
        user = UserFactory()
        TreasurerFactory(user=user)
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year

    def test_treasurer_report_requires_auth(self, api_client):
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_pastor_can_access_treasurer_report(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_200_OK

    def test_pastor_can_access_treasurer_report_with_year(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/2024/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2024

    def test_admin_can_access_treasurer_report(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_200_OK

    def test_treasurer_report_response_fields(self, api_client):
        user = UserFactory()
        TreasurerFactory(user=user)
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert 'year' in response.data
        assert 'total' in response.data
        assert 'total_count' in response.data
        assert 'unique_donors' in response.data
        assert 'monthly' in response.data

    def test_member_cannot_access_treasurer_report_with_year(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/treasurer/donations/2025/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDashboardAdminAccess:
    """Tests for Dashboard admin access."""

    def test_admin_can_access_dashboard(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_member_stats(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/members/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_events(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/events/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_help_requests(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/dashboard/help_requests/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_reports_attendance(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/attendance/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_reports_volunteers(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/volunteers/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_reports_donations(self, api_client):
        user = UserFactory()
        MemberFactory(user=user, role='admin')
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/reports/reports/donations/2026/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestReportDonationYearFallback:
    """Tests for ReportViewSet.donations when year is invalid (lines 112-113)."""

    def test_donations_none_year_falls_back_to_current(self, pastor_user):
        """When year=None, falls back to current year via TypeError."""
        user, member = pastor_user
        factory = APIRequestFactory()
        request = factory.get('/')
        force_authenticate(request, user=user)
        view = ReportViewSet.as_view({'get': 'donations'})
        response = view(request, year=None)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year

    def test_donations_invalid_year_falls_back_to_current(self, pastor_user):
        """When year is an unparseable string, falls back to current year via ValueError."""
        user, member = pastor_user
        factory = APIRequestFactory()
        request = factory.get('/')
        force_authenticate(request, user=user)
        view = ReportViewSet.as_view({'get': 'donations'})
        response = view(request, year='abc')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year


@pytest.mark.django_db
class TestTreasurerDonationYearFallback:
    """Tests for TreasurerDonationReportView.get when year is invalid (lines 150-151)."""

    def test_treasurer_invalid_year_falls_back_to_current(self):
        """When year is an invalid string, falls back to current year."""
        user = UserFactory()
        MemberFactory(user=user, role='pastor')
        factory = APIRequestFactory()
        request = factory.get('/')
        force_authenticate(request, user=user)
        view = TreasurerDonationReportView.as_view()
        response = view(request, year='abc')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year

    def test_treasurer_none_year_uses_current(self):
        """When year is not provided (None), uses current year."""
        user = UserFactory()
        MemberFactory(user=user, role='treasurer')
        factory = APIRequestFactory()
        request = factory.get('/')
        force_authenticate(request, user=user)
        view = TreasurerDonationReportView.as_view()
        response = view(request, year=None)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == date.today().year
