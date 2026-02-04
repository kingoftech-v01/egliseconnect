"""
Tests for donations frontend views.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from apps.core.constants import DonationType, PaymentMethod, Roles
from apps.donations.models import Donation, DonationCampaign, TaxReceipt
from apps.members.tests.factories import (
    MemberFactory,
    MemberWithUserFactory,
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


def make_logged_in_client(user):
    """Create a Django test client logged in as the given user."""
    client = Client()
    client.force_login(user)
    return client


# =============================================================================
# DONATION CREATE VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationCreateView:
    """Tests for donation_create view."""

    def test_get_donation_form(self):
        """Authenticated member can access donation form."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get('/donations/donate/')
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'campaigns' in response.context

    def test_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        client = Client()
        response = client.get('/donations/donate/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_redirects_if_no_member_profile(self):
        """User without member profile is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/donate/')
        assert response.status_code == 302

    def test_post_valid_donation(self):
        """Creating a donation with valid data succeeds."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        data = {
            'amount': '50.00',
            'donation_type': DonationType.OFFERING,
            'notes': 'Test donation',
        }
        response = client.post('/donations/donate/', data)
        assert response.status_code == 302
        donation = Donation.objects.filter(member=member).first()
        assert donation is not None
        assert donation.amount == Decimal('50.00')
        assert donation.payment_method == PaymentMethod.ONLINE

    def test_post_invalid_donation(self):
        """Creating a donation with invalid data shows form errors."""
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        data = {
            'amount': '-10.00',
            'donation_type': DonationType.OFFERING,
        }
        response = client.post('/donations/donate/', data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_post_donation_with_campaign(self):
        """Creating a donation with a campaign succeeds."""
        user, member = make_member_with_user()
        campaign = DonationCampaignFactory()
        client = make_logged_in_client(user)

        data = {
            'amount': '100.00',
            'donation_type': DonationType.CAMPAIGN,
            'campaign': campaign.pk,
        }
        response = client.post('/donations/donate/', data)
        assert response.status_code == 302
        donation = Donation.objects.filter(member=member).first()
        assert donation is not None
        assert donation.campaign == campaign

    def test_active_campaigns_in_context(self):
        """Active campaigns are included in the form context."""
        user, member = make_member_with_user()
        active = DonationCampaignFactory(is_active=True)
        inactive = DonationCampaignFactory(is_active=False)
        client = make_logged_in_client(user)

        response = client.get('/donations/donate/')
        assert response.status_code == 200
        campaigns = list(response.context['campaigns'])
        assert active in campaigns
        assert inactive not in campaigns


# =============================================================================
# DONATION DETAIL VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationDetailView:
    """Tests for donation_detail view."""

    def test_view_own_donation(self):
        """Member can view their own donation."""
        user, member = make_member_with_user()
        donation = DonationFactory(member=member)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{donation.pk}/')
        assert response.status_code == 200
        assert response.context['donation'] == donation

    def test_view_other_donation_as_member_forbidden(self):
        """Regular member cannot view another member's donation."""
        user, member = make_member_with_user()
        other_donation = DonationFactory()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{other_donation.pk}/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_view_any_donation_as_treasurer(self):
        """Treasurer can view any donation."""
        user, member = make_member_with_user(Roles.TREASURER)
        donation = DonationFactory()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{donation.pk}/')
        assert response.status_code == 200

    def test_view_any_donation_as_pastor(self):
        """Pastor can view any donation."""
        user, member = make_member_with_user(Roles.PASTOR)
        donation = DonationFactory()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{donation.pk}/')
        assert response.status_code == 200

    def test_view_any_donation_as_admin(self):
        """Admin can view any donation."""
        user, member = make_member_with_user(Roles.ADMIN)
        donation = DonationFactory()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{donation.pk}/')
        assert response.status_code == 200

    def test_view_donation_as_staff_user(self):
        """Django staff user can view any donation."""
        user = UserFactory(is_staff=True)
        donation = DonationFactory()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{donation.pk}/')
        assert response.status_code == 200

    def test_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        donation = DonationFactory()
        client = Client()

        response = client.get(f'/donations/{donation.pk}/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_nonexistent_donation_returns_404(self):
        """Requesting a nonexistent donation returns 404."""
        import uuid
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/{uuid.uuid4()}/')
        assert response.status_code == 404


# =============================================================================
# DONATION HISTORY VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationHistoryView:
    """Tests for donation_history view."""

    def test_view_history(self):
        """Member can view their donation history."""
        user, member = make_member_with_user()
        DonationFactory(member=member, amount=Decimal('50.00'))
        DonationFactory(member=member, amount=Decimal('100.00'))
        client = make_logged_in_client(user)

        response = client.get('/donations/history/')
        assert response.status_code == 200
        assert 'donations' in response.context
        assert response.context['total'] == Decimal('150.00')

    def test_history_with_year_filter(self):
        """History can be filtered by year."""
        user, member = make_member_with_user()
        DonationFactory(member=member, date=date(2026, 1, 1), amount=Decimal('100.00'))
        DonationFactory(member=member, date=date(2025, 6, 1), amount=Decimal('200.00'))
        client = make_logged_in_client(user)

        response = client.get('/donations/history/?year=2026')
        assert response.status_code == 200
        assert response.context['total'] == Decimal('100.00')
        assert response.context['selected_year'] == '2026'

    def test_history_with_invalid_year(self):
        """Invalid year filter is ignored."""
        user, member = make_member_with_user()
        DonationFactory(member=member)
        client = make_logged_in_client(user)

        response = client.get('/donations/history/?year=abc')
        assert response.status_code == 200

    def test_history_redirects_if_no_member_profile(self):
        """User without member profile is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/history/')
        assert response.status_code == 302

    def test_history_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        client = Client()
        response = client.get('/donations/history/')
        assert response.status_code == 302

    def test_history_pagination(self):
        """History view paginates results."""
        user, member = make_member_with_user()
        # Create 25 donations (page size is 20)
        for i in range(25):
            DonationFactory(member=member)
        client = make_logged_in_client(user)

        response = client.get('/donations/history/')
        assert response.status_code == 200
        donations_page = response.context['donations']
        assert donations_page.paginator.num_pages == 2

    def test_history_page_2(self):
        """Can navigate to page 2 of history."""
        user, member = make_member_with_user()
        for i in range(25):
            DonationFactory(member=member)
        client = make_logged_in_client(user)

        response = client.get('/donations/history/?page=2')
        assert response.status_code == 200

    def test_history_years_in_context(self):
        """Available years are in the context."""
        user, member = make_member_with_user()
        DonationFactory(member=member, date=date(2026, 1, 1))
        DonationFactory(member=member, date=date(2025, 6, 1))
        client = make_logged_in_client(user)

        response = client.get('/donations/history/')
        assert response.status_code == 200
        assert 'years' in response.context


# =============================================================================
# DONATION ADMIN LIST VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationAdminListView:
    """Tests for donation_admin_list view."""

    def test_treasurer_can_access(self):
        """Treasurer can access the admin list."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 200
        assert 'donations' in response.context
        assert 'total' in response.context

    def test_pastor_can_access(self):
        """Pastor can access the admin list."""
        user, member = make_member_with_user(Roles.PASTOR)
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 200

    def test_admin_can_access(self):
        """Admin can access the admin list."""
        user, member = make_member_with_user(Roles.ADMIN)
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 200

    def test_regular_member_redirected(self):
        """Regular member is redirected from admin list."""
        user, member = make_member_with_user(Roles.MEMBER)
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_staff_user_can_access(self):
        """Django staff user can access the admin list."""
        user = UserFactory(is_staff=True)
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 200

    def test_non_staff_user_without_profile_redirected(self):
        """User without member profile and not staff is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_filter_by_date_range(self):
        """Can filter donations by date range."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(date=date(2026, 1, 15))
        DonationFactory(date=date(2026, 2, 15))
        client = make_logged_in_client(user)

        response = client.get(
            '/donations/admin/?date_from=2026-01-01&date_to=2026-01-31'
        )
        assert response.status_code == 200

    def test_filter_by_donation_type(self):
        """Can filter donations by type."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(donation_type=DonationType.TITHE)
        DonationFactory(donation_type=DonationType.OFFERING)
        client = make_logged_in_client(user)

        response = client.get(
            f'/donations/admin/?donation_type={DonationType.TITHE}'
        )
        assert response.status_code == 200

    def test_filter_by_payment_method(self):
        """Can filter donations by payment method."""
        user, member = make_member_with_user(Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get(
            f'/donations/admin/?payment_method={PaymentMethod.CASH}'
        )
        assert response.status_code == 200

    def test_filter_by_campaign(self):
        """Can filter donations by campaign."""
        user, member = make_member_with_user(Roles.TREASURER)
        campaign = DonationCampaignFactory()
        DonationFactory(campaign=campaign)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/admin/?campaign={campaign.pk}')
        assert response.status_code == 200

    def test_filter_by_member_search(self):
        """Can search donations by member name."""
        user, member = make_member_with_user(Roles.TREASURER)
        target_member = MemberFactory(first_name='Jean', last_name='Dupont')
        DonationFactory(member=target_member)
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/?member=Dupont')
        assert response.status_code == 200

    def test_pagination(self):
        """Admin list paginates results."""
        user, member = make_member_with_user(Roles.TREASURER)
        for i in range(55):
            DonationFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/admin/')
        assert response.status_code == 200
        donations_page = response.context['donations']
        assert donations_page.paginator.num_pages == 2


# =============================================================================
# DONATION RECORD VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationRecordView:
    """Tests for donation_record view."""

    def test_treasurer_can_access_form(self):
        """Treasurer can access the record form."""
        user, member = make_member_with_user(Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/record/')
        assert response.status_code == 200
        assert 'form' in response.context

    def test_admin_can_access_form(self):
        """Admin can access the record form."""
        user, member = make_member_with_user(Roles.ADMIN)
        client = make_logged_in_client(user)

        response = client.get('/donations/record/')
        assert response.status_code == 200

    def test_regular_member_redirected(self):
        """Regular member is redirected from record form."""
        user, member = make_member_with_user(Roles.MEMBER)
        client = make_logged_in_client(user)

        response = client.get('/donations/record/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_pastor_redirected(self):
        """Pastor is redirected from record form (treasurer/admin only)."""
        user, member = make_member_with_user(Roles.PASTOR)
        client = make_logged_in_client(user)

        response = client.get('/donations/record/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_staff_user_can_access_form(self):
        """Django staff user can access the record form."""
        user = UserFactory(is_staff=True)
        # Staff user needs a member_profile to be the recorded_by
        # But for just GET, the form should render
        client = make_logged_in_client(user)

        response = client.get('/donations/record/')
        assert response.status_code == 200

    def test_non_staff_user_without_profile_redirected(self):
        """User without member profile and not staff is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/record/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_post_valid_donation(self):
        """Recording a valid physical donation succeeds."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        target_member = MemberFactory()
        client = make_logged_in_client(user)

        data = {
            'member': target_member.pk,
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
        }
        response = client.post('/donations/record/', data)
        assert response.status_code == 302
        donation = Donation.objects.filter(member=target_member).first()
        assert donation is not None
        assert donation.recorded_by == treasurer

    def test_post_invalid_donation(self):
        """Recording an invalid donation shows form errors."""
        user, treasurer = make_member_with_user(Roles.TREASURER)
        client = make_logged_in_client(user)

        data = {
            'amount': '100.00',
            'donation_type': DonationType.OFFERING,
            'payment_method': PaymentMethod.CASH,
            'date': date.today().isoformat(),
            # Missing member
        }
        response = client.post('/donations/record/', data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


# =============================================================================
# CAMPAIGN LIST VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestCampaignListView:
    """Tests for campaign_list view."""

    def test_authenticated_user_can_access(self):
        """Authenticated user can access the campaign list."""
        user, member = make_member_with_user()
        DonationCampaignFactory(is_active=True)
        DonationCampaignFactory(is_active=True)
        client = make_logged_in_client(user)

        response = client.get('/donations/campaigns/')
        assert response.status_code == 200
        assert 'campaigns' in response.context

    def test_only_active_campaigns_shown(self):
        """Only active campaigns are shown."""
        user, member = make_member_with_user()
        active = DonationCampaignFactory(is_active=True)
        inactive = DonationCampaignFactory(is_active=False)
        client = make_logged_in_client(user)

        response = client.get('/donations/campaigns/')
        assert response.status_code == 200
        campaigns = list(response.context['campaigns'])
        assert active in campaigns
        assert inactive not in campaigns

    def test_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        client = Client()
        response = client.get('/donations/campaigns/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# CAMPAIGN DETAIL VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestCampaignDetailView:
    """Tests for campaign_detail view."""

    def test_view_campaign(self):
        """Authenticated user can view campaign details."""
        user, member = make_member_with_user()
        campaign = DonationCampaignFactory()
        DonationFactory(campaign=campaign)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/campaigns/{campaign.pk}/')
        assert response.status_code == 200
        assert response.context['campaign'] == campaign
        assert 'recent_donations' in response.context

    def test_nonexistent_campaign_returns_404(self):
        """Requesting a nonexistent campaign returns 404."""
        import uuid
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/campaigns/{uuid.uuid4()}/')
        assert response.status_code == 404

    def test_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        campaign = DonationCampaignFactory()
        client = Client()

        response = client.get(f'/donations/campaigns/{campaign.pk}/')
        assert response.status_code == 302

    def test_recent_donations_limited_to_10(self):
        """Recent donations are limited to 10."""
        user, member = make_member_with_user()
        campaign = DonationCampaignFactory()
        for i in range(15):
            DonationFactory(campaign=campaign)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/campaigns/{campaign.pk}/')
        assert response.status_code == 200
        assert len(response.context['recent_donations']) <= 10


# =============================================================================
# RECEIPT LIST VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestReceiptListView:
    """Tests for receipt_list view."""

    def test_regular_member_sees_own_receipts(self):
        """Regular member sees only their own receipts."""
        user, member = make_member_with_user(Roles.MEMBER)
        own_receipt = TaxReceiptFactory(member=member, year=2025)
        other_receipt = TaxReceiptFactory(year=2024)
        client = make_logged_in_client(user)

        response = client.get('/donations/receipts/')
        assert response.status_code == 200
        receipts = list(response.context['receipts'])
        assert own_receipt in receipts
        assert other_receipt not in receipts
        assert response.context['is_finance'] is False

    def test_treasurer_sees_all_receipts(self):
        """Treasurer sees all receipts."""
        user, member = make_member_with_user(Roles.TREASURER)
        TaxReceiptFactory(year=2025)
        TaxReceiptFactory(year=2024)
        client = make_logged_in_client(user)

        response = client.get('/donations/receipts/')
        assert response.status_code == 200
        assert response.context['is_finance'] is True
        assert len(response.context['receipts']) == 2

    def test_admin_sees_all_receipts(self):
        """Admin sees all receipts."""
        user, member = make_member_with_user(Roles.ADMIN)
        TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get('/donations/receipts/')
        assert response.status_code == 200
        assert response.context['is_finance'] is True

    def test_staff_user_sees_all_receipts(self):
        """Django staff user with member profile sees all receipts."""
        user = UserFactory(is_staff=True)
        member = MemberFactory(user=user, role=Roles.MEMBER)
        TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get('/donations/receipts/')
        assert response.status_code == 200
        assert response.context['is_finance'] is True

    def test_redirects_if_no_member_profile(self):
        """User without member profile is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/receipts/')
        assert response.status_code == 302

    def test_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        client = Client()
        response = client.get('/donations/receipts/')
        assert response.status_code == 302

    def test_pagination(self):
        """Receipt list paginates results."""
        user, member = make_member_with_user(Roles.TREASURER)
        for i in range(25):
            TaxReceiptFactory(
                year=2000 + i,
                receipt_number=f'REC-PGTEST-{i:04d}',
            )
        client = make_logged_in_client(user)

        response = client.get('/donations/receipts/')
        assert response.status_code == 200
        receipts_page = response.context['receipts']
        assert receipts_page.paginator.num_pages == 2


# =============================================================================
# RECEIPT DETAIL VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestReceiptDetailView:
    """Tests for receipt_detail view."""

    def test_view_own_receipt(self):
        """Member can view their own receipt."""
        user, member = make_member_with_user()
        receipt = TaxReceiptFactory(member=member, year=2025)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{receipt.pk}/')
        assert response.status_code == 200
        assert response.context['receipt'] == receipt

    def test_view_other_receipt_as_member_forbidden(self):
        """Regular member cannot view another member's receipt."""
        user, member = make_member_with_user()
        other_receipt = TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{other_receipt.pk}/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_view_any_receipt_as_treasurer(self):
        """Treasurer can view any receipt."""
        user, member = make_member_with_user(Roles.TREASURER)
        receipt = TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{receipt.pk}/')
        assert response.status_code == 200

    def test_view_any_receipt_as_admin(self):
        """Admin can view any receipt."""
        user, member = make_member_with_user(Roles.ADMIN)
        receipt = TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{receipt.pk}/')
        assert response.status_code == 200

    def test_view_receipt_as_staff_user(self):
        """Django staff user can view any receipt."""
        user = UserFactory(is_staff=True)
        receipt = TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{receipt.pk}/')
        assert response.status_code == 200

    def test_nonexistent_receipt_returns_404(self):
        """Requesting a nonexistent receipt returns 404."""
        import uuid
        user, member = make_member_with_user()
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{uuid.uuid4()}/')
        assert response.status_code == 404

    def test_redirects_if_not_logged_in(self):
        """Unauthenticated user is redirected to login."""
        receipt = TaxReceiptFactory(year=2025)
        client = Client()

        response = client.get(f'/donations/receipts/{receipt.pk}/')
        assert response.status_code == 302

    def test_user_without_member_profile_forbidden(self):
        """User without member profile and not staff is redirected."""
        user = UserFactory()
        receipt = TaxReceiptFactory(year=2025)
        client = make_logged_in_client(user)

        response = client.get(f'/donations/receipts/{receipt.pk}/')
        assert response.status_code == 302
        assert response.url == '/'


# =============================================================================
# MONTHLY REPORT VIEW TESTS
# =============================================================================


@pytest.mark.django_db
class TestDonationMonthlyReportView:
    """Tests for donation_monthly_report view."""

    def test_treasurer_can_access(self):
        """Treasurer can access the monthly report."""
        user, member = make_member_with_user(Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/')
        assert response.status_code == 200
        assert 'donations' in response.context
        assert 'total' in response.context
        assert 'count' in response.context
        assert 'by_type' in response.context
        assert 'by_method' in response.context

    def test_pastor_can_access(self):
        """Pastor can access the monthly report."""
        user, member = make_member_with_user(Roles.PASTOR)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/')
        assert response.status_code == 200

    def test_admin_can_access(self):
        """Admin can access the monthly report."""
        user, member = make_member_with_user(Roles.ADMIN)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/')
        assert response.status_code == 200

    def test_regular_member_redirected(self):
        """Regular member is redirected from monthly report."""
        user, member = make_member_with_user(Roles.MEMBER)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_staff_user_can_access(self):
        """Django staff user can access the monthly report."""
        user = UserFactory(is_staff=True)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/')
        assert response.status_code == 200

    def test_non_staff_user_without_profile_redirected(self):
        """User without member profile and not staff is redirected."""
        user = UserFactory()
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_with_year_and_month_params(self):
        """Report can be filtered by year and month."""
        user, member = make_member_with_user(Roles.TREASURER)
        DonationFactory(date=date(2026, 1, 15), amount=Decimal('100.00'))
        DonationFactory(date=date(2026, 1, 20), amount=Decimal('200.00'))
        DonationFactory(date=date(2026, 2, 15), amount=Decimal('50.00'))
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/?year=2026&month=1')
        assert response.status_code == 200
        assert response.context['year'] == 2026
        assert response.context['month'] == 1
        assert response.context['total'] == Decimal('300.00')
        assert response.context['count'] == 2

    def test_with_invalid_year(self):
        """Invalid year defaults to current year."""
        user, member = make_member_with_user(Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/?year=abc')
        assert response.status_code == 200
        assert response.context['year'] == timezone.now().year

    def test_with_invalid_month(self):
        """Invalid month defaults to current month."""
        user, member = make_member_with_user(Roles.TREASURER)
        client = make_logged_in_client(user)

        response = client.get('/donations/reports/monthly/?month=abc')
        assert response.status_code == 200
        assert response.context['month'] == timezone.now().month

    def test_report_shows_breakdown_by_type(self):
        """Report includes breakdown by donation type."""
        user, member = make_member_with_user(Roles.TREASURER)
        today = timezone.now().date()
        DonationFactory(
            date=today,
            donation_type=DonationType.TITHE,
            amount=Decimal('100.00'),
        )
        DonationFactory(
            date=today,
            donation_type=DonationType.OFFERING,
            amount=Decimal('50.00'),
        )
        client = make_logged_in_client(user)

        response = client.get(
            f'/donations/reports/monthly/?year={today.year}&month={today.month}'
        )
        assert response.status_code == 200
        by_type = list(response.context['by_type'])
        assert len(by_type) == 2

    def test_report_shows_breakdown_by_method(self):
        """Report includes breakdown by payment method."""
        user, member = make_member_with_user(Roles.TREASURER)
        today = timezone.now().date()
        DonationFactory(
            date=today,
            payment_method=PaymentMethod.CASH,
            amount=Decimal('100.00'),
        )
        DonationFactory(
            date=today,
            payment_method=PaymentMethod.ONLINE,
            amount=Decimal('50.00'),
        )
        client = make_logged_in_client(user)

        response = client.get(
            f'/donations/reports/monthly/?year={today.year}&month={today.month}'
        )
        assert response.status_code == 200
        by_method = list(response.context['by_method'])
        assert len(by_method) == 2
