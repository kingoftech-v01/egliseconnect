"""Onboarding models: training courses, lessons, interviews, invitations,
mentor assignments, custom forms, welcome sequences, documents, gamification,
multi-track onboarding, video training, and visitor follow-up."""
import secrets
import string

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import (
    LessonStatus, InterviewStatus, Roles, CustomFieldType,
    MentorAssignmentStatus, WelcomeStepChannel, DocumentType,
    DocumentStatus, OnboardingTrack as OnboardingTrackChoices,
    AchievementTrigger, VisitorFollowUpStatus,
)
from apps.core.validators import validate_pdf_file


# ─── Existing models ─────────────────────────────────────────────────────────


class TrainingCourse(BaseModel):
    """Template for a training program assigned to new members."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du parcours'),
        help_text=_('Ex: Parcours Decouverte 2025')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    total_lessons = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Nombre de lecons')
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Parcours par defaut'),
        help_text=_('Utilise automatiquement pour les nouveaux membres')
    )

    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_courses',
        verbose_name=_('Cree par')
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
        help_text=_('Numero de la lecon dans le parcours')
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
        verbose_name=_('Duree (minutes)')
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

    # P3: Video-Based Training (item 44)
    video_url = models.URLField(
        blank=True,
        verbose_name=_('URL de la video'),
        help_text=_('Lien YouTube ou Vimeo pour la video de la lecon')
    )

    class Meta:
        verbose_name = _('Lecon')
        verbose_name_plural = _('Lecons')
        ordering = ['course', 'order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f'Le\u00e7on {self.order}: {self.title}'


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
        verbose_name=_('Assigne par')
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Assigne le')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complete le')
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Complete')
    )

    # P3: Multi-Track (item 36) - track assignment
    track = models.ForeignKey(
        'OnboardingTrackModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_enrollments',
        verbose_name=_('Parcours multi-piste'),
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
        verbose_name=_('Lecon')
    )

    scheduled_date = models.DateTimeField(
        verbose_name=_('Date et heure prevue')
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
        verbose_name=_('Present a')
    )

    marked_by = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='marked_lessons',
        verbose_name=_('Marque par')
    )

    is_makeup = models.BooleanField(
        default=False,
        verbose_name=_('Session de rattrapage')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    # P3: Video completion tracking (item 45)
    video_completed = models.BooleanField(
        default=False,
        verbose_name=_('Video vue'),
    )
    video_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Video vue le'),
    )

    reminder_5days_sent = models.BooleanField(default=False)
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Lecon planifiee')
        verbose_name_plural = _('Lecons planifiees')
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
        verbose_name=_('Date proposee')
    )

    counter_proposed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Contre-proposition du membre')
    )

    confirmed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date confirmee')
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
        verbose_name=_('Complete le')
    )

    result_notes = models.TextField(
        blank=True,
        verbose_name=_('Notes de resultat')
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
    """Code d'invitation pour integrer un nouveau membre ou assigner un role."""

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
        verbose_name=_('Role assigne'),
        help_text=_('Role attribue au membre lors de l\'utilisation'),
    )

    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='created_invitations',
        verbose_name=_('Cree par'),
    )

    used_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_invitations',
        verbose_name=_('Utilise par'),
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Utilise le'),
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
        help_text=_('Si coche, le membre devient actif immediatement (membres pre-existants)'),
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


# ─── P1: Mentor/Buddy Assignment (items 1-5) ─────────────────────────────────


class MentorAssignment(BaseModel):
    """Assignment of an experienced member as mentor to a new member."""

    new_member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='mentor_assignments_as_mentee',
        verbose_name=_('Nouveau membre'),
    )

    mentor = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='mentor_assignments_as_mentor',
        verbose_name=_('Mentor'),
    )

    start_date = models.DateField(
        default=timezone.now,
        verbose_name=_('Date de debut'),
    )

    status = models.CharField(
        max_length=20,
        choices=MentorAssignmentStatus.CHOICES,
        default=MentorAssignmentStatus.ACTIVE,
        verbose_name=_('Statut'),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
    )

    check_in_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de suivis'),
    )

    class Meta:
        verbose_name = _('Assignation de mentor')
        verbose_name_plural = _('Assignations de mentor')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.mentor.full_name} -> {self.new_member.full_name}'


