"""Volunteer scheduling and management models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.core.constants import (
    VolunteerRole, ScheduleStatus, VolunteerFrequency,
    BackgroundCheckStatus, SkillProficiency, MilestoneType, DayOfWeek,
)


class VolunteerPosition(BaseModel):
    """A volunteer role that members can sign up for."""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    role_type = models.CharField(max_length=20, choices=VolunteerRole.CHOICES, verbose_name=_('Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    min_volunteers = models.PositiveIntegerField(default=1, verbose_name=_('Min requis'))
    max_volunteers = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Max'))
    skills_required = models.TextField(blank=True, verbose_name=_('Competences requises'))

    class Meta:
        verbose_name = _('Poste de benevolat')
        verbose_name_plural = _('Postes de benevolat')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def volunteer_count(self):
        return self.available_volunteers.count()


class VolunteerAvailability(BaseModel):
    """Tracks when a member is available for a specific position."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_availability')
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='available_volunteers')
    is_available = models.BooleanField(default=True, verbose_name=_('Disponible'))
    frequency = models.CharField(max_length=20, choices=VolunteerFrequency.CHOICES, default=VolunteerFrequency.MONTHLY, verbose_name=_('Frequence'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Disponibilite')
        verbose_name_plural = _('Disponibilites')
        unique_together = ['member', 'position']


class VolunteerSchedule(BaseModel):
    """A scheduled volunteer assignment for a specific date."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_schedules')
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='schedules')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True, related_name='volunteer_schedules')
    date = models.DateField(verbose_name=_('Date'))
    status = models.CharField(max_length=20, choices=ScheduleStatus.CHOICES, default=ScheduleStatus.SCHEDULED, verbose_name=_('Statut'))
    reminder_sent = models.BooleanField(default=False, verbose_name=_('Rappel envoye'))
    reminder_5days_sent = models.BooleanField(default=False)
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Horaire')
        verbose_name_plural = _('Horaires')
        ordering = ['date']

    def __str__(self):
        return f'{self.member.full_name} - {self.position.name} ({self.date})'


class PlannedAbsence(BaseModel):
    """Pre-declared absence period to avoid scheduling a member."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='planned_absences')
    start_date = models.DateField(verbose_name=_('Date de debut'))
    end_date = models.DateField(verbose_name=_('Date de fin'))
    reason = models.TextField(blank=True, verbose_name=_('Raison'))
    approved_by = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_absences', verbose_name=_('Approuve par'))

    class Meta:
        verbose_name = _('Absence prevue')
        verbose_name_plural = _('Absences prevues')
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.member.full_name}: {self.start_date} -> {self.end_date}'


class SwapRequest(BaseModel):
    """Request to swap a scheduled shift with another volunteer."""
    original_schedule = models.ForeignKey(VolunteerSchedule, on_delete=models.CASCADE, related_name='swap_requests')
    requested_by = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='swap_requests_made')
    swap_with = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='swap_requests_received')
    status = models.CharField(max_length=20, choices=[('pending', _('En attente')), ('approved', _('Approuve')), ('declined', _('Refuse'))], default='pending')
    reason = models.TextField(blank=True, verbose_name=_('Raison'))

    class Meta:
        verbose_name = _("Demande d'echange")
        verbose_name_plural = _("Demandes d'echange")


# ──────────────────────────────────────────────────────────────────────────────
# P1: Volunteer Hour Tracking
# ──────────────────────────────────────────────────────────────────────────────

