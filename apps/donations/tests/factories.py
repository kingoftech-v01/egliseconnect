"""Test factories for donations app."""
from decimal import Decimal

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.core.constants import DonationType, PaymentMethod
from apps.members.tests.factories import MemberFactory

from apps.donations.models import Donation, DonationCampaign, TaxReceipt


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
