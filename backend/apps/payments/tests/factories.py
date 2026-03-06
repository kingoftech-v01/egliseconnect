"""Test factories for payments app."""
import factory
from decimal import Decimal
from factory.django import DjangoModelFactory

from apps.members.tests.factories import MemberFactory
from apps.payments.models import StripeCustomer, OnlinePayment, RecurringDonation, PaymentStatus


class StripeCustomerFactory(DjangoModelFactory):
    """Creates StripeCustomer instances for testing."""

    class Meta:
        model = StripeCustomer

    member = factory.SubFactory(MemberFactory)
    stripe_customer_id = factory.Sequence(lambda n: f'cus_test_{n}')


class OnlinePaymentFactory(DjangoModelFactory):
    """Creates OnlinePayment instances for testing."""

    class Meta:
        model = OnlinePayment

    member = factory.SubFactory(MemberFactory)
    stripe_payment_intent_id = factory.Sequence(lambda n: f'pi_test_{n}')
    amount = factory.LazyFunction(lambda: Decimal('50.00'))
    currency = 'CAD'
    status = PaymentStatus.PENDING
    donation_type = 'offering'
    receipt_email = factory.LazyAttribute(lambda obj: obj.member.email)


class SucceededPaymentFactory(OnlinePaymentFactory):
    """Creates a succeeded OnlinePayment."""

    status = PaymentStatus.SUCCEEDED


class FailedPaymentFactory(OnlinePaymentFactory):
    """Creates a failed OnlinePayment."""

    status = PaymentStatus.FAILED


class RecurringDonationFactory(DjangoModelFactory):
    """Creates RecurringDonation instances for testing."""

    class Meta:
        model = RecurringDonation

    member = factory.SubFactory(MemberFactory)
    stripe_subscription_id = factory.Sequence(lambda n: f'sub_test_{n}')
    amount = factory.LazyFunction(lambda: Decimal('25.00'))
    currency = 'CAD'
    frequency = 'monthly'
    donation_type = 'tithe'
    is_active_subscription = True


class CancelledRecurringFactory(RecurringDonationFactory):
    """Creates a cancelled RecurringDonation."""

    is_active_subscription = False
    cancelled_at = factory.LazyFunction(
        lambda: __import__('django.utils.timezone', fromlist=['now']).now()
    )
