"""Tests for payment models: StripeCustomer, OnlinePayment, RecurringDonation."""
import pytest
from decimal import Decimal

from apps.payments.models import (
    StripeCustomer,
    OnlinePayment,
    RecurringDonation,
    PaymentStatus,
    RecurringFrequency,
)
from apps.members.tests.factories import MemberFactory
from apps.payments.tests.factories import (
    StripeCustomerFactory,
    OnlinePaymentFactory,
    SucceededPaymentFactory,
    FailedPaymentFactory,
    RecurringDonationFactory,
    CancelledRecurringFactory,
)


@pytest.mark.django_db
class TestStripeCustomer:
    """Tests for the StripeCustomer model."""

    def test_str(self):
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        customer = StripeCustomerFactory(
            member=member,
            stripe_customer_id='cus_abc123',
        )
        assert str(customer) == 'Jean Dupont (cus_abc123)'

    def test_one_to_one_relationship(self):
        customer = StripeCustomerFactory()
        assert customer.member.stripe_customer is not None
        assert customer.member.stripe_customer == customer

    def test_unique_stripe_customer_id(self):
        StripeCustomerFactory(stripe_customer_id='cus_unique_1')
        with pytest.raises(Exception):
            StripeCustomerFactory(stripe_customer_id='cus_unique_1')

    def test_has_uuid_pk(self):
        customer = StripeCustomerFactory()
        assert customer.pk is not None
        assert hasattr(customer, 'created_at')
        assert hasattr(customer, 'updated_at')

    def test_verbose_names(self):
        meta = StripeCustomer._meta
        assert meta.verbose_name == 'Client Stripe'
        assert meta.verbose_name_plural == 'Clients Stripe'


