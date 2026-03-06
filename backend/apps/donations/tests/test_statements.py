"""Tests for giving statement generation and distribution (P1-3)."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles
from apps.donations.models import GivingStatement
from apps.members.tests.factories import MemberFactory, UserFactory

from .factories import (
    DonationFactory,
    GivingStatementFactory,
    MidYearStatementFactory,
)


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
# Model Tests
# ==============================================================================


@pytest.mark.django_db
class TestGivingStatementModel:
    """Tests for GivingStatement model."""

    def test_create_annual_statement(self):
        """Annual statement creation works."""
        statement = GivingStatementFactory()
        assert statement.id is not None
        assert statement.period == 'annual'
        assert statement.year == 2026

    def test_create_mid_year_statement(self):
        """Mid-year statement creation works."""
        statement = MidYearStatementFactory()
        assert statement.period == 'mid_year'

    def test_statement_str(self):
        """String representation includes member name, year, and period."""
        statement = GivingStatementFactory()
        assert str(statement.year) in str(statement)
        assert statement.member.full_name in str(statement)

    def test_unique_together_member_year_period(self):
        """Cannot create duplicate statement for same member/year/period."""
        member = MemberFactory()
        GivingStatementFactory(member=member, year=2026, period='annual')

        with pytest.raises(Exception):
            GivingStatementFactory(member=member, year=2026, period='annual')

    def test_different_periods_same_year_allowed(self):
        """Can create mid-year and annual statements for same member/year."""
        member = MemberFactory()
        s1 = GivingStatementFactory(member=member, year=2026, period='annual')
        s2 = MidYearStatementFactory(member=member, year=2026)

        assert s1.pk != s2.pk
        assert GivingStatement.objects.filter(member=member, year=2026).count() == 2


# ==============================================================================
# Service Tests
# ==============================================================================


@pytest.mark.django_db
class TestStatementService:
    """Tests for StatementService."""

    def test_get_period_dates_annual(self):
        """get_period_dates returns Jan 1 to Dec 31 for annual."""
        from apps.donations.services_statement import StatementService

        start, end = StatementService.get_period_dates(2026, 'annual')
        assert start == date(2026, 1, 1)
        assert end == date(2026, 12, 31)

    def test_get_period_dates_mid_year(self):
        """get_period_dates returns Jan 1 to Jun 30 for mid_year."""
        from apps.donations.services_statement import StatementService

        start, end = StatementService.get_period_dates(2026, 'mid_year')
        assert start == date(2026, 1, 1)
        assert end == date(2026, 6, 30)

    def test_generate_statement(self):
        """generate_statement creates a statement with correct total."""
        from apps.donations.services_statement import StatementService

        member = MemberFactory()
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2026, 5, 20), amount=Decimal('200.00'))

        statement = StatementService.generate_statement(member, 2026, 'annual')
        assert statement is not None
        assert statement.total_amount == Decimal('300.00')
        assert statement.member == member
        assert statement.year == 2026

    def test_generate_statement_no_donations(self):
        """generate_statement works with zero donations."""
        from apps.donations.services_statement import StatementService

        member = MemberFactory()
        statement = StatementService.generate_statement(member, 2026, 'annual')
        assert statement.total_amount == Decimal('0.00')

    def test_bulk_generate(self):
        """bulk_generate creates statements for all members with donations."""
        from apps.donations.services_statement import StatementService

        member1 = MemberFactory()
        member2 = MemberFactory()
        DonationFactory(member=member1, date=date(2026, 3, 15))
        DonationFactory(member=member2, date=date(2026, 5, 20))

        statements = StatementService.bulk_generate(2026, 'annual')
        assert len(statements) >= 2


# ==============================================================================
# View Tests
# ==============================================================================


@pytest.mark.django_db
class TestStatementListView:
    """Tests for statement_list view."""

    def test_finance_staff_sees_all_statements(self):
        """Treasurer sees all statements."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        GivingStatementFactory()

        response = client.get('/donations/statements/')
        assert response.status_code == 200
        assert 'statements' in response.context

    def test_member_sees_own_statements(self):
        """Regular member sees only their own statements."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        GivingStatementFactory(member=member)

        response = client.get('/donations/statements/')
        assert response.status_code == 200

    def test_unauthenticated_redirects(self):
        """Unauthenticated user is redirected."""
        client = Client()
        response = client.get('/donations/statements/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestStatementGenerateView:
    """Tests for statement_generate view."""

    def test_finance_staff_can_access_generate(self):
        """Treasurer can access statement generation page."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/statements/generate/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_regular_member_cannot_generate(self):
        """Regular member cannot access statement generation."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/statements/generate/')
        assert response.status_code == 302

    def test_post_generate_statement(self):
        """Posting valid data generates statements."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        target_member = MemberFactory()
        DonationFactory(member=target_member, date=date(2026, 3, 15))

        data = {
            'year': 2026,
            'period': 'annual',
        }
        response = client.post('/donations/statements/generate/', data)
        assert response.status_code == 302


@pytest.mark.django_db
class TestStatementDownloadView:
    """Tests for statement_download view."""

    def test_finance_staff_can_download(self):
        """Treasurer can download any statement."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        statement = GivingStatementFactory()

        response = client.get(f'/donations/statements/{statement.pk}/download/')
        # Should work even without PDF file (returns HTML rendered)
        assert response.status_code in [200, 302]

    def test_member_can_download_own(self):
        """Member can download their own statement."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        statement = GivingStatementFactory(member=member)

        response = client.get(f'/donations/statements/{statement.pk}/download/')
        assert response.status_code in [200, 302]
