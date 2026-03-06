"""Donation tracking and tax receipts for church giving."""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SoftDeleteModel
from apps.core.constants import DonationType, PaymentMethod, PledgeStatus, PledgeFrequency
from apps.core.validators import validate_image_file


class DonationCampaign(BaseModel):
    """Special fundraising campaign with goals and deadlines."""

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


class Donation(SoftDeleteModel):
    """Individual donation record with auto-generated donation number."""

    donation_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_('Numéro de don'),
        help_text=_('Généré automatiquement')
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='donations',
        verbose_name=_('Membre')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant')
    )

    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.OFFERING,
        verbose_name=_('Type de don')
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.CHOICES,
        default=PaymentMethod.CASH,
        verbose_name=_('Mode de paiement')
    )

    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        verbose_name=_('Campagne')
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name=_('Date du don')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    recorded_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_donations',
        verbose_name=_('Enregistré par'),
        help_text=_('Personne qui a enregistré le don (pour les dons en espèces)')
    )

    check_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Numéro de chèque')
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('ID de transaction'),
        help_text=_('Référence de la transaction en ligne')
    )

    currency = models.CharField(
        max_length=3,
        default='CAD',
        verbose_name=_('Devise'),
        help_text=_('Code de devise ISO 4217')
    )

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


class TaxReceipt(BaseModel):
    """Annual CRA tax receipt, generated yearly or on demand."""

    receipt_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Numéro de reçu')
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='tax_receipts',
        verbose_name=_('Membre')
    )

    year = models.PositiveIntegerField(
        verbose_name=_('Année')
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant total')
    )

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

    pdf_file = models.FileField(
        upload_to='receipts/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Fichier PDF')
    )

    email_sent = models.BooleanField(
        default=False,
        verbose_name=_('Envoyé par courriel')
    )

    email_sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'envoi')
    )

    # Snapshot of member info at generation time for historical accuracy
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
        """Capture member info snapshot on first save."""
        if not self.member_name:
            self.member_name = self.member.full_name
        if not self.member_address:
            self.member_address = self.member.full_address
        super().save(*args, **kwargs)


class FinanceDelegation(BaseModel):
    """Delegation of finance access from a pastor to another leader."""

    delegated_to = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='finance_delegations_received',
        verbose_name=_('Délégué à')
    )

    delegated_by = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='finance_delegations_granted',
        verbose_name=_('Délégué par')
    )

    granted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Accordé le')
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Révoqué le')
    )

    reason = models.TextField(
        blank=True,
        verbose_name=_('Motif')
    )

    class Meta:
        verbose_name = _('Délégation financière')
        verbose_name_plural = _('Délégations financières')
        ordering = ['-granted_at']

    def __str__(self):
        return f'{self.delegated_by} → {self.delegated_to}'

    @property
    def is_active_delegation(self):
        return self.is_active and self.revoked_at is None


# ==============================================================================
# Pledge & Commitment Tracking
# ==============================================================================


