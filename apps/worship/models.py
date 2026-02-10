"""Worship service planning models."""
from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import (
    WorshipServiceStatus, ServiceSectionType, AssignmentStatus,
)


class WorshipService(BaseModel):
    """A planned worship service (culte)."""

    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(verbose_name=_('Heure de début'))
    end_time = models.TimeField(
        blank=True, null=True, verbose_name=_('Heure de fin')
    )
    duration_minutes = models.PositiveIntegerField(
        default=120, verbose_name=_('Durée (minutes)')
    )

    status = models.CharField(
        max_length=20,
        choices=WorshipServiceStatus.CHOICES,
        default=WorshipServiceStatus.DRAFT,
        verbose_name=_('Statut'),
    )

    theme = models.CharField(
        max_length=300, blank=True, verbose_name=_('Thème')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_services',
        verbose_name=_('Créé par'),
    )

    validation_deadline = models.DateField(
        blank=True, null=True,
        verbose_name=_('Date limite de validation'),
        help_text=_('14 jours avant le culte par défaut'),
    )

    event = models.ForeignKey(
        'events.Event',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='worship_services',
        verbose_name=_('Événement associé'),
    )

    class Meta:
        verbose_name = _('Culte')
        verbose_name_plural = _('Cultes')
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'Culte du {self.date:%d/%m/%Y} à {self.start_time:%H:%M}'

    def save(self, *args, **kwargs):
        if not self.validation_deadline:
            self.validation_deadline = self.date - timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def confirmation_rate(self):
        """Percentage of assignments that are confirmed."""
        total = ServiceAssignment.objects.filter(
            section__service=self
        ).count()
        if total == 0:
            return 0
        confirmed = ServiceAssignment.objects.filter(
            section__service=self,
            status=AssignmentStatus.CONFIRMED,
        ).count()
        return int((confirmed / total) * 100)

    @property
    def total_assignments(self):
        return ServiceAssignment.objects.filter(section__service=self).count()

    @property
    def confirmed_assignments(self):
        return ServiceAssignment.objects.filter(
            section__service=self, status=AssignmentStatus.CONFIRMED
        ).count()


class ServiceSection(BaseModel):
    """A section/segment within a worship service."""

    service = models.ForeignKey(
        WorshipService,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('Culte'),
    )

    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    order = models.PositiveIntegerField(verbose_name=_('Ordre'))
    duration_minutes = models.PositiveIntegerField(
        default=15, verbose_name=_('Durée (minutes)')
    )

    section_type = models.CharField(
        max_length=30,
        choices=ServiceSectionType.CHOICES,
        default=ServiceSectionType.OTHER,
        verbose_name=_('Type de section'),
    )

    department = models.ForeignKey(
        'members.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='service_sections',
        verbose_name=_('Département responsable'),
    )

    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Section de culte')
        verbose_name_plural = _('Sections de culte')
        ordering = ['service', 'order']
        unique_together = ['service', 'order']

    def __str__(self):
        return f'{self.order}. {self.name}'


class ServiceAssignment(BaseModel):
    """Assignment of a member to a section of a worship service."""

    section = models.ForeignKey(
        ServiceSection,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Section'),
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='service_assignments',
        verbose_name=_('Membre'),
    )

    task_type = models.ForeignKey(
        'members.DepartmentTaskType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='service_assignments',
        verbose_name=_('Type de tâche'),
    )

    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.CHOICES,
        default=AssignmentStatus.ASSIGNED,
        verbose_name=_('Statut'),
    )

    responded_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Répondu le')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    reminder_5days_sent = models.BooleanField(default=False)
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Assignation')
        verbose_name_plural = _('Assignations')
        unique_together = ['section', 'member']

    def __str__(self):
        return f'{self.member.full_name} → {self.section.name}'


class EligibleMemberList(BaseModel):
    """Defines which members are eligible for a specific section type."""

    section_type = models.CharField(
        max_length=30,
        choices=ServiceSectionType.CHOICES,
        unique=True,
        verbose_name=_('Type de section'),
    )

    members = models.ManyToManyField(
        'members.Member',
        blank=True,
        related_name='eligible_for_sections',
        verbose_name=_('Membres éligibles'),
    )

    department = models.ForeignKey(
        'members.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='eligible_lists',
        verbose_name=_('Département'),
    )

    class Meta:
        verbose_name = _('Liste d\'éligibilité')
        verbose_name_plural = _('Listes d\'éligibilité')

    def __str__(self):
        return f'Éligibles: {self.get_section_type_display()}'
