"""Tests for donations forms."""
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


@pytest.mark.django_db
class TestDonationForm:
    """Tests for DonationForm."""

    def test_valid_form(self):
        """Valid donation data."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
            'notes': 'Test donation',
        })
        assert form.is_valid(), form.errors

    def test_valid_form_with_campaign(self):
        """Valid data with campaign selected."""
        campaign = DonationCampaignFactory()
        form = DonationForm(data={
            'amount': '100.00',
            'donation_type': DonationType.CAMPAIGN,
            'campaign': campaign.pk,
            'notes': '',
        })
        assert form.is_valid(), form.errors

    def test_amount_required(self):
        """Amount is required."""
        form = DonationForm(data={
            'donation_type': DonationType.OFFERING,
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_donation_type_required(self):
        """Donation type is required."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': '',
        })
        assert not form.is_valid()
        assert 'donation_type' in form.errors

    def test_negative_amount_rejected(self):
        """Negative amounts are rejected."""
        form = DonationForm(data={
            'amount': '-10.00',
            'donation_type': DonationType.OFFERING,
        })
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_zero_amount_accepted_by_form(self):
        """Zero amount passes form validation (model/serializer may catch it)."""
        form = DonationForm(data={
            'amount': '0.00',
            'donation_type': DonationType.OFFERING,
        })
        assert form.is_valid()

    def test_campaign_not_required(self):
        """Campaign is optional."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
        })
        assert form.is_valid(), form.errors

    def test_notes_not_required(self):
        """Notes are optional."""
        form = DonationForm(data={
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
        })
        assert form.is_valid(), form.errors

    def test_inactive_campaign_not_in_queryset(self):
        """Inactive campaigns excluded from choices."""
        active_campaign = DonationCampaignFactory(is_active=True)
        inactive_campaign = DonationCampaignFactory(is_active=False)
        form = DonationForm()
        campaign_qs = form.fields['campaign'].queryset
        assert active_campaign in campaign_qs
        assert inactive_campaign not in campaign_qs

    def test_form_fields(self):
        """Form has correct fields."""
        form = DonationForm()
        expected_fields = ['amount', 'donation_type', 'campaign', 'notes']
        assert list(form.fields.keys()) == expected_fields

    def test_amount_widget_attrs(self):
        """Amount widget has min and step attributes."""
        form = DonationForm()
        widget = form.fields['amount'].widget
        assert widget.attrs.get('min') == '1'
        assert widget.attrs.get('step') == '0.01'

    def test_large_valid_amount(self):
        """Large valid amounts accepted."""
        form = DonationForm(data={
            'amount': '999999.99',
            'donation_type': DonationType.TITHE,
        })
        assert form.is_valid(), form.errors

    def test_all_donation_types_accepted(self):
        """All donation types accepted."""
        for dtype, _ in DonationType.CHOICES:
            form = DonationForm(data={
                'amount': '50.00',
                'donation_type': dtype,
            })
            assert form.is_valid(), f"Failed for type {dtype}: {form.errors}"


@pytest.mark.django_db
class TestPhysicalDonationForm:
    """Tests for PhysicalDonationForm used for recording in-person donations."""

    def test_valid_cash_donation(self):
        """Valid cash donation."""
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
        """Valid check donation with check number."""
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
        """Check payments require check number."""
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
        """Cash payments don't require check number."""
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
        """Member is required."""
        form = PhysicalDonationForm(data={
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        })
        assert not form.is_valid()
        assert 'member' in form.errors

    def test_amount_required(self):
        """Amount is required."""
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
        """Date is required."""
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
        """Payment methods limited to physical options only."""
        form = PhysicalDonationForm()
        method_choices = [c[0] for c in form.fields['payment_method'].choices]
        assert PaymentMethod.CASH in method_choices
        assert PaymentMethod.CHECK in method_choices
        assert PaymentMethod.BANK_TRANSFER in method_choices
        assert PaymentMethod.OTHER in method_choices
        assert PaymentMethod.ONLINE not in method_choices
        assert PaymentMethod.CARD not in method_choices

    def test_form_fields(self):
        """Form has correct fields."""
        form = PhysicalDonationForm()
        expected_fields = [
            'member', 'amount', 'donation_type', 'payment_method',
            'date', 'campaign', 'check_number', 'notes',
        ]
        assert list(form.fields.keys()) == expected_fields

    def test_inactive_campaign_not_in_queryset(self):
        """Inactive campaigns excluded from choices."""
        active_campaign = DonationCampaignFactory(is_active=True)
        inactive_campaign = DonationCampaignFactory(is_active=False)
        form = PhysicalDonationForm()
        campaign_qs = form.fields['campaign'].queryset
        assert active_campaign in campaign_qs
        assert inactive_campaign not in campaign_qs

    def test_campaign_not_required(self):
        """Campaign is optional."""
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
        """Bank transfer payment method works."""
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
        """Form accepts notes."""
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