class Pledge(BaseModel):
    """Member pledge/commitment to give over time."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='pledges',
        verbose_name=_('Membre')
    )

    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pledges',
        verbose_name=_('Campagne')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant promis')
    )

    frequency = models.CharField(
        max_length=20,
        choices=PledgeFrequency.CHOICES,
        default=PledgeFrequency.MONTHLY,
        verbose_name=_('Fréquence')
    )

    start_date = models.DateField(
        verbose_name=_('Date de début')
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de fin')
    )

    status = models.CharField(
        max_length=20,
        choices=PledgeStatus.CHOICES,
        default=PledgeStatus.ACTIVE,
        verbose_name=_('Statut')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Engagement')
        verbose_name_plural = _('Engagements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['campaign']),
        ]

    def __str__(self):
        return f'{self.member.full_name} - {self.amount}$ ({self.get_frequency_display()})'

    @property
    def fulfilled_amount(self):
        """Total amount fulfilled through linked donations."""
        total = self.fulfillments.aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')

    @property
    def progress_percentage(self):
        """Percentage of pledge fulfilled."""
        if not self.amount or self.amount == 0:
            return 0
        return min(100, int((self.fulfilled_amount / self.amount) * 100))

    @property
    def remaining_amount(self):
        """Amount still to be fulfilled."""
        return max(Decimal('0.00'), self.amount - self.fulfilled_amount)


class PledgeFulfillment(BaseModel):
    """Links a donation to a pledge as partial or full fulfillment."""

    pledge = models.ForeignKey(
        Pledge,
        on_delete=models.CASCADE,
        related_name='fulfillments',
        verbose_name=_('Engagement')
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name='pledge_fulfillments',
        verbose_name=_('Don')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant appliqué')
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name=_('Date')
    )

    class Meta:
        verbose_name = _('Réalisation d\'engagement')
        verbose_name_plural = _('Réalisations d\'engagement')
        ordering = ['-date']

    def __str__(self):
        return f'{self.pledge} - {self.amount}$'


# ==============================================================================
# Giving Statements
# ==============================================================================


class GivingStatement(BaseModel):
    """Periodic giving statement for members."""

    PERIOD_CHOICES = [
        ('mid_year', _('Mi-année')),
        ('annual', _('Annuel')),
    ]

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='donation_giving_statements',
        verbose_name=_('Membre')
    )

    year = models.PositiveIntegerField(
        verbose_name=_('Année')
    )

    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        verbose_name=_('Période')
    )

    start_date = models.DateField(
        verbose_name=_('Date de début')
    )

    end_date = models.DateField(
        verbose_name=_('Date de fin')
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Montant total')
    )

    pdf_file = models.FileField(
        upload_to='statements/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Fichier PDF')
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de génération')
    )

    emailed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'envoi par courriel')
    )

    class Meta:
        verbose_name = _('Relevé de dons')
        verbose_name_plural = _('Relevés de dons')
        ordering = ['-year', '-generated_at']
        unique_together = ['member', 'year', 'period']
        indexes = [
            models.Index(fields=['member', 'year']),
            models.Index(fields=['year', 'period']),
        ]

    def __str__(self):
        return f'{self.member.full_name} - {self.year} ({self.get_period_display()})'


# ==============================================================================
# Giving Goals
# ==============================================================================


class GivingGoal(BaseModel):
    """Annual giving target for a member."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='donation_giving_goals',
        verbose_name=_('Membre')
    )

    year = models.PositiveIntegerField(
        verbose_name=_('Année')
    )

    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant cible')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Objectif de dons')
        verbose_name_plural = _('Objectifs de dons')
        unique_together = ['member', 'year']
        ordering = ['-year']

    def __str__(self):
        return f'{self.member.full_name} - {self.year}: {self.target_amount}$'

    @property
    def current_amount(self):
        """Total donations for this member in the target year."""
        total = Donation.objects.filter(
            member=self.member,
            date__year=self.year,
            is_active=True,
        ).aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')

    @property
    def progress_percentage(self):
        """Percentage progress toward the goal."""
        if not self.target_amount or self.target_amount == 0:
            return 0
        return min(100, int((self.current_amount / self.target_amount) * 100))

    @property
    def remaining_amount(self):
        """Amount remaining to reach the goal."""
        return max(Decimal('0.00'), self.target_amount - self.current_amount)


# ==============================================================================
# Donation Import
# ==============================================================================


class DonationImport(BaseModel):
    """Batch import of donations from CSV/OFX files."""

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En traitement')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
    ]

    file = models.FileField(
        upload_to='imports/%Y/%m/',
        verbose_name=_('Fichier')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )

    imported_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donation_imports',
        verbose_name=_('Importé par')
    )

    error_log = models.TextField(
        blank=True,
        verbose_name=_('Journal d\'erreurs')
    )

    total_rows = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total de lignes')
    )

    imported_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre importé')
    )

    skipped_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre ignoré')
    )

    class Meta:
        verbose_name = _('Import de dons')
        verbose_name_plural = _('Imports de dons')
        ordering = ['-created_at']

    def __str__(self):
        return f'Import {self.pk} - {self.get_status_display()}'


