"""Communication models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.core.constants import (
    NewsletterStatus, NotificationType, SMSStatus, AutomationTrigger,
    AutomationStepChannel, AutomationStatus, ABTestStatus,
    EmailTemplateCategory,
)


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
    """Tracks delivery and open status per recipient."""
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
    """In-app notification for a member."""
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
    """Per-member settings for notification channels."""
    member = models.OneToOneField('members.Member', on_delete=models.CASCADE, related_name='notification_preferences')
    email_newsletter = models.BooleanField(default=True)
    email_events = models.BooleanField(default=True)
    email_birthdays = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Préférence de notification')
        verbose_name_plural = _('Préférences de notification')


# ─── P1: SMS Messaging ──────────────────────────────────────────────────────────


class SMSTemplate(BaseModel):
    """Reusable SMS template with merge-field support."""
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    body_template = models.TextField(
        verbose_name=_('Corps du modèle'),
        help_text=_('Utilisez {{member_name}}, {{event_title}}, etc.'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))

    class Meta:
        verbose_name = _('Modèle SMS')
        verbose_name_plural = _('Modèles SMS')
        ordering = ['name']

    def __str__(self):
        return self.name


class SMSMessage(BaseModel):
    """Individual SMS message sent to a member."""
    recipient_member = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sms_messages', verbose_name=_('Membre destinataire'),
    )
    phone_number = models.CharField(max_length=20, verbose_name=_('Numéro de téléphone'))
    body = models.TextField(verbose_name=_('Message'))
    status = models.CharField(
        max_length=20, choices=SMSStatus.CHOICES, default=SMSStatus.PENDING,
        verbose_name=_('Statut'),
    )
    twilio_sid = models.CharField(max_length=50, blank=True, verbose_name=_('Twilio SID'))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Envoyé le'))
    template = models.ForeignKey(
        SMSTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='messages', verbose_name=_('Modèle'),
    )
    sent_by = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_sms', verbose_name=_('Envoyé par'),
    )

    class Meta:
        verbose_name = _('Message SMS')
        verbose_name_plural = _('Messages SMS')
        ordering = ['-created_at']

    def __str__(self):
        return f'SMS -> {self.phone_number} ({self.get_status_display()})'


class SMSOptOut(BaseModel):
    """Tracks SMS opt-out per member or phone number."""
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE, null=True, blank=True,
        related_name='sms_optouts', verbose_name=_('Membre'),
    )
    phone_number = models.CharField(max_length=20, verbose_name=_('Numéro de téléphone'))
    opted_out_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de désinscription'))

    class Meta:
        verbose_name = _('Désinscription SMS')
        verbose_name_plural = _('Désinscriptions SMS')
        unique_together = ['phone_number']

    def __str__(self):
        return f'Opt-out: {self.phone_number}'


# ─── P1: Push Notifications ─────────────────────────────────────────────────────


class PushSubscription(BaseModel):
    """Web push subscription for a member (VAPID / service worker)."""
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='push_subscriptions', verbose_name=_('Membre'),
    )
    endpoint = models.URLField(max_length=500, verbose_name=_('Endpoint'))
    p256dh_key = models.CharField(max_length=200, verbose_name=_('Clé P256DH'))
    auth_key = models.CharField(max_length=200, verbose_name=_('Clé Auth'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))

    class Meta:
        verbose_name = _('Abonnement push')
        verbose_name_plural = _('Abonnements push')
        unique_together = ['member', 'endpoint']

    def __str__(self):
        return f'Push: {self.member} ({self.endpoint[:40]}...)'


# ─── P1: Email Template Library ─────────────────────────────────────────────────


class EmailTemplate(BaseModel):
    """Reusable email template with merge-field support."""
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    subject_template = models.CharField(
        max_length=300, verbose_name=_('Sujet du modèle'),
        help_text=_('Utilisez {{member_name}}, {{event_title}}, etc.'),
    )
    body_html_template = models.TextField(
        verbose_name=_('Corps HTML'),
        help_text=_('Contenu HTML du modèle avec variables de fusion.'),
    )
    category = models.CharField(
        max_length=30, choices=EmailTemplateCategory.CHOICES,
        default=EmailTemplateCategory.GENERAL, verbose_name=_('Catégorie'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))

    class Meta:
        verbose_name = _('Modèle de courriel')
        verbose_name_plural = _('Modèles de courriel')
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'


# ─── P2: Automation & Drip Campaigns ────────────────────────────────────────────


class Automation(BaseModel):
    """Communication automation with a trigger and sequence of steps."""
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    trigger_type = models.CharField(
        max_length=30, choices=AutomationTrigger.CHOICES,
        default=AutomationTrigger.MEMBER_CREATED, verbose_name=_('Déclencheur'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_by = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_automations', verbose_name=_('Créé par'),
    )

    class Meta:
        verbose_name = _('Automatisation')
        verbose_name_plural = _('Automatisations')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_trigger_type_display()})'


class AutomationStep(BaseModel):
    """A single step in an automation sequence."""
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name='steps',
        verbose_name=_('Automatisation'),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    delay_days = models.PositiveIntegerField(
        default=0, verbose_name=_('Délai (jours)'),
        help_text=_('Nombre de jours à attendre avant d\'envoyer ce message.'),
    )
    subject = models.CharField(max_length=300, verbose_name=_('Sujet'))
    body = models.TextField(verbose_name=_('Corps du message'))
    channel = models.CharField(
        max_length=20, choices=AutomationStepChannel.CHOICES,
        default=AutomationStepChannel.EMAIL, verbose_name=_('Canal'),
    )

    class Meta:
        verbose_name = _('Étape d\'automatisation')
        verbose_name_plural = _('Étapes d\'automatisation')
        ordering = ['automation', 'order']
        unique_together = ['automation', 'order']

    def __str__(self):
        return f'{self.automation.name} - Étape {self.order}'


class AutomationEnrollment(BaseModel):
    """Tracks a member's progress through an automation sequence."""
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name='enrollments',
        verbose_name=_('Automatisation'),
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE, related_name='automation_enrollments',
        verbose_name=_('Membre'),
    )
    current_step = models.PositiveIntegerField(default=0, verbose_name=_('Étape actuelle'))
    status = models.CharField(
        max_length=20, choices=AutomationStatus.CHOICES,
        default=AutomationStatus.ACTIVE, verbose_name=_('Statut'),
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Débuté le'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Terminé le'))
    next_step_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Prochaine étape le'))

    class Meta:
        verbose_name = _('Inscription d\'automatisation')
        verbose_name_plural = _('Inscriptions d\'automatisation')
        unique_together = ['automation', 'member']

    def __str__(self):
        return f'{self.member} - {self.automation.name} (étape {self.current_step})'