class MentorCheckIn(BaseModel):
    """Check-in log between mentor and mentee."""

    assignment = models.ForeignKey(
        MentorAssignment,
        on_delete=models.CASCADE,
        related_name='check_ins',
        verbose_name=_('Assignation'),
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name=_('Date'),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
    )

    logged_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='logged_checkins',
        verbose_name=_('Note par'),
    )

    class Meta:
        verbose_name = _('Suivi mentor')
        verbose_name_plural = _('Suivis mentor')
        ordering = ['-date']

    def __str__(self):
        return f'Suivi {self.date} - {self.assignment}'


# ─── P1: Custom Onboarding Form Builder (items 6-10) ─────────────────────────


class OnboardingFormField(BaseModel):
    """Custom field definition for the onboarding form builder."""

    label = models.CharField(
        max_length=200,
        verbose_name=_('Libelle'),
    )

    field_type = models.CharField(
        max_length=20,
        choices=CustomFieldType.CHOICES,
        verbose_name=_('Type de champ'),
    )

    is_required = models.BooleanField(
        default=False,
        verbose_name=_('Obligatoire'),
    )

    options = models.JSONField(
        blank=True,
        default=list,
        verbose_name=_('Options'),
        help_text=_('Liste de choix pour les listes deroulantes (JSON array)'),
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordre'),
    )

    conditional_field = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dependent_fields',
        verbose_name=_('Champ conditionnel'),
        help_text=_('Ce champ ne s\'affiche que si le champ conditionnel a la valeur specifiee'),
    )

    conditional_value = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Valeur conditionnelle'),
    )

    class Meta:
        verbose_name = _('Champ de formulaire')
        verbose_name_plural = _('Champs de formulaire')
        ordering = ['order']

    def __str__(self):
        return f'{self.label} ({self.get_field_type_display()})'


class OnboardingFormResponse(BaseModel):
    """Response to a custom onboarding form field."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='form_responses',
        verbose_name=_('Membre'),
    )

    field = models.ForeignKey(
        OnboardingFormField,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('Champ'),
    )

    value = models.TextField(
        blank=True,
        verbose_name=_('Valeur'),
    )

    file = models.FileField(
        upload_to='onboarding/form_responses/%Y/',
        blank=True,
        null=True,
        verbose_name=_('Fichier'),
    )

    class Meta:
        verbose_name = _('Reponse au formulaire')
        verbose_name_plural = _('Reponses au formulaire')
        unique_together = ['member', 'field']

    def __str__(self):
        return f'{self.member.full_name} - {self.field.label}'


# ─── P1: Automated Welcome Sequence (items 11-13) ────────────────────────────


class WelcomeSequence(BaseModel):
    """A named sequence of automated welcome steps."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de la sequence'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )

    class Meta:
        verbose_name = _('Sequence de bienvenue')
        verbose_name_plural = _('Sequences de bienvenue')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WelcomeStep(BaseModel):
    """A single step in a welcome sequence."""

    sequence = models.ForeignKey(
        WelcomeSequence,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('Sequence'),
    )

    day_offset = models.PositiveIntegerField(
        verbose_name=_('Jour (apres inscription)'),
        help_text=_('Nombre de jours apres l\'inscription pour envoyer ce message'),
    )

    channel = models.CharField(
        max_length=10,
        choices=WelcomeStepChannel.CHOICES,
        default=WelcomeStepChannel.EMAIL,
        verbose_name=_('Canal'),
    )

    subject = models.CharField(
        max_length=200,
        verbose_name=_('Sujet'),
    )

    body = models.TextField(
        verbose_name=_('Corps du message'),
        help_text=_('Utilisez {{ member_name }} pour le nom du membre'),
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordre'),
    )

    class Meta:
        verbose_name = _('Etape de bienvenue')
        verbose_name_plural = _('Etapes de bienvenue')
        ordering = ['sequence', 'order']

    def __str__(self):
        return f'Jour {self.day_offset}: {self.subject}'