class VolunteerHours(BaseModel):
    """Tracks volunteer hours worked for a position on a given date."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_hours', verbose_name=_('Membre'))
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='logged_hours', verbose_name=_('Poste'))
    date = models.DateField(verbose_name=_('Date'))
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Heures travaillees'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    approved_by = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_hours', verbose_name=_('Approuve par'))
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Date d\'approbation'))

    class Meta:
        verbose_name = _('Heures de benevolat')
        verbose_name_plural = _('Heures de benevolat')
        ordering = ['-date']

    def __str__(self):
        return f'{self.member.full_name} - {self.hours_worked}h ({self.date})'


# ──────────────────────────────────────────────────────────────────────────────
# P1: Background Check Status
# ──────────────────────────────────────────────────────────────────────────────

class VolunteerBackgroundCheck(BaseModel):
    """Background check status for a volunteer at a specific position."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_background_checks', verbose_name=_('Membre'))
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, null=True, blank=True, related_name='background_checks', verbose_name=_('Poste'))
    status = models.CharField(max_length=20, choices=BackgroundCheckStatus.CHOICES, default=BackgroundCheckStatus.PENDING, verbose_name=_('Statut'))
    check_date = models.DateField(null=True, blank=True, verbose_name=_('Date de verification'))
    expiry_date = models.DateField(null=True, blank=True, verbose_name=_("Date d'expiration"))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Verification des antecedents')
        verbose_name_plural = _('Verifications des antecedents')
        ordering = ['-check_date']

    def __str__(self):
        return f'{self.member.full_name} - {self.get_status_display()}'

    @property
    def is_expired(self):
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def is_valid(self):
        return self.status == BackgroundCheckStatus.APPROVED and not self.is_expired


# ──────────────────────────────────────────────────────────────────────────────
# P1: Team Communication
# ──────────────────────────────────────────────────────────────────────────────

class TeamAnnouncement(BaseModel):
    """Announcement posted to all volunteers in a specific position/team."""
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='announcements', verbose_name=_('Poste'))
    author = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='team_announcements', verbose_name=_('Auteur'))
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    body = models.TextField(verbose_name=_('Message'))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Date d'envoi"))

    class Meta:
        verbose_name = _("Annonce d'equipe")
        verbose_name_plural = _("Annonces d'equipe")
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.position.name})'


# ──────────────────────────────────────────────────────────────────────────────
# P2: Volunteer Onboarding Checklist
# ──────────────────────────────────────────────────────────────────────────────

class PositionChecklist(BaseModel):
    """A checklist item required for onboarding to a position."""
    position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='checklist_items', verbose_name=_('Poste'))
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    is_required = models.BooleanField(default=True, verbose_name=_('Requis'))

    class Meta:
        verbose_name = _("Element de checklist")
        verbose_name_plural = _("Elements de checklist")
        ordering = ['position', 'order']

    def __str__(self):
        return f'{self.position.name} - {self.title}'


