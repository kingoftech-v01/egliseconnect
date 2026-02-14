"""Help Requests models."""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import (
    HelpRequestUrgency, HelpRequestStatus,
    CareType, CareStatus, PrayerRequestStatus,
    BenevolenceStatus, MealTrainStatus,
)


class HelpRequestCategory(BaseModel):
    """Category like Prayer, Financial, Material, or Pastoral."""
    name = models.CharField(max_length=100)
    name_fr = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for UI")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('Catégorie de demande')
        verbose_name_plural = _('Catégories de demandes')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class HelpRequest(BaseModel):
    """Support ticket submitted by a member."""
    request_number = models.CharField(max_length=20, unique=True, editable=False)
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='help_requests'
    )
    category = models.ForeignKey(
        HelpRequestCategory,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    urgency = models.CharField(
        max_length=20,
        choices=HelpRequestUrgency.choices,
        default=HelpRequestUrgency.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=HelpRequestStatus.choices,
        default=HelpRequestStatus.NEW
    )
    assigned_to = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_help_requests'
    )
    is_confidential = models.BooleanField(
        default=False,
        help_text="Only visible to pastors and admins"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Demande d\'aide')
        verbose_name_plural = _('Demandes d\'aide')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = self._generate_request_number()
        super().save(*args, **kwargs)

    def _generate_request_number(self):
        """Generate unique request number: HR-YYYYMM-XXXX."""
        from apps.core.utils import generate_request_number
        return generate_request_number()

    def mark_resolved(self, notes=''):
        self.status = HelpRequestStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'resolution_notes', 'updated_at'])

    def assign_to(self, member):
        """Assign to staff and auto-transition from NEW to IN_PROGRESS."""
        self.assigned_to = member
        if self.status == HelpRequestStatus.NEW:
            self.status = HelpRequestStatus.IN_PROGRESS
        self.save(update_fields=['assigned_to', 'status', 'updated_at'])


class HelpRequestComment(BaseModel):
    """Comment or internal note on a help request."""
    help_request = models.ForeignKey(
        HelpRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='help_request_comments'
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal staff-only note"
    )

    class Meta:
        verbose_name = _('Commentaire')
        verbose_name_plural = _('Commentaires')
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.help_request.request_number} by {self.author}"


# ─── P1: Pastoral Care ───────────────────────────────────────────────────────


class PastoralCare(BaseModel):
    """Tracks pastoral care visits, phone calls, counseling sessions."""
    care_type = models.CharField(
        max_length=30,
        choices=CareType.CHOICES,
        default=CareType.HOME_VISIT,
        verbose_name=_('Type de soin'),
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='pastoral_care_received',
        verbose_name=_('Membre'),
    )
    assigned_to = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pastoral_care_assigned',
        verbose_name=_('Assigné à'),
    )
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Date'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
    )
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de suivi'),
    )
    status = models.CharField(
        max_length=20,
        choices=CareStatus.CHOICES,
        default=CareStatus.OPEN,
        verbose_name=_('Statut'),
    )
    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pastoral_care_created',
        verbose_name=_('Créé par'),
    )

    class Meta:
        verbose_name = _('Soin pastoral')
        verbose_name_plural = _('Soins pastoraux')
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_care_type_display()} - {self.member}"


# ─── P1: Prayer Request ──────────────────────────────────────────────────────


class PrayerRequest(BaseModel):
    """Prayer requests that can be posted on the prayer wall."""
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titre'),
    )
    description = models.TextField(
        verbose_name=_('Description'),
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prayer_requests',
        verbose_name=_('Membre'),
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_('Anonyme'),
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Public'),
        help_text=_('Visible sur le mur de prière'),
    )
    status = models.CharField(
        max_length=20,
        choices=PrayerRequestStatus.CHOICES,
        default=PrayerRequestStatus.ACTIVE,
        verbose_name=_('Statut'),
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'exaucement'),
    )
    testimony = models.TextField(
        blank=True,
        verbose_name=_('Témoignage'),
        help_text=_('Témoignage lorsque la prière est exaucée'),
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_('Approuvée'),
        help_text=_('Les demandes anonymes doivent être approuvées'),
    )

    class Meta:
        verbose_name = _('Demande de prière')
        verbose_name_plural = _('Demandes de prière')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def mark_answered(self, testimony=''):
        """Mark this prayer request as answered with optional testimony."""
        self.status = PrayerRequestStatus.ANSWERED
        self.answered_at = timezone.now()
        self.testimony = testimony
        self.save(update_fields=['status', 'answered_at', 'testimony', 'updated_at'])


# ─── P1: Care Team ───────────────────────────────────────────────────────────


class CareTeam(BaseModel):
    """A care ministry team with a leader and members."""
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nom de l\'équipe'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )
    leader = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_care_teams',
        verbose_name=_('Leader'),
    )

    class Meta:
        verbose_name = _('Équipe de soins')
        verbose_name_plural = _('Équipes de soins')
        ordering = ['name']

    def __str__(self):
        return self.name


