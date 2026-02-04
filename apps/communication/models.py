"""Communication models - Newsletter and notifications."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.core.constants import NewsletterStatus, NotificationType


class Newsletter(BaseModel):
    """Email newsletter."""
    subject = models.CharField(max_length=200, verbose_name=_('Sujet'))
    content = models.TextField(verbose_name=_('Contenu HTML'))
    content_plain = models.TextField(blank=True, verbose_name=_('Contenu texte'))
    created_by = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, related_name='created_newsletters')
    status = models.CharField(max_length=20, choices=NewsletterStatus.CHOICES, default=NewsletterStatus.DRAFT, verbose_name=_('Statut'))
    scheduled_for = models.DateTimeField(null=True, blank=True, verbose_name=_('Planifiée pour'))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Envoyée le'))
    send_to_all = models.BooleanField(default=True, verbose_name=_('Envoyer à tous'))
    target_groups = models.ManyToManyField('members.Group', blank=True, related_name='newsletters', verbose_name=_('Groupes cibles'))
    recipients_count = models.PositiveIntegerField(default=0, verbose_name=_('Destinataires'))
    opened_count = models.PositiveIntegerField(default=0, verbose_name=_('Ouvertures'))

    class Meta:
        verbose_name = _('Infolettre')
        verbose_name_plural = _('Infolettres')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} ({self.get_status_display()})'


class NewsletterRecipient(BaseModel):
    """Newsletter recipient tracking."""
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE, related_name='recipients')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='received_newsletters')
    email = models.EmailField(verbose_name=_('Courriel'))
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    failed = models.BooleanField(default=False)
    failure_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Destinataire')
        verbose_name_plural = _('Destinataires')
        unique_together = ['newsletter', 'member']


class Notification(BaseModel):
    """Individual notification."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    message = models.TextField(verbose_name=_('Message'))
    notification_type = models.CharField(max_length=50, choices=NotificationType.CHOICES, default=NotificationType.GENERAL)
    link = models.URLField(blank=True, verbose_name=_('Lien'))
    is_read = models.BooleanField(default=False, verbose_name=_('Lu'))
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']


class NotificationPreference(BaseModel):
    """Member notification preferences."""
    member = models.OneToOneField('members.Member', on_delete=models.CASCADE, related_name='notification_preferences')
    email_newsletter = models.BooleanField(default=True)
    email_events = models.BooleanField(default=True)
    email_birthdays = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Préférence de notification')
        verbose_name_plural = _('Préférences de notification')
