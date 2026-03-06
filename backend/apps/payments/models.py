"""Payment models for Stripe integration, giving statements, goals, SMS donations, kiosk, etc."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.core.constants import DonationType, PaymentPlanStatus, PledgeFrequency


class PaymentStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    CANCELLED = 'cancelled'

    CHOICES = [
        (PENDING, _('En attente')),
        (PROCESSING, _('En cours')),
        (SUCCEEDED, _('Réussi')),
        (FAILED, _('Échoué')),
        (REFUNDED, _('Remboursé')),
        (CANCELLED, _('Annulé')),
    ]


class RecurringFrequency:
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

    CHOICES = [
        (WEEKLY, _('Hebdomadaire')),
        (MONTHLY, _('Mensuel')),
    ]


class StatementType:
    QUARTERLY = 'quarterly'
    ANNUAL = 'annual'

    CHOICES = [
        (QUARTERLY, _('Trimestriel')),
        (ANNUAL, _('Annuel')),
    ]


class CurrencyChoices:
    CAD = 'CAD'
    USD = 'USD'
    EUR = 'EUR'

    CHOICES = [
        (CAD, 'CAD - Dollar canadien'),
        (USD, 'USD - Dollar américain'),
        (EUR, 'EUR - Euro'),
    ]


# ─── Existing models ────────────────────────────────────────────────────────────


class StripeCustomer(BaseModel):
    """Links a member to their Stripe customer account."""
    member = models.OneToOneField(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='stripe_customer',
        verbose_name=_('Membre')
    )
    stripe_customer_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Stripe Customer ID')
    )

    class Meta:
        verbose_name = _('Client Stripe')
        verbose_name_plural = _('Clients Stripe')

    def __str__(self):
        return f'{self.member.full_name} ({self.stripe_customer_id})'


class OnlinePayment(BaseModel):
    """Individual online payment via Stripe."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='online_payments',
        verbose_name=_('Membre')
    )
    donation = models.OneToOneField(
        'donations.Donation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='online_payment',
        verbose_name=_('Don lié')
    )
    stripe_payment_intent_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Stripe Payment Intent ID')
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant')
    )
    currency = models.CharField(
        max_length=3,
        default='CAD',
        verbose_name=_('Devise')
    )
    status = models.CharField(
        max_length=30,
        choices=PaymentStatus.CHOICES,
        default=PaymentStatus.PENDING,
        verbose_name=_('Statut')
    )
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.OFFERING,
        verbose_name=_('Type de don')
    )
    campaign = models.ForeignKey(
        'donations.DonationCampaign',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='online_payments',
        verbose_name=_('Campagne')
    )
    receipt_email = models.EmailField(
        blank=True,
        verbose_name=_('Email du reçu')
    )
    stripe_receipt_url = models.URLField(
        blank=True,
        verbose_name=_('URL du reçu Stripe')
    )
    payment_method_type = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name=_('Méthode de paiement'),
        help_text=_('card, apple_pay, google_pay, ach_debit, etc.')
    )

    class Meta:
        verbose_name = _('Paiement en ligne')
        verbose_name_plural = _('Paiements en ligne')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.amount} {self.currency} ({self.get_status_display()})'

    @property
    def amount_display(self):
        return f'{self.amount:.2f} {self.currency}'

    @property
    def is_successful(self):
        return self.status == PaymentStatus.SUCCEEDED


class RecurringDonation(BaseModel):
    """Recurring donation via Stripe Subscription."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='recurring_donations',
        verbose_name=_('Membre')
    )
    stripe_subscription_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Stripe Subscription ID')
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant')
    )
    currency = models.CharField(
        max_length=3,
        default='CAD',
        verbose_name=_('Devise')
    )
    frequency = models.CharField(
        max_length=20,
        choices=RecurringFrequency.CHOICES,
        default=RecurringFrequency.MONTHLY,
        verbose_name=_('Fréquence')
    )
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.TITHE,
        verbose_name=_('Type de don')
    )
    next_payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Prochain paiement')
    )
    is_active_subscription = models.BooleanField(
        default=True,
        verbose_name=_('Abonnement actif')
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Annulé le')
    )

    class Meta:
        verbose_name = _('Don récurrent')
        verbose_name_plural = _('Dons récurrents')
        ordering = ['-created_at']

    def __str__(self):
        freq = self.get_frequency_display()
        return f'{self.member.full_name} - {self.amount} {self.currency}/{freq}'

    @property
    def amount_display(self):
        return f'{self.amount:.2f} {self.currency}'


# ─── P1: Giving Statements ──────────────────────────────────────────────────────


class GivingStatement(BaseModel):
    """Tax giving statement for a member covering a time period."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='giving_statements',
        verbose_name=_('Membre')
    )
    period_start = models.DateField(
        verbose_name=_('Début de la période')
    )
    period_end = models.DateField(
        verbose_name=_('Fin de la période')
    )
    statement_type = models.CharField(
        max_length=20,
        choices=StatementType.CHOICES,
        default=StatementType.ANNUAL,
        verbose_name=_('Type de relevé')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Montant total')
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Généré le')
    )
    pdf_file = models.FileField(
        upload_to='statements/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Fichier PDF')
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Envoyé le')
    )

    class Meta:
        verbose_name = _('Relevé de dons')
        verbose_name_plural = _('Relevés de dons')
        ordering = ['-period_end', '-generated_at']
        unique_together = ['member', 'period_start', 'period_end', 'statement_type']

    def __str__(self):
        return f'{self.member.full_name} - {self.get_statement_type_display()} ({self.period_start} à {self.period_end})'

    @property
    def is_sent(self):
        return self.sent_at is not None


