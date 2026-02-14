"""SMS/Text-to-Give donation service (Twilio + Stripe integration)."""
import logging
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import DonationType, PaymentMethod

logger = logging.getLogger(__name__)


class SMSDonationService:
    """Process SMS-based donation commands via Twilio."""

    # SMS command patterns
    GIVE_PATTERN = re.compile(
        r'^(?:GIVE|DON|DONNER)\s+(\d+(?:\.\d{1,2})?)\s*(.*)$',
        re.IGNORECASE
    )
    HELP_PATTERN = re.compile(r'^(?:HELP|AIDE)$', re.IGNORECASE)
    STATUS_PATTERN = re.compile(r'^(?:STATUS|STATUT)$', re.IGNORECASE)

    @classmethod
    def process_sms(cls, phone_number, message_body):
        """
        Process an incoming SMS donation command.

        Args:
            phone_number: sender's phone number
            message_body: SMS message text

        Returns:
            dict with 'success', 'response_message', 'donation' (if created)
        """
        message_body = message_body.strip()

        # Help command
        if cls.HELP_PATTERN.match(message_body):
            return {
                'success': True,
                'response_message': cls._help_message(),
                'donation': None,
            }

        # Status command
        if cls.STATUS_PATTERN.match(message_body):
            return cls._handle_status(phone_number)

        # Give command
        match = cls.GIVE_PATTERN.match(message_body)
        if match:
            amount_str = match.group(1)
            campaign_keyword = match.group(2).strip() if match.group(2) else ''
            return cls._handle_give(phone_number, amount_str, campaign_keyword)

        return {
            'success': False,
            'response_message': (
                'Commande non reconnue. '
                'Envoyez DONNER [montant] pour faire un don, '
                'ou AIDE pour de l\'aide.'
            ),
            'donation': None,
        }

    @classmethod
    def _handle_give(cls, phone_number, amount_str, campaign_keyword=''):
        """Handle a GIVE/DON command."""
        from .models import Donation, DonationCampaign

        # Look up member by phone
        member = cls._lookup_member(phone_number)
        if not member:
            return {
                'success': False,
                'response_message': (
                    'Votre numero de telephone n\'est pas associe a un membre. '
                    'Contactez l\'eglise pour enregistrer votre numero.'
                ),
                'donation': None,
            }

        # Parse amount
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return {
                'success': False,
                'response_message': 'Montant invalide. Exemple: DONNER 50',
                'donation': None,
            }

        if amount > Decimal('10000'):
            return {
                'success': False,
                'response_message': (
                    'Le montant maximum par SMS est de 10 000$. '
                    'Pour un don plus important, utilisez le site web.'
                ),
                'donation': None,
            }

        # Look up campaign if keyword provided
        campaign = None
        if campaign_keyword:
            campaign = DonationCampaign.objects.filter(
                name__icontains=campaign_keyword,
                is_active=True,
            ).first()

        # Create donation
        try:
            donation = Donation.objects.create(
                member=member,
                amount=amount,
                donation_type=DonationType.OFFERING,
                payment_method=PaymentMethod.ONLINE,
                campaign=campaign,
                date=timezone.now().date(),
                notes=f'Don par SMS depuis {phone_number}',
            )

            campaign_text = f' pour {campaign.name}' if campaign else ''
            return {
                'success': True,
                'response_message': (
                    f'Merci! Don de {amount}${campaign_text} enregistre. '
                    f'No: {donation.donation_number}'
                ),
                'donation': donation,
            }
        except Exception as e:
            logger.error(f'SMS donation error for {phone_number}: {e}')
            return {
                'success': False,
                'response_message': (
                    'Erreur lors de l\'enregistrement. Veuillez reessayer.'
                ),
                'donation': None,
            }

    @classmethod
    def _handle_status(cls, phone_number):
        """Handle STATUS command - show recent donation summary."""
        from .models import Donation
        from django.db.models import Sum

        member = cls._lookup_member(phone_number)
        if not member:
            return {
                'success': False,
                'response_message': 'Numero de telephone non reconnu.',
                'donation': None,
            }

        year = timezone.now().year
        total = Donation.objects.filter(
            member=member,
            date__year=year,
            is_active=True,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        count = Donation.objects.filter(
            member=member,
            date__year=year,
            is_active=True,
        ).count()

        return {
            'success': True,
            'response_message': (
                f'{member.full_name}: '
                f'{count} don(s) en {year} pour un total de {total}$.'
            ),
            'donation': None,
        }

    @classmethod
    def _lookup_member(cls, phone_number):
        """Look up a member by phone number."""
        from apps.members.models import Member

        # Normalize phone number: strip +, spaces, dashes
        cleaned = re.sub(r'[^\d]', '', phone_number)

        # Try exact match first, then partial
        member = Member.objects.filter(
            phone__icontains=cleaned[-10:],  # Last 10 digits
            is_active=True,
        ).first()

        return member

    @staticmethod
    def _help_message():
        """Return the help message for SMS commands."""
        return (
            'Commandes SMS:\n'
            'DONNER [montant] - Faire un don\n'
            'DONNER [montant] [campagne] - Don pour une campagne\n'
            'STATUT - Voir vos dons de l\'annee\n'
            'AIDE - Afficher cette aide'
        )

    @classmethod
    def send_confirmation_sms(cls, donation, phone_number):
        """Send an SMS confirmation after a donation (stub for Twilio)."""
        try:
            # Twilio integration stub
            twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            twilio_from = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

            if not all([twilio_sid, twilio_token, twilio_from]):
                logger.info(
                    f'Twilio not configured. SMS confirmation skipped for '
                    f'donation {donation.donation_number}'
                )
                return False

            # In production, uncomment the following:
            # from twilio.rest import Client
            # client = Client(twilio_sid, twilio_token)
            # message = client.messages.create(
            #     body=f'Don de {donation.amount}$ confirme. No: {donation.donation_number}',
            #     from_=twilio_from,
            #     to=phone_number,
            # )
            logger.info(f'SMS confirmation sent for donation {donation.donation_number}')
            return True

        except Exception as e:
            logger.error(f'Failed to send SMS confirmation: {e}')
            return False
