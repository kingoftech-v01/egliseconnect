"""Login audit trail for security monitoring."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class LoginAudit(BaseModel):
    """Journal of all login attempts."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_audits',
        verbose_name=_('Utilisateur'),
        null=True,
        blank=True,
    )

    email_attempted = models.EmailField(
        blank=True,
        verbose_name=_('Email tenté')
    )

    ip_address = models.GenericIPAddressField(
        verbose_name=_('Adresse IP')
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )

    success = models.BooleanField(
        default=True,
        verbose_name=_('Réussi')
    )

    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Raison de l\'échec')
    )

    method = models.CharField(
        max_length=30,
        default='password',
        verbose_name=_('Méthode'),
        choices=[
            ('password', _('Mot de passe')),
            ('totp', _('TOTP 2FA')),
            ('social', _('Compte social')),
            ('code', _('Code par email')),
        ]
    )

    class Meta:
        verbose_name = _('Audit de connexion')
        verbose_name_plural = _('Audits de connexion')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        status = 'OK' if self.success else 'FAIL'
        return f'{self.email_attempted} [{status}] {self.ip_address}'
