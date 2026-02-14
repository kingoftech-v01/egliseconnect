"""Reports models for scheduled reports, saved reports, and report sharing."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import BaseModel
from apps.core.constants import ReportFrequency, ReportType


class ReportSchedule(BaseModel):
    """Scheduled email report configuration."""
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    report_type = models.CharField(
        max_length=30,
        choices=ReportType.CHOICES,
        verbose_name=_('Type de rapport'),
    )
    frequency = models.CharField(
        max_length=20,
        choices=ReportFrequency.CHOICES,
        default=ReportFrequency.WEEKLY,
        verbose_name=_('Frequence'),
    )
    recipients = models.ManyToManyField(
        'members.Member',
        related_name='report_schedules',
        blank=True,
        verbose_name=_('Destinataires'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    last_sent_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Dernier envoi'),
    )
    next_run_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Prochain envoi'),
    )
    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_schedules',
        verbose_name=_('Cree par'),
    )
    filters_json = models.JSONField(
        default=dict, blank=True, verbose_name=_('Filtres (JSON)'),
    )
    template_name = models.CharField(
        max_length=200, blank=True, verbose_name=_('Nom du template'),
    )

    class Meta:
        verbose_name = _('Rapport planifie')
        verbose_name_plural = _('Rapports planifies')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_frequency_display()})'

    def compute_next_run(self):
        """Compute the next run datetime based on frequency."""
        now = timezone.now()
        if self.frequency == ReportFrequency.DAILY:
            return now + timezone.timedelta(days=1)
        elif self.frequency == ReportFrequency.WEEKLY:
            return now + timezone.timedelta(weeks=1)
        elif self.frequency == ReportFrequency.MONTHLY:
            return now + timezone.timedelta(days=30)
        elif self.frequency == ReportFrequency.QUARTERLY:
            return now + timezone.timedelta(days=90)
        return now + timezone.timedelta(weeks=1)


class SavedReport(BaseModel):
    """User-created custom report with saved filters and columns."""
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    report_type = models.CharField(
        max_length=30,
        choices=ReportType.CHOICES,
        verbose_name=_('Type de rapport'),
    )
    filters_json = models.JSONField(
        default=dict, blank=True, verbose_name=_('Filtres (JSON)'),
    )
    columns_json = models.JSONField(
        default=list, blank=True, verbose_name=_('Colonnes (JSON)'),
    )
    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_saved_reports',
        verbose_name=_('Cree par'),
    )
    shared_with = models.ManyToManyField(
        'members.Member',
        related_name='shared_reports',
        blank=True,
        verbose_name=_('Partage avec'),
    )

    class Meta:
        verbose_name = _('Rapport sauvegarde')
        verbose_name_plural = _('Rapports sauvegardes')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_report_type_display()})'
