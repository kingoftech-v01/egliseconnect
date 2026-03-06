"""Attendance models: QR codes, check-in sessions, absence alerts,
child check-in, kiosk, NFC, geo-fence, visitor tracking, streaks."""
import hmac
import hashlib
import random
import string
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import (
    AttendanceSessionType, CheckInMethod, VisitorSource,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

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


def generate_security_code():
    """Generate a random 6-digit numeric security code for child check-in."""
    return ''.join(random.choices(string.digits, k=6))


# ═══════════════════════════════════════════════════════════════════════════════
# Original Models
# ═══════════════════════════════════════════════════════════════════════════════

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

    # P2 item 37: Check-out time tracking
    checked_out_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sorti à'),
        help_text=_('Heure de sortie (check-out)')
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

    @property
    def duration_minutes(self):
        """Calculate duration in minutes if both check-in and check-out exist."""
        if self.checked_in_at and self.checked_out_at:
            delta = self.checked_out_at - self.checked_in_at
            return int(delta.total_seconds() / 60)
        return None

    @property
    def is_early_departure(self):
        """Check if the member left before the session ended."""
        if not self.checked_out_at or not self.session.end_time:
            return False
        from datetime import datetime
        session_end = datetime.combine(self.session.date, self.session.end_time)
        session_end = timezone.make_aware(session_end) if timezone.is_naive(session_end) else session_end
        return self.checked_out_at < session_end


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

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Reconnu le')
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


# ═══════════════════════════════════════════════════════════════════════════════
# P1: Child Check-In / Check-Out (items 1-6)
# ═══════════════════════════════════════════════════════════════════════════════

class ChildCheckIn(BaseModel):
    """Tracks child check-in/check-out with security codes and medical info."""

    child = models.ForeignKey(
        'members.Child',
        on_delete=models.CASCADE,
        related_name='checkins',
        verbose_name=_('Enfant')
    )

    parent_member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='child_checkins',
        verbose_name=_('Parent / tuteur')
    )

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='child_checkins',
        verbose_name=_('Session')
    )

    check_in_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Heure d'arrivée")
    )

    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Heure de sortie')
    )

    security_code = models.CharField(
        max_length=6,
        unique=True,
        db_index=True,
        verbose_name=_('Code de sécurité'),
        help_text=_('Code à 6 chiffres pour le retrait sécurisé')
    )

    checked_out_by = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_checkouts',
        verbose_name=_('Retiré par')
    )

    class Meta:
        verbose_name = _("Enregistrement enfant")
        verbose_name_plural = _("Enregistrements enfants")
        ordering = ['-check_in_time']

    def __str__(self):
        return f'{self.child.full_name} @ {self.session.name}'

    def save(self, *args, **kwargs):
        if not self.security_code:
            self.security_code = generate_security_code()
            # Ensure uniqueness
            while ChildCheckIn.all_objects.filter(
                security_code=self.security_code
            ).exists():
                self.security_code = generate_security_code()
        super().save(*args, **kwargs)

    @property
    def is_checked_out(self):
        return self.check_out_time is not None


# ═══════════════════════════════════════════════════════════════════════════════
# P1: Kiosk Self-Check-In (items 7-13)
# ═══════════════════════════════════════════════════════════════════════════════

