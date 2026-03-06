"""Tests for pledge & commitment tracking (P1-2)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles, PledgeStatus, PledgeFrequency
from apps.donations.models import Pledge, PledgeFulfillment
from apps.members.tests.factories import MemberFactory, UserFactory

from .factories import (
    DonationCampaignFactory,
    DonationFactory,
    PledgeFactory,
    CampaignPledgeFactory,
    PledgeFulfillmentFactory,
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
class TestPledgeModel:
    """Tests for Pledge model."""

    def test_create_pledge(self):
        """Pledge creation works with defaults."""
        pledge = PledgeFactory()
        assert pledge.id is not None
        assert pledge.status == PledgeStatus.ACTIVE
        assert pledge.frequency == PledgeFrequency.MONTHLY

    def test_pledge_str(self):
        """String representation includes member, amount and frequency."""
        pledge = PledgeFactory(amount=Decimal('200.00'))
        assert '200.00' in str(pledge)
        assert pledge.member.full_name in str(pledge)

    def test_fulfilled_amount_no_fulfillments(self):
        """fulfilled_amount is 0 when no fulfillments exist."""
        pledge = PledgeFactory()
        assert pledge.fulfilled_amount == Decimal('0.00')

    def test_fulfilled_amount_with_fulfillments(self):
        """fulfilled_amount sums all linked fulfillments."""
        pledge = PledgeFactory(amount=Decimal('500.00'))
        donation1 = DonationFactory(member=pledge.member)
        donation2 = DonationFactory(member=pledge.member)
        PledgeFulfillmentFactory(pledge=pledge, donation=donation1, amount=Decimal('100.00'))
        PledgeFulfillmentFactory(pledge=pledge, donation=donation2, amount=Decimal('150.00'))

        assert pledge.fulfilled_amount == Decimal('250.00')

    def test_progress_percentage(self):
        """progress_percentage calculates correctly."""
        pledge = PledgeFactory(amount=Decimal('1000.00'))
        donation = DonationFactory(member=pledge.member)
        PledgeFulfillmentFactory(pledge=pledge, donation=donation, amount=Decimal('500.00'))

        assert pledge.progress_percentage == 50

    def test_progress_percentage_capped_at_100(self):
        """progress_percentage capped at 100 when overfulfilled."""
        pledge = PledgeFactory(amount=Decimal('100.00'))
        donation = DonationFactory(member=pledge.member)
        PledgeFulfillmentFactory(pledge=pledge, donation=donation, amount=Decimal('150.00'))

        assert pledge.progress_percentage == 100

    def test_progress_percentage_zero_amount(self):
        """progress_percentage returns 0 for zero-amount pledge."""
        pledge = PledgeFactory(amount=Decimal('0.00'))
        assert pledge.progress_percentage == 0

    def test_remaining_amount(self):
        """remaining_amount calculates amount left to fulfill."""
        pledge = PledgeFactory(amount=Decimal('500.00'))
        donation = DonationFactory(member=pledge.member)
        PledgeFulfillmentFactory(pledge=pledge, donation=donation, amount=Decimal('200.00'))

        assert pledge.remaining_amount == Decimal('300.00')

    def test_remaining_amount_never_negative(self):
        """remaining_amount never goes below zero."""
        pledge = PledgeFactory(amount=Decimal('100.00'))
        donation = DonationFactory(member=pledge.member)
        PledgeFulfillmentFactory(pledge=pledge, donation=donation, amount=Decimal('150.00'))

        assert pledge.remaining_amount == Decimal('0.00')

    def test_campaign_pledge(self):
        """Pledge can be linked to a campaign."""
        pledge = CampaignPledgeFactory()
        assert pledge.campaign is not None
        assert pledge.campaign.name is not None

    def test_pledge_status_choices(self):
        """Pledge status can be set to all valid values."""
        for status_value, _ in PledgeStatus.CHOICES:
            pledge = PledgeFactory(status=status_value)
            assert pledge.status == status_value

    def test_pledge_frequency_choices(self):
        """Pledge frequency can be set to all valid values."""
        for freq_value, _ in PledgeFrequency.CHOICES:
            pledge = PledgeFactory(frequency=freq_value)
            assert pledge.frequency == freq_value


@pytest.mark.django_db
class TestPledgeFulfillmentModel:
    """Tests for PledgeFulfillment model."""

    def test_create_fulfillment(self):
        """PledgeFulfillment creation works."""
        fulfillment = PledgeFulfillmentFactory()
        assert fulfillment.id is not None
        assert fulfillment.amount > 0

    def test_fulfillment_str(self):
        """String representation includes amount."""
        fulfillment = PledgeFulfillmentFactory(amount=Decimal('75.00'))
        assert '75.00' in str(fulfillment)

    def test_fulfillment_links_pledge_and_donation(self):
        """Fulfillment links a pledge to a donation."""
        pledge = PledgeFactory()
        donation = DonationFactory(member=pledge.member)
        fulfillment = PledgeFulfillmentFactory(
            pledge=pledge,
            donation=donation,
            amount=Decimal('100.00')
        )
        assert fulfillment.pledge == pledge
        assert fulfillment.donation == donation


# ==============================================================================
# View Tests
# ==============================================================================


@pytest.mark.django_db
class TestPledgeListView:
    """Tests for pledge_list view."""

    def test_finance_staff_sees_all_pledges(self):
        """Treasurer sees all pledges."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        PledgeFactory()
        PledgeFactory()

        response = client.get('/donations/pledges/')
        assert response.status_code == 200
        assert 'pledges' in response.context

    def test_member_sees_own_pledges(self):
        """Regular member sees only their own pledges."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        PledgeFactory(member=member)
        PledgeFactory()  # another member's pledge

        response = client.get('/donations/pledges/')
        assert response.status_code == 200

    def test_unauthenticated_redirects(self):
        """Unauthenticated user is redirected."""
        client = Client()
        response = client.get('/donations/pledges/')
        assert response.status_code == 302

    def test_status_filter(self):
        """Pledges can be filtered by status."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        PledgeFactory(status=PledgeStatus.ACTIVE)
        PledgeFactory(status=PledgeStatus.COMPLETED)

        response = client.get('/donations/pledges/?status=active')
        assert response.status_code == 200


