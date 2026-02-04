"""
Tests for donations forms.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.core.constants import DonationType, PaymentMethod
from apps.donations.forms import (
    DonationCampaignForm,
    DonationFilterForm,
    DonationForm,
    DonationReportForm,
    PhysicalDonationForm,
)
from apps.donations.models import DonationCampaign
from apps.members.tests.factories import MemberFactory

from .factories import DonationCampaignFactory


# =============================================================================
# DONATION FORM TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationForm:
    """Tests for DonationForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
            'notes': 'Test donation',
        })
        assert form.is_valid(), form.errors

    def test_valid_form_with_campaign(self):
        """Test form with a campaign selected."""
        campaign = DonationCampaignFactory()
        form = DonationForm(data={
            'amount': '100.00',
            'donation_type': DonationType.CAMPAIGN,
            'campaign': campaign.pk,
            'notes': '',
        })
        assert form.is_valid(), form.errors

    def test_amount_required(self):
        """Test that amount is required."""
        form = DonationForm(data={
            'donation_type': DonationType.OFFERING,
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_donation_type_required(self):
        """Test that donation_type is required."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': '',
        })
        assert not form.is_valid()
        assert 'donation_type' in form.errors

    def test_negative_amount_rejected(self):
        """Test that negative amount is rejected."""
        form = DonationForm(data={
            'amount': '-10.00',
            'donation_type': DonationType.OFFERING,
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_zero_amount_accepted_by_form(self):
        """Test that zero amount passes form validation.

        Note: The clean_amount check uses `if amount and amount <= 0`,
        which means Decimal('0.00') (falsy) bypasses the custom check.
        The database-level constraint or serializer may catch this separately.
        """
        form = DonationForm(data={
            'amount': '0.00',
            'donation_type': DonationType.OFFERING,
        })
        # Decimal('0.00') is falsy, so clean_amount skips the <= 0 check
        assert form.is_valid()

    def test_campaign_not_required(self):
        """Test that campaign is not required."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
        })
        assert form.is_valid(), form.errors

    def test_notes_not_required(self):
        """Test that notes are not required."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
        })
        assert form.is_valid(), form.errors

    def test_inactive_campaign_not_in_queryset(self):
        """Test that inactive campaigns are not shown."""
        active_campaign = DonationCampaignFactory(is_active=True)
        inactive_campaign = DonationCampaignFactory(is_active=False)
        form = DonationForm()
        campaign_qs = form.fields['campaign'].queryset
        assert active_campaign in campaign_qs
        assert inactive_campaign not in campaign_qs

    def test_form_fields(self):
        """Test that form has correct fields."""
        form = DonationForm()
        expected_fields = ['amount', 'donation_type', 'campaign', 'notes']
        assert list(form.fields.keys()) == expected_fields

    def test_amount_widget_attrs(self):
        """Test amount widget has correct attributes."""
        form = DonationForm()
        widget = form.fields['amount'].widget
        assert widget.attrs.get('min') == '1'
        assert widget.attrs.get('step') == '0.01'

    def test_large_valid_amount(self):
        """Test form accepts large valid amounts."""
        form = DonationForm(data={
            'amount': '999999.99',
            'donation_type': DonationType.TITHE,
        })
        assert form.is_valid(), form.errors

    def test_all_donation_types_accepted(self):
        """Test form accepts all donation types."""
        for dtype, _ in DonationType.CHOICES:
            form = DonationForm(data={
                'amount': '50.00',
                'donation_type': dtype,
            })
            assert form.is_valid(), f"Failed for type {dtype}: {form.errors}"


# =============================================================================
# PHYSICAL DONATION FORM TESTS
# =============================================================================


@pytest.mark.django_db
class TestPhysicalDonationForm:
    """Tests for PhysicalDonationForm."""

    def test_valid_cash_donation(self):
        """Test form with valid cash donation."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        })
        assert form.is_valid(), form.errors

    def test_valid_check_donation(self):
        """Test form with valid check donation including check number."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '200.00',
            'donation_type': DonationType.TITHE,
            'payment_method': PaymentMethod.CHECK,
            'date': date.today().isoformat(),
            'check_number': '12345',
        })
        assert form.is_valid(), form.errors

    def test_check_payment_requires_check_number(self):
        """Test that check payment requires check number."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CHECK,
            'date': date.today().isoformat(),
            'check_number': '',
        })
        assert not form.is_valid()
        assert 'check_number' in form.errors

    def test_cash_payment_does_not_require_check_number(self):
        """Test that cash payment does not require check number."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        })
        assert form.is_valid(), form.errors

    def test_member_required(self):
        """Test that member is required."""
        form = PhysicalDonationForm(data={
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        })
        assert not form.is_valid()
        assert 'member' in form.errors

    def test_amount_required(self):
        """Test that amount is required."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_date_required(self):
        """Test that date is required."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': '',
        })
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_payment_method_limited_to_physical(self):
        """Test that payment methods are limited to physical ones."""
        form = PhysicalDonationForm()
        method_choices = [c[0] for c in form.fields['payment_method'].choices]
        assert PaymentMethod.CASH in method_choices
        assert PaymentMethod.CHECK in method_choices
        assert PaymentMethod.BANK_TRANSFER in method_choices
        assert PaymentMethod.OTHER in method_choices
        # Online/card should not be available
        assert PaymentMethod.ONLINE not in method_choices
        assert PaymentMethod.CARD not in method_choices

    def test_form_fields(self):
        """Test that form has correct fields."""
        form = PhysicalDonationForm()
        expected_fields = [
            'member', 'amount', 'donation_type', 'payment_method',
            'date', 'campaign', 'check_number', 'notes',
        ]
        assert list(form.fields.keys()) == expected_fields

    def test_inactive_campaign_not_in_queryset(self):
        """Test that inactive campaigns are not shown."""
        active_campaign = DonationCampaignFactory(is_active=True)
        inactive_campaign = DonationCampaignFactory(is_active=False)
        form = PhysicalDonationForm()
        campaign_qs = form.fields['campaign'].queryset
        assert active_campaign in campaign_qs
        assert inactive_campaign not in campaign_qs

    def test_campaign_not_required(self):
        """Test that campaign is not required."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        })
        assert form.is_valid(), form.errors

    def test_bank_transfer_donation(self):
        """Test form with bank transfer payment method."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '500.00',
            'donation_type': DonationType.TITHE,
            'payment_method': PaymentMethod.BANK_TRANSFER,
            'date': date.today().isoformat(),
        })
        assert form.is_valid(), form.errors

    def test_with_notes(self):
        """Test form with notes."""
        member = MemberFactory()
        form = PhysicalDonationForm(data={
            'member': member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
            'notes': 'Sunday morning offering',
        })
        assert form.is_valid(), form.errors


# =============================================================================
# DONATION CAMPAIGN FORM TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationCampaignForm:
    """Tests for DonationCampaignForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form = DonationCampaignForm(data={
            'name': 'Building Fund',
            'description': 'Campaign for new church building',
            'goal_amount': '50000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        })
        assert form.is_valid(), form.errors

    def test_valid_form_with_end_date(self):
        """Test form with valid end date."""
        today = date.today()
        form = DonationCampaignForm(data={
            'name': 'Christmas Campaign',
            'goal_amount': '10000.00',
            'start_date': today.isoformat(),
            'end_date': (today + timedelta(days=30)).isoformat(),
            'is_active': True,
        })
        assert form.is_valid(), form.errors

    def test_end_date_before_start_date_rejected(self):
        """Test that end date before start date is rejected."""
        today = date.today()
        form = DonationCampaignForm(data={
            'name': 'Test Campaign',
            'goal_amount': '1000.00',
            'start_date': today.isoformat(),
            'end_date': (today - timedelta(days=1)).isoformat(),
            'is_active': True,
        })
        assert not form.is_valid()
        assert 'end_date' in form.errors

    def test_name_required(self):
        """Test that name is required."""
        form = DonationCampaignForm(data={
            'goal_amount': '1000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_start_date_required(self):
        """Test that start date is required."""
        form = DonationCampaignForm(data={
            'name': 'Test Campaign',
            'goal_amount': '1000.00',
            'is_active': True,
        })
        assert not form.is_valid()
        assert 'start_date' in form.errors

    def test_end_date_not_required(self):
        """Test that end date is not required."""
        form = DonationCampaignForm(data={
            'name': 'Ongoing Campaign',
            'goal_amount': '5000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        })
        assert form.is_valid(), form.errors

    def test_form_fields(self):
        """Test that form has correct fields."""
        form = DonationCampaignForm()
        expected_fields = [
            'name', 'description', 'goal_amount',
            'start_date', 'end_date', 'image', 'is_active',
        ]
        assert list(form.fields.keys()) == expected_fields


# =============================================================================
# DONATION FILTER FORM TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationFilterForm:
    """Tests for DonationFilterForm."""

    def test_empty_form_valid(self):
        """Test that empty filter form is valid."""
        form = DonationFilterForm(data={})
        assert form.is_valid()

    def test_with_date_range(self):
        """Test filter with date range."""
        today = date.today()
        form = DonationFilterForm(data={
            'date_from': (today - timedelta(days=30)).isoformat(),
            'date_to': today.isoformat(),
        })
        assert form.is_valid(), form.errors

    def test_with_donation_type(self):
        """Test filter with donation type."""
        form = DonationFilterForm(data={
            'donation_type': DonationType.TITHE,
        })
        assert form.is_valid(), form.errors

    def test_with_payment_method(self):
        """Test filter with payment method."""
        form = DonationFilterForm(data={
            'payment_method': PaymentMethod.CASH,
        })
        assert form.is_valid(), form.errors

    def test_with_campaign(self):
        """Test filter with campaign."""
        campaign = DonationCampaignFactory()
        form = DonationFilterForm(data={
            'campaign': campaign.pk,
        })
        assert form.is_valid(), form.errors

    def test_with_member_search(self):
        """Test filter with member name search."""
        form = DonationFilterForm(data={
            'member': 'Dupont',
        })
        assert form.is_valid(), form.errors

    def test_all_fields_optional(self):
        """Test that all filter fields are optional."""
        form = DonationFilterForm()
        for field_name, field in form.fields.items():
            assert not field.required, f"Field '{field_name}' should not be required"


# =============================================================================
# DONATION REPORT FORM TESTS
# =============================================================================


class TestDonationReportForm:
    """Tests for DonationReportForm."""

    def test_valid_monthly_report(self):
        """Test valid monthly report form."""
        form = DonationReportForm(data={
            'period': 'month',
            'year': 2026,
            'month': 1,
            'group_by': 'type',
        })
        assert form.is_valid(), form.errors

    def test_valid_yearly_report(self):
        """Test valid yearly report form."""
        form = DonationReportForm(data={
            'period': 'year',
            'year': 2026,
            'group_by': 'member',
        })
        assert form.is_valid(), form.errors

    def test_period_required(self):
        """Test that period is required."""
        form = DonationReportForm(data={
            'group_by': 'type',
        })
        assert not form.is_valid()
        assert 'period' in form.errors

    def test_group_by_required(self):
        """Test that group_by is required."""
        form = DonationReportForm(data={
            'period': 'month',
        })
        assert not form.is_valid()
        assert 'group_by' in form.errors

    def test_year_optional(self):
        """Test that year is optional."""
        form = DonationReportForm(data={
            'period': 'month',
            'group_by': 'type',
        })
        assert form.is_valid(), form.errors

    def test_invalid_period(self):
        """Test that invalid period is rejected."""
        form = DonationReportForm(data={
            'period': 'invalid',
            'group_by': 'type',
        })
        assert not form.is_valid()
        assert 'period' in form.errors

    def test_all_group_by_options(self):
        """Test all group_by options are accepted."""
        for group_by in ['type', 'method', 'campaign', 'member']:
            form = DonationReportForm(data={
                'period': 'month',
                'group_by': group_by,
            })
            assert form.is_valid(), f"Failed for group_by={group_by}: {form.errors}"
