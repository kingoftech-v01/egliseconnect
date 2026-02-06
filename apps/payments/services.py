"""Stripe payment service layer."""
import logging
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_stripe():
    """Get configured stripe module. Returns None if not configured."""
    try:
        import stripe
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not stripe.api_key:
            return None
        return stripe
    except ImportError:
        return None


class PaymentService:
    """Manages Stripe payment operations."""

    @staticmethod
    def get_or_create_stripe_customer(member):
        """Get existing or create new Stripe customer for a member."""
        from .models import StripeCustomer

        try:
            return member.stripe_customer
        except StripeCustomer.DoesNotExist:
            pass

        stripe = get_stripe()
        if not stripe:
            # Create a mock customer ID for development
            customer_id = f'cus_dev_{member.pk}'
        else:
            customer = stripe.Customer.create(
                email=member.email,
                name=member.full_name,
                metadata={'member_id': str(member.pk)},
            )
            customer_id = customer.id

        return StripeCustomer.objects.create(
            member=member,
            stripe_customer_id=customer_id,
        )

    @staticmethod
    def create_payment_intent(member, amount, donation_type='offering', campaign=None):
        """Create a Stripe PaymentIntent and local record."""
        from .models import OnlinePayment, PaymentStatus

        amount_decimal = Decimal(str(amount))
        stripe_customer = PaymentService.get_or_create_stripe_customer(member)

        stripe = get_stripe()
        if stripe:
            intent = stripe.PaymentIntent.create(
                amount=int(amount_decimal * 100),  # cents
                currency='cad',
                customer=stripe_customer.stripe_customer_id,
                metadata={
                    'member_id': str(member.pk),
                    'donation_type': donation_type,
                    'campaign_id': str(campaign.pk) if campaign else '',
                },
            )
            intent_id = intent.id
            client_secret = intent.client_secret
        else:
            # Development mode without Stripe
            import uuid
            intent_id = f'pi_dev_{uuid.uuid4().hex[:16]}'
            client_secret = f'{intent_id}_secret_dev'

        payment = OnlinePayment.objects.create(
            member=member,
            stripe_payment_intent_id=intent_id,
            amount=amount_decimal,
            status=PaymentStatus.PENDING,
            donation_type=donation_type,
            campaign=campaign,
            receipt_email=member.email,
        )

        return payment, client_secret

    @staticmethod
    def handle_payment_succeeded(payment_intent_id, receipt_url=''):
        """Handle successful payment webhook."""
        from .models import OnlinePayment, PaymentStatus
        from apps.donations.models import Donation
        from apps.core.constants import PaymentMethod, DonationType

        try:
            payment = OnlinePayment.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
        except OnlinePayment.DoesNotExist:
            logger.error(f'Payment not found: {payment_intent_id}')
            return None

        payment.status = PaymentStatus.SUCCEEDED
        payment.stripe_receipt_url = receipt_url
        payment.save(update_fields=['status', 'stripe_receipt_url', 'updated_at'])

        # Create a Donation record in the existing donations app
        donation = Donation.objects.create(
            member=payment.member,
            amount=payment.amount,
            donation_type=payment.donation_type,
            payment_method=PaymentMethod.ONLINE,
            date=timezone.now().date(),
            campaign=payment.campaign,
            notes=f'Paiement en ligne Stripe ({payment_intent_id})',
        )
        payment.donation = donation
        payment.save(update_fields=['donation', 'updated_at'])

        # Create notification
        from apps.communication.models import Notification
        Notification.objects.create(
            member=payment.member,
            title='Paiement reçu',
            message=f'Votre don de {payment.amount_display} a été traité avec succès.',
            notification_type='donation',
            link='/payments/history/',
        )

        return payment

    @staticmethod
    def handle_payment_failed(payment_intent_id, failure_reason=''):
        """Handle failed payment webhook."""
        from .models import OnlinePayment, PaymentStatus

        try:
            payment = OnlinePayment.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
        except OnlinePayment.DoesNotExist:
            return None

        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=['status', 'updated_at'])

        from apps.communication.models import Notification
        Notification.objects.create(
            member=payment.member,
            title='Paiement échoué',
            message=f'Votre paiement de {payment.amount_display} a échoué. {failure_reason}',
            notification_type='donation',
        )

        return payment

    @staticmethod
    def refund_payment(payment):
        """Refund a successful payment."""
        from .models import PaymentStatus

        if payment.status != PaymentStatus.SUCCEEDED:
            raise ValueError('Can only refund succeeded payments')

        stripe = get_stripe()
        if stripe:
            stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id
            )

        payment.status = PaymentStatus.REFUNDED
        payment.save(update_fields=['status', 'updated_at'])
        return payment

    @staticmethod
    def create_recurring_donation(member, amount, frequency='monthly', donation_type='tithe'):
        """Create a recurring donation via Stripe Subscription."""
        from .models import RecurringDonation

        stripe_customer = PaymentService.get_or_create_stripe_customer(member)

        stripe = get_stripe()
        if stripe:
            price = stripe.Price.create(
                unit_amount=int(Decimal(str(amount)) * 100),
                currency='cad',
                recurring={'interval': 'week' if frequency == 'weekly' else 'month'},
                product_data={'name': f'Don {donation_type} - {member.full_name}'},
            )
            subscription = stripe.Subscription.create(
                customer=stripe_customer.stripe_customer_id,
                items=[{'price': price.id}],
            )
            sub_id = subscription.id
        else:
            import uuid
            sub_id = f'sub_dev_{uuid.uuid4().hex[:16]}'

        return RecurringDonation.objects.create(
            member=member,
            stripe_subscription_id=sub_id,
            amount=Decimal(str(amount)),
            frequency=frequency,
            donation_type=donation_type,
        )

    @staticmethod
    def cancel_recurring_donation(recurring):
        """Cancel a recurring donation."""
        stripe = get_stripe()
        if stripe and not recurring.stripe_subscription_id.startswith('sub_dev_'):
            stripe.Subscription.delete(recurring.stripe_subscription_id)

        recurring.is_active_subscription = False
        recurring.cancelled_at = timezone.now()
        recurring.save(update_fields=['is_active_subscription', 'cancelled_at', 'updated_at'])
        return recurring
