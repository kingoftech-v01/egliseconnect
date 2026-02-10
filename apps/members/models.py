"""Member profiles, families, and groups."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SoftDeleteModel
from apps.core.constants import (
    Roles, FamilyStatus, GroupType, PrivacyLevel, Province, MembershipStatus,
    DepartmentRole, DisciplinaryType, ApprovalStatus, ModificationRequestStatus,
)
from apps.core.validators import validate_image_file

User = get_user_model()


class Family(BaseModel):
    """Family unit that shares a common address and can track donations together."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom de famille'),
        help_text=_('Ex: Famille Dupont')
    )

    address = models.TextField(
        blank=True,
        verbose_name=_('Adresse')
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ville')
    )

    province = models.CharField(
        max_length=2,
        choices=Province.CHOICES,
        default=Province.QC,
        verbose_name=_('Province')
    )

    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Code postal')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Famille')
        verbose_name_plural = _('Familles')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        """Count of active members in this family."""
        return self.members.filter(is_active=True).count()

    @property
    def full_address(self):
        """Formatted address string."""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(filter(None, parts))


class Member(SoftDeleteModel):
    """Church member with auto-generated member number (MBR-YYYY-XXXX)."""

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profile',
        verbose_name=_('Compte utilisateur')
    )

    member_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_('Numéro de membre'),
        help_text=_('Généré automatiquement')
    )

    first_name = models.CharField(
        max_length=100,
        verbose_name=_('Prénom')
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Nom')
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

    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone secondaire')
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de naissance')
    )

    address = models.TextField(
        blank=True,
        verbose_name=_('Adresse')
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ville')
    )

    province = models.CharField(
        max_length=2,
        choices=Province.CHOICES,
        default=Province.QC,
        verbose_name=_('Province')
    )

    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Code postal')
    )

    photo = models.ImageField(
        upload_to='members/photos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Photo'),
        validators=[validate_image_file],
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        default=Roles.MEMBER,
        verbose_name=_('Rôle')
    )

    family_status = models.CharField(
        max_length=20,
        choices=FamilyStatus.CHOICES,
        default=FamilyStatus.SINGLE,
        verbose_name=_('État civil')
    )

    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_('Famille')
    )

    joined_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'adhésion')
    )

    baptism_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de baptême')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes pastorales'),
        help_text=_('Visible uniquement par l\'équipe pastorale')
    )

    # --- Onboarding fields ---
    membership_status = models.CharField(
        max_length=30,
        choices=MembershipStatus.CHOICES,
        default=MembershipStatus.REGISTERED,
        db_index=True,
        verbose_name=_('Statut d\'adhésion')
    )

    registration_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'inscription')
    )

    form_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date limite formulaire')
    )

    form_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Formulaire soumis le')
    )

    admin_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Révisé par admin le')
    )

    admin_reviewed_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_members',
        verbose_name=_('Révisé par')
    )

    became_active_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Devenu membre actif le')
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_('Raison du refus')
    )

    # --- 2FA fields ---
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name=_('2FA activé')
    )

    two_factor_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date limite activation 2FA')
    )

    class Meta:
        verbose_name = _('Membre')
        verbose_name_plural = _('Membres')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['member_number']),
            models.Index(fields=['email']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['birth_date']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.member_number})'

    def save(self, *args, **kwargs):
        """Auto-generate member number on first save."""
        if not self.member_number:
            from apps.core.utils import generate_member_number
            self.member_number = generate_member_number()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_address(self):
        """Formatted address string."""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(filter(None, parts))

    @property
    def age(self):
        """Calculate age from birth date."""
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def days_remaining_for_form(self):
        """Days remaining to submit the onboarding form."""
        if not self.form_deadline:
            return None
        from django.utils import timezone
        delta = self.form_deadline - timezone.now()
        return max(0, delta.days)

    @property
    def is_form_expired(self):
        """Has the 30-day form deadline passed?"""
        if not self.form_deadline:
            return False
        from django.utils import timezone
        return timezone.now() > self.form_deadline

    @property
    def has_full_access(self):
        """Does this member have full dashboard access?"""
        return self.membership_status in MembershipStatus.FULL_ACCESS

    @property
    def can_use_qr(self):
        """Can this member use QR code for attendance?"""
        return self.membership_status in MembershipStatus.QR_ALLOWED

    @property
    def is_in_onboarding(self):
        """Is this member currently in the onboarding process?"""
        return self.membership_status in MembershipStatus.IN_PROCESS

    @property
    def is_2fa_overdue(self):
        """Has the 2FA setup deadline passed?"""
        if not self.two_factor_deadline:
            return False
        from django.utils import timezone
        return timezone.now() > self.two_factor_deadline and not self.two_factor_enabled

    @property
    def all_roles(self):
        """Returns set of all roles including primary and additional."""
        roles = {self.role}
        try:
            roles.update(self.additional_roles.values_list('role', flat=True))
        except (AttributeError, ValueError, TypeError):
            pass
        return roles

    def has_role(self, role):
        """Check if member has a specific role (primary or additional)."""
        return role in self.all_roles

    @property
    def is_staff_member(self):
        return bool(self.all_roles & set(Roles.STAFF_ROLES))

    @property
    def can_manage_finances(self):
        return bool(self.all_roles & set(Roles.FINANCE_ROLES))

    def get_groups(self):
        """Get all active groups this member belongs to."""
        return Group.objects.filter(memberships__member=self, memberships__is_active=True)


