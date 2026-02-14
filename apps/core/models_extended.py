"""Extended models for core app: branding, webhooks, audit logging, campus."""
import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .models import BaseModel


class ChurchBranding(BaseModel):
    """Church-configurable branding settings (logo, colors, name)."""

    church_name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de l\'église'),
        help_text=_('Nom affiché dans l\'en-tête et les documents'),
    )

    logo = models.ImageField(
        upload_to='branding/logos/',
        blank=True,
        null=True,
        verbose_name=_('Logo'),
        help_text=_('Logo de l\'église (format recommandé: PNG, 200x200px)'),
    )

    favicon = models.ImageField(
        upload_to='branding/favicons/',
        blank=True,
        null=True,
        verbose_name=_('Favicon'),
    )

    primary_color = models.CharField(
        max_length=7,
        default='#1a73e8',
        verbose_name=_('Couleur primaire'),
        help_text=_('Code hexadécimal (ex: #1a73e8)'),
    )

    secondary_color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name=_('Couleur secondaire'),
        help_text=_('Code hexadécimal (ex: #6c757d)'),
    )

    accent_color = models.CharField(
        max_length=7,
        default='#28a745',
        verbose_name=_('Couleur d\'accent'),
        help_text=_('Code hexadécimal (ex: #28a745)'),
    )

    address = models.TextField(
        blank=True,
        verbose_name=_('Adresse'),
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone'),
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_('Courriel'),
    )

    website = models.URLField(
        blank=True,
        verbose_name=_('Site web'),
    )

    class Meta:
        verbose_name = _('Image de marque')
        verbose_name_plural = _('Image de marque')
        ordering = ['-created_at']

    def __str__(self):
        return self.church_name

    @classmethod
    def get_current(cls):
        """Get the active branding config, or None."""
        return cls.objects.first()


class WebhookEndpoint(BaseModel):
    """Configurable outgoing webhook endpoint for external integrations."""

    WEBHOOK_EVENTS = [
        ('member.created', _('Membre créé')),
        ('member.updated', _('Membre mis à jour')),
        ('donation.received', _('Don reçu')),
        ('event.created', _('Événement créé')),
        ('attendance.checked_in', _('Présence enregistrée')),
        ('help_request.created', _('Demande d\'aide créée')),
        ('help_request.resolved', _('Demande d\'aide résolue')),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom'),
        help_text=_('Nom descriptif pour identifier ce webhook'),
    )

    url = models.URLField(
        verbose_name=_('URL de destination'),
        validators=[URLValidator(schemes=['https', 'http'])],
    )

    secret = models.CharField(
        max_length=255,
        verbose_name=_('Clé secrète'),
        help_text=_('Utilisée pour signer les requêtes (HMAC-SHA256)'),
    )

    events = models.JSONField(
        default=list,
        verbose_name=_('Événements'),
        help_text=_('Liste des événements déclencheurs'),
    )

    headers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('En-têtes personnalisés'),
    )

    max_retries = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Tentatives max'),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Créé par'),
    )

    class Meta:
        verbose_name = _('Point de terminaison webhook')
        verbose_name_plural = _('Points de terminaison webhook')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.url})'

    def sign_payload(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for payload."""
        return hmac.new(
            self.secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()


class WebhookDelivery(BaseModel):
    """Log of webhook delivery attempts with retry tracking."""

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('success', _('Succès')),
        ('failed', _('Échoué')),
        ('retrying', _('Nouvelle tentative')),
    ]

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name=_('Point de terminaison'),
    )

    event = models.CharField(
        max_length=100,
        verbose_name=_('Événement'),
    )

    payload = models.JSONField(
        default=dict,
        verbose_name=_('Contenu'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut'),
    )

    response_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Code de réponse'),
    )

    response_body = models.TextField(
        blank=True,
        verbose_name=_('Corps de la réponse'),
    )

    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Tentatives'),
    )

    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Dernière tentative'),
    )

    error_message = models.TextField(
        blank=True,
        verbose_name=_('Message d\'erreur'),
    )

    class Meta:
        verbose_name = _('Livraison webhook')
        verbose_name_plural = _('Livraisons webhook')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['endpoint', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.event} -> {self.endpoint.name} [{self.status}]'


class AuditLog(BaseModel):
    """Comprehensive audit trail for admin-visible activity logging."""

    ACTION_CHOICES = [
        ('create', _('Création')),
        ('update', _('Modification')),
        ('delete', _('Suppression')),
        ('restore', _('Restauration')),
        ('login', _('Connexion')),
        ('logout', _('Déconnexion')),
        ('export', _('Exportation')),
        ('import', _('Importation')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Utilisateur'),
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('Action'),
    )

    model_name = models.CharField(
        max_length=100,
        verbose_name=_('Modèle'),
        help_text=_('Nom du modèle affecté (ex: Member, Donation)'),
    )

    object_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('ID de l\'objet'),
    )

    object_repr = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Représentation'),
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Changements'),
        help_text=_('Détails des modifications (ancien/nouveau)'),
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Adresse IP'),
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent'),
    )

    class Meta:
        verbose_name = _('Journal d\'audit')
        verbose_name_plural = _('Journaux d\'audit')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['model_name', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f'{user_str} - {self.get_action_display()} - {self.model_name}'


class Campus(BaseModel):
    """Multi-campus support for churches with multiple locations."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du campus'),
    )

    address = models.TextField(
        blank=True,
        verbose_name=_('Adresse'),
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ville'),
    )

    province = models.CharField(
        max_length=2,
        blank=True,
        verbose_name=_('Province'),
    )

    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Code postal'),
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone'),
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_('Courriel'),
    )

    pastor = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campus_pastor',
        verbose_name=_('Pasteur responsable'),
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name=_('Campus principal'),
    )

    class Meta:
        verbose_name = _('Campus')
        verbose_name_plural = _('Campus')
        ordering = ['-is_main', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one main campus
        if self.is_main:
            Campus.objects.filter(is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)
