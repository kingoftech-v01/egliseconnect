"""Onboarding models: training courses, lessons, interviews, invitations."""
import secrets
import string

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import LessonStatus, InterviewStatus, Roles
from apps.core.validators import validate_pdf_file


class TrainingCourse(BaseModel):
    """Template for a training program assigned to new members."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du parcours'),
        help_text=_('Ex: Parcours Découverte 2025')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    total_lessons = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Nombre de leçons')
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Parcours par défaut'),
        help_text=_('Utilisé automatiquement pour les nouveaux membres')
    )

    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_courses',
        verbose_name=_('Créé par')
    )

    class Meta:
        verbose_name = _('Parcours de formation')
        verbose_name_plural = _('Parcours de formation')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def lesson_count(self):
        return self.lessons.filter(is_active=True).count()

    @property
    def lessons_count(self):
        return self.lesson_count

    @property
    def participants_count(self):
        return self.enrollments.filter(is_active=True).count()


class Lesson(BaseModel):
    """Individual lesson within a training course."""

    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('Parcours')
    )

    order = models.PositiveIntegerField(
        verbose_name=_('Ordre'),
        help_text=_('Numéro de la leçon dans le parcours')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Titre')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    duration_minutes = models.PositiveIntegerField(
        default=90,
        verbose_name=_('Durée (minutes)')
    )

    materials_pdf = models.FileField(
        upload_to='lessons/pdf/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Document PDF'),
        validators=[validate_pdf_file]
    )

    materials_notes = models.TextField(
        blank=True,
        verbose_name=_('Notes de cours')
    )

    class Meta:
        verbose_name = _('Leçon')
        verbose_name_plural = _('Leçons')
        ordering = ['course', 'order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f'Leçon {self.order}: {self.title}'


class MemberTraining(BaseModel):
    """Enrollment of a specific member in a training course."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='trainings',
        verbose_name=_('Membre')
    )

    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('Parcours')
    )

    assigned_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_trainings',
        verbose_name=_('Assigné par')
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Assigné le')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complété le')
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Complété')
    )

    class Meta:
        verbose_name = _('Formation membre')
        verbose_name_plural = _('Formations membres')
        unique_together = ['member', 'course']

    def __str__(self):
        return f'{self.member.full_name} - {self.course.name}'

    @property
    def progress_percentage(self):
        total = self.scheduled_lessons.count()
        if total == 0:
            return 0
        done = self.scheduled_lessons.filter(
            status=LessonStatus.COMPLETED
        ).count()
        return int((done / total) * 100)

    @property
    def completed_count(self):
        return self.scheduled_lessons.filter(
            status=LessonStatus.COMPLETED
        ).count()

    @property
    def total_count(self):
        return self.scheduled_lessons.count()

    @property
    def absent_count(self):
        return self.scheduled_lessons.filter(
            status=LessonStatus.ABSENT
        ).count()


class ScheduledLesson(BaseModel):
    """A specific lesson scheduled for a member at a date/time."""

    training = models.ForeignKey(
        MemberTraining,
        on_delete=models.CASCADE,
        related_name='scheduled_lessons',
        verbose_name=_('Formation')
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='scheduled_instances',
        verbose_name=_('Leçon')
    )

    scheduled_date = models.DateTimeField(
        verbose_name=_('Date et heure prévue')
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Lieu')
    )

    status = models.CharField(
        max_length=20,
        choices=LessonStatus.CHOICES,
        default=LessonStatus.UPCOMING,
        verbose_name=_('Statut')
    )

    attended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Présent à')
    )

    marked_by = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='marked_lessons',
        verbose_name=_('Marqué par')
    )

    is_makeup = models.BooleanField(
        default=False,
        verbose_name=_('Session de rattrapage')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    reminder_5days_sent = models.BooleanField(default=False)
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Leçon planifiée')
        verbose_name_plural = _('Leçons planifiées')
        ordering = ['scheduled_date']

    def __str__(self):
        return f'{self.lesson.title} - {self.scheduled_date:%Y-%m-%d %H:%M}'


class Interview(BaseModel):
    """Final interview to become an official member."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name=_('Membre')
    )

    training = models.ForeignKey(
        MemberTraining,
        on_delete=models.CASCADE,
        related_name='interview',
        verbose_name=_('Formation')
    )

    status = models.CharField(
        max_length=20,
        choices=InterviewStatus.CHOICES,
        default=InterviewStatus.PROPOSED,
        verbose_name=_('Statut')
    )

    proposed_date = models.DateTimeField(
        verbose_name=_('Date proposée')
    )

    counter_proposed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Contre-proposition du membre')
    )

    confirmed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date confirmée')
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Lieu')
    )

    interviewer = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_interviews',
        verbose_name=_('Intervieweur')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complété le')
    )

    result_notes = models.TextField(
        blank=True,
        verbose_name=_('Notes de résultat')
    )

    reminder_5days_sent = models.BooleanField(default=False)
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Interview')
        verbose_name_plural = _('Interviews')
        ordering = ['-proposed_date']

    def __str__(self):
        return f'Interview {self.member.full_name} - {self.get_status_display()}'

    @property
    def final_date(self):
        """The definitive date for this interview."""
        return self.confirmed_date or self.proposed_date


def _generate_invitation_code():
    """Generate a unique 8-char uppercase alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


class InvitationCode(BaseModel):
    """Code d'invitation pour intégrer un nouveau membre ou assigner un rôle."""

    code = models.CharField(
        max_length=32,
        unique=True,
        default=_generate_invitation_code,
        verbose_name=_('Code'),
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        default=Roles.MEMBER,
        verbose_name=_('Rôle assigné'),
        help_text=_('Rôle attribué au membre lors de l\'utilisation'),
    )

    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='created_invitations',
        verbose_name=_('Créé par'),
    )

    used_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_invitations',
        verbose_name=_('Utilisé par'),
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Utilisé le'),
    )

    expires_at = models.DateTimeField(
        verbose_name=_('Expire le'),
    )

    max_uses = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Utilisations max'),
    )

    use_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre d\'utilisations'),
    )

    skip_onboarding = models.BooleanField(
        default=False,
        verbose_name=_('Passer le parcours'),
        help_text=_('Si coché, le membre devient actif immédiatement (membres pré-existants)'),
    )

    note = models.TextField(
        blank=True,
        verbose_name=_('Note'),
    )

    class Meta:
        verbose_name = _('Code d\'invitation')
        verbose_name_plural = _('Codes d\'invitation')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.get_role_display()})'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_usable(self):
        return (
            self.is_active
            and not self.is_expired
            and self.use_count < self.max_uses
        )
