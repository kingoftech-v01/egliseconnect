"""
Donations models - Donation tracking and receipts.

Models:
- DonationCampaign: Special fundraising campaigns
- Donation: Individual donations
- TaxReceipt: Annual tax receipts for CRA
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SoftDeleteModel
from apps.core.constants import DonationType, PaymentMethod
from apps.core.validators import validate_image_file


# =============================================================================
# DONATION CAMPAIGN MODEL
# =============================================================================

class DonationCampaign(BaseModel):
    """
    Special fundraising campaign.

    Campaigns have goals and deadlines for specific projects.
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de la campagne')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    goal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Objectif'),
        help_text=_('Montant cible de la campagne')
    )

    start_date = models.DateField(
        verbose_name=_('Date de début')
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de fin')
    )

    image = models.ImageField(
        upload_to='campaigns/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Image'),
        validators=[validate_image_file],
    )

    class Meta:
        verbose_name = _('Campagne de dons')
        verbose_name_plural = _('Campagnes de dons')
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def current_amount(self):
        """Calculate total donations for this campaign."""
        total = self.donations.filter(is_active=True).aggregate(
            total=Sum('amount')
        )['total']
        return total or Decimal('0.00')

    @property
    def progress_percentage(self):
        """Calculate progress towards goal."""
        if not self.goal_amount or self.goal_amount == 0:
            return 0
        return min(100, int((self.current_amount / self.goal_amount) * 100))

    @property
    def is_ongoing(self):
        """Check if campaign is currently active."""
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.end_date and today > self.end_date:
            return False
        return today >= self.start_date


# =============================================================================
# DONATION MODEL
# =============================================================================

class Donation(SoftDeleteModel):
    """
    Individual donation record.

    Tracks donations from members with auto-generated donation numbers.
    """

    # Unique donation number (auto-generated)
    donation_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_('Numéro de don'),
        help_text=_('Généré automatiquement')
    )

    # Donor
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='donations',
        verbose_name=_('Membre')
    )

    # Amount
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant')
    )

    # Type
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.OFFERING,
        verbose_name=_('Type de don')
    )

    # Payment method
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.CHOICES,
        default=PaymentMethod.CASH,
        verbose_name=_('Mode de paiement')
    )

    # Optional campaign link
    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        verbose_name=_('Campagne')
    )

    # Date
    date = models.DateField(
        default=timezone.now,
        verbose_name=_('Date du don')
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    # Recording info (for physical donations)
    recorded_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_donations',
        verbose_name=_('Enregistré par'),
        help_text=_('Personne qui a enregistré le don (pour les dons en espèces)')
    )

    # Check details (for check payments)
    check_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Numéro de chèque')
    )

    # Online transaction reference
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('ID de transaction'),
        help_text=_('Référence de la transaction en ligne')
    )

    # Receipt tracking
    receipt_sent = models.BooleanField(
        default=False,
        verbose_name=_('Reçu envoyé')
    )

    receipt_sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'envoi du reçu')
    )

    class Meta:
        verbose_name = _('Don')
        verbose_name_plural = _('Dons')
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['donation_number']),
            models.Index(fields=['member', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['donation_type']),
            models.Index(fields=['payment_method']),
        ]

    def __str__(self):
        return f'{self.donation_number} - {self.member.full_name} - ${self.amount}'

    def save(self, *args, **kwargs):
        """Auto-generate donation number on first save."""
        if not self.donation_number:
            from apps.core.utils import generate_donation_number
            self.donation_number = generate_donation_number()
        super().save(*args, **kwargs)

    @property
    def is_online(self):
        """Check if this was an online donation."""
        return self.payment_method in [PaymentMethod.ONLINE, PaymentMethod.CARD]


# =============================================================================
# TAX RECEIPT MODEL
# =============================================================================

class TaxReceipt(BaseModel):
    """
    Annual tax receipt for CRA.

    Generated for each member at the end of the year or on demand.
    """

    # Unique receipt number
    receipt_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Numéro de reçu')
    )

    # Recipient
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='tax_receipts',
        verbose_name=_('Membre')
    )

    # Year
    year = models.PositiveIntegerField(
        verbose_name=_('Année')
    )

    # Total amount
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant total')
    )

    # Generation info
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de génération')
    )

    generated_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_receipts',
        verbose_name=_('Généré par')
    )

    # PDF file
    pdf_file = models.FileField(
        upload_to='receipts/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Fichier PDF')
    )

    # Email tracking
    email_sent = models.BooleanField(
        default=False,
        verbose_name=_('Envoyé par courriel')
    )

    email_sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'envoi')
    )

    # Member info snapshot (for historical accuracy)
    member_name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du membre'),
        help_text=_('Nom au moment de la génération')
    )

    member_address = models.TextField(
        blank=True,
        verbose_name=_('Adresse du membre'),
        help_text=_('Adresse au moment de la génération')
    )

    class Meta:
        verbose_name = _('Reçu fiscal')
        verbose_name_plural = _('Reçus fiscaux')
        ordering = ['-year', '-generated_at']
        unique_together = ['member', 'year']
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['member', 'year']),
            models.Index(fields=['year']),
        ]

    def __str__(self):
        return f'{self.receipt_number} - {self.member_name} ({self.year})'

    def save(self, *args, **kwargs):
        """Capture member info on save."""
        if not self.member_name:
            self.member_name = self.member.full_name
        if not self.member_address:
            self.member_address = self.member.full_address
        super().save(*args, **kwargs)