class CareTeamMember(BaseModel):
    """Membership in a care team."""
    team = models.ForeignKey(
        CareTeam,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('Équipe'),
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='care_team_memberships',
        verbose_name=_('Membre'),
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date d\'adhésion'),
    )

    class Meta:
        verbose_name = _('Membre d\'équipe de soins')
        verbose_name_plural = _('Membres d\'équipe de soins')
        unique_together = ['team', 'member']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.member} - {self.team}"


# ─── P3: Benevolence Fund ────────────────────────────────────────────────────


class BenevolenceFund(BaseModel):
    """Tracks a benevolence fund and its balance."""
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nom du fonds'),
    )
    total_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Solde total'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )

    class Meta:
        verbose_name = _('Fonds de bienfaisance')
        verbose_name_plural = _('Fonds de bienfaisance')
        ordering = ['name']

    def __str__(self):
        return self.name


class BenevolenceRequest(BaseModel):
    """Request for financial assistance from the benevolence fund."""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='benevolence_requests',
        verbose_name=_('Membre'),
    )
    fund = models.ForeignKey(
        BenevolenceFund,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        verbose_name=_('Fonds'),
    )
    amount_requested = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Montant demandé'),
    )
    reason = models.TextField(
        verbose_name=_('Raison'),
    )
    status = models.CharField(
        max_length=20,
        choices=BenevolenceStatus.CHOICES,
        default=BenevolenceStatus.SUBMITTED,
        verbose_name=_('Statut'),
    )
    approved_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='benevolence_approvals',
        verbose_name=_('Approuvé par'),
    )
    amount_granted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Montant accordé'),
    )
    disbursed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de versement'),
    )

    class Meta:
        verbose_name = _('Demande de bienfaisance')
        verbose_name_plural = _('Demandes de bienfaisance')
        ordering = ['-created_at']

    def __str__(self):
        return f"Demande de {self.member} - {self.amount_requested}$"


# ─── P3: Meal Train ──────────────────────────────────────────────────────────


class MealTrain(BaseModel):
    """Meal train coordination for a member in need."""
    recipient = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='meal_trains_received',
        verbose_name=_('Bénéficiaire'),
    )
    reason = models.TextField(
        verbose_name=_('Raison'),
    )
    start_date = models.DateField(
        verbose_name=_('Date de début'),
    )
    end_date = models.DateField(
        verbose_name=_('Date de fin'),
    )
    dietary_restrictions = models.TextField(
        blank=True,
        verbose_name=_('Restrictions alimentaires'),
    )
    status = models.CharField(
        max_length=20,
        choices=MealTrainStatus.CHOICES,
        default=MealTrainStatus.ACTIVE,
        verbose_name=_('Statut'),
    )

    class Meta:
        verbose_name = _('Train de repas')
        verbose_name_plural = _('Trains de repas')
        ordering = ['-start_date']

    def __str__(self):
        return f"Repas pour {self.recipient} ({self.start_date} - {self.end_date})"


class MealSignup(BaseModel):
    """Volunteer sign-up for a specific date in a meal train."""
    meal_train = models.ForeignKey(
        MealTrain,
        on_delete=models.CASCADE,
        related_name='signups',
        verbose_name=_('Train de repas'),
    )
    volunteer = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='meal_signups',
        verbose_name=_('Volontaire'),
    )
    date = models.DateField(
        verbose_name=_('Date'),
    )
    confirmed = models.BooleanField(
        default=False,
        verbose_name=_('Confirmé'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
    )

    class Meta:
        verbose_name = _('Inscription repas')
        verbose_name_plural = _('Inscriptions repas')
        unique_together = ['meal_train', 'volunteer', 'date']
        ordering = ['date']

    def __str__(self):
        return f"{self.volunteer} - {self.date}"


# ─── P3: Crisis Response ─────────────────────────────────────────────────────


class CrisisProtocol(BaseModel):
    """Crisis response protocol template."""
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titre'),
    )
    protocol_type = models.CharField(
        max_length=50,
        verbose_name=_('Type de protocole'),
        help_text=_('Ex: décès, hospitalisation, catastrophe naturelle'),
    )
    steps_json = models.JSONField(
        default=list,
        verbose_name=_('Étapes'),
        help_text=_('Liste des étapes du protocole en JSON'),
    )

    class Meta:
        verbose_name = _('Protocole de crise')
        verbose_name_plural = _('Protocoles de crise')
        ordering = ['title']

    def __str__(self):
        return self.title


class CrisisResource(BaseModel):
    """Resource library for crisis support."""
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titre'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )
    contact_info = models.TextField(
        blank=True,
        verbose_name=_('Coordonnées'),
    )
    url = models.URLField(
        blank=True,
        verbose_name=_('Lien'),
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Catégorie'),
        help_text=_('Ex: soutien au deuil, ressources communautaires'),
    )

    class Meta:
        verbose_name = _('Ressource de crise')
        verbose_name_plural = _('Ressources de crise')
        ordering = ['category', 'title']

    def __str__(self):
        return self.title