class Group(BaseModel):
    """Church group (cell, ministry, committee) with leaders and members."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom du groupe')
    )

    group_type = models.CharField(
        max_length=20,
        choices=GroupType.CHOICES,
        default=GroupType.CELL,
        verbose_name=_('Type de groupe')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    leader = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_groups',
        verbose_name=_('Leader')
    )

    meeting_day = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Jour de réunion')
    )

    meeting_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Heure de réunion')
    )

    meeting_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Lieu de réunion')
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_('Courriel du groupe')
    )

    class Meta:
        verbose_name = _('Groupe')
        verbose_name_plural = _('Groupes')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_group_type_display()})'

    @property
    def member_count(self):
        """Count of active members in this group."""
        return self.memberships.filter(is_active=True).count()


class GroupMembership(BaseModel):
    """Tracks when members joined groups and their role within the group."""

    MEMBERSHIP_ROLE_CHOICES = [
        ('member', _('Membre')),
        ('leader', _('Leader')),
        ('assistant', _('Assistant')),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name=_('Membre')
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('Groupe')
    )

    role = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_ROLE_CHOICES,
        default='member',
        verbose_name=_('Rôle dans le groupe')
    )

    joined_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Date d\'adhésion')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Adhésion au groupe')
        verbose_name_plural = _('Adhésions aux groupes')
        unique_together = ['member', 'group']
        ordering = ['group__name', 'member__last_name']

    def __str__(self):
        return f'{self.member.full_name} - {self.group.name}'


class DirectoryPrivacy(BaseModel):
    """Controls what information other members can see in the directory."""

    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        related_name='privacy_settings',
        verbose_name=_('Membre')
    )

    visibility = models.CharField(
        max_length=20,
        choices=PrivacyLevel.CHOICES,
        default=PrivacyLevel.PUBLIC,
        verbose_name=_('Visibilité du profil')
    )

    show_email = models.BooleanField(
        default=True,
        verbose_name=_('Afficher le courriel')
    )

    show_phone = models.BooleanField(
        default=True,
        verbose_name=_('Afficher le téléphone')
    )

    show_address = models.BooleanField(
        default=False,
        verbose_name=_('Afficher l\'adresse')
    )

    show_birth_date = models.BooleanField(
        default=True,
        verbose_name=_('Afficher la date de naissance')
    )

    show_photo = models.BooleanField(
        default=True,
        verbose_name=_('Afficher la photo')
    )

    class Meta:
        verbose_name = _('Paramètres de confidentialité')
        verbose_name_plural = _('Paramètres de confidentialité')

    def __str__(self):
        return f'Confidentialité - {self.member.full_name}'


class MemberRole(BaseModel):
    """Allows a member to hold multiple roles simultaneously."""

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='additional_roles',
        verbose_name=_('Membre')
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        verbose_name=_('Rôle')
    )

    class Meta:
        verbose_name = _('Rôle supplémentaire')
        verbose_name_plural = _('Rôles supplémentaires')
        unique_together = ['member', 'role']

    def __str__(self):
        return f'{self.member.full_name} - {self.get_role_display()}'


class Department(BaseModel):
    """Specialized group with leader, calendar, and custom task types."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nom')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    leader = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_departments',
        verbose_name=_('Leader')
    )

    parent_department = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_departments',
        verbose_name=_('Département parent')
    )

    meeting_day = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Jour de réunion')
    )

    meeting_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Heure de réunion')
    )

    meeting_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Lieu de réunion')
    )

    class Meta:
        verbose_name = _('Département')
        verbose_name_plural = _('Départements')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()