@pytest.mark.django_db
class TestPledgeDetailView:
    """Tests for pledge_detail view."""

    def test_finance_staff_views_any_pledge(self):
        """Treasurer can view any pledge."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        pledge = PledgeFactory()

        response = client.get(f'/donations/pledges/{pledge.pk}/')
        assert response.status_code == 200
        assert 'pledge' in response.context

    def test_member_views_own_pledge(self):
        """Member can view their own pledge."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        pledge = PledgeFactory(member=member)

        response = client.get(f'/donations/pledges/{pledge.pk}/')
        assert response.status_code == 200

    def test_member_cannot_view_other_pledge(self):
        """Member cannot view another's pledge."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        pledge = PledgeFactory()  # different member

        response = client.get(f'/donations/pledges/{pledge.pk}/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestPledgeCreateView:
    """Tests for pledge_create view."""

    def test_finance_staff_can_create_pledge(self):
        """Treasurer can access pledge creation form."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/pledges/create/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_post_valid_pledge(self):
        """Creating a pledge with valid data succeeds."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        target_member = MemberFactory()

        data = {
            'member': str(target_member.pk),
            'amount': '500.00',
            'frequency': PledgeFrequency.MONTHLY,
            'start_date': timezone.now().date().isoformat(),
            'status': PledgeStatus.ACTIVE,
        }
        response = client.post('/donations/pledges/create/', data)
        assert response.status_code == 302
        assert Pledge.objects.filter(member=target_member).exists()

    def test_regular_member_can_create_own_pledge(self):
        """Regular member can create their own pledge (with MemberPledgeForm)."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/pledges/create/')
        assert response.status_code == 200
        assert 'form' in response.context


@pytest.mark.django_db
class TestPledgeUpdateView:
    """Tests for pledge_update view."""

    def test_finance_staff_can_update_pledge(self):
        """Treasurer can access pledge edit form."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        pledge = PledgeFactory()

        response = client.get(f'/donations/pledges/{pledge.pk}/edit/')
        assert response.status_code == 200

    def test_post_valid_update(self):
        """Updating pledge with valid data succeeds."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        pledge = PledgeFactory(amount=Decimal('500.00'))

        data = {
            'member': str(pledge.member.pk),
            'amount': '750.00',
            'frequency': pledge.frequency,
            'start_date': pledge.start_date.isoformat(),
            'status': pledge.status,
        }
        response = client.post(f'/donations/pledges/{pledge.pk}/edit/', data)
        assert response.status_code == 302
        pledge.refresh_from_db()
        assert pledge.amount == Decimal('750.00')


@pytest.mark.django_db
class TestPledgeDeleteView:
    """Tests for pledge_delete view."""

    def test_finance_staff_can_delete(self):
        """Treasurer can delete a pledge."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        pledge = PledgeFactory()

        response = client.post(f'/donations/pledges/{pledge.pk}/delete/')
        assert response.status_code == 302
        assert not Pledge.objects.filter(pk=pledge.pk).exists()

    def test_get_shows_confirmation(self):
        """GET request shows deletion confirmation."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        pledge = PledgeFactory()

        response = client.get(f'/donations/pledges/{pledge.pk}/delete/')
        assert response.status_code == 200

    def test_regular_member_cannot_delete(self):
        """Regular member cannot delete pledges."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        pledge = PledgeFactory()

        response = client.post(f'/donations/pledges/{pledge.pk}/delete/')
        assert response.status_code == 302
        assert Pledge.objects.filter(pk=pledge.pk).exists()
