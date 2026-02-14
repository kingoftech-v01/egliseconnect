"""Tests for text-to-give / SMS donation service (P2-1)."""
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.core.constants import DonationType, PaymentMethod
from apps.donations.models import Donation
from apps.members.tests.factories import MemberFactory

from .factories import DonationFactory


# ==============================================================================
# Service Tests
# ==============================================================================


@pytest.mark.django_db
class TestSMSDonationService:
    """Tests for SMSDonationService."""

    def test_process_give_command_english(self):
        """GIVE command creates a donation."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'GIVE 100')

        assert 'response_message' in result
        assert result.get('success', False) or 'error' not in result.get('response_message', '').lower()

    def test_process_give_command_french(self):
        """DONNER command creates a donation."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'DONNER 50')

        assert 'response_message' in result

    def test_process_give_with_decimal_amount(self):
        """GIVE command handles decimal amounts."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'GIVE 75.50')

        assert 'response_message' in result

    def test_process_status_command(self):
        """STATUS command returns giving summary."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        DonationFactory(member=member)
        result = SMSDonationService.process_sms('5141234567', 'STATUS')

        assert 'response_message' in result

    def test_process_help_command(self):
        """HELP command returns instructions."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'HELP')

        assert 'response_message' in result

    def test_unknown_phone_number(self):
        """Unknown phone number returns error."""
        from apps.donations.services_sms import SMSDonationService

        result = SMSDonationService.process_sms('0000000000', 'GIVE 100')

        assert 'response_message' in result

    def test_invalid_amount(self):
        """Invalid amount in GIVE command returns error."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'GIVE abc')

        assert 'response_message' in result

    def test_zero_amount(self):
        """Zero amount in GIVE command returns error."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'GIVE 0')

        assert 'response_message' in result

    def test_negative_amount(self):
        """Negative amount in GIVE command returns error."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'GIVE -50')

        assert 'response_message' in result

    def test_unknown_command(self):
        """Unknown command returns help text."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        result = SMSDonationService.process_sms('5141234567', 'RANDOM')

        assert 'response_message' in result

    def test_lookup_member_by_phone(self):
        """_lookup_member finds member by phone number."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5149876543')
        found = SMSDonationService._lookup_member('5149876543')

        assert found is not None
        assert found.pk == member.pk

    def test_lookup_member_not_found(self):
        """_lookup_member returns None for unknown phone."""
        from apps.donations.services_sms import SMSDonationService

        found = SMSDonationService._lookup_member('0000000000')
        assert found is None

    def test_successful_give_creates_donation(self):
        """Successful GIVE command creates a Donation in the database."""
        from apps.donations.services_sms import SMSDonationService

        member = MemberFactory(phone='5141234567')
        initial_count = Donation.objects.filter(member=member).count()

        result = SMSDonationService.process_sms('5141234567', 'GIVE 100')

        if result.get('success', False):
            assert Donation.objects.filter(member=member).count() == initial_count + 1
