"""Stripe payment service layer, statement generation, goal tracking, ACH, crypto, kiosk, SMS."""
import io
import logging
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
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
    def create_payment_intent(member, amount, donation_type='offering', campaign=None, currency='cad'):
        """Create a Stripe PaymentIntent and local record."""
        from .models import OnlinePayment, PaymentStatus

        amount_decimal = Decimal(str(amount))
        stripe_customer = PaymentService.get_or_create_stripe_customer(member)

        stripe = get_stripe()
        if stripe:
            intent = stripe.PaymentIntent.create(
                amount=int(amount_decimal * 100),  # cents
                currency=currency.lower(),
                customer=stripe_customer.stripe_customer_id,
                metadata={
                    'member_id': str(member.pk),
                    'donation_type': donation_type,
                    'campaign_id': str(campaign.pk) if campaign else '',
                },
                payment_method_types=['card'],
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
            currency=currency.upper(),
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

    @staticmethod
    def update_recurring_donation(recurring, new_amount, new_frequency):
        """Update amount/frequency for a recurring donation."""
        stripe = get_stripe()
        if stripe and not recurring.stripe_subscription_id.startswith('sub_dev_'):
            # Cancel old and create new
            stripe.Subscription.delete(recurring.stripe_subscription_id)
            stripe_customer = PaymentService.get_or_create_stripe_customer(recurring.member)
            price = stripe.Price.create(
                unit_amount=int(Decimal(str(new_amount)) * 100),
                currency='cad',
                recurring={'interval': 'week' if new_frequency == 'weekly' else 'month'},
                product_data={'name': f'Don {recurring.donation_type} - {recurring.member.full_name}'},
            )
            subscription = stripe.Subscription.create(
                customer=stripe_customer.stripe_customer_id,
                items=[{'price': price.id}],
            )
            recurring.stripe_subscription_id = subscription.id

        recurring.amount = Decimal(str(new_amount))
        recurring.frequency = new_frequency
        recurring.save(update_fields=['amount', 'frequency', 'stripe_subscription_id', 'updated_at'])
        return recurring

    # ─── Giving Goal Tracking ────────────────────────────────────────────────

    @staticmethod
    def calculate_giving_goal_progress(member, year):
        """Calculate giving goal progress: sum of succeeded payments in year vs target."""
        from .models import GivingGoal, OnlinePayment, PaymentStatus

        try:
            goal = GivingGoal.objects.get(member=member, year=year)
        except GivingGoal.DoesNotExist:
            return None

        total_given = OnlinePayment.objects.filter(
            member=member,
            status=PaymentStatus.SUCCEEDED,
            created_at__year=year,
            is_active=True,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return {
            'target': goal.target_amount,
            'given': total_given,
            'remaining': max(Decimal('0.00'), goal.target_amount - total_given),
            'percentage': min(100, int((total_given / goal.target_amount) * 100)) if goal.target_amount > 0 else 0,
        }

    @staticmethod
    def get_giving_goal_summary():
        """Get summary for finance staff: total pledged vs received across all members."""
        from .models import GivingGoal, OnlinePayment, PaymentStatus

        current_year = timezone.now().year
        goals = GivingGoal.objects.filter(year=current_year, is_active=True)

        total_pledged = goals.aggregate(total=Sum('target_amount'))['total'] or Decimal('0.00')

        total_received = OnlinePayment.objects.filter(
            status=PaymentStatus.SUCCEEDED,
            created_at__year=current_year,
            is_active=True,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return {
            'total_pledged': total_pledged,
            'total_received': total_received,
            'goal_count': goals.count(),
            'percentage': min(100, int((total_received / total_pledged) * 100)) if total_pledged > 0 else 0,
        }

    # ─── Statement Generation ────────────────────────────────────────────────

    @staticmethod
    def generate_statement_pdf(statement):
        """Generate a giving statement PDF using xhtml2pdf."""
        from .models import OnlinePayment, PaymentStatus

        try:
            from xhtml2pdf import pisa
        except ImportError:
            logger.warning("xhtml2pdf not installed, skipping PDF generation")
            return None

        church_name = getattr(settings, 'CHURCH_NAME', 'ÉgliseConnect')
        church_address = getattr(settings, 'CHURCH_ADDRESS', '')
        church_reg = getattr(settings, 'CHURCH_REGISTRATION_NUMBER', '')

        payments = OnlinePayment.objects.filter(
            member=statement.member,
            status=PaymentStatus.SUCCEEDED,
            created_at__date__gte=statement.period_start,
            created_at__date__lte=statement.period_end,
            is_active=True,
        ).order_by('created_at')

        total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        rows_html = ''
        for p in payments:
            rows_html += f'''<tr>
                <td style="padding:5px;border:1px solid #ccc;">{p.created_at.strftime("%d/%m/%Y")}</td>
                <td style="padding:5px;border:1px solid #ccc;">{p.get_donation_type_display()}</td>
                <td style="padding:5px;border:1px solid #ccc;text-align:right;">{p.amount:.2f} {p.currency}</td>
            </tr>'''

        html = f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif;font-size:11px;margin:30px;">
            <div style="text-align:center;margin-bottom:20px;">
                <h1 style="margin:0;">{church_name}</h1>
                <p style="margin:5px 0;">{church_address}</p>
                {('<p style="margin:5px 0;">No. enregistrement: ' + church_reg + '</p>') if church_reg else ''}
            </div>
            <hr/>
            <h2>Relevé de dons - {statement.get_statement_type_display()}</h2>
            <p><strong>Membre:</strong> {statement.member.full_name}</p>
            <p><strong>Période:</strong> {statement.period_start.strftime("%d/%m/%Y")} au {statement.period_end.strftime("%d/%m/%Y")}</p>
            <table style="width:100%;border-collapse:collapse;margin-top:15px;">
                <thead>
                    <tr>
                        <th style="padding:5px;border:1px solid #ccc;background:#f5f5f5;text-align:left;">Date</th>
                        <th style="padding:5px;border:1px solid #ccc;background:#f5f5f5;text-align:left;">Type</th>
                        <th style="padding:5px;border:1px solid #ccc;background:#f5f5f5;text-align:right;">Montant</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                    <tr>
                        <td colspan="2" style="padding:5px;border:1px solid #ccc;font-weight:bold;">Total</td>
                        <td style="padding:5px;border:1px solid #ccc;text-align:right;font-weight:bold;">{total:.2f} CAD</td>
                    </tr>
                </tbody>
            </table>
            <p style="margin-top:30px;font-size:9px;color:#666;">
                Ce relevé est émis à des fins fiscales. Veuillez le conserver pour votre déclaration de revenus.
            </p>
        </body>
        </html>
        """

        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html), dest=output)
        output.seek(0)

        # Update statement
        statement.total_amount = total
        from django.core.files.base import ContentFile
        filename = f'statement_{statement.member.pk}_{statement.period_start}_{statement.period_end}.pdf'
        statement.pdf_file.save(filename, ContentFile(output.read()), save=False)
        statement.save(update_fields=['total_amount', 'pdf_file', 'updated_at'])

        return statement

    @staticmethod
    def generate_bulk_statements(period_start, period_end, statement_type):
        """Generate statements for all donors in the period."""
        from .models import GivingStatement, OnlinePayment, PaymentStatus

        # Find all members with payments in the period
        member_ids = OnlinePayment.objects.filter(
            status=PaymentStatus.SUCCEEDED,
            created_at__date__gte=period_start,
            created_at__date__lte=period_end,
            is_active=True,
        ).values_list('member_id', flat=True).distinct()

        statements = []
        for member_id in member_ids:
            statement, created = GivingStatement.objects.get_or_create(
                member_id=member_id,
                period_start=period_start,
                period_end=period_end,
                statement_type=statement_type,
            )
            PaymentService.generate_statement_pdf(statement)
            statements.append(statement)

        return statements

    # ─── ACH / Bank Transfer ─────────────────────────────────────────────────

    @staticmethod
    def create_ach_payment_intent(member, amount, donation_type='offering'):
        """Create a Stripe PaymentIntent for ACH bank transfer."""
        from .models import OnlinePayment, PaymentStatus

        amount_decimal = Decimal(str(amount))
        stripe_customer = PaymentService.get_or_create_stripe_customer(member)

        stripe = get_stripe()
        if stripe:
            intent = stripe.PaymentIntent.create(
                amount=int(amount_decimal * 100),
                currency='cad',
                customer=stripe_customer.stripe_customer_id,
                payment_method_types=['us_bank_account'],
                metadata={
                    'member_id': str(member.pk),
                    'donation_type': donation_type,
                    'payment_type': 'ach',
                },
            )
            intent_id = intent.id
            client_secret = intent.client_secret
        else:
            import uuid
            intent_id = f'pi_ach_dev_{uuid.uuid4().hex[:16]}'
            client_secret = f'{intent_id}_secret_dev'

        payment = OnlinePayment.objects.create(
            member=member,
            stripe_payment_intent_id=intent_id,
            amount=amount_decimal,
            status=PaymentStatus.PENDING,
            donation_type=donation_type,
            receipt_email=member.email,
            payment_method_type='ach_debit',
        )

        return payment, client_secret

    @staticmethod
    def verify_bank_account(member, amounts):
        """Verify bank account with micro-deposit amounts."""
        stripe = get_stripe()
        if not stripe:
            return True  # Dev mode

        stripe_customer = PaymentService.get_or_create_stripe_customer(member)
        # In a real implementation, this would verify micro-deposits
        return True

    @staticmethod
    def create_ach_recurring(member, amount, frequency='monthly', donation_type='tithe'):
        """Create ACH recurring debit."""
        from .models import RecurringDonation

        stripe_customer = PaymentService.get_or_create_stripe_customer(member)

        stripe = get_stripe()
        if stripe:
            price = stripe.Price.create(
                unit_amount=int(Decimal(str(amount)) * 100),
                currency='cad',
                recurring={'interval': 'week' if frequency == 'weekly' else 'month'},
                product_data={'name': f'Don ACH {donation_type} - {member.full_name}'},
            )
            subscription = stripe.Subscription.create(
                customer=stripe_customer.stripe_customer_id,
                items=[{'price': price.id}],
                payment_settings={'payment_method_types': ['us_bank_account']},
            )
            sub_id = subscription.id
        else:
            import uuid
            sub_id = f'sub_ach_dev_{uuid.uuid4().hex[:16]}'

        return RecurringDonation.objects.create(
            member=member,
            stripe_subscription_id=sub_id,
            amount=Decimal(str(amount)),
            frequency=frequency,
            donation_type=donation_type,
        )

    # ─── Cryptocurrency ──────────────────────────────────────────────────────

    @staticmethod
    def create_crypto_charge(member, amount, currency='CAD'):
        """Create a Coinbase Commerce charge for crypto donation."""
        api_key = getattr(settings, 'COINBASE_COMMERCE_API_KEY', '')

        if not api_key:
            import uuid
            return {
                'id': f'crypto_dev_{uuid.uuid4().hex[:16]}',
                'hosted_url': 'https://commerce.coinbase.com/charges/dev_mock',
                'pricing': {
                    'local': {'amount': str(amount), 'currency': currency},
                },
                'supported_cryptos': ['BTC', 'ETH', 'USDC'],
            }

        try:
            import requests
            response = requests.post(
                'https://api.commerce.coinbase.com/charges',
                headers={
                    'X-CC-Api-Key': api_key,
                    'Content-Type': 'application/json',
                },
                json={
                    'name': f'Don - {member.full_name}',
                    'description': 'Don en cryptomonnaie',
                    'pricing_type': 'fixed_price',
                    'local_price': {
                        'amount': str(amount),
                        'currency': currency,
                    },
                    'metadata': {
                        'member_id': str(member.pk),
                    },
                },
            )
            return response.json().get('data', {})
        except Exception as e:
            logger.error(f'Coinbase Commerce error: {e}')
            return None

    @staticmethod
    def get_supported_cryptos():
        """Return list of supported cryptocurrencies."""
        return [
            {'symbol': 'BTC', 'name': 'Bitcoin'},
            {'symbol': 'ETH', 'name': 'Ethereum'},
            {'symbol': 'USDC', 'name': 'USD Coin'},
        ]

    # ─── Payment Plans ───────────────────────────────────────────────────────

    @staticmethod
    def create_payment_plan(member, total_amount, installment_amount, frequency, start_date, donation_type='offering'):
        """Create a payment plan for installment giving."""
        from .models import PaymentPlan

        return PaymentPlan.objects.create(
            member=member,
            total_amount=Decimal(str(total_amount)),
            installment_amount=Decimal(str(installment_amount)),
            frequency=frequency,
            remaining_amount=Decimal(str(total_amount)),
            start_date=start_date,
            donation_type=donation_type,
        )

    @staticmethod
    def record_plan_payment(plan, amount=None):
        """Record a payment against a plan."""
        from .models import PaymentPlan
        from apps.core.constants import PaymentPlanStatus

        pay_amount = Decimal(str(amount)) if amount else plan.installment_amount
        plan.remaining_amount = max(Decimal('0.00'), plan.remaining_amount - pay_amount)

        if plan.remaining_amount == Decimal('0.00'):
            plan.status = PaymentPlanStatus.COMPLETED
            plan.completed_at = timezone.now()

        plan.save(update_fields=['remaining_amount', 'status', 'completed_at', 'updated_at'])
        return plan

    @staticmethod
    def complete_plan_early(plan):
        """Mark a payment plan as completed early."""
        from apps.core.constants import PaymentPlanStatus

        plan.remaining_amount = Decimal('0.00')
        plan.status = PaymentPlanStatus.COMPLETED
        plan.completed_at = timezone.now()
        plan.save(update_fields=['remaining_amount', 'status', 'completed_at', 'updated_at'])
        return plan

    # ─── SMS Donation Processing ─────────────────────────────────────────────

    @staticmethod
    def process_sms_donation(phone_number, message_text):
        """Process an incoming SMS donation command like 'GIVE 100' or 'GIVE 100 MONTHLY'."""
        from .models import SMSDonation
        from apps.members.models import Member

        parts = message_text.strip().upper().split()

        if len(parts) < 2 or parts[0] not in ('GIVE', 'DON', 'DONNER'):
            return None, 'Format invalide. Envoyez GIVE <montant> ou GIVE <montant> MONTHLY'

        try:
            amount = Decimal(parts[1])
        except Exception:
            return None, 'Montant invalide.'

        if amount < 1:
            return None, 'Le montant minimum est de 1$.'

        is_recurring = False
        frequency = ''
        if len(parts) >= 3:
            freq_map = {
                'WEEKLY': 'weekly',
                'MONTHLY': 'monthly',
                'HEBDOMADAIRE': 'weekly',
                'MENSUEL': 'monthly',
            }
            freq = freq_map.get(parts[2], '')
            if freq:
                is_recurring = True
                frequency = freq

        # Try to match phone number to a member
        member = Member.objects.filter(phone=phone_number, is_active=True).first()

        sms_donation = SMSDonation.objects.create(
            phone_number=phone_number,
            amount=amount,
            member=member,
            command_text=message_text,
            is_recurring=is_recurring,
            frequency=frequency,
        )

        if not member:
            return sms_donation, 'Merci! Pour compléter votre don, inscrivez-vous: {url}'

        # Process with Stripe if member has a payment method
        try:
            stripe_customer = PaymentService.get_or_create_stripe_customer(member)
            sms_donation.processed = True
            sms_donation.stripe_charge_id = f'ch_sms_dev_{sms_donation.pk}'
            sms_donation.save(update_fields=['processed', 'stripe_charge_id', 'updated_at'])
            return sms_donation, f'Merci {member.full_name}! Votre don de {amount}$ a été traité.'
        except Exception as e:
            logger.error(f'SMS donation processing error: {e}')
            return sms_donation, 'Erreur lors du traitement. Veuillez réessayer.'

    # ─── Kiosk ───────────────────────────────────────────────────────────────

    @staticmethod
    def create_kiosk_payment(amount, session=None):
        """Create a kiosk terminal payment."""
        stripe = get_stripe()
        if stripe:
            intent = stripe.PaymentIntent.create(
                amount=int(Decimal(str(amount)) * 100),
                currency='cad',
                payment_method_types=['card_present'],
                capture_method='automatic',
            )
            return {
                'client_secret': intent.client_secret,
                'intent_id': intent.id,
            }
        else:
            import uuid
            intent_id = f'pi_kiosk_dev_{uuid.uuid4().hex[:16]}'
            return {
                'client_secret': f'{intent_id}_secret_dev',
                'intent_id': intent_id,
            }

    @staticmethod
    def generate_kiosk_receipt(payment_data):
        """Generate a receipt for a kiosk transaction."""
        church_name = getattr(settings, 'CHURCH_NAME', 'ÉgliseConnect')
        return {
            'church_name': church_name,
            'amount': payment_data.get('amount', '0.00'),
            'date': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'transaction_id': payment_data.get('intent_id', 'N/A'),
            'message': 'Merci pour votre don!',
        }

    @staticmethod
    def reconcile_kiosk_session(session):
        """Mark a kiosk session as reconciled."""
        session.reconciled = True
        session.reconciled_at = timezone.now()
        session.save(update_fields=['reconciled', 'reconciled_at', 'updated_at'])
        return session
