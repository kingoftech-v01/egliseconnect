"""Tests for PaymentService - all Stripe operations in dev mode (no actual Stripe)."""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.payments.services import PaymentService, get_stripe
from apps.payments.models import (
    StripeCustomer,
    OnlinePayment,
    RecurringDonation,
    PaymentStatus,
)
from apps.members.tests.factories import MemberFactory
from apps.payments.tests.factories import (
    StripeCustomerFactory,
    OnlinePaymentFactory,
    SucceededPaymentFactory,
    FailedPaymentFactory,
    RecurringDonationFactory,
)
from apps.communication.models import Notification
from apps.donations.models import Donation


@pytest.mark.django_db
class TestGetStripe:
    """Tests for the get_stripe helper function."""

    def test_returns_none_without_key(self):
        with patch('apps.payments.services.settings') as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = ''
            result = get_stripe()
            assert result is None

    def test_returns_none_when_stripe_not_installed(self):
        with patch.dict('sys.modules', {'stripe': None}):
            result = get_stripe()
            assert result is None

    def test_returns_none_when_no_setting(self):
        with patch('apps.payments.services.settings', spec=[]):
            result = get_stripe()
            assert result is None

    def test_returns_none_when_stripe_importable_but_no_key(self):
        """When stripe is importable but STRIPE_SECRET_KEY is empty, returns None."""
        import types
        mock_stripe_module = types.ModuleType('stripe')
        mock_stripe_module.api_key = None
        with patch.dict('sys.modules', {'stripe': mock_stripe_module}):
            with patch('apps.payments.services.settings') as mock_settings:
                mock_settings.STRIPE_SECRET_KEY = ''
                result = get_stripe()
                assert result is None

    def test_returns_stripe_when_key_configured(self):
        """When stripe is importable and STRIPE_SECRET_KEY is set, returns stripe module."""
        import types
        mock_stripe_module = types.ModuleType('stripe')
        mock_stripe_module.api_key = None
        with patch.dict('sys.modules', {'stripe': mock_stripe_module}):
            with patch('apps.payments.services.settings') as mock_settings:
                mock_settings.STRIPE_SECRET_KEY = 'sk_test_12345'
                result = get_stripe()
                assert result is not None
                assert result.api_key == 'sk_test_12345'


@pytest.mark.django_db
class TestGetOrCreateStripeCustomer:
    """Tests for PaymentService.get_or_create_stripe_customer."""

    def test_returns_existing_customer(self):
        member = MemberFactory()
        existing = StripeCustomerFactory(member=member)

        result = PaymentService.get_or_create_stripe_customer(member)
        assert result == existing
        assert StripeCustomer.objects.count() == 1

    def test_creates_new_customer_dev_mode(self):
        member = MemberFactory()

        # Ensure no stripe module loaded (dev mode)
        with patch('apps.payments.services.get_stripe', return_value=None):
            result = PaymentService.get_or_create_stripe_customer(member)

        assert result is not None
        assert result.member == member
        assert result.stripe_customer_id == f'cus_dev_{member.pk}'
        assert StripeCustomer.objects.count() == 1

    def test_creates_new_customer_with_stripe(self):
        member = MemberFactory()

        mock_stripe = MagicMock()
        mock_customer = MagicMock()
        mock_customer.id = 'cus_real_123'
        mock_stripe.Customer.create.return_value = mock_customer

        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            result = PaymentService.get_or_create_stripe_customer(member)

        assert result.stripe_customer_id == 'cus_real_123'
        mock_stripe.Customer.create.assert_called_once_with(
            email=member.email,
            name=member.full_name,
            metadata={'member_id': str(member.pk)},
        )


