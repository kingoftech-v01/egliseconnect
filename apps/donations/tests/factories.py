"""Test factories for donations app."""
from decimal import Decimal

import factory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.core.constants import DonationType, PaymentMethod, PledgeStatus, PledgeFrequency
from apps.members.tests.factories import MemberFactory

from apps.donations.models import (
    Donation, DonationCampaign, TaxReceipt, FinanceDelegation,
    Pledge, PledgeFulfillment, GivingStatement, GivingGoal,
    DonationImport, DonationImportRow, MatchingCampaign, CryptoDonation,
)


class DonationCampaignFactory(DjangoModelFactory):
    """Creates DonationCampaign instances for testing."""

    class Meta:
        model = DonationCampaign

    name = factory.Sequence(lambda n: f'Campaign {n}')
    description = factory.Faker('paragraph')
    goal_amount = Decimal('10000.00')
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    is_active = True


class DonationFactory(DjangoModelFactory):
    """Creates Donation instances with default online payment."""

    class Meta:
        model = Donation

    member = factory.SubFactory(MemberFactory)
    amount = factory.LazyFunction(lambda: Decimal('100.00'))
    donation_type = DonationType.OFFERING
    payment_method = PaymentMethod.ONLINE
    date = factory.LazyFunction(lambda: timezone.now().date())


class CashDonationFactory(DonationFactory):
    """Creates cash donations."""

    payment_method = PaymentMethod.CASH


class CheckDonationFactory(DonationFactory):
    """Creates check donations with check number."""

    payment_method = PaymentMethod.CHECK
    check_number = factory.Sequence(lambda n: f'{n:06d}')


class TitheDonationFactory(DonationFactory):
    """Creates tithe donations."""

    donation_type = DonationType.TITHE


class TaxReceiptFactory(DjangoModelFactory):
    """Creates TaxReceipt instances for testing."""

    class Meta:
        model = TaxReceipt

    receipt_number = factory.Sequence(lambda n: f'REC-2026-{n:04d}')
    member = factory.SubFactory(MemberFactory)
    year = 2026
    total_amount = Decimal('1200.00')


class FinanceDelegationFactory(DjangoModelFactory):
    """Creates FinanceDelegation instances for testing."""

    class Meta:
        model = FinanceDelegation

    delegated_to = factory.SubFactory(MemberFactory)
    delegated_by = factory.SubFactory(MemberFactory)
    reason = factory.Faker('sentence')


class PledgeFactory(DjangoModelFactory):
    """Creates Pledge instances for testing."""

    class Meta:
        model = Pledge

    member = factory.SubFactory(MemberFactory)
    amount = Decimal('500.00')
    frequency = PledgeFrequency.MONTHLY
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    status = PledgeStatus.ACTIVE


class CampaignPledgeFactory(PledgeFactory):
    """Creates a Pledge linked to a campaign."""

    campaign = factory.SubFactory(DonationCampaignFactory)


class PledgeFulfillmentFactory(DjangoModelFactory):
    """Creates PledgeFulfillment instances for testing."""

    class Meta:
        model = PledgeFulfillment

    pledge = factory.SubFactory(PledgeFactory)
    donation = factory.SubFactory(DonationFactory)
    amount = Decimal('100.00')
    date = factory.LazyFunction(lambda: timezone.now().date())


class GivingStatementFactory(DjangoModelFactory):
    """Creates GivingStatement instances for testing."""

    class Meta:
        model = GivingStatement

    member = factory.SubFactory(MemberFactory)
    year = 2026
    period = 'annual'
    start_date = factory.LazyFunction(lambda: timezone.now().date().replace(month=1, day=1))
    end_date = factory.LazyFunction(lambda: timezone.now().date().replace(month=12, day=31))
    total_amount = Decimal('2400.00')


class MidYearStatementFactory(GivingStatementFactory):
    """Creates a mid-year statement."""

    period = 'mid_year'
    end_date = factory.LazyFunction(lambda: timezone.now().date().replace(month=6, day=30))


class GivingGoalFactory(DjangoModelFactory):
    """Creates GivingGoal instances for testing."""

    class Meta:
        model = GivingGoal

    member = factory.SubFactory(MemberFactory)
    year = 2026
    target_amount = Decimal('5000.00')


class DonationImportFactory(DjangoModelFactory):
    """Creates DonationImport instances for testing."""

    class Meta:
        model = DonationImport

    file = factory.LazyFunction(
        lambda: SimpleUploadedFile('test_import.csv', b'member_number,amount,date\n001,100,2026-01-01', content_type='text/csv')
    )
    status = 'pending'
    imported_by = factory.SubFactory(MemberFactory)


class CompletedImportFactory(DonationImportFactory):
    """Creates a completed import."""

    status = 'completed'
    total_rows = 10
    imported_count = 8
    skipped_count = 2


class DonationImportRowFactory(DjangoModelFactory):
    """Creates DonationImportRow instances for testing."""

    class Meta:
        model = DonationImportRow

    donation_import = factory.SubFactory(DonationImportFactory)
    row_number = factory.Sequence(lambda n: n + 1)
    data_json = factory.LazyFunction(lambda: {'member_number': '001', 'amount': '100.00', 'date': '2026-01-01'})
    status = 'valid'


class InvalidImportRowFactory(DonationImportRowFactory):
    """Creates an invalid import row."""

    status = 'invalid'
    error_message = 'Membre introuvable'


class MatchingCampaignFactory(DjangoModelFactory):
    """Creates MatchingCampaign instances for testing."""

    class Meta:
        model = MatchingCampaign

    campaign = factory.SubFactory(DonationCampaignFactory)
    matcher_name = factory.Faker('company')
    match_ratio = Decimal('1.00')
    match_cap = Decimal('10000.00')
    matched_total = Decimal('0.00')


class CryptoDonationFactory(DjangoModelFactory):
    """Creates CryptoDonation instances for testing."""

    class Meta:
        model = CryptoDonation

    member = factory.SubFactory(MemberFactory)
    crypto_type = 'BTC'
    amount_crypto = Decimal('0.01000000')
    amount_cad = Decimal('500.00')
    status = 'pending'


class ConfirmedCryptoDonationFactory(CryptoDonationFactory):
    """Creates a confirmed crypto donation."""

    status = 'confirmed'
    coinbase_charge_id = factory.Sequence(lambda n: f'CHARGE-{n:06d}')