class WelcomeProgress(BaseModel):
    """Tracking a member's progress through a welcome sequence."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='welcome_progress',
        verbose_name=_('Membre'),
    )

    sequence = models.ForeignKey(
        WelcomeSequence,
        on_delete=models.CASCADE,
        related_name='member_progress',
        verbose_name=_('Sequence'),
    )

    current_step = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Etape courante'),
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Debut'),
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Termine le'),
    )

    class Meta:
        verbose_name = _('Progression bienvenue')
        verbose_name_plural = _('Progressions bienvenue')
        unique_together = ['member', 'sequence']

    def __str__(self):
        return f'{self.member.full_name} - {self.sequence.name} (etape {self.current_step})'


# ─── P2: Digital Document Signing (items 28-32) ──────────────────────────────


class OnboardingDocument(BaseModel):
    """A document that onboarding members may need to sign."""

    title = models.CharField(
        max_length=200,
        verbose_name=_('Titre'),
    )

    content = models.TextField(
        verbose_name=_('Contenu'),
    )

    requires_signature = models.BooleanField(
        default=True,
        verbose_name=_('Signature requise'),
    )

    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.CHOICES,
        default=DocumentType.COVENANT,
        verbose_name=_('Type de document'),
    )

    class Meta:
        verbose_name = _('Document d\'integration')
        verbose_name_plural = _('Documents d\'integration')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DocumentSignature(BaseModel):
    """Record of a member signing a document."""

    document = models.ForeignKey(
        OnboardingDocument,
        on_delete=models.CASCADE,
        related_name='signatures',
        verbose_name=_('Document'),
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='document_signatures',
        verbose_name=_('Membre'),
    )

    signature_text = models.CharField(
        max_length=200,
        verbose_name=_('Signature (nom complet)'),
    )

    signed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Signe le'),
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Adresse IP'),
    )

    class Meta:
        verbose_name = _('Signature de document')
        verbose_name_plural = _('Signatures de documents')
        unique_together = ['document', 'member']
        ordering = ['-signed_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.document.title}'


# ─── P2: Visitor Follow-Up (items 24-27) ─────────────────────────────────────


class VisitorFollowUp(BaseModel):
    """Assignment to follow up with a first-time visitor."""

    visitor_name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du visiteur'),
    )

    visitor_email = models.EmailField(
        blank=True,
        verbose_name=_('Courriel du visiteur'),
    )

    visitor_phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_('Telephone du visiteur'),
    )

    first_visit_date = models.DateField(
        verbose_name=_('Date de la premiere visite'),
    )

    assigned_to = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitor_followups',
        verbose_name=_('Assigne a'),
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitor_profile',
        verbose_name=_('Profil membre cree'),
        help_text=_('Si le visiteur a cree un profil membre'),
    )

    status = models.CharField(
        max_length=20,
        choices=VisitorFollowUpStatus.CHOICES,
        default=VisitorFollowUpStatus.PENDING,
        verbose_name=_('Statut'),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
    )

    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Converti le'),
    )

    class Meta:
        verbose_name = _('Suivi de visiteur')
        verbose_name_plural = _('Suivis de visiteurs')
        ordering = ['-first_visit_date']

    def __str__(self):
        return f'{self.visitor_name} ({self.first_visit_date})'


# ─── P3: Multi-Track Onboarding Paths (items 35-38) ──────────────────────────


class OnboardingTrackModel(BaseModel):
    """A named onboarding track with specific courses and documents."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du parcours'),
    )

    track_type = models.CharField(
        max_length=20,
        choices=OnboardingTrackChoices.CHOICES,
        default=OnboardingTrackChoices.DEFAULT,
        verbose_name=_('Type de parcours'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )

    courses = models.ManyToManyField(
        TrainingCourse,
        blank=True,
        related_name='tracks',
        verbose_name=_('Formations associees'),
    )

    documents = models.ManyToManyField(
        OnboardingDocument,
        blank=True,
        related_name='tracks',
        verbose_name=_('Documents associes'),
    )

    class Meta:
        verbose_name = _('Parcours multi-piste')
        verbose_name_plural = _('Parcours multi-pistes')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_track_type_display()})'


