"""Tests for giving goals (P1-4)."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles
from apps.donations.models import GivingGoal
from apps.members.tests.factories import MemberFactory, UserFactory

from .factories import DonationFactory, GivingGoalFactory


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
class TestGivingGoalModel:
    """Tests for GivingGoal model."""

    def test_create_goal(self):
        """Goal creation works with defaults."""
        goal = GivingGoalFactory()
        assert goal.id is not None
        assert goal.year == 2026
        assert goal.target_amount == Decimal('5000.00')

    def test_goal_str(self):
        """String representation includes member, year and amount."""
        goal = GivingGoalFactory()
        assert str(goal.year) in str(goal)
        assert str(goal.target_amount) in str(goal)

    def test_unique_together_member_year(self):
        """Cannot create duplicate goal for same member/year."""
        member = MemberFactory()
        GivingGoalFactory(member=member, year=2026)

        with pytest.raises(Exception):
            GivingGoalFactory(member=member, year=2026)

    def test_current_amount_no_donations(self):
        """current_amount is 0 with no donations."""
        goal = GivingGoalFactory()
        assert goal.current_amount == Decimal('0.00')

    def test_current_amount_with_donations(self):
        """current_amount sums donations for the member in the target year."""
        member = MemberFactory()
        goal = GivingGoalFactory(member=member, year=2026)

        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('500.00'))
        DonationFactory(member=member, date=date(2026, 6, 20), amount=Decimal('300.00'))

        assert goal.current_amount == Decimal('800.00')

    def test_current_amount_excludes_other_years(self):
        """current_amount only includes donations in the target year."""
        member = MemberFactory()
        goal = GivingGoalFactory(member=member, year=2026)

        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('500.00'))
        DonationFactory(member=member, date=date(2025, 3, 15), amount=Decimal('300.00'))

        assert goal.current_amount == Decimal('500.00')

    def test_progress_percentage(self):
        """progress_percentage calculates correctly."""
        member = MemberFactory()
        goal = GivingGoalFactory(member=member, year=2026, target_amount=Decimal('1000.00'))
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('250.00'))

        assert goal.progress_percentage == 25

    def test_progress_percentage_capped_at_100(self):
        """progress_percentage capped at 100 when goal exceeded."""
        member = MemberFactory()
        goal = GivingGoalFactory(member=member, year=2026, target_amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('150.00'))

        assert goal.progress_percentage == 100

    def test_progress_percentage_zero_target(self):
        """progress_percentage returns 0 for zero-target goal."""
        goal = GivingGoalFactory(target_amount=Decimal('0.00'))
        assert goal.progress_percentage == 0

    def test_remaining_amount(self):
        """remaining_amount calculates amount left."""
        member = MemberFactory()
        goal = GivingGoalFactory(member=member, year=2026, target_amount=Decimal('1000.00'))
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('600.00'))

        assert goal.remaining_amount == Decimal('400.00')

    def test_remaining_amount_never_negative(self):
        """remaining_amount never goes below zero."""
        member = MemberFactory()
        goal = GivingGoalFactory(member=member, year=2026, target_amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2026, 3, 15), amount=Decimal('150.00'))

        assert goal.remaining_amount == Decimal('0.00')


# ==============================================================================
# View Tests
# ==============================================================================


@pytest.mark.django_db
class TestGoalCreateView:
    """Tests for goal_create view."""

    def test_member_can_access_goal_form(self):
        """Authenticated member can access goal creation form."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/goals/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_post_valid_goal(self):
        """Creating a goal with valid data succeeds."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        data = {
            'year': 2026,
            'target_amount': '3000.00',
        }
        response = client.post('/donations/goals/', data)
        assert response.status_code == 302
        assert GivingGoal.objects.filter(member=member, year=2026).exists()

    def test_update_existing_goal(self):
        """Updating an existing goal works."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        goal = GivingGoalFactory(member=member, year=2026, target_amount=Decimal('2000.00'))

        data = {
            'year': 2026,
            'target_amount': '3000.00',
        }
        response = client.post('/donations/goals/', data)
        assert response.status_code == 302
        goal.refresh_from_db()
        assert goal.target_amount == Decimal('3000.00')

    def test_unauthenticated_redirects(self):
        """Unauthenticated user is redirected."""
        client = Client()
        response = client.get('/donations/goals/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestGoalReportView:
    """Tests for goal_report view."""

    def test_finance_staff_can_access_report(self):
        """Treasurer can access goal report."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        GivingGoalFactory()

        response = client.get('/donations/goals/report/')
        assert response.status_code == 200
        assert 'goals' in response.context
        assert 'year' in response.context

    def test_regular_member_cannot_access_report(self):
        """Regular member cannot access goal report."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/goals/report/')
        assert response.status_code == 302

    def test_year_filter(self):
        """Report respects year filter."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/goals/report/?year=2025')
        assert response.status_code == 200
        assert response.context['year'] == 2025
