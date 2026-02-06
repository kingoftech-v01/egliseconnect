"""Tests for donations models."""
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.donations.models import Donation, DonationCampaign, TaxReceipt

from .factories import (
    DonationFactory,
    DonationCampaignFactory,
    TaxReceiptFactory,
    TitheDonationFactory,
)
from apps.members.tests.factories import MemberFactory


@pytest.mark.django_db
class TestDonationModel:
    """Tests for Donation model."""

    def test_create_donation(self):
        """Donation creation auto-generates donation number."""
        donation = DonationFactory()
        assert donation.id is not None
        assert donation.donation_number is not None
        assert donation.donation_number.startswith('DON-')

    def test_donation_number_auto_generated(self):
        """Donation number generated on save if not set."""
        member = MemberFactory()
        donation = Donation(
            member=member,
            amount=Decimal('100.00'),
        )
        donation.save()

        assert donation.donation_number is not None
        assert donation.donation_number.startswith('DON-')

    def test_donation_number_unique(self):
        """Each donation gets a unique donation number."""
        donation1 = DonationFactory()
        donation2 = DonationFactory()

        assert donation1.donation_number != donation2.donation_number

    def test_soft_delete(self):
        """Soft delete hides from default queryset but keeps in all_objects."""
        donation = DonationFactory()
        pk = donation.pk
        donation.delete()

        assert not Donation.objects.filter(pk=pk).exists()
        assert Donation.all_objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestDonationCampaignModel:
    """Tests for DonationCampaign model."""

    def test_create_campaign(self):
        """Campaign creation works."""
        campaign = DonationCampaignFactory()
        assert campaign.id is not None
        assert campaign.name is not None

    def test_current_amount_calculation(self):
        """current_amount sums donations for the campaign."""
        campaign = DonationCampaignFactory(goal_amount=Decimal('1000.00'))
        DonationFactory(campaign=campaign, amount=Decimal('100.00'))
        DonationFactory(campaign=campaign, amount=Decimal('200.00'))

        assert campaign.current_amount == Decimal('300.00')

    def test_progress_percentage(self):
        """progress_percentage calculates correctly."""
        campaign = DonationCampaignFactory(goal_amount=Decimal('1000.00'))
        DonationFactory(campaign=campaign, amount=Decimal('500.00'))

        assert campaign.progress_percentage == 50

    def test_progress_percentage_capped_at_100(self):
        """progress_percentage capped at 100% when goal exceeded."""
        campaign = DonationCampaignFactory(goal_amount=Decimal('100.00'))
        DonationFactory(campaign=campaign, amount=Decimal('150.00'))

        assert campaign.progress_percentage == 100

    def test_is_ongoing(self):
        """is_ongoing reflects active status and dates."""
        today = timezone.now().date()

        campaign = DonationCampaignFactory(
            start_date=today,
            end_date=None,
            is_active=True
        )
        assert campaign.is_ongoing is True

        campaign.is_active = False
        assert campaign.is_ongoing is False


@pytest.mark.django_db
class TestTaxReceiptModel:
    """Tests for TaxReceipt model."""

    def test_create_receipt(self):
        """Receipt creation works."""
        receipt = TaxReceiptFactory()
        assert receipt.id is not None
        assert receipt.receipt_number is not None

    def test_member_info_captured(self):
        """Member info captured at receipt generation time for audit trail."""
        member = MemberFactory(
            first_name='Jean',
            last_name='Dupont',
            address='123 Rue Test'
        )
        receipt = TaxReceipt(
            receipt_number='REC-2026-0001',
            member=member,
            year=2026,
            total_amount=Decimal('1000.00')
        )
        receipt.save()

        assert receipt.member_name == 'Jean Dupont'
        assert '123 Rue Test' in receipt.member_address

    def test_unique_together_member_year(self):
        """Member can only have one receipt per year."""
        member = MemberFactory()
        TaxReceiptFactory(member=member, year=2026)

        with pytest.raises(Exception):
            TaxReceiptFactory(member=member, year=2026)
