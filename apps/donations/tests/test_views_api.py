"""
Tests for donations API views.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.constants import DonationType, PaymentMethod, Roles
from apps.donations.models import Donation, DonationCampaign, TaxReceipt
from apps.members.tests.factories import (
    AdminMemberFactory,
    MemberFactory,
    MemberWithUserFactory,
    PastorFactory,
    TreasurerFactory,
    UserFactory,
)

from .factories import (
    DonationCampaignFactory,
    DonationFactory,
    TaxReceiptFactory,
)

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================


def make_member_with_user(role=Roles.MEMBER):
    """Create a member with a linked user account and return (user, member)."""
    user = UserFactory()
    member = MemberFactory(user=user, role=role)
    return user, member


def make_api_client(user=None):
    """Create an APIClient, optionally authenticated."""
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


# =============================================================================
# DONATION VIEWSET TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationViewSetList:
    """Tests for DonationViewSet list action."""

    def test_list_donations_unauthenticated(self):
        """Unauthenticated user cannot list donations."""
        client = make_api_client()
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_donations_regular_member_sees_own(self):
        """Regular member sees only their own donations."""
        user, member = make_member_with_user(Roles.MEMBER)
        other_member = MemberFactory()
        own_donation = DonationFactory(member=member)
        other_donation = DonationFactory(member=other_member)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_200_OK
        donation_ids = [d['id'] for d in response.data['results']]
        assert str(own_donation.pk) in donation_ids
        assert str(other_donation.pk) not in donation_ids

    def test_list_donations_treasurer_sees_all(self):
        """Treasurer sees all donations."""
        user, member = make_member_with_user(Roles.TREASURER)
        other_member = MemberFactory()
        DonationFactory(member=member)
        DonationFactory(member=other_member)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_donations_pastor_sees_all(self):
        """Pastor sees all donations."""
        user, member = make_member_with_user(Roles.PASTOR)
        DonationFactory()
        DonationFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_donations_admin_sees_all(self):
        """Admin sees all donations."""
        user, member = make_member_with_user(Roles.ADMIN)
        DonationFactory()
        DonationFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_donations_staff_user_sees_all(self):
        """Django staff user sees all donations."""
        user = UserFactory(is_staff=True)
        DonationFactory()
        DonationFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_donations_user_without_member_profile(self):
        """User without member profile sees empty list."""
        user = UserFactory()
        DonationFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestDonationViewSetRetrieve:
    """Tests for DonationViewSet retrieve action."""

    def test_retrieve_own_donation(self):
        """Member can retrieve their own donation."""
        user, member = make_member_with_user(Roles.MEMBER)
        donation = DonationFactory(member=member)

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/donations/{donation.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(donation.pk)

    def test_retrieve_other_donation_as_member_fails(self):
        """Regular member cannot retrieve another member's donation."""
        user, member = make_member_with_user(Roles.MEMBER)
        other_donation = DonationFactory()

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/donations/{other_donation.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_any_donation_as_treasurer(self):
        """Treasurer can retrieve any donation."""
        user, member = make_member_with_user(Roles.TREASURER)
        donation = DonationFactory()

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/donations/{donation.pk}/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDonationViewSetCreate:
    """Tests for DonationViewSet create action."""

    def test_create_donation(self):
        """Authenticated member can create a donation."""
        user, member = make_member_with_user(Roles.MEMBER)
        campaign = DonationCampaignFactory()

        client = make_api_client(user)
        data = {
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
            'campaign': str(campaign.pk),
            'notes': 'Test donation',
        }
        response = client.post('/api/v1/donations/donations/', data)
        assert response.status_code == status.HTTP_201_CREATED
        # DonationCreateSerializer returns only amount, donation_type, campaign, notes
        donation = Donation.objects.filter(member=member).first()
        assert donation is not None
        assert donation.member == member
        assert donation.payment_method == PaymentMethod.ONLINE
        assert donation.amount == Decimal('50.00')

    def test_create_donation_without_campaign(self):
        """Donation can be created without a campaign."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        data = {
            'amount': '25.00',
            'donation_type': DonationType.TITHE,
        }
        response = client.post('/api/v1/donations/donations/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_donation_without_member_profile(self):
        """User without member profile cannot create donation."""
        user = UserFactory()

        client = make_api_client(user)
        data = {
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
        }
        response = client.post('/api/v1/donations/donations/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_donation_unauthenticated(self):
        """Unauthenticated user cannot create donation."""
        client = make_api_client()
        data = {
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
        }
        response = client.post('/api/v1/donations/donations/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_donation_negative_amount(self):
        """Cannot create donation with negative amount."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        data = {
            'amount': '-10.00',
            'donation_type': DonationType.OFFERING,
        }
        response = client.post('/api/v1/donations/donations/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_donation_zero_amount(self):
        """Cannot create donation with zero amount."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        data = {
            'amount': '0.00',
            'donation_type': DonationType.OFFERING,
        }
        response = client.post('/api/v1/donations/donations/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDonationViewSetUpdate:
    """Tests for DonationViewSet update action."""

    def test_update_donation_as_treasurer(self):
        """Treasurer can update a donation."""
        user, member = make_member_with_user(Roles.TREASURER)
        donation = DonationFactory()

        client = make_api_client(user)
        data = {
            'amount': '200.00',
            'member': str(donation.member.pk),
            'donation_type': DonationType.TITHE,
            'payment_method': PaymentMethod.CASH,
            'date': donation.date.isoformat(),
        }
        response = client.put(f'/api/v1/donations/donations/{donation.pk}/', data)
        assert response.status_code == status.HTTP_200_OK
        donation.refresh_from_db()
        assert donation.amount == Decimal('200.00')

    def test_update_donation_as_regular_member_fails(self):
        """Regular member cannot update a donation."""
        user, member = make_member_with_user(Roles.MEMBER)
        donation = DonationFactory(member=member)

        client = make_api_client(user)
        data = {
            'amount': '200.00',
            'donation_type': DonationType.OFFERING,
        }
        response = client.put(f'/api/v1/donations/donations/{donation.pk}/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_as_finance_staff(self):
        """Finance staff can partially update a donation."""
        user, member = make_member_with_user(Roles.PASTOR)
        donation = DonationFactory()

        client = make_api_client(user)
        response = client.patch(
            f'/api/v1/donations/donations/{donation.pk}/',
            {'notes': 'Updated note'},
        )
        assert response.status_code == status.HTTP_200_OK
        donation.refresh_from_db()
        assert donation.notes == 'Updated note'


@pytest.mark.django_db
class TestDonationViewSetDelete:
    """Tests for DonationViewSet delete action."""

    def test_delete_donation_as_treasurer(self):
        """Treasurer can delete (soft-delete) a donation."""
        user, member = make_member_with_user(Roles.TREASURER)
        donation = DonationFactory()

        client = make_api_client(user)
        response = client.delete(f'/api/v1/donations/donations/{donation.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_donation_as_regular_member_fails(self):
        """Regular member cannot delete a donation."""
        user, member = make_member_with_user(Roles.MEMBER)
        donation = DonationFactory(member=member)

        client = make_api_client(user)
        response = client.delete(f'/api/v1/donations/donations/{donation.pk}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationViewSetMyHistory:
    """Tests for DonationViewSet my_history action."""

    def test_my_history(self):
        """Member can get their donation history."""
        user, member = make_member_with_user(Roles.MEMBER)
        donation1 = DonationFactory(member=member, date=date(2026, 1, 15))
        donation2 = DonationFactory(member=member, date=date(2026, 2, 15))
        DonationFactory()  # another member's donation

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/my-history/')
        assert response.status_code == status.HTTP_200_OK
        donation_ids = [d['id'] for d in response.data['results']]
        assert str(donation1.pk) in donation_ids
        assert str(donation2.pk) in donation_ids

    def test_my_history_with_year_filter(self):
        """Member can filter history by year."""
        user, member = make_member_with_user(Roles.MEMBER)
        donation_2026 = DonationFactory(member=member, date=date(2026, 6, 1))
        donation_2025 = DonationFactory(member=member, date=date(2025, 6, 1))

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/my-history/?year=2026')
        assert response.status_code == status.HTTP_200_OK
        donation_ids = [d['id'] for d in response.data['results']]
        assert str(donation_2026.pk) in donation_ids
        assert str(donation_2025.pk) not in donation_ids

    def test_my_history_with_invalid_year(self):
        """Invalid year parameter is ignored."""
        user, member = make_member_with_user(Roles.MEMBER)
        DonationFactory(member=member)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/my-history/?year=abc')
        assert response.status_code == status.HTTP_200_OK

    def test_my_history_no_member_profile(self):
        """User without member profile gets 404."""
        user = UserFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/my-history/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_my_history_unauthenticated(self):
        """Unauthenticated user cannot access my_history."""
        client = make_api_client()
        response = client.get('/api/v1/donations/donations/my-history/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationViewSetRecordPhysical:
    """Tests for DonationViewSet record_physical action."""

    def test_record_physical_donation_as_treasurer(self):
        """Treasurer can record a physical donation."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member = MemberFactory()

        client = make_api_client(user)
        data = {
            'member': str(member.pk),
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/donations/record-physical/', data)
        assert response.status_code == status.HTTP_201_CREATED
        donation = Donation.objects.get(pk=response.data['id'])
        assert donation.recorded_by == treasurer
        assert donation.member == member

    def test_record_physical_check_without_check_number(self):
        """Check donation without check number fails."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member = MemberFactory()

        client = make_api_client(user)
        data = {
            'member': str(member.pk),
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CHECK,
            'date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/donations/record-physical/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_record_physical_as_regular_member_fails(self):
        """Regular member cannot record physical donations."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        data = {
            'member': str(member.pk),
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/donations/record-physical/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_record_physical_as_admin(self):
        """Admin can record physical donations."""
        user, admin = make_member_with_user(Roles.ADMIN)
        member = MemberFactory()

        client = make_api_client(user)
        data = {
            'member': str(member.pk),
            'amount': '50.00',
            'donation_type': DonationType.TITHE,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/donations/record-physical/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_record_physical_invalid_data(self):
        """Record physical with invalid data returns 400."""
        user, treasurer = make_member_with_user(Roles.TREASURER)

        client = make_api_client(user)
        data = {
            'amount': '-10.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
        }
        response = client.post('/api/v1/donations/donations/record-physical/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDonationViewSetSummary:
    """Tests for DonationViewSet summary action."""

    def test_summary_default(self):
        """Get default donation summary (current month)."""
        user, member = make_member_with_user(Roles.TREASURER)
        today = timezone.now().date()
        DonationFactory(
            amount=Decimal('100.00'),
            date=today,
            donation_type=DonationType.OFFERING,
            payment_method=PaymentMethod.CASH,
        )
        DonationFactory(
            amount=Decimal('200.00'),
            date=today,
            donation_type=DonationType.TITHE,
            payment_method=PaymentMethod.ONLINE,
        )

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/summary/')
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_amount']) == Decimal('300.00')
        assert response.data['donation_count'] == 2

    def test_summary_by_year(self):
        """Get donation summary for a specific year."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(amount=Decimal('500.00'), date=date(2026, 3, 15))
        DonationFactory(amount=Decimal('300.00'), date=date(2025, 6, 15))

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/summary/?period=year&year=2026')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['period'] == '2026'
        assert Decimal(response.data['total_amount']) == Decimal('500.00')

    def test_summary_by_month(self):
        """Get donation summary for a specific month."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(amount=Decimal('150.00'), date=date(2026, 1, 10))
        DonationFactory(amount=Decimal('250.00'), date=date(2026, 1, 20))
        DonationFactory(amount=Decimal('100.00'), date=date(2026, 2, 10))

        client = make_api_client(user)
        response = client.get(
            '/api/v1/donations/donations/summary/?period=month&year=2026&month=1'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['period'] == '1/2026'
        assert Decimal(response.data['total_amount']) == Decimal('400.00')
        assert response.data['donation_count'] == 2

    def test_summary_regular_member_forbidden(self):
        """Regular member cannot access summary."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/summary/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_summary_with_invalid_year(self):
        """Invalid year defaults to current year."""
        user, member = make_member_with_user(Roles.TREASURER)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/summary/?year=invalid')
        assert response.status_code == status.HTTP_200_OK

    def test_summary_with_invalid_month(self):
        """Invalid month is treated as None."""
        user, member = make_member_with_user(Roles.TREASURER)

        client = make_api_client(user)
        response = client.get(
            '/api/v1/donations/donations/summary/?period=month&month=invalid'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_summary_no_donations(self):
        """Summary with no donations returns zeros."""
        user, member = make_member_with_user(Roles.TREASURER)

        client = make_api_client(user)
        response = client.get(
            '/api/v1/donations/donations/summary/?period=year&year=2020'
        )
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_amount']) == Decimal('0.00')
        assert response.data['donation_count'] == 0

    def test_summary_includes_by_type_and_method(self):
        """Summary includes breakdown by type and method."""
        user, member = make_member_with_user(Roles.TREASURER)
        today = timezone.now().date()
        DonationFactory(
            amount=Decimal('100.00'),
            date=today,
            donation_type=DonationType.OFFERING,
            payment_method=PaymentMethod.CASH,
        )

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/summary/')
        assert response.status_code == status.HTTP_200_OK
        assert 'by_type' in response.data
        assert 'by_method' in response.data

    def test_summary_unauthenticated(self):
        """Unauthenticated user cannot access summary."""
        client = make_api_client()
        response = client.get('/api/v1/donations/donations/summary/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# DONATION CAMPAIGN VIEWSET TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationCampaignViewSetList:
    """Tests for DonationCampaignViewSet list action."""

    def test_list_campaigns_authenticated(self):
        """Authenticated member can list campaigns."""
        user, member = make_member_with_user(Roles.MEMBER)
        DonationCampaignFactory()
        DonationCampaignFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/campaigns/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_campaigns_unauthenticated(self):
        """Unauthenticated user cannot list campaigns."""
        client = make_api_client()
        response = client.get('/api/v1/donations/campaigns/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationCampaignViewSetRetrieve:
    """Tests for DonationCampaignViewSet retrieve action."""

    def test_retrieve_campaign(self):
        """Authenticated member can retrieve a campaign."""
        user, member = make_member_with_user(Roles.MEMBER)
        campaign = DonationCampaignFactory()

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/campaigns/{campaign.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == campaign.name


@pytest.mark.django_db
class TestDonationCampaignViewSetCreate:
    """Tests for DonationCampaignViewSet create action."""

    def test_create_campaign_as_pastor(self):
        """Pastor can create a campaign."""
        user, member = make_member_with_user(Roles.PASTOR)

        client = make_api_client(user)
        data = {
            'name': 'Building Fund',
            'description': 'New building project',
            'goal_amount': '50000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        }
        response = client.post('/api/v1/donations/campaigns/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert DonationCampaign.objects.filter(name='Building Fund').exists()

    def test_create_campaign_as_admin(self):
        """Admin can create a campaign."""
        user, member = make_member_with_user(Roles.ADMIN)

        client = make_api_client(user)
        data = {
            'name': 'Missions Fund',
            'goal_amount': '20000.00',
            'start_date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/campaigns/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_campaign_as_regular_member_fails(self):
        """Regular member cannot create a campaign."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        data = {
            'name': 'Test Campaign',
            'goal_amount': '1000.00',
            'start_date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/campaigns/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_campaign_as_treasurer_fails(self):
        """Treasurer cannot create a campaign (pastor/admin only)."""
        user, member = make_member_with_user(Roles.TREASURER)

        client = make_api_client(user)
        data = {
            'name': 'Test Campaign',
            'goal_amount': '1000.00',
            'start_date': date.today().isoformat(),
        }
        response = client.post('/api/v1/donations/campaigns/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationCampaignViewSetUpdate:
    """Tests for DonationCampaignViewSet update action."""

    def test_update_campaign_as_pastor(self):
        """Pastor can update a campaign."""
        user, member = make_member_with_user(Roles.PASTOR)
        campaign = DonationCampaignFactory()

        client = make_api_client(user)
        data = {
            'name': 'Updated Campaign',
            'goal_amount': '75000.00',
            'start_date': campaign.start_date.isoformat(),
        }
        response = client.patch(f'/api/v1/donations/campaigns/{campaign.pk}/', data)
        assert response.status_code == status.HTTP_200_OK
        campaign.refresh_from_db()
        assert campaign.name == 'Updated Campaign'

    def test_update_campaign_as_member_fails(self):
        """Regular member cannot update a campaign."""
        user, member = make_member_with_user(Roles.MEMBER)
        campaign = DonationCampaignFactory()

        client = make_api_client(user)
        response = client.patch(
            f'/api/v1/donations/campaigns/{campaign.pk}/',
            {'name': 'Hacked'},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationCampaignViewSetDelete:
    """Tests for DonationCampaignViewSet delete action."""

    def test_delete_campaign_as_admin(self):
        """Admin can delete a campaign."""
        user, member = make_member_with_user(Roles.ADMIN)
        campaign = DonationCampaignFactory()

        client = make_api_client(user)
        response = client.delete(f'/api/v1/donations/campaigns/{campaign.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_campaign_as_member_fails(self):
        """Regular member cannot delete a campaign."""
        user, member = make_member_with_user(Roles.MEMBER)
        campaign = DonationCampaignFactory()

        client = make_api_client(user)
        response = client.delete(f'/api/v1/donations/campaigns/{campaign.pk}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDonationCampaignViewSetActive:
    """Tests for DonationCampaignViewSet active action."""

    def test_active_campaigns(self):
        """Get active campaigns returns only currently active ones.

        Note: The 'active' action falls through to IsPastorOrAdmin permission,
        so only pastor/admin can access it.
        """
        user, member = make_member_with_user(Roles.PASTOR)
        today = timezone.now().date()

        active_campaign = DonationCampaignFactory(
            start_date=today - timedelta(days=10),
            end_date=today + timedelta(days=10),
            is_active=True,
        )
        future_campaign = DonationCampaignFactory(
            start_date=today + timedelta(days=10),
            is_active=True,
        )
        ended_campaign = DonationCampaignFactory(
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
            is_active=True,
        )
        inactive_campaign = DonationCampaignFactory(
            start_date=today - timedelta(days=10),
            is_active=False,
        )

        client = make_api_client(user)
        response = client.get('/api/v1/donations/campaigns/active/')
        assert response.status_code == status.HTTP_200_OK
        campaign_ids = [c['id'] for c in response.data]
        assert str(active_campaign.pk) in campaign_ids
        assert str(future_campaign.pk) not in campaign_ids
        assert str(ended_campaign.pk) not in campaign_ids
        # inactive_campaign has is_active=False, so won't appear in default queryset

    def test_active_campaigns_with_no_end_date(self):
        """Active campaigns with no end date are included if started."""
        user, member = make_member_with_user(Roles.ADMIN)
        today = timezone.now().date()

        campaign = DonationCampaignFactory(
            start_date=today - timedelta(days=5),
            end_date=None,
            is_active=True,
        )

        client = make_api_client(user)
        response = client.get('/api/v1/donations/campaigns/active/')
        assert response.status_code == status.HTTP_200_OK
        campaign_ids = [c['id'] for c in response.data]
        assert str(campaign.pk) in campaign_ids

    def test_active_campaigns_regular_member_forbidden(self):
        """Regular member cannot access active campaigns endpoint."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/campaigns/active/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# TAX RECEIPT VIEWSET TESTS
# =============================================================================


@pytest.mark.django_db
class TestTaxReceiptViewSetList:
    """Tests for TaxReceiptViewSet list action."""

    def test_list_receipts_regular_member_sees_own(self):
        """Regular member sees only their own receipts."""
        user, member = make_member_with_user(Roles.MEMBER)
        own_receipt = TaxReceiptFactory(member=member, year=2025)
        other_receipt = TaxReceiptFactory(year=2024)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/')
        assert response.status_code == status.HTTP_200_OK
        receipt_ids = [r['id'] for r in response.data['results']]
        assert str(own_receipt.pk) in receipt_ids
        assert str(other_receipt.pk) not in receipt_ids

    def test_list_receipts_treasurer_sees_all(self):
        """Treasurer sees all receipts."""
        user, member = make_member_with_user(Roles.TREASURER)
        TaxReceiptFactory(year=2025)
        TaxReceiptFactory(year=2024)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_receipts_admin_sees_all(self):
        """Admin sees all receipts."""
        user, member = make_member_with_user(Roles.ADMIN)
        TaxReceiptFactory(year=2025)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_list_receipts_staff_user_sees_all(self):
        """Django staff user sees all receipts."""
        user = UserFactory(is_staff=True)
        TaxReceiptFactory(year=2025)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_receipts_user_without_profile_empty(self):
        """User without member profile sees empty list."""
        user = UserFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_list_receipts_unauthenticated(self):
        """Unauthenticated user cannot list receipts."""
        client = make_api_client()
        response = client.get('/api/v1/donations/receipts/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaxReceiptViewSetRetrieve:
    """Tests for TaxReceiptViewSet retrieve action."""

    def test_retrieve_own_receipt(self):
        """Member can retrieve their own receipt."""
        user, member = make_member_with_user(Roles.MEMBER)
        receipt = TaxReceiptFactory(member=member, year=2025)

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/receipts/{receipt.pk}/')
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_other_receipt_as_member_fails(self):
        """Regular member cannot retrieve another member's receipt."""
        user, member = make_member_with_user(Roles.MEMBER)
        other_receipt = TaxReceiptFactory(year=2025)

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/receipts/{other_receipt.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_any_receipt_as_treasurer(self):
        """Treasurer can retrieve any receipt."""
        user, member = make_member_with_user(Roles.TREASURER)
        receipt = TaxReceiptFactory(year=2025)

        client = make_api_client(user)
        response = client.get(f'/api/v1/donations/receipts/{receipt.pk}/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTaxReceiptViewSetMyReceipts:
    """Tests for TaxReceiptViewSet my_receipts action."""

    def test_my_receipts(self):
        """Member can get their own receipts."""
        user, member = make_member_with_user(Roles.MEMBER)
        receipt = TaxReceiptFactory(member=member, year=2025)
        TaxReceiptFactory(year=2024)  # another member's receipt

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/my-receipts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == str(receipt.pk)

    def test_my_receipts_no_member_profile(self):
        """User without member profile gets 404."""
        user = UserFactory()

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/my-receipts/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaxReceiptViewSetGenerate:
    """Tests for TaxReceiptViewSet generate action."""

    def test_generate_receipt_for_specific_member(self):
        """Treasurer can generate receipt for a specific member."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member = MemberFactory()
        DonationFactory(member=member, amount=Decimal('500.00'), date=date(2025, 6, 1))
        DonationFactory(member=member, amount=Decimal('300.00'), date=date(2025, 9, 1))

        client = make_api_client(user)
        response = client.post(
            f'/api/v1/donations/receipts/generate/2025/?member={member.pk}'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data['total_amount']) == Decimal('800.00')
        assert TaxReceipt.objects.filter(member=member, year=2025).exists()

    def test_generate_receipt_for_all_members(self):
        """Treasurer can generate receipts for all members with donations."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member1 = MemberFactory()
        member2 = MemberFactory()
        DonationFactory(member=member1, amount=Decimal('200.00'), date=date(2025, 3, 1))
        DonationFactory(member=member2, amount=Decimal('400.00'), date=date(2025, 5, 1))

        client = make_api_client(user)
        response = client.post('/api/v1/donations/receipts/generate/2025/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['generated_count'] == 2
        assert response.data['year'] == 2025

    def test_generate_receipt_member_not_found(self):
        """Generate receipt for non-existent member returns 404."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        import uuid
        fake_uuid = uuid.uuid4()

        client = make_api_client(user)
        response = client.post(
            f'/api/v1/donations/receipts/generate/2025/?member={fake_uuid}'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_generate_receipt_no_donations(self):
        """Generate receipt for member with no donations returns 400."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member = MemberFactory()

        client = make_api_client(user)
        response = client.post(
            f'/api/v1/donations/receipts/generate/2025/?member={member.pk}'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_receipt_already_exists(self):
        """Generate receipt when one already exists returns the existing one."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member = MemberFactory()
        DonationFactory(member=member, amount=Decimal('100.00'), date=date(2025, 1, 1))
        existing_receipt = TaxReceiptFactory(
            member=member,
            year=2025,
            total_amount=Decimal('100.00'),
        )

        client = make_api_client(user)
        response = client.post(
            f'/api/v1/donations/receipts/generate/2025/?member={member.pk}'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] == str(existing_receipt.pk)

    def test_generate_receipt_as_regular_member_fails(self):
        """Regular member cannot generate receipts."""
        user, member = make_member_with_user(Roles.MEMBER)

        client = make_api_client(user)
        response = client.post('/api/v1/donations/receipts/generate/2025/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_receipt_as_admin(self):
        """Admin can generate receipts."""
        user, admin = make_member_with_user(Roles.ADMIN)
        member = MemberFactory()
        DonationFactory(member=member, amount=Decimal('100.00'), date=date(2025, 1, 1))

        client = make_api_client(user)
        response = client.post(
            f'/api/v1/donations/receipts/generate/2025/?member={member.pk}'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_generate_receipt_sets_generated_by(self):
        """Generated receipt has correct generated_by field."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member = MemberFactory()
        DonationFactory(member=member, amount=Decimal('100.00'), date=date(2025, 1, 1))

        client = make_api_client(user)
        response = client.post(
            f'/api/v1/donations/receipts/generate/2025/?member={member.pk}'
        )
        assert response.status_code == status.HTTP_201_CREATED
        receipt = TaxReceipt.objects.get(pk=response.data['id'])
        assert receipt.generated_by == treasurer

    def test_generate_receipts_skips_members_without_donations(self):
        """Bulk generation skips members without donations for the year."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        member_with_donations = MemberFactory()
        DonationFactory(
            member=member_with_donations,
            amount=Decimal('100.00'),
            date=date(2024, 6, 1),
        )

        client = make_api_client(user)
        response = client.post('/api/v1/donations/receipts/generate/2024/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['generated_count'] == 1


# =============================================================================
# FILTERING AND SEARCHING TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationFiltering:
    """Tests for donation filtering and search capabilities."""

    def test_filter_by_donation_type(self):
        """Filter donations by type."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(donation_type=DonationType.TITHE)
        DonationFactory(donation_type=DonationType.OFFERING)

        client = make_api_client(user)
        response = client.get(
            f'/api/v1/donations/donations/?donation_type={DonationType.TITHE}'
        )
        assert response.status_code == status.HTTP_200_OK
        for d in response.data['results']:
            assert d['donation_type'] == DonationType.TITHE

    def test_filter_by_payment_method(self):
        """Filter donations by payment method."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(payment_method=PaymentMethod.CASH)
        DonationFactory(payment_method=PaymentMethod.ONLINE)

        client = make_api_client(user)
        response = client.get(
            f'/api/v1/donations/donations/?payment_method={PaymentMethod.CASH}'
        )
        assert response.status_code == status.HTTP_200_OK
        for d in response.data['results']:
            assert d['payment_method'] == PaymentMethod.CASH

    def test_search_by_donation_number(self):
        """Search donations by donation number."""
        user, member = make_member_with_user(Roles.TREASURER)
        donation = DonationFactory()

        client = make_api_client(user)
        response = client.get(
            f'/api/v1/donations/donations/?search={donation.donation_number}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_ordering_by_amount(self):
        """Order donations by amount."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(amount=Decimal('50.00'))
        DonationFactory(amount=Decimal('200.00'))
        DonationFactory(amount=Decimal('100.00'))

        client = make_api_client(user)
        response = client.get('/api/v1/donations/donations/?ordering=amount')
        assert response.status_code == status.HTTP_200_OK
        amounts = [Decimal(d['amount']) for d in response.data['results']]
        assert amounts == sorted(amounts)

    def test_search_campaigns(self):
        """Search campaigns by name."""
        user, member = make_member_with_user(Roles.MEMBER)
        DonationCampaignFactory(name='Building Fund')
        DonationCampaignFactory(name='Missions Trip')

        client = make_api_client(user)
        response = client.get('/api/v1/donations/campaigns/?search=Building')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        names = [r['name'] for r in response.data['results']]
        assert 'Building Fund' in names

    def test_filter_receipts_by_year(self):
        """Filter receipts by year."""
        user, member = make_member_with_user(Roles.TREASURER)
        TaxReceiptFactory(year=2025)
        TaxReceiptFactory(year=2024)

        client = make_api_client(user)
        response = client.get('/api/v1/donations/receipts/?year=2025')
        assert response.status_code == status.HTTP_200_OK
        for r in response.data['results']:
            assert r['year'] == 2025