@pytest.mark.django_db
class TestCreatePaymentIntent:
    """Tests for PaymentService.create_payment_intent."""

    def test_creates_payment_intent_dev_mode(self):
        member = MemberFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            payment, client_secret = PaymentService.create_payment_intent(
                member=member,
                amount=50.00,
                donation_type='offering',
            )

        assert payment is not None
        assert payment.member == member
        assert payment.amount == Decimal('50.00')
        assert payment.status == PaymentStatus.PENDING
        assert payment.donation_type == 'offering'
        assert payment.receipt_email == member.email
        assert payment.stripe_payment_intent_id.startswith('pi_dev_')
        assert '_secret_dev' in client_secret
        assert payment.campaign is None

    def test_creates_payment_intent_with_campaign(self):
        from apps.donations.models import DonationCampaign
        member = MemberFactory()
        campaign = DonationCampaign.objects.create(
            name='Test Campaign',
            goal_amount=Decimal('10000.00'),
            start_date=timezone.now().date(),
        )

        with patch('apps.payments.services.get_stripe', return_value=None):
            payment, client_secret = PaymentService.create_payment_intent(
                member=member,
                amount=100.00,
                donation_type='campaign',
                campaign=campaign,
            )

        assert payment.campaign == campaign
        assert payment.donation_type == 'campaign'

    def test_creates_stripe_customer_if_needed(self):
        member = MemberFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            payment, client_secret = PaymentService.create_payment_intent(
                member=member,
                amount=25.00,
            )

        assert StripeCustomer.objects.filter(member=member).exists()

    def test_reuses_existing_stripe_customer(self):
        member = MemberFactory()
        StripeCustomerFactory(member=member)

        with patch('apps.payments.services.get_stripe', return_value=None):
            payment, _ = PaymentService.create_payment_intent(
                member=member,
                amount=25.00,
            )

        assert StripeCustomer.objects.filter(member=member).count() == 1

    def test_creates_payment_intent_with_stripe(self):
        member = MemberFactory()

        mock_stripe = MagicMock()
        mock_intent = MagicMock()
        mock_intent.id = 'pi_real_abc'
        mock_intent.client_secret = 'pi_real_abc_secret_live'
        mock_stripe.PaymentIntent.create.return_value = mock_intent
        # For get_or_create_stripe_customer
        mock_customer = MagicMock()
        mock_customer.id = 'cus_real_xyz'
        mock_stripe.Customer.create.return_value = mock_customer

        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            payment, client_secret = PaymentService.create_payment_intent(
                member=member,
                amount=75.00,
                donation_type='tithe',
            )

        assert payment.stripe_payment_intent_id == 'pi_real_abc'
        assert client_secret == 'pi_real_abc_secret_live'
        mock_stripe.PaymentIntent.create.assert_called_once()

    def test_amount_converted_to_decimal(self):
        member = MemberFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            payment, _ = PaymentService.create_payment_intent(
                member=member,
                amount='33.33',
            )

        assert payment.amount == Decimal('33.33')