class KioskConfig(BaseModel):
    """Configuration for a self-check-in kiosk device."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du kiosque'),
        help_text=_("Ex: Kiosque entrée principale")
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Emplacement')
    )

    admin_pin = models.CharField(
        max_length=10,
        verbose_name=_("PIN d'administration"),
        help_text=_('Code PIN pour accéder à la configuration')
    )

    auto_timeout_seconds = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Délai d'inactivité (secondes)"),
        help_text=_("Retour à l'écran d'accueil après inactivité")
    )

    session = models.ForeignKey(
        AttendanceSession,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='kiosks',
        verbose_name=_('Session courante')
    )

    class Meta:
        verbose_name = _('Configuration kiosque')
        verbose_name_plural = _('Configurations kiosques')

    def __str__(self):
        return f'{self.name} ({self.location})'


# ═══════════════════════════════════════════════════════════════════════════════
# P2: NFC / Tap Check-In (items 28-32)
# ═══════════════════════════════════════════════════════════════════════════════

class NFCTag(BaseModel):
    """NFC tag assigned to a member for tap check-in."""

    member = models.OneToOneField(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='nfc_tag',
        verbose_name=_('Membre')
    )

    tag_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_('Identifiant NFC'),
        help_text=_('Identifiant unique du tag NFC')
    )

    registered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Enregistré le')
    )

    class Meta:
        verbose_name = _('Tag NFC')
        verbose_name_plural = _('Tags NFC')

    def __str__(self):
        return f'NFC {self.member.full_name} ({self.tag_id[:8]}...)'


# ═══════════════════════════════════════════════════════════════════════════════
# P2: Attendance-Based Engagement Scoring (items 33-36)
# ═══════════════════════════════════════════════════════════════════════════════

class AttendanceStreak(BaseModel):
    """Tracks consecutive attendance streaks for members."""

    member = models.OneToOneField(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='attendance_streak',
        verbose_name=_('Membre')
    )

    current_streak = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Série actuelle'),
        help_text=_('Semaines consécutives avec présence')
    )

    longest_streak = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Plus longue série')
    )

    last_attendance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Dernière présence')
    )

    class Meta:
        verbose_name = _('Série de présence')
        verbose_name_plural = _('Séries de présence')

    def __str__(self):
        return f'{self.member.full_name} - {self.current_streak} sem.'

    def update_streak(self, attendance_date):
        """Update streak based on new attendance."""
        from datetime import timedelta
        if self.last_attendance_date is None:
            self.current_streak = 1
        else:
            days_diff = (attendance_date - self.last_attendance_date).days
            if days_diff <= 7:
                # Within a week, continue streak
                if days_diff >= 1:
                    self.current_streak += 1
            else:
                # Streak broken
                self.current_streak = 1
        self.last_attendance_date = attendance_date
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()


# ═══════════════════════════════════════════════════════════════════════════════
# P3: Geo-Fenced Check-In (items 43-46)
# ═══════════════════════════════════════════════════════════════════════════════

class GeoFence(BaseModel):
    """Geographic fence for location-based automatic check-in."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom'),
        help_text=_("Ex: Église principale")
    )

    latitude = models.FloatField(
        verbose_name=_('Latitude'),
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]
    )

    longitude = models.FloatField(
        verbose_name=_('Longitude'),
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )

    radius_meters = models.PositiveIntegerField(
        default=100,
        verbose_name=_('Rayon (mètres)'),
        help_text=_('Rayon de la zone de check-in automatique')
    )

    class Meta:
        verbose_name = _('Zone géographique')
        verbose_name_plural = _('Zones géographiques')

    def __str__(self):
        return f'{self.name} ({self.latitude:.4f}, {self.longitude:.4f})'

    def is_within_fence(self, lat, lng):
        """Check if given coordinates are within this geo-fence."""
        import math
        # Haversine formula
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(self.latitude)
        phi2 = math.radians(lat)
        delta_phi = math.radians(lat - self.latitude)
        delta_lambda = math.radians(lng - self.longitude)

        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance <= self.radius_meters


# ═══════════════════════════════════════════════════════════════════════════════
# P3: Visitor Follow-Up (items 50-54)
# ═══════════════════════════════════════════════════════════════════════════════

class VisitorInfo(BaseModel):
    """Information about a first-time visitor for follow-up."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom complet')
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_('Courriel')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone')
    )

    source = models.CharField(
        max_length=20,
        choices=VisitorSource.CHOICES,
        default=VisitorSource.WALK_IN,
        verbose_name=_('Source')
    )

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitors',
        verbose_name=_('Session')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    follow_up_assigned_to = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='attendance_visitor_followups',
        verbose_name=_('Suivi assigné à')
    )

    follow_up_completed = models.BooleanField(
        default=False,
        verbose_name=_('Suivi complété')
    )

    follow_up_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Suivi complété le')
    )

    welcome_sent = models.BooleanField(
        default=False,
        verbose_name=_('Bienvenue envoyée')
    )

    class Meta:
        verbose_name = _('Visiteur')
        verbose_name_plural = _('Visiteurs')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_source_display()})'
