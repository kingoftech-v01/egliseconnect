"""Event, RSVP, room booking, registration, template, waitlist, volunteer needs,
photo gallery, survey, and recurrence models."""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import (
    EventType, RSVPStatus, RecurrenceFrequency, BookingStatus,
    VolunteerSignupStatus, VirtualPlatform,
)
from apps.core.validators import validate_image_file


# ──────────────────────────────────────────────────────────────────────────────
# Event
# ──────────────────────────────────────────────────────────────────────────────

class Event(BaseModel):
    """Church event with RSVP, recurrence, and virtual support."""

    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    event_type = models.CharField(
        max_length=20, choices=EventType.CHOICES,
        default=EventType.WORSHIP, verbose_name=_('Type'),
    )
    start_datetime = models.DateTimeField(verbose_name=_('Début'))
    end_datetime = models.DateTimeField(verbose_name=_('Fin'))
    all_day = models.BooleanField(default=False, verbose_name=_('Toute la journée'))
    location = models.CharField(max_length=255, blank=True, verbose_name=_('Lieu'))
    location_address = models.TextField(blank=True, verbose_name=_('Adresse'))
    is_online = models.BooleanField(default=False, verbose_name=_('En ligne'))
    online_link = models.URLField(blank=True, verbose_name=_('Lien'))
    organizer = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='organized_events', verbose_name=_('Organisateur'),
    )
    max_attendees = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('Capacité max'),
    )
    requires_rsvp = models.BooleanField(default=False, verbose_name=_('RSVP requis'))
    image = models.ImageField(
        upload_to='events/%Y/%m/', blank=True, null=True,
        verbose_name=_('Image'), validators=[validate_image_file],
    )
    is_published = models.BooleanField(default=True, verbose_name=_('Publié'))
    is_cancelled = models.BooleanField(default=False, verbose_name=_('Annulé'))

    # Recurrence fields (P2)
    is_recurring = models.BooleanField(default=False, verbose_name=_('Récurrent'))
    recurrence_frequency = models.CharField(
        max_length=20, choices=RecurrenceFrequency.CHOICES,
        blank=True, default='', verbose_name=_('Fréquence de récurrence'),
    )
    recurrence_rule = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name=_('Règle de récurrence'),
        help_text=_('Format RRULE iCal (optionnel, surcharge fréquence)'),
    )
    recurrence_end_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Date de fin de récurrence'),
    )
    parent_event = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='occurrences',
    )

    # Virtual event fields (P3)
    virtual_url = models.URLField(
        blank=True, default='', verbose_name=_('URL de la réunion virtuelle'),
    )
    virtual_platform = models.CharField(
        max_length=20, choices=VirtualPlatform.CHOICES,
        blank=True, default='', verbose_name=_('Plateforme virtuelle'),
    )
    is_hybrid = models.BooleanField(
        default=False, verbose_name=_('Événement hybride'),
        help_text=_('En personne et en ligne'),
    )

    # Multi-campus (P3)
    campus = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name=_('Campus'),
    )

    # Kiosk (P1)
    kiosk_mode_enabled = models.BooleanField(
        default=False, verbose_name=_('Mode kiosque activé'),
    )

    class Meta:
        verbose_name = _('Événement')
        verbose_name_plural = _('Événements')
        ordering = ['start_datetime']

    def __str__(self):
        return f'{self.title} ({self.start_datetime.date()})'

    @property
    def confirmed_count(self):
        return self.rsvps.filter(status=RSVPStatus.CONFIRMED).count()

    @property
    def is_full(self):
        if not self.max_attendees:
            return False
        return self.confirmed_count >= self.max_attendees

    @property
    def available_spots(self):
        if not self.max_attendees:
            return None
        return max(0, self.max_attendees - self.confirmed_count)

    @property
    def waitlist_count(self):
        return self.waitlist_entries.count()


# ──────────────────────────────────────────────────────────────────────────────
# RSVP
# ──────────────────────────────────────────────────────────────────────────────