@pytest.mark.django_db
class TestHandlePaymentSucceeded:
    """Tests for PaymentService.handle_payment_succeeded."""

    def test_updates_status_to_succeeded(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        result = PaymentService.handle_payment_succeeded(
            payment_intent_id=payment.stripe_payment_intent_id,
            receipt_url='https://stripe.com/receipt/123',
        )

        payment.refresh_from_db()
        assert payment.status == PaymentStatus.SUCCEEDED
        assert payment.stripe_receipt_url == 'https://stripe.com/receipt/123'
        assert result == payment

    def test_creates_donation_record(self):
        payment = OnlinePaymentFactory(
            status=PaymentStatus.PENDING,
            donation_type='tithe',
        )
        PaymentService.handle_payment_succeeded(
            payment_intent_id=payment.stripe_payment_intent_id,
        )

        payment.refresh_from_db()
        assert payment.donation is not None
        donation = payment.donation
        assert donation.member == payment.member
        assert donation.amount == payment.amount
        assert donation.donation_type == 'tithe'
        assert donation.payment_method == 'online'

    def test_creates_notification(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        PaymentService.handle_payment_succeeded(
            payment_intent_id=payment.stripe_payment_intent_id,
        )

        notification = Notification.objects.filter(member=payment.member).first()
        assert notification is not None
        assert notification.title == 'Paiement reçu'
        assert notification.notification_type == 'donation'
        assert payment.amount_display in notification.message

    def test_returns_none_for_unknown_intent(self):
        result = PaymentService.handle_payment_succeeded(
            payment_intent_id='pi_nonexistent',
        )
        assert result is None

    def test_receipt_url_default_empty(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        PaymentService.handle_payment_succeeded(
            payment_intent_id=payment.stripe_payment_intent_id,
        )

        payment.refresh_from_db()
        assert payment.stripe_receipt_url == ''

    def test_with_campaign(self):
        from apps.donations.models import DonationCampaign
        campaign = DonationCampaign.objects.create(
            name='Build Fund',
            goal_amount=Decimal('5000.00'),
            start_date=timezone.now().date(),
        )
        payment = OnlinePaymentFactory(
            status=PaymentStatus.PENDING,
            donation_type='campaign',
            campaign=campaign,
        )
        PaymentService.handle_payment_succeeded(
            payment_intent_id=payment.stripe_payment_intent_id,
        )

        payment.refresh_from_db()
        assert payment.donation.campaign == campaign

    def test_donation_notes_contain_intent_id(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        PaymentService.handle_payment_succeeded(
            payment_intent_id=payment.stripe_payment_intent_id,
        )

        payment.refresh_from_db()
        assert payment.stripe_payment_intent_id in payment.donation.notes


@pytest.mark.django_db
class TestHandlePaymentFailed:
    """Tests for PaymentService.handle_payment_failed."""

    def test_updates_status_to_failed(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        result = PaymentService.handle_payment_failed(
            payment_intent_id=payment.stripe_payment_intent_id,
            failure_reason='Card declined',
        )

        payment.refresh_from_db()
        assert payment.status == PaymentStatus.FAILED
        assert result == payment

    def test_creates_failure_notification(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        PaymentService.handle_payment_failed(
            payment_intent_id=payment.stripe_payment_intent_id,
            failure_reason='Insufficient funds',
        )

        notification = Notification.objects.filter(member=payment.member).first()
        assert notification is not None
        assert notification.title == 'Paiement échoué'
        assert 'Insufficient funds' in notification.message
        assert payment.amount_display in notification.message

    def test_returns_none_for_unknown_intent(self):
        result = PaymentService.handle_payment_failed(
            payment_intent_id='pi_nonexistent',
        )
        assert result is None

    def test_no_donation_created(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        PaymentService.handle_payment_failed(
            payment_intent_id=payment.stripe_payment_intent_id,
        )

        assert Donation.objects.count() == 0

    def test_empty_failure_reason(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)
        PaymentService.handle_payment_failed(
            payment_intent_id=payment.stripe_payment_intent_id,
            failure_reason='',
        )

        payment.refresh_from_db()
        assert payment.status == PaymentStatus.FAILED


@pytest.mark.django_db
class TestRefundPayment:
    """Tests for PaymentService.refund_payment."""

    def test_refund_succeeded_payment_dev_mode(self):
        payment = SucceededPaymentFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            result = PaymentService.refund_payment(payment)

        payment.refresh_from_db()
        assert payment.status == PaymentStatus.REFUNDED
        assert result == payment

    def test_refund_pending_raises_error(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        with pytest.raises(ValueError, match='Can only refund succeeded payments'):
            PaymentService.refund_payment(payment)

    def test_refund_failed_raises_error(self):
        payment = FailedPaymentFactory()

        with pytest.raises(ValueError, match='Can only refund succeeded payments'):
            PaymentService.refund_payment(payment)

    def test_refund_already_refunded_raises_error(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.REFUNDED)

        with pytest.raises(ValueError):
            PaymentService.refund_payment(payment)

    def test_refund_cancelled_raises_error(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.CANCELLED)

        with pytest.raises(ValueError):
            PaymentService.refund_payment(payment)

    def test_refund_calls_stripe_when_available(self):
        payment = SucceededPaymentFactory()

        mock_stripe = MagicMock()
        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            PaymentService.refund_payment(payment)

        mock_stripe.Refund.create.assert_called_once_with(
            payment_intent=payment.stripe_payment_intent_id
        )


@pytest.mark.django_db
class TestCreateRecurringDonation:
    """Tests for PaymentService.create_recurring_donation."""

    def test_creates_recurring_dev_mode(self):
        member = MemberFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            recurring = PaymentService.create_recurring_donation(
                member=member,
                amount=50.00,
                frequency='monthly',
                donation_type='tithe',
            )

        assert recurring is not None
        assert recurring.member == member
        assert recurring.amount == Decimal('50.00')
        assert recurring.frequency == 'monthly'
        assert recurring.donation_type == 'tithe'
        assert recurring.is_active_subscription is True
        assert recurring.stripe_subscription_id.startswith('sub_dev_')

    def test_creates_recurring_weekly(self):
        member = MemberFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            recurring = PaymentService.create_recurring_donation(
                member=member,
                amount=20.00,
                frequency='weekly',
                donation_type='offering',
            )

        assert recurring.frequency == 'weekly'
        assert recurring.donation_type == 'offering'

    def test_creates_stripe_customer_if_needed(self):
        member = MemberFactory()

        with patch('apps.payments.services.get_stripe', return_value=None):
            PaymentService.create_recurring_donation(
                member=member,
                amount=25.00,
            )

        assert StripeCustomer.objects.filter(member=member).exists()

    def test_creates_recurring_with_stripe(self):
        member = MemberFactory()

        mock_stripe = MagicMock()
        mock_price = MagicMock()
        mock_price.id = 'price_test_123'
        mock_stripe.Price.create.return_value = mock_price
        mock_subscription = MagicMock()
        mock_subscription.id = 'sub_real_abc'
        mock_stripe.Subscription.create.return_value = mock_subscription
        # For get_or_create_stripe_customer
        mock_customer = MagicMock()
        mock_customer.id = 'cus_real_abc'
        mock_stripe.Customer.create.return_value = mock_customer

        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            recurring = PaymentService.create_recurring_donation(
                member=member,
                amount=100.00,
                frequency='monthly',
            )

        assert recurring.stripe_subscription_id == 'sub_real_abc'
        mock_stripe.Price.create.assert_called_once()
        mock_stripe.Subscription.create.assert_called_once()

    def test_creates_weekly_subscription_with_stripe(self):
        member = MemberFactory()

        mock_stripe = MagicMock()
        mock_price = MagicMock()
        mock_price.id = 'price_weekly'
        mock_stripe.Price.create.return_value = mock_price
        mock_sub = MagicMock()
        mock_sub.id = 'sub_weekly'
        mock_stripe.Subscription.create.return_value = mock_sub
        mock_customer = MagicMock()
        mock_customer.id = 'cus_weekly'
        mock_stripe.Customer.create.return_value = mock_customer

        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            PaymentService.create_recurring_donation(
                member=member,
                amount=10.00,
                frequency='weekly',
            )

        call_args = mock_stripe.Price.create.call_args
        assert call_args.kwargs['recurring']['interval'] == 'week'


@pytest.mark.django_db
class TestCancelRecurringDonation:
    """Tests for PaymentService.cancel_recurring_donation."""

    def test_cancels_dev_subscription(self):
        recurring = RecurringDonationFactory(
            stripe_subscription_id='sub_dev_abc123',
        )

        result = PaymentService.cancel_recurring_donation(recurring)

        recurring.refresh_from_db()
        assert recurring.is_active_subscription is False
        assert recurring.cancelled_at is not None
        assert result == recurring

    def test_cancels_with_stripe(self):
        recurring = RecurringDonationFactory(
            stripe_subscription_id='sub_real_abc',
        )

        mock_stripe = MagicMock()
        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            PaymentService.cancel_recurring_donation(recurring)

        mock_stripe.Subscription.delete.assert_called_once_with('sub_real_abc')

    def test_does_not_call_stripe_for_dev_sub(self):
        recurring = RecurringDonationFactory(
            stripe_subscription_id='sub_dev_testid123',
        )

        mock_stripe = MagicMock()
        with patch('apps.payments.services.get_stripe', return_value=mock_stripe):
            PaymentService.cancel_recurring_donation(recurring)

        mock_stripe.Subscription.delete.assert_not_called()

    def test_sets_cancelled_at_to_now(self):
        recurring = RecurringDonationFactory()
        before = timezone.now()

        with patch('apps.payments.services.get_stripe', return_value=None):
            PaymentService.cancel_recurring_donation(recurring)

        recurring.refresh_from_db()
        assert recurring.cancelled_at >= before
        assert recurring.cancelled_at <= timezone.now()

    def test_cancel_without_stripe(self):
        recurring = RecurringDonationFactory(
            stripe_subscription_id='sub_real_xyz',
        )

        with patch('apps.payments.services.get_stripe', return_value=None):
            PaymentService.cancel_recurring_donation(recurring)

        recurring.refresh_from_db()
        assert recurring.is_active_subscription is False