@pytest.mark.django_db
class TestOnlinePayment:
    """Tests for the OnlinePayment model."""

    def test_str(self):
        member = MemberFactory(first_name='Marie', last_name='Tremblay')
        payment = OnlinePaymentFactory(
            member=member,
            amount=Decimal('100.00'),
            currency='CAD',
            status=PaymentStatus.PENDING,
        )
        assert 'Marie Tremblay' in str(payment)
        assert '100.00' in str(payment)
        assert 'CAD' in str(payment)
        assert 'En attente' in str(payment)

    def test_str_succeeded(self):
        payment = SucceededPaymentFactory()
        assert 'Réussi' in str(payment)

    def test_str_failed(self):
        payment = FailedPaymentFactory()
        assert 'Échoué' in str(payment)

    def test_amount_display(self):
        payment = OnlinePaymentFactory(amount=Decimal('75.50'), currency='CAD')
        assert payment.amount_display == '75.50 CAD'

    def test_amount_display_format(self):
        payment = OnlinePaymentFactory(amount=Decimal('100'), currency='USD')
        assert payment.amount_display == '100.00 USD'

    def test_is_successful_true(self):
        payment = SucceededPaymentFactory()
        assert payment.is_successful is True

    def test_is_successful_false_pending(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        assert payment.is_successful is False

    def test_is_successful_false_failed(self):
        payment = FailedPaymentFactory()
        assert payment.is_successful is False

    def test_is_successful_false_refunded(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.REFUNDED)
        assert payment.is_successful is False

    def test_ordering_newest_first(self):
        member = MemberFactory()
        p1 = OnlinePaymentFactory(member=member)
        p2 = OnlinePaymentFactory(member=member)
        payments = list(OnlinePayment.objects.filter(member=member))
        assert payments[0] == p2
        assert payments[1] == p1

    def test_unique_payment_intent_id(self):
        OnlinePaymentFactory(stripe_payment_intent_id='pi_unique_1')
        with pytest.raises(Exception):
            OnlinePaymentFactory(stripe_payment_intent_id='pi_unique_1')

    def test_default_currency(self):
        payment = OnlinePaymentFactory()
        assert payment.currency == 'CAD'

    def test_default_status(self):
        member = MemberFactory()
        payment = OnlinePayment.objects.create(
            member=member,
            stripe_payment_intent_id='pi_defaults_test',
            amount=Decimal('10.00'),
        )
        assert payment.status == PaymentStatus.PENDING

    def test_donation_nullable(self):
        payment = OnlinePaymentFactory()
        assert payment.donation is None

    def test_campaign_nullable(self):
        payment = OnlinePaymentFactory()
        assert payment.campaign is None

    def test_verbose_names(self):
        meta = OnlinePayment._meta
        assert meta.verbose_name == 'Paiement en ligne'
        assert meta.verbose_name_plural == 'Paiements en ligne'

    def test_all_status_choices(self):
        """Verify all payment status choices are valid."""
        member = MemberFactory()
        for i, (status_val, _) in enumerate(PaymentStatus.CHOICES):
            payment = OnlinePayment.objects.create(
                member=member,
                stripe_payment_intent_id=f'pi_status_test_{i}',
                amount=Decimal('10.00'),
                status=status_val,
            )
            assert payment.status == status_val


@pytest.mark.django_db
class TestRecurringDonation:
    """Tests for the RecurringDonation model."""

    def test_str_monthly(self):
        member = MemberFactory(first_name='Paul', last_name='Martin')
        recurring = RecurringDonationFactory(
            member=member,
            amount=Decimal('50.00'),
            currency='CAD',
            frequency='monthly',
        )
        result = str(recurring)
        assert 'Paul Martin' in result
        assert '50.00' in result
        assert 'CAD' in result
        assert 'Mensuel' in result

    def test_str_weekly(self):
        member = MemberFactory(first_name='Luc', last_name='Roy')
        recurring = RecurringDonationFactory(
            member=member,
            amount=Decimal('20.00'),
            frequency='weekly',
        )
        assert 'Hebdomadaire' in str(recurring)

    def test_amount_display(self):
        recurring = RecurringDonationFactory(amount=Decimal('99.99'), currency='CAD')
        assert recurring.amount_display == '99.99 CAD'

    def test_amount_display_format(self):
        recurring = RecurringDonationFactory(amount=Decimal('100'), currency='USD')
        assert recurring.amount_display == '100.00 USD'

    def test_ordering_newest_first(self):
        from django.utils import timezone
        from datetime import timedelta
        member = MemberFactory()
        r1 = RecurringDonationFactory(member=member)
        r2 = RecurringDonationFactory(member=member)
        # Ensure deterministic ordering by setting distinct created_at values
        earlier = timezone.now() - timedelta(hours=1)
        RecurringDonation.objects.filter(pk=r1.pk).update(created_at=earlier)
        RecurringDonation.objects.filter(pk=r2.pk).update(created_at=timezone.now())
        donations = list(RecurringDonation.objects.filter(member=member))
        assert donations[0] == r2
        assert donations[1] == r1

    def test_default_active(self):
        recurring = RecurringDonationFactory()
        assert recurring.is_active_subscription is True

    def test_default_cancelled_at_none(self):
        recurring = RecurringDonationFactory()
        assert recurring.cancelled_at is None

    def test_cancelled_factory(self):
        cancelled = CancelledRecurringFactory()
        assert cancelled.is_active_subscription is False
        assert cancelled.cancelled_at is not None

    def test_unique_subscription_id(self):
        RecurringDonationFactory(stripe_subscription_id='sub_unique_1')
        with pytest.raises(Exception):
            RecurringDonationFactory(stripe_subscription_id='sub_unique_1')

    def test_default_currency(self):
        recurring = RecurringDonationFactory()
        assert recurring.currency == 'CAD'

    def test_frequency_choices(self):
        for freq_val, _ in RecurringFrequency.CHOICES:
            recurring = RecurringDonationFactory(frequency=freq_val)
            assert recurring.frequency == freq_val

    def test_verbose_names(self):
        meta = RecurringDonation._meta
        assert meta.verbose_name == 'Don récurrent'
        assert meta.verbose_name_plural == 'Dons récurrents'

    def test_next_payment_date_nullable(self):
        recurring = RecurringDonationFactory()
        assert recurring.next_payment_date is None

    def test_has_uuid_pk(self):
        recurring = RecurringDonationFactory()
        assert recurring.pk is not None
        assert hasattr(recurring, 'created_at')