# ─── P1: Giving Goals ───────────────────────────────────────────────────────────


class GivingGoal(BaseModel):
    """Annual giving goal for a member."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='giving_goals',
        verbose_name=_('Membre')
    )
    year = models.IntegerField(
        verbose_name=_('Année')
    )
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant cible')
    )

    class Meta:
        verbose_name = _('Objectif de don')
        verbose_name_plural = _('Objectifs de don')
        unique_together = ['member', 'year']
        ordering = ['-year']

    def __str__(self):
        return f'{self.member.full_name} - {self.year}: {self.target_amount}'


# ─── P2: SMS Donations ──────────────────────────────────────────────────────────


class SMSDonation(BaseModel):
    """Donation initiated via SMS text-to-give."""
    phone_number = models.CharField(
        max_length=20,
        verbose_name=_('Numéro de téléphone')
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant')
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_donations',
        verbose_name=_('Membre')
    )
    processed = models.BooleanField(
        default=False,
        verbose_name=_('Traité')
    )
    stripe_charge_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name=_('Stripe Charge ID')
    )
    command_text = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('Commande SMS'),
        help_text=_('Texte original du SMS reçu')
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name=_('Récurrent')
    )
    frequency = models.CharField(
        max_length=20,
        choices=RecurringFrequency.CHOICES,
        blank=True,
        default='',
        verbose_name=_('Fréquence')
    )

    class Meta:
        verbose_name = _('Don par SMS')
        verbose_name_plural = _('Dons par SMS')
        ordering = ['-created_at']

    def __str__(self):
        member_name = self.member.full_name if self.member else self.phone_number
        return f'{member_name} - {self.amount} CAD (SMS)'


# ─── P2: Kiosk Session Tracking ─────────────────────────────────────────────────


class KioskSession(BaseModel):
    """Tracks a giving kiosk session for daily reconciliation."""
    session_date = models.DateField(
        verbose_name=_('Date de session')
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('Emplacement')
    )
    total_transactions = models.IntegerField(
        default=0,
        verbose_name=_('Nombre de transactions')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Montant total')
    )
    reconciled = models.BooleanField(
        default=False,
        verbose_name=_('Réconcilié')
    )
    reconciled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Réconcilié le')
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Session kiosque')
        verbose_name_plural = _('Sessions kiosque')
        ordering = ['-session_date']

    def __str__(self):
        return f'Kiosque {self.session_date} - {self.total_amount} CAD'


# ─── P3: Payment Plans ──────────────────────────────────────────────────────────


class PaymentPlan(BaseModel):
    """Payment plan to split a large gift into installments."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='payment_plans',
        verbose_name=_('Membre')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant total')
    )
    installment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant par versement')
    )
    frequency = models.CharField(
        max_length=20,
        choices=PledgeFrequency.CHOICES,
        default=PledgeFrequency.MONTHLY,
        verbose_name=_('Fréquence')
    )
    remaining_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant restant')
    )
    start_date = models.DateField(
        verbose_name=_('Date de début')
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentPlanStatus.CHOICES,
        default=PaymentPlanStatus.ACTIVE,
        verbose_name=_('Statut')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complété le')
    )
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.OFFERING,
        verbose_name=_('Type de don')
    )

    class Meta:
        verbose_name = _('Plan de paiement')
        verbose_name_plural = _('Plans de paiement')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.total_amount} CAD ({self.get_status_display()})'

    @property
    def progress_percentage(self):
        if self.total_amount == 0:
            return 100
        paid = self.total_amount - self.remaining_amount
        return min(100, int((paid / self.total_amount) * 100))

    @property
    def amount_paid(self):
        return self.total_amount - self.remaining_amount


# ─── P3: Employer Matching ───────────────────────────────────────────────────────


class EmployerMatch(BaseModel):
    """Tracks employer matching program for a member."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='employer_matches',
        verbose_name=_('Membre')
    )
    employer_name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de l\'employeur')
    )
    match_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name=_('Ratio de jumelage'),
        help_text=_('ex: 1.00 = dollar pour dollar, 0.50 = 50 cents par dollar')
    )
    annual_cap = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Plafond annuel'),
        help_text=_('0 = pas de plafond')
    )
    match_amount_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Montant de jumelage reçu')
    )

    class Meta:
        verbose_name = _('Jumelage employeur')
        verbose_name_plural = _('Jumelages employeur')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.employer_name} ({self.match_ratio}x)'


# ─── P3: Year-End Campaigns ─────────────────────────────────────────────────────


class GivingCampaign(BaseModel):
    """Year-end or special giving campaign with goal tracking and countdown."""
    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de la campagne')
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Description')
    )
    goal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Objectif')
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Montant actuel')
    )
    start_date = models.DateField(
        verbose_name=_('Date de début')
    )
    end_date = models.DateField(
        verbose_name=_('Date de fin')
    )
    is_year_end = models.BooleanField(
        default=False,
        verbose_name=_('Campagne de fin d\'année')
    )
    image = models.ImageField(
        upload_to='giving_campaigns/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Image')
    )

    class Meta:
        verbose_name = _('Campagne de dons')
        verbose_name_plural = _('Campagnes de dons')
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def progress_percentage(self):
        if not self.goal_amount or self.goal_amount == 0:
            return 0
        return min(100, int((self.current_amount / self.goal_amount) * 100))

    @property
    def is_ongoing(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    @property
    def days_remaining(self):
        from django.utils import timezone
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days
