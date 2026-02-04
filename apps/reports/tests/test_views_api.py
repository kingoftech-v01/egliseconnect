"""Reports API view tests."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.members.tests.factories import MemberFactory, UserFactory


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
    """Tests for Dashboard API."""

    def test_dashboard_requires_auth(self, api_client):
        """Test dashboard requires authentication."""
        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_requires_pastor_role(self, api_client, member_user):
        """Test dashboard requires pastor/admin role."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_accessible_by_pastor(self, api_client, pastor_user):
        """Test pastor can access dashboard."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'members' in response.data
        assert 'donations' in response.data

    def test_member_stats_endpoint(self, api_client, pastor_user):
        """Test member stats endpoint."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/dashboard/members/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'active' in response.data

    def test_donation_stats_endpoint(self, api_client, pastor_user):
        """Test donation stats endpoint."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/dashboard/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_amount' in response.data

    def test_donation_stats_with_year(self, api_client, pastor_user):
        """Test donation stats with year parameter."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/dashboard/donations/?year=2025')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2025

    def test_birthdays_endpoint(self, api_client, pastor_user):
        """Test birthdays endpoint."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/dashboard/birthdays/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestReportAPI:
    """Tests for Report API."""

    def test_attendance_report(self, api_client, pastor_user):
        """Test attendance report endpoint."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/reports/attendance/')
        assert response.status_code == status.HTTP_200_OK
        assert 'events' in response.data

    def test_donation_report(self, api_client, pastor_user):
        """Test donation report endpoint."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/reports/donations/2026/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year'] == 2026

    def test_volunteer_report(self, api_client, pastor_user):
        """Test volunteer report endpoint."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/reports/volunteers/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_shifts' in response.data


@pytest.mark.django_db
class TestTreasurerAccess:
    """Tests for treasurer-specific access."""

    def test_treasurer_can_access_donation_report(self, api_client):
        """Test treasurer can access donation reports."""
        user = UserFactory()
        member = MemberFactory(user=user, role='treasurer')
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_200_OK

    def test_member_cannot_access_treasurer_reports(self, api_client, member_user):
        """Test regular member cannot access treasurer reports."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/reports/treasurer/donations/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
