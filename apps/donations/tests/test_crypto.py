"""Tests for cryptocurrency donations (P3-1)."""
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles
from apps.donations.models import CryptoDonation
from apps.members.tests.factories import MemberFactory, UserFactory

from .factories import (
    CryptoDonationFactory,
    ConfirmedCryptoDonationFactory,
    MatchingCampaignFactory,
    DonationCampaignFactory,
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
class TestCryptoDonationModel:
    """Tests for CryptoDonation model."""

    def test_create_crypto_donation(self):
        """Crypto donation creation works."""
        crypto = CryptoDonationFactory()
        assert crypto.id is not None
        assert crypto.status == 'pending'
        assert crypto.crypto_type == 'BTC'

    def test_crypto_str(self):
        """String representation includes amount and type."""
        crypto = CryptoDonationFactory(amount_crypto=Decimal('0.05000000'), crypto_type='ETH')
        assert 'ETH' in str(crypto)
        assert '0.05' in str(crypto)

    def test_confirmed_crypto(self):
        """Confirmed crypto donation has charge ID."""
        crypto = ConfirmedCryptoDonationFactory()
        assert crypto.status == 'confirmed'
        assert crypto.coinbase_charge_id != ''

    def test_crypto_type_choices(self):
        """All valid crypto types can be used."""
        for crypto_type, _ in CryptoDonation.CRYPTO_CHOICES:
            crypto = CryptoDonationFactory(crypto_type=crypto_type)
            assert crypto.crypto_type == crypto_type

    def test_crypto_status_choices(self):
        """All valid statuses can be set."""
        for status_value, _ in CryptoDonation.STATUS_CHOICES:
            crypto = CryptoDonationFactory(status=status_value)
            assert crypto.status == status_value

    def test_crypto_without_member(self):
        """Crypto donation can be anonymous (no member)."""
        crypto = CryptoDonationFactory(member=None)
        assert crypto.member is None

    def test_crypto_with_donation_link(self):
        """Crypto donation can link to a Donation record."""
        from .factories import DonationFactory
        donation = DonationFactory()
        crypto = CryptoDonationFactory(donation=donation)
        assert crypto.donation == donation


# ==============================================================================
# MatchingCampaign Model Tests
# ==============================================================================


@pytest.mark.django_db
class TestMatchingCampaignModel:
    """Tests for MatchingCampaign model."""

    def test_create_matching_campaign(self):
        """Matching campaign creation works."""
        matching = MatchingCampaignFactory()
        assert matching.id is not None
        assert matching.match_ratio == Decimal('1.00')

    def test_matching_str(self):
        """String representation includes matcher name and campaign."""
        matching = MatchingCampaignFactory()
        assert matching.matcher_name in str(matching)
        assert matching.campaign.name in str(matching)

    def test_match_progress_percentage(self):
        """match_progress_percentage calculates correctly."""
        matching = MatchingCampaignFactory(
            match_cap=Decimal('10000.00'),
            matched_total=Decimal('5000.00'),
        )
        assert matching.match_progress_percentage == 50

    def test_match_progress_percentage_capped_at_100(self):
        """match_progress_percentage capped at 100."""
        matching = MatchingCampaignFactory(
            match_cap=Decimal('1000.00'),
            matched_total=Decimal('1500.00'),
        )
        assert matching.match_progress_percentage == 100

    def test_match_progress_percentage_zero_cap(self):
        """match_progress_percentage returns 0 for zero cap."""
        matching = MatchingCampaignFactory(match_cap=Decimal('0.00'))
        assert matching.match_progress_percentage == 0

    def test_remaining_match(self):
        """remaining_match calculates correctly."""
        matching = MatchingCampaignFactory(
            match_cap=Decimal('10000.00'),
            matched_total=Decimal('3000.00'),
        )
        assert matching.remaining_match == Decimal('7000.00')

    def test_remaining_match_never_negative(self):
        """remaining_match never goes below zero."""
        matching = MatchingCampaignFactory(
            match_cap=Decimal('1000.00'),
            matched_total=Decimal('1500.00'),
        )
        assert matching.remaining_match == Decimal('0.00')


# ==============================================================================
# View Tests
# ==============================================================================


@pytest.mark.django_db
class TestCryptoDonateView:
    """Tests for crypto_donate view."""

    def test_member_can_access_crypto_form(self):
        """Authenticated member can access crypto donation form."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/crypto/')
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'wallet_addresses' in response.context

    def test_post_valid_crypto_donation(self):
        """Creating a crypto donation with valid data succeeds."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        data = {
            'crypto_type': 'BTC',
            'amount_crypto': '0.01000000',
        }
        response = client.post('/donations/crypto/', data)
        assert response.status_code == 302
        assert CryptoDonation.objects.filter(member=member).exists()

    def test_unauthenticated_redirects(self):
        """Unauthenticated user is redirected."""
        client = Client()
        response = client.get('/donations/crypto/')
        assert response.status_code == 302

    def test_user_without_member_profile_redirects(self):
        """User without member profile is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/crypto/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestCryptoDetailView:
    """Tests for crypto_detail view."""

    def test_member_views_own_crypto(self):
        """Member can view their own crypto donation."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        crypto = CryptoDonationFactory(member=member)

        response = client.get(f'/donations/crypto/{crypto.pk}/')
        assert response.status_code == 200
        assert 'crypto' in response.context

    def test_member_cannot_view_others_crypto(self):
        """Member cannot view another's crypto donation."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)
        crypto = CryptoDonationFactory()  # different member

        response = client.get(f'/donations/crypto/{crypto.pk}/')
        assert response.status_code == 302

    def test_finance_staff_views_any_crypto(self):
        """Staff user can view any crypto donation."""
        user, member = make_member_with_user(role=Roles.ADMIN)
        user.is_staff = True
        user.save()
        client = make_logged_in_client(user)
        crypto = CryptoDonationFactory()

        response = client.get(f'/donations/crypto/{crypto.pk}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestKioskDonationView:
    """Tests for kiosk_donation view."""

    def test_finance_staff_can_access_kiosk(self):
        """Treasurer can access kiosk mode."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/kiosk/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_regular_member_cannot_access_kiosk(self):
        """Regular member cannot access kiosk."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/kiosk/')
        assert response.status_code == 302

    def test_post_kiosk_donation(self):
        """Submitting a kiosk donation creates a donation."""
        user, member = make_member_with_user(role=Roles.TREASURER)
        client = make_logged_in_client(user)
        target_member = MemberFactory()

        data = {
            'member': str(target_member.pk),
            'amount': '50.00',
            'donation_type': 'offering',
            'payment_method': 'cash',
        }
        response = client.post('/donations/kiosk/', data)
        assert response.status_code == 302