class DonationImportRow(BaseModel):
    """Individual row from a donation import file."""

    ROW_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('valid', _('Valide')),
        ('invalid', _('Invalide')),
        ('imported', _('Importé')),
        ('duplicate', _('Doublon')),
        ('skipped', _('Ignoré')),
    ]

    donation_import = models.ForeignKey(
        DonationImport,
        on_delete=models.CASCADE,
        related_name='rows',
        verbose_name=_('Import')
    )

    row_number = models.PositiveIntegerField(
        verbose_name=_('Numéro de ligne')
    )

    data_json = models.JSONField(
        default=dict,
        verbose_name=_('Données brutes')
    )

    status = models.CharField(
        max_length=20,
        choices=ROW_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )

    error_message = models.TextField(
        blank=True,
        verbose_name=_('Message d\'erreur')
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_rows',
        verbose_name=_('Don créé')
    )

    class Meta:
        verbose_name = _('Ligne d\'import')
        verbose_name_plural = _('Lignes d\'import')
        ordering = ['row_number']

    def __str__(self):
        return f'Ligne {self.row_number} - {self.get_status_display()}'


# ==============================================================================
# Gift Matching Campaigns
# ==============================================================================


class MatchingCampaign(BaseModel):
    """Matching gift campaign where a donor matches donations."""

    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.CASCADE,
        related_name='matching_campaigns',
        verbose_name=_('Campagne')
    )

    matcher_name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du donateur jumelé'),
        help_text=_('Nom de la personne ou organisation qui jumelle les dons')
    )

    match_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name=_('Ratio de jumelage'),
        help_text=_('Ex: 1.00 = dollar pour dollar, 0.50 = 50 cents par dollar')
    )

    match_cap = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Plafond de jumelage'),
        help_text=_('Montant maximal que le donateur jumelé contribuera')
    )

    matched_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total jumelé à ce jour')
    )

    class Meta:
        verbose_name = _('Campagne de jumelage')
        verbose_name_plural = _('Campagnes de jumelage')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.matcher_name} - {self.campaign.name}'

    @property
    def match_progress_percentage(self):
        """Percentage of match cap used."""
        if not self.match_cap or self.match_cap == 0:
            return 0
        return min(100, int((self.matched_total / self.match_cap) * 100))

    @property
    def remaining_match(self):
        """Remaining match amount available."""
        return max(Decimal('0.00'), self.match_cap - self.matched_total)


# ==============================================================================
# Cryptocurrency Donations
# ==============================================================================


class CryptoDonation(BaseModel):
    """Cryptocurrency donation record."""

    CRYPTO_CHOICES = [
        ('BTC', _('Bitcoin')),
        ('ETH', _('Ethereum')),
        ('LTC', _('Litecoin')),
        ('USDC', _('USD Coin')),
        ('OTHER', _('Autre')),
    ]

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('confirmed', _('Confirmé')),
        ('completed', _('Complété')),
        ('failed', _('Échoué')),
        ('expired', _('Expiré')),
    ]

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='crypto_donations',
        verbose_name=_('Membre')
    )

    crypto_type = models.CharField(
        max_length=10,
        choices=CRYPTO_CHOICES,
        verbose_name=_('Type de cryptomonnaie')
    )

    wallet_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Adresse du portefeuille')
    )

    amount_crypto = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        verbose_name=_('Montant en cryptomonnaie')
    )

    amount_cad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Équivalent en CAD'),
        help_text=_('Valeur en CAD au moment de la donation')
    )

    coinbase_charge_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('ID de charge Coinbase')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )

    donation = models.OneToOneField(
        Donation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crypto_detail',
        verbose_name=_('Don lié'),
        help_text=_('Don créé une fois la transaction confirmée')
    )

    class Meta:
        verbose_name = _('Don en cryptomonnaie')
        verbose_name_plural = _('Dons en cryptomonnaie')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.amount_crypto} {self.crypto_type} ({self.amount_cad} CAD)'