# ─── P2: A/B Testing ────────────────────────────────────────────────────────────


class ABTest(BaseModel):
    """A/B test for newsletter subject lines or content."""
    newsletter = models.OneToOneField(
        Newsletter, on_delete=models.CASCADE, related_name='ab_test',
        verbose_name=_('Infolettre'),
    )
    variant_a_subject = models.CharField(max_length=300, verbose_name=_('Sujet variante A'))
    variant_b_subject = models.CharField(max_length=300, verbose_name=_('Sujet variante B'))
    variant_a_content = models.TextField(blank=True, verbose_name=_('Contenu variante A'))
    variant_b_content = models.TextField(blank=True, verbose_name=_('Contenu variante B'))
    test_size_pct = models.PositiveIntegerField(
        default=20, verbose_name=_('Taille du test (%)'),
        help_text=_('Pourcentage d\'audience pour chaque variante.'),
    )
    variant_a_opens = models.PositiveIntegerField(default=0, verbose_name=_('Ouvertures A'))
    variant_b_opens = models.PositiveIntegerField(default=0, verbose_name=_('Ouvertures B'))
    variant_a_clicks = models.PositiveIntegerField(default=0, verbose_name=_('Clics A'))
    variant_b_clicks = models.PositiveIntegerField(default=0, verbose_name=_('Clics B'))
    winner = models.CharField(
        max_length=1, blank=True, verbose_name=_('Gagnant'),
        help_text=_('A ou B'),
    )
    status = models.CharField(
        max_length=20, choices=ABTestStatus.CHOICES, default=ABTestStatus.DRAFT,
        verbose_name=_('Statut'),
    )

    class Meta:
        verbose_name = _('Test A/B')
        verbose_name_plural = _('Tests A/B')

    def __str__(self):
        return f'A/B: {self.newsletter.subject}'


# ─── P3: In-App Messaging ───────────────────────────────────────────────────────


class DirectMessage(BaseModel):
    """Direct member-to-member message."""
    sender = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE, related_name='sent_messages',
        verbose_name=_('Expéditeur'),
    )
    recipient = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE, related_name='received_messages',
        verbose_name=_('Destinataire'),
    )
    body = models.TextField(verbose_name=_('Message'))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Lu le'))

    class Meta:
        verbose_name = _('Message direct')
        verbose_name_plural = _('Messages directs')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} -> {self.recipient}'

    @property
    def is_read(self):
        return self.read_at is not None


class GroupChat(BaseModel):
    """Group chat room for ministry/team communication."""
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    members = models.ManyToManyField(
        'members.Member', related_name='group_chats', blank=True,
        verbose_name=_('Membres'),
    )
    created_by = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True,
        related_name='created_group_chats', verbose_name=_('Créé par'),
    )

    class Meta:
        verbose_name = _('Discussion de groupe')
        verbose_name_plural = _('Discussions de groupe')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class GroupChatMessage(BaseModel):
    """A message in a group chat."""
    chat = models.ForeignKey(
        GroupChat, on_delete=models.CASCADE, related_name='messages',
        verbose_name=_('Discussion'),
    )
    sender = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE, related_name='group_chat_messages',
        verbose_name=_('Expéditeur'),
    )
    body = models.TextField(verbose_name=_('Message'))
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Envoyé le'))

    class Meta:
        verbose_name = _('Message de groupe')
        verbose_name_plural = _('Messages de groupe')
        ordering = ['sent_at']

    def __str__(self):
        return f'{self.sender} @ {self.chat.name}'