class DepartmentMembership(BaseModel):
    """Member's enrollment in a department."""

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='department_memberships',
        verbose_name=_('Membre')
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('Département')
    )

    role = models.CharField(
        max_length=20,
        choices=DepartmentRole.CHOICES,
        default=DepartmentRole.MEMBER,
        verbose_name=_('Rôle')
    )

    joined_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Date d\'adhésion')
    )

    class Meta:
        verbose_name = _('Adhésion au département')
        verbose_name_plural = _('Adhésions aux départements')
        unique_together = ['member', 'department']
        ordering = ['department__name']

    def __str__(self):
        return f'{self.member.full_name} - {self.department.name}'


class DepartmentTaskType(BaseModel):
    """Custom task types specific to a department."""

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='task_types',
        verbose_name=_('Département')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Nom de la tâche')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    max_assignees = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Nombre max d\'assignés')
    )

    class Meta:
        verbose_name = _('Type de tâche')
        verbose_name_plural = _('Types de tâches')
        unique_together = ['department', 'name']
        ordering = ['department', 'name']

    def __str__(self):
        return f'{self.department.name} - {self.name}'


class DisciplinaryAction(BaseModel):
    """Punishment, exemption, or suspension of a member."""

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='disciplinary_actions',
        verbose_name=_('Membre')
    )

    action_type = models.CharField(
        max_length=20,
        choices=DisciplinaryType.CHOICES,
        verbose_name=_('Type d\'action')
    )

    reason = models.TextField(
        verbose_name=_('Motif')
    )

    start_date = models.DateField(
        verbose_name=_('Date de début')
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de fin')
    )

    created_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_disciplinary_actions',
        verbose_name=_('Créé par')
    )

    approved_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_disciplinary_actions',
        verbose_name=_('Approuvé par')
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.CHOICES,
        default=ApprovalStatus.PENDING,
        verbose_name=_('Statut d\'approbation')
    )

    auto_suspend_membership = models.BooleanField(
        default=True,
        verbose_name=_('Suspendre automatiquement le compte')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        verbose_name = _('Action disciplinaire')
        verbose_name_plural = _('Actions disciplinaires')
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.get_action_type_display()} - {self.member.full_name}'

    @property
    def is_current(self):
        """Is this action currently in effect?"""
        from datetime import date
        today = date.today()
        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today


class ProfileModificationRequest(BaseModel):
    """Request from staff asking a member to update their personal information."""

    target_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='modification_requests',
        verbose_name=_('Membre cible')
    )

    requested_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_modification_requests',
        verbose_name=_('Demandé par')
    )

    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Décrivez les modifications demandées')
    )

    status = models.CharField(
        max_length=20,
        choices=ModificationRequestStatus.CHOICES,
        default=ModificationRequestStatus.PENDING,
        verbose_name=_('Statut')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complété le')
    )

    class Meta:
        verbose_name = _('Demande de modification de profil')
        verbose_name_plural = _('Demandes de modification de profil')
        ordering = ['-created_at']

    def __str__(self):
        return f'Demande pour {self.target_member.full_name} par {self.requested_by}'