@pytest.mark.django_db
class TestDonationCampaignForm:
    """Tests for DonationCampaignForm."""

    def test_valid_form(self):
        """Valid campaign data."""
        form = DonationCampaignForm(data={
            'name': 'Building Fund',
            'description': 'Campaign for new church building',
            'goal_amount': '50000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        })
        assert form.is_valid(), form.errors

    def test_valid_form_with_end_date(self):
        """Valid data with end date."""
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
        """End date before start date rejected."""
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
        """Name is required."""
        form = DonationCampaignForm(data={
            'goal_amount': '1000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_start_date_required(self):
        """Start date is required."""
        form = DonationCampaignForm(data={
            'name': 'Test Campaign',
            'goal_amount': '1000.00',
            'is_active': True,
        })
        assert not form.is_valid()
        assert 'start_date' in form.errors

    def test_end_date_not_required(self):
        """End date is optional for ongoing campaigns."""
        form = DonationCampaignForm(data={
            'name': 'Ongoing Campaign',
            'goal_amount': '5000.00',
            'start_date': date.today().isoformat(),
            'is_active': True,
        })
        assert form.is_valid(), form.errors

    def test_form_fields(self):
        """Form has correct fields."""
        form = DonationCampaignForm()
        expected_fields = [
            'name', 'description', 'goal_amount',
            'start_date', 'end_date', 'image', 'is_active',
        ]
        assert list(form.fields.keys()) == expected_fields


@pytest.mark.django_db
class TestDonationFilterForm:
    """Tests for DonationFilterForm."""

    def test_empty_form_valid(self):
        """Empty filter form is valid."""
        form = DonationFilterForm(data={})
        assert form.is_valid()

    def test_with_date_range(self):
        """Date range filter works."""
        today = date.today()
        form = DonationFilterForm(data={
            'date_from': (today - timedelta(days=30)).isoformat(),
            'date_to': today.isoformat(),
        })
        assert form.is_valid(), form.errors

    def test_with_donation_type(self):
        """Donation type filter works."""
        form = DonationFilterForm(data={
            'donation_type': DonationType.TITHE,
        })
        assert form.is_valid(), form.errors

    def test_with_payment_method(self):
        """Payment method filter works."""
        form = DonationFilterForm(data={
            'payment_method': PaymentMethod.CASH,
        })
        assert form.is_valid(), form.errors

    def test_with_campaign(self):
        """Campaign filter works."""
        campaign = DonationCampaignFactory()
        form = DonationFilterForm(data={
            'campaign': campaign.pk,
        })
        assert form.is_valid(), form.errors

    def test_with_member_search(self):
        """Member name search works."""
        form = DonationFilterForm(data={
            'member': 'Dupont',
        })
        assert form.is_valid(), form.errors

    def test_all_fields_optional(self):
        """All filter fields are optional."""
        form = DonationFilterForm()
        for field_name, field in form.fields.items():
            assert not field.required, f"Field '{field_name}' should not be required"


class TestDonationReportForm:
    """Tests for DonationReportForm."""

    def test_valid_monthly_report(self):
        """Valid monthly report form."""
        form = DonationReportForm(data={
            'period': 'month',
            'year': 2026,
            'month': 1,
            'group_by': 'type',
        })
        assert form.is_valid(), form.errors

    def test_valid_yearly_report(self):
        """Valid yearly report form."""
        form = DonationReportForm(data={
            'period': 'year',
            'year': 2026,
            'group_by': 'member',
        })
        assert form.is_valid(), form.errors

    def test_period_required(self):
        """Period is required."""
        form = DonationReportForm(data={
            'group_by': 'type',
        })
        assert not form.is_valid()
        assert 'period' in form.errors

    def test_group_by_required(self):
        """Group by is required."""
        form = DonationReportForm(data={
            'period': 'month',
        })
        assert not form.is_valid()
        assert 'group_by' in form.errors

    def test_year_optional(self):
        """Year is optional."""
        form = DonationReportForm(data={
            'period': 'month',
            'group_by': 'type',
        })
        assert form.is_valid(), form.errors

    def test_invalid_period(self):
        """Invalid period rejected."""
        form = DonationReportForm(data={
            'period': 'invalid',
            'group_by': 'type',
        })
        assert not form.is_valid()
        assert 'period' in form.errors

    def test_all_group_by_options(self):
        """All group_by options accepted."""
        for group_by in ['type', 'method', 'campaign', 'member']:
            form = DonationReportForm(data={
                'period': 'month',
                'group_by': group_by,
            })
            assert form.is_valid(), f"Failed for group_by={group_by}: {form.errors}"
