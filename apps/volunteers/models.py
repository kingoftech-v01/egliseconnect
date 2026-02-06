"""Volunteer scheduling and management models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.core.constants import VolunteerRole, ScheduleStatus, VolunteerFrequency


class VolunteerPosition(BaseModel):
    """A volunteer role that members can sign up for."""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    role_type = models.CharField(max_length=20, choices=VolunteerRole.CHOICES, verbose_name=_('Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    min_volunteers = models.PositiveIntegerField(default=1, verbose_name=_('Min requis'))
    max_volunteers = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Max'))
    skills_required = models.TextField(blank=True, verbose_name=_('Compétences requises'))

    class Meta:
        verbose_name = _('Poste de bénévolat')
        verbose_name_plural = _('Postes de bénévolat')
        ordering = ['name']

    def __str__(self):
        return self.name


class VolunteerAvailability(BaseModel):
    """Tracks when a member is available for a specific position."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_availability')
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='available_volunteers')
    is_available = models.BooleanField(default=True, verbose_name=_('Disponible'))
    frequency = models.CharField(max_length=20, choices=VolunteerFrequency.CHOICES, default=VolunteerFrequency.MONTHLY, verbose_name=_('Fréquence'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Disponibilité')
        verbose_name_plural = _('Disponibilités')
        unique_together = ['member', 'position']


class VolunteerSchedule(BaseModel):
    """A scheduled volunteer assignment for a specific date."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_schedules')
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='schedules')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True, related_name='volunteer_schedules')
    date = models.DateField(verbose_name=_('Date'))
    status = models.CharField(max_length=20, choices=ScheduleStatus.CHOICES, default=ScheduleStatus.SCHEDULED, verbose_name=_('Statut'))
    reminder_sent = models.BooleanField(default=False, verbose_name=_('Rappel envoyé'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Horaire')
        verbose_name_plural = _('Horaires')
        ordering = ['date']

    def __str__(self):
        return f'{self.member.full_name} - {self.position.name} ({self.date})'


class SwapRequest(BaseModel):
    """Request to swap a scheduled shift with another volunteer."""
    original_schedule = models.ForeignKey(VolunteerSchedule, on_delete=models.CASCADE, related_name='swap_requests')
    requested_by = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='swap_requests_made')
    swap_with = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='swap_requests_received')
    status = models.CharField(max_length=20, choices=[('pending', _('En attente')), ('approved', _('Approuvé')), ('declined', _('Refusé'))], default='pending')
    reason = models.TextField(blank=True, verbose_name=_('Raison'))

    class Meta:
        verbose_name = _('Demande d\'échange')
        verbose_name_plural = _('Demandes d\'échange')