class EventRSVP(BaseModel):
    """RSVP for an event."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='rsvps',
        verbose_name=_('Événement'),
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='event_rsvps', verbose_name=_('Membre'),
    )
    status = models.CharField(
        max_length=20, choices=RSVPStatus.CHOICES,
        default=RSVPStatus.PENDING, verbose_name=_('Statut'),
    )
    guests = models.PositiveIntegerField(default=0, verbose_name=_('Invités'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('RSVP')
        verbose_name_plural = _('RSVPs')
        unique_together = ['event', 'member']

    def __str__(self):
        return f'{self.member.full_name} - {self.event.title}'


# ──────────────────────────────────────────────────────────────────────────────
# Facility / Room Booking (P1)
# ──────────────────────────────────────────────────────────────────────────────

class Room(BaseModel):
    """Church room / facility available for booking."""

    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    capacity = models.PositiveIntegerField(
        default=0, verbose_name=_('Capacité'),
    )
    location = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name=_('Emplacement'),
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    amenities_json = models.JSONField(
        default=list, blank=True,
        verbose_name=_('Équipements'),
        help_text=_('Liste JSON des équipements disponibles'),
    )
    photo = models.ImageField(
        upload_to='rooms/', blank=True, null=True,
        verbose_name=_('Photo'), validators=[validate_image_file],
    )

    class Meta:
        verbose_name = _('Salle')
        verbose_name_plural = _('Salles')
        ordering = ['name']

    def __str__(self):
        return self.name


class RoomBooking(BaseModel):
    """A booking of a room for a time slot, optionally linked to an event."""

    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='bookings',
        verbose_name=_('Salle'),
    )
    event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='room_bookings', verbose_name=_('Événement'),
    )
    booked_by = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='room_bookings', verbose_name=_('Réservé par'),
    )
    start_datetime = models.DateTimeField(verbose_name=_('Début'))
    end_datetime = models.DateTimeField(verbose_name=_('Fin'))
    status = models.CharField(
        max_length=20, choices=BookingStatus.CHOICES,
        default=BookingStatus.PENDING, verbose_name=_('Statut'),
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Réservation de salle')
        verbose_name_plural = _('Réservations de salles')
        ordering = ['start_datetime']

    def __str__(self):
        return f'{self.room.name} - {self.start_datetime:%Y-%m-%d %H:%M}'


# ──────────────────────────────────────────────────────────────────────────────
# Custom Registration Forms (P2)
# ──────────────────────────────────────────────────────────────────────────────

class RegistrationForm(BaseModel):
    """Custom registration form attached to an event."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='registration_forms',
        verbose_name=_('Événement'),
    )
    title = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name=_('Titre du formulaire'),
    )
    fields_json = models.JSONField(
        default=list, blank=True,
        verbose_name=_('Champs du formulaire'),
        help_text=_('Liste JSON des champs: [{name, type, label, required, options}]'),
    )

    class Meta:
        verbose_name = _("Formulaire d'inscription")
        verbose_name_plural = _("Formulaires d'inscription")

    def __str__(self):
        return f'{self.title or "Formulaire"} - {self.event.title}'


class RegistrationEntry(BaseModel):
    """A member's submission for a custom registration form."""

    form = models.ForeignKey(
        RegistrationForm, on_delete=models.CASCADE, related_name='entries',
        verbose_name=_('Formulaire'),
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='registration_entries', verbose_name=_('Membre'),
    )
    data_json = models.JSONField(
        default=dict, blank=True,
        verbose_name=_('Données soumises'),
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Soumis le'),
    )

    class Meta:
        verbose_name = _("Inscription")
        verbose_name_plural = _("Inscriptions")
        unique_together = ['form', 'member']

    def __str__(self):
        return f'{self.member.full_name} - {self.form}'


# ──────────────────────────────────────────────────────────────────────────────
# Event Templates (P2)
# ──────────────────────────────────────────────────────────────────────────────

class EventTemplate(BaseModel):
    """Reusable event template for quick event creation."""

    name = models.CharField(max_length=200, verbose_name=_('Nom du modèle'))
    event_type = models.CharField(
        max_length=20, choices=EventType.CHOICES,
        default=EventType.WORSHIP, verbose_name=_('Type'),
    )
    default_duration = models.DurationField(
        null=True, blank=True,
        verbose_name=_('Durée par défaut'),
        help_text=_('Format: HH:MM:SS'),
    )
    default_description = models.TextField(
        blank=True, verbose_name=_('Description par défaut'),
    )
    default_capacity = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('Capacité par défaut'),
    )
    default_location = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name=_('Lieu par défaut'),
    )
    requires_rsvp = models.BooleanField(
        default=False, verbose_name=_('RSVP requis par défaut'),
    )

    class Meta:
        verbose_name = _("Modèle d'événement")
        verbose_name_plural = _("Modèles d'événements")
        ordering = ['name']

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────────────────────────────────────
# Waitlist (P2)
# ──────────────────────────────────────────────────────────────────────────────

