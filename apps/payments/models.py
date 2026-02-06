"""Payment models for Stripe integration."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.core.constants import DonationType


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