# ─── P3: Gamification (items 39-42) ──────────────────────────────────────────


class Achievement(BaseModel):
    """A badge/achievement that can be earned during onboarding."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Icone'),
        help_text=_('Classe CSS de l\'icone (ex: fas fa-star)'),
    )

    badge_image = models.ImageField(
        upload_to='onboarding/badges/',
        blank=True,
        null=True,
        verbose_name=_('Image du badge'),
    )

    points = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Points'),
    )

    trigger_type = models.CharField(
        max_length=30,
        choices=AchievementTrigger.CHOICES,
        verbose_name=_('Type de declencheur'),
    )

    class Meta:
        verbose_name = _('Accomplissement')
        verbose_name_plural = _('Accomplissements')
        ordering = ['name']

    def __str__(self):
        return self.name


class MemberAchievement(BaseModel):
    """Record of a member earning an achievement."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name=_('Membre'),
    )

    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='member_achievements',
        verbose_name=_('Accomplissement'),
    )

    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Obtenu le'),
    )

    class Meta:
        verbose_name = _('Accomplissement membre')
        verbose_name_plural = _('Accomplissements membre')
        unique_together = ['member', 'achievement']
        ordering = ['-earned_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.achievement.name}'


# ─── P3: Video-Based Training — Quiz (items 46-47) ──────────────────────────


class Quiz(BaseModel):
    """Quiz associated with a lesson."""

    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quiz',
        verbose_name=_('Lecon'),
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Titre'),
    )

    passing_score = models.PositiveIntegerField(
        default=70,
        verbose_name=_('Score de reussite (%)'),
    )

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quiz')

    def __str__(self):
        return self.title


class QuizQuestion(BaseModel):
    """A question in a quiz."""

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Quiz'),
    )

    text = models.TextField(
        verbose_name=_('Question'),
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordre'),
    )

    class Meta:
        verbose_name = _('Question de quiz')
        verbose_name_plural = _('Questions de quiz')
        ordering = ['quiz', 'order']

    def __str__(self):
        return f'Q{self.order}: {self.text[:50]}'


class QuizAnswer(BaseModel):
    """An answer option for a quiz question."""

    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Question'),
    )

    text = models.CharField(
        max_length=500,
        verbose_name=_('Reponse'),
    )

    is_correct = models.BooleanField(
        default=False,
        verbose_name=_('Correcte'),
    )

    class Meta:
        verbose_name = _('Reponse de quiz')
        verbose_name_plural = _('Reponses de quiz')

    def __str__(self):
        return f'{self.text[:50]} ({"correct" if self.is_correct else "incorrect"})'


class QuizAttempt(BaseModel):
    """A member's attempt at a quiz."""

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_('Membre'),
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('Quiz'),
    )

    score = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Score (%)'),
    )

    passed = models.BooleanField(
        default=False,
        verbose_name=_('Reussi'),
    )

    answers = models.JSONField(
        default=dict,
        verbose_name=_('Reponses'),
        help_text=_('Mapping question_id -> answer_id'),
    )

    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Termine le'),
    )

    class Meta:
        verbose_name = _('Tentative de quiz')
        verbose_name_plural = _('Tentatives de quiz')
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.quiz.title} ({self.score}%)'
