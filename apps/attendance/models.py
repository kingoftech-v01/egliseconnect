"""Attendance models: QR codes, check-in sessions, absence alerts."""
import hmac
import hashlib
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import AttendanceSessionType, CheckInMethod


def generate_secure_qr_code():
    """Generate a unique, non-guessable QR code string."""
    unique = str(uuid.uuid4())
    secret = settings.SECRET_KEY
    signature = hmac.new(
        secret.encode(),
        unique.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    return f'EC-{unique[:8]}-{signature}'


def generate_qr_image(code):
    """Generate a QR code image from a code string."""
    import qrcode

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=f'qr_{code[:8]}.png')


class MemberQRCode(BaseModel):
    """Unique rotating QR code for each member."""

    member = models.OneToOneField(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='qr_code',
        verbose_name=_('Membre')
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_('Code')
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Généré le')
    )

    expires_at = models.DateTimeField(
        verbose_name=_('Expire le')
    )

    qr_image = models.ImageField(
        upload_to='qrcodes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Image QR')
    )

    class Meta:
        verbose_name = _('Code QR membre')
        verbose_name_plural = _('Codes QR membres')

    def __str__(self):
        return f'QR {self.member.full_name}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_secure_qr_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        if not self.qr_image:
            self.qr_image = generate_qr_image(self.code)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return timezone.now() < self.expires_at

    def regenerate(self):
        """Generate a new code and QR image."""
        self.code = generate_secure_qr_code()
        self.generated_at = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=7)
        self.qr_image = generate_qr_image(self.code)
        self.save()


class AttendanceSession(BaseModel):
    """A check-in session for a service, event, or lesson."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de la session'),
        help_text=_('Ex: Culte du 15 mars 2025')
    )

    session_type = models.CharField(
        max_length=30,
        choices=AttendanceSessionType.CHOICES,
        default=AttendanceSessionType.WORSHIP,
        verbose_name=_('Type de session')
    )

    event = models.ForeignKey(
        'events.Event',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='attendance_sessions',
        verbose_name=_('Événement lié')
    )

    scheduled_lesson = models.ForeignKey(
        'onboarding.ScheduledLesson',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='attendance_session',
        verbose_name=_('Leçon liée')
    )

    date = models.DateField(
        verbose_name=_('Date')
    )

    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Heure de début')
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Heure de fin')
    )

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Durée (minutes)'),
        help_text=_('Durée prévue de la session en minutes')
    )

    opened_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='opened_sessions',
        verbose_name=_('Ouvert par')
    )

    is_open = models.BooleanField(
        default=True,
        verbose_name=_('Session ouverte'),
        help_text=_('Le check-in est accepté')
    )

    class Meta:
        verbose_name = _('Session de présence')
        verbose_name_plural = _('Sessions de présence')
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'{self.name} ({self.date})'

    @property
    def attendee_count(self):
        return self.records.count()


class AttendanceRecord(BaseModel):
    """Individual check-in record for a member at a session."""

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name=_('Session')
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_('Membre')
    )

    checked_in_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Enregistré à')
    )

    checked_in_by = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='scanned_records',
        verbose_name=_('Scanné par')
    )

    method = models.CharField(
        max_length=20,
        choices=CheckInMethod.CHOICES,
        default=CheckInMethod.QR_SCAN,
        verbose_name=_('Méthode')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Enregistrement de présence')
        verbose_name_plural = _('Enregistrements de présence')
        unique_together = ['session', 'member']
        ordering = ['-checked_in_at']

    def __str__(self):
        return f'{self.member.full_name} @ {self.session.name}'


class AbsenceAlert(BaseModel):
    """Alert generated when a member misses multiple sessions."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='absence_alerts',
        verbose_name=_('Membre')
    )

    consecutive_absences = models.PositiveIntegerField(
        verbose_name=_('Absences consécutives')
    )

    last_attendance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Dernière présence')
    )

    alert_sent = models.BooleanField(
        default=False,
        verbose_name=_('Alerte envoyée')
    )

    alert_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Alerte envoyée le')
    )

    acknowledged_by = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='acknowledged_alerts',
        verbose_name=_('Reconnu par')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _("Alerte d'absence")
        verbose_name_plural = _("Alertes d'absence")
        ordering = ['-consecutive_absences']

    def __str__(self):
        return f'{self.member.full_name} - {self.consecutive_absences} absences'