class EventWaitlist(BaseModel):
    """Waitlist entry when an event is at max capacity."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='waitlist_entries',
        verbose_name=_('Événement'),
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='event_waitlists', verbose_name=_('Membre'),
    )
    position = models.PositiveIntegerField(
        default=0, verbose_name=_('Position'),
    )
    added_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Ajouté le'),
    )
    promoted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Promu le'),
    )

    class Meta:
        verbose_name = _("Liste d'attente")
        verbose_name_plural = _("Listes d'attente")
        unique_together = ['event', 'member']
        ordering = ['position']

    def __str__(self):
        return f'{self.member.full_name} - #{self.position} - {self.event.title}'


# ──────────────────────────────────────────────────────────────────────────────
# Event Volunteer Needs (P2)
# ──────────────────────────────────────────────────────────────────────────────

class EventVolunteerNeed(BaseModel):
    """A volunteer position requirement for an event."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='volunteer_needs',
        verbose_name=_('Événement'),
    )
    position_name = models.CharField(
        max_length=200, verbose_name=_('Nom du poste'),
    )
    required_count = models.PositiveIntegerField(
        default=1, verbose_name=_('Nombre requis'),
    )
    description = models.TextField(
        blank=True, verbose_name=_('Description'),
    )

    class Meta:
        verbose_name = _('Besoin de bénévole')
        verbose_name_plural = _('Besoins de bénévoles')

    def __str__(self):
        return f'{self.position_name} ({self.required_count}) - {self.event.title}'

    @property
    def filled_count(self):
        return self.signups.filter(
            status=VolunteerSignupStatus.CONFIRMED,
        ).count()

    @property
    def is_filled(self):
        return self.filled_count >= self.required_count

    @property
    def remaining(self):
        return max(0, self.required_count - self.filled_count)


class EventVolunteerSignup(BaseModel):
    """A member's signup for a volunteer position at an event."""

    need = models.ForeignKey(
        EventVolunteerNeed, on_delete=models.CASCADE, related_name='signups',
        verbose_name=_('Besoin'),
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='event_volunteer_signups', verbose_name=_('Membre'),
    )
    status = models.CharField(
        max_length=20, choices=VolunteerSignupStatus.CHOICES,
        default=VolunteerSignupStatus.PENDING,
        verbose_name=_('Statut'),
    )

    class Meta:
        verbose_name = _('Inscription bénévole')
        verbose_name_plural = _('Inscriptions bénévoles')
        unique_together = ['need', 'member']

    def __str__(self):
        return f'{self.member.full_name} - {self.need.position_name}'


# ──────────────────────────────────────────────────────────────────────────────
# Event Photo Gallery (P3)
# ──────────────────────────────────────────────────────────────────────────────

class EventPhoto(BaseModel):
    """Photo attached to an event for the gallery."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='photos',
        verbose_name=_('Événement'),
    )
    image = models.ImageField(
        upload_to='events/photos/%Y/%m/',
        verbose_name=_('Image'), validators=[validate_image_file],
    )
    caption = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name=_('Légende'),
    )
    uploaded_by = models.ForeignKey(
        'members.Member', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_event_photos', verbose_name=_('Téléversé par'),
    )
    is_approved = models.BooleanField(
        default=False, verbose_name=_('Approuvé'),
    )

    class Meta:
        verbose_name = _("Photo d'événement")
        verbose_name_plural = _("Photos d'événements")
        ordering = ['-created_at']

    def __str__(self):
        return f'Photo - {self.event.title} ({self.caption or "sans légende"})'


# ──────────────────────────────────────────────────────────────────────────────
# Event Surveys / Feedback (P3)
# ──────────────────────────────────────────────────────────────────────────────

class EventSurvey(BaseModel):
    """Post-event survey definition."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='surveys',
        verbose_name=_('Événement'),
    )
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    questions_json = models.JSONField(
        default=list, blank=True,
        verbose_name=_('Questions'),
        help_text=_('Liste JSON: [{question, type, options, required}]'),
    )
    send_after_hours = models.PositiveIntegerField(
        default=24,
        verbose_name=_("Envoyer X heures après l'événement"),
    )
    survey_sent = models.BooleanField(
        default=False, verbose_name=_('Sondage envoyé'),
    )

    class Meta:
        verbose_name = _('Sondage')
        verbose_name_plural = _('Sondages')

    def __str__(self):
        return f'{self.title} - {self.event.title}'


class SurveyResponse(BaseModel):
    """A member's response to an event survey."""

    survey = models.ForeignKey(
        EventSurvey, on_delete=models.CASCADE, related_name='responses',
        verbose_name=_('Sondage'),
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='survey_responses', verbose_name=_('Membre'),
    )
    answers_json = models.JSONField(
        default=dict, blank=True,
        verbose_name=_('Réponses'),
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Soumis le'),
    )

    class Meta:
        verbose_name = _('Réponse au sondage')
        verbose_name_plural = _('Réponses aux sondages')
        unique_together = ['survey', 'member']

    def __str__(self):
        return f'{self.member.full_name} - {self.survey.title}'
