"""
Events models - Event and RSVP management.

Models:
- Event: Church events with calendar support
- EventRSVP: RSVP tracking for events
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import EventType, RSVPStatus
from apps.core.validators import validate_image_file


class Event(BaseModel):
    """Church event with RSVP support."""

    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    event_type = models.CharField(max_length=20, choices=EventType.CHOICES, default=EventType.WORSHIP, verbose_name=_('Type'))
    start_datetime = models.DateTimeField(verbose_name=_('Début'))
    end_datetime = models.DateTimeField(verbose_name=_('Fin'))
    all_day = models.BooleanField(default=False, verbose_name=_('Toute la journée'))
    location = models.CharField(max_length=255, blank=True, verbose_name=_('Lieu'))
    location_address = models.TextField(blank=True, verbose_name=_('Adresse'))
    is_online = models.BooleanField(default=False, verbose_name=_('En ligne'))
    online_link = models.URLField(blank=True, verbose_name=_('Lien'))
    organizer = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='organized_events', verbose_name=_('Organisateur'))
    max_attendees = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Capacité max'))
    requires_rsvp = models.BooleanField(default=False, verbose_name=_('RSVP requis'))
    image = models.ImageField(upload_to='events/%Y/%m/', blank=True, null=True, verbose_name=_('Image'), validators=[validate_image_file])
    is_published = models.BooleanField(default=True, verbose_name=_('Publié'))
    is_cancelled = models.BooleanField(default=False, verbose_name=_('Annulé'))
    is_recurring = models.BooleanField(default=False, verbose_name=_('Récurrent'))
    parent_event = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='occurrences')

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


class EventRSVP(BaseModel):
    """RSVP for an event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps', verbose_name=_('Événement'))
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='event_rsvps', verbose_name=_('Membre'))
    status = models.CharField(max_length=20, choices=RSVPStatus.CHOICES, default=RSVPStatus.PENDING, verbose_name=_('Statut'))
    guests = models.PositiveIntegerField(default=0, verbose_name=_('Invités'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('RSVP')
        verbose_name_plural = _('RSVPs')
        unique_together = ['event', 'member']

    def __str__(self):
        return f'{self.member.full_name} - {self.event.title}'