class ChecklistProgress(BaseModel):
    """Tracks a volunteer's progress on a specific checklist item."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='checklist_progress', verbose_name=_('Membre'))
    checklist_item = models.ForeignKey(PositionChecklist, on_delete=models.CASCADE, related_name='progress_records', verbose_name=_('Element'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Complete le'))
    verified_by = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_checklist_items', verbose_name=_('Verifie par'))

    class Meta:
        verbose_name = _('Progres de checklist')
        verbose_name_plural = _('Progres de checklist')
        unique_together = ['member', 'checklist_item']

    def __str__(self):
        status = 'Complete' if self.completed_at else 'En cours'
        return f'{self.member.full_name} - {self.checklist_item.title} ({status})'

    @property
    def is_completed(self):
        return self.completed_at is not None


# ──────────────────────────────────────────────────────────────────────────────
# P2: Skills Matrix Matching
# ──────────────────────────────────────────────────────────────────────────────

class Skill(BaseModel):
    """A skill or qualification that volunteers can have."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Nom'))
    category = models.CharField(max_length=100, blank=True, verbose_name=_('Categorie'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    class Meta:
        verbose_name = _('Competence')
        verbose_name_plural = _('Competences')
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class VolunteerSkill(BaseModel):
    """Links a volunteer to a skill with proficiency level."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='volunteer_skills', verbose_name=_('Membre'))
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='volunteer_skills', verbose_name=_('Competence'))
    proficiency_level = models.CharField(max_length=20, choices=SkillProficiency.CHOICES, default=SkillProficiency.BEGINNER, verbose_name=_('Niveau'))
    certified_at = models.DateField(null=True, blank=True, verbose_name=_('Date de certification'))
    verified_by = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_skills', verbose_name=_('Verifie par'))

    class Meta:
        verbose_name = _('Competence de benevole')
        verbose_name_plural = _('Competences de benevoles')
        unique_together = ['member', 'skill']

    def __str__(self):
        return f'{self.member.full_name} - {self.skill.name} ({self.get_proficiency_level_display()})'


# ──────────────────────────────────────────────────────────────────────────────
# P2: Volunteer Recognition System
# ──────────────────────────────────────────────────────────────────────────────

class Milestone(BaseModel):
    """A volunteer achievement milestone (e.g. 100 hours, 1 year)."""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    milestone_type = models.CharField(max_length=20, choices=MilestoneType.CHOICES, verbose_name=_('Type'))
    threshold = models.PositiveIntegerField(verbose_name=_('Seuil'), help_text=_('Nombre d\'heures ou d\'annees'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    badge_icon = models.CharField(max_length=100, blank=True, verbose_name=_('Icone'), help_text=_('Classe CSS FontAwesome'))

    class Meta:
        verbose_name = _('Jalon')
        verbose_name_plural = _('Jalons')
        ordering = ['milestone_type', 'threshold']
        unique_together = ['milestone_type', 'threshold']

    def __str__(self):
        return f'{self.name} ({self.threshold} {self.get_milestone_type_display()})'


class MilestoneAchievement(BaseModel):
    """Records when a volunteer achieves a milestone."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='milestone_achievements', verbose_name=_('Membre'))
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='achievements', verbose_name=_('Jalon'))
    achieved_at = models.DateTimeField(verbose_name=_('Atteint le'))
    notified = models.BooleanField(default=False, verbose_name=_('Notifie'))

    class Meta:
        verbose_name = _('Jalon atteint')
        verbose_name_plural = _('Jalons atteints')
        unique_together = ['member', 'milestone']
        ordering = ['-achieved_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.milestone.name}'


# ──────────────────────────────────────────────────────────────────────────────
# P3: Volunteer Availability Heatmap
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilitySlot(BaseModel):
    """Time-slot availability for a member on a specific day of the week."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='availability_slots', verbose_name=_('Membre'))
    day_of_week = models.IntegerField(choices=DayOfWeek.CHOICES, verbose_name=_('Jour'))
    time_start = models.TimeField(verbose_name=_('Heure de debut'))
    time_end = models.TimeField(verbose_name=_('Heure de fin'))
    is_available = models.BooleanField(default=True, verbose_name=_('Disponible'))

    class Meta:
        verbose_name = _('Plage de disponibilite')
        verbose_name_plural = _('Plages de disponibilite')
        ordering = ['day_of_week', 'time_start']

    def __str__(self):
        return f'{self.member.full_name} - {self.get_day_of_week_display()} {self.time_start}-{self.time_end}'


# ──────────────────────────────────────────────────────────────────────────────
# P3: Cross-Training Tracking
# ──────────────────────────────────────────────────────────────────────────────

class CrossTraining(BaseModel):
    """Records cross-training of a volunteer from one position to another."""
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='cross_trainings', verbose_name=_('Membre'))
    original_position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='cross_training_from', verbose_name=_('Poste original'))
    trained_position = models.ForeignKey(VolunteerPosition, on_delete=models.CASCADE, related_name='cross_training_to', verbose_name=_('Poste forme'))
    certified_at = models.DateField(null=True, blank=True, verbose_name=_('Date de certification'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Formation croisee')
        verbose_name_plural = _('Formations croisees')
        unique_together = ['member', 'original_position', 'trained_position']

    def __str__(self):
        return f'{self.member.full_name}: {self.original_position.name} -> {self.trained_position.name}'
