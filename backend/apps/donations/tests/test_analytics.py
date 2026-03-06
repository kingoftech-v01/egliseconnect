"""Tests for giving analytics dashboard (P2-3)."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles
from apps.members.tests.factories import MemberFactory, UserFactory

from .factories import DonationFactory


def make_member_with_user(role=Roles.MEMBER):
    """Create a member with a linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=role)
    return user, member


def make_logged_in_client(user):
    """Create a Django test client logged in as the given user."""
    client = Client()
    client.force_login(user)
    return client


# ==============================================================================
# Service Tests
# ==============================================================================


@pytest.mark.django_db
class TestGivingAnalyticsService:
    """Tests for GivingAnalyticsService."""

    def test_giving_trends_monthly(self):
        """giving_trends returns monthly data."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 1, 15), amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2026, 2, 15), amount=Decimal('200.00'))

        trends = GivingAnalyticsService.giving_trends('monthly', 2026)
        assert isinstance(trends, list)
        assert len(trends) > 0

    def test_giving_trends_quarterly(self):
        """giving_trends returns quarterly data."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 3, 15))

        trends = GivingAnalyticsService.giving_trends('quarterly', 2026)
        assert isinstance(trends, list)

    def test_yoy_comparison(self):
        """yoy_comparison compares current and previous year."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2025, 3, 15), amount=Decimal('80.00'))

        result = GivingAnalyticsService.yoy_comparison(2026)
        assert 'current_data' in result
        assert 'previous_data' in result
        assert 'previous_year' in result

    def test_donor_retention(self):
        """donor_retention identifies new, returning, and lapsed donors."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member1 = MemberFactory()
        member2 = MemberFactory()
        # member1 donated both years
        DonationFactory(member=member1, date=date(2025, 6, 1))
        DonationFactory(member=member1, date=date(2026, 6, 1))
        # member2 only donated in 2025 (lapsed)
        DonationFactory(member=member2, date=date(2025, 6, 1))

        retention = GivingAnalyticsService.donor_retention(2026)
        assert 'new_donors' in retention
        assert 'returning_donors' in retention
        assert 'lapsed_donors' in retention
        assert 'retention_rate' in retention

    def test_avg_gift_size(self):
        """avg_gift_size returns list of period averages."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 1, 15), amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2026, 2, 15), amount=Decimal('200.00'))

        avg = GivingAnalyticsService.avg_gift_size(2026)
        assert isinstance(avg, list)
        assert len(avg) > 0

    def test_avg_gift_size_no_donations(self):
        """avg_gift_size returns empty list when no donations."""
        from apps.donations.services_analytics import GivingAnalyticsService

        avg = GivingAnalyticsService.avg_gift_size(2099)
        assert isinstance(avg, list)
        assert len(avg) == 0

    def test_first_time_donors(self):
        """first_time_donors identifies members donating for first time."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 3, 15))

        first_time = GivingAnalyticsService.first_time_donors(2026)
        assert isinstance(first_time, list)

    def test_top_donors(self):
        """top_donors returns sorted list of top donors."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member1 = MemberFactory()
        member2 = MemberFactory()
        DonationFactory(member=member1, date=date(2026, 3, 15), amount=Decimal('1000.00'))
        DonationFactory(member=member2, date=date(2026, 3, 15), amount=Decimal('500.00'))

        top = GivingAnalyticsService.top_donors(2026, limit=10)
        assert isinstance(top, list)
        assert len(top) == 2
        # First donor should have highest total
        assert top[0]['total_amount'] >= top[1]['total_amount']

    def test_dashboard_summary(self):
        """dashboard_summary returns aggregated data."""
        from apps.donations.services_analytics import GivingAnalyticsService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('100.00'))

        summary = GivingAnalyticsService.dashboard_summary(2026)
        assert 'total_amount' in summary
        assert 'total_count' in summary
        assert 'avg_amount' in summary
        assert 'monthly_trends' in summary
        assert 'yoy_comparison' in summary
        assert 'retention' in summary
        assert 'top_donors' in summary
        assert 'first_time_donors' in summary


# ==============================================================================
# View Tests
# ==============================================================================


@pytest.mark.django_db
class TestAnalyticsDashboardView:
    """Tests for analytics_dashboard view."""

    def test_finance_staff_can_access(self):
        """Treasurer can access analytics dashboard."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        DonationFactory(date=date(2026, 3, 15))

        response = client.get('/donations/analytics/')
        assert response.status_code == 200
        assert 'data' in response.context
        assert 'year' in response.context
        assert 'monthly_labels_json' in response.context
        assert 'monthly_amounts_json' in response.context

    def test_regular_member_cannot_access(self):
        """Regular member cannot access analytics."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/analytics/')
        assert response.status_code == 302

    def test_year_filter(self):
        """Dashboard respects year filter."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/analytics/?year=2025')
        assert response.status_code == 200
        assert response.context['year'] == 2025

    def test_invalid_year_defaults_to_current(self):
        """Invalid year parameter defaults to current year."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/analytics/?year=abc')
        assert response.status_code == 200
        assert response.context['year'] == timezone.now().year

    def test_unauthenticated_redirects(self):
        """Unauthenticated user is redirected."""
        client = Client()
        response = client.get('/donations/analytics/')
        assert response.status_code == 302
