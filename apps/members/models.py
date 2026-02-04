"""
Members models - Member profiles, families, and groups.

Models:
- Member: Church member profile with auto-generated member number
- Family: Family unit grouping related members
- Group: Church groups (cells, ministries, committees)
- GroupMembership: Many-to-many relationship between members and groups
- DirectoryPrivacy: Privacy settings for member directory visibility
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SoftDeleteModel
from apps.core.constants import Roles, FamilyStatus, GroupType, PrivacyLevel, Province

User = get_user_model()


# =============================================================================
# FAMILY MODEL
# =============================================================================

class Family(BaseModel):
    """
    Family unit grouping related members.

    A family shares a common address and can have donations tracked together.
    """

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
        """Return the number of members in this family."""
        return self.members.filter(is_active=True).count()

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(filter(None, parts))


# =============================================================================
# MEMBER MODEL
# =============================================================================

class Member(SoftDeleteModel):
    """
    Church member profile.

    Each member has a unique auto-generated member number (MBR-YYYY-XXXX).
    Members can be linked to a Django User for authentication.
    """

    # Link to Django User (optional, for authentication)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profile',
        verbose_name=_('Compte utilisateur')
    )

    # Unique member number (auto-generated)
    member_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_('Numéro de membre'),
        help_text=_('Généré automatiquement')
    )

    # Personal information
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

    # Address (can inherit from family or be individual)
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

    # Photo
    photo = models.ImageField(
        upload_to='members/photos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Photo')
    )

    # Role in the church
    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        default=Roles.MEMBER,
        verbose_name=_('Rôle')
    )

    # Family status
    family_status = models.CharField(
        max_length=20,
        choices=FamilyStatus.CHOICES,
        default=FamilyStatus.SINGLE,
        verbose_name=_('État civil')
    )

    # Family link
    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_('Famille')
    )

    # Church membership details
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

    # Notes (visible only to staff)
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes pastorales'),
        help_text=_('Visible uniquement par l\'équipe pastorale')
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
        """Return full name."""
        return f'{self.first_name} {self.last_name}'

    @property
    def full_address(self):
        """Return formatted full address."""
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
    def is_staff_member(self):
        """Check if member has staff role."""
        return self.role in Roles.STAFF_ROLES

    @property
    def can_manage_finances(self):
        """Check if member can manage finances."""
        return self.role in Roles.FINANCE_ROLES

    def get_groups(self):
        """Get all groups this member belongs to."""
        return Group.objects.filter(memberships__member=self, memberships__is_active=True)


# =============================================================================
# GROUP MODEL
# =============================================================================

class Group(BaseModel):
    """
    Church group (cell, ministry, committee, etc.).

    Groups have leaders and members with different roles.
    """

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

    # Leader
    leader = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_groups',
        verbose_name=_('Leader')
    )

    # Meeting details
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

    # Contact
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
        """Return the number of active members in this group."""
        return self.memberships.filter(is_active=True).count()


# =============================================================================
# GROUP MEMBERSHIP MODEL
# =============================================================================

class GroupMembership(BaseModel):
    """
    Membership of a member in a group.

    Tracks when members joined groups and their role within the group.
    """

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


# =============================================================================
# DIRECTORY PRIVACY MODEL
# =============================================================================

class DirectoryPrivacy(BaseModel):
    """
    Privacy settings for member directory visibility.

    Controls what information other members can see in the directory.
    """

    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        related_name='privacy_settings',
        verbose_name=_('Membre')
    )

    # Overall visibility
    visibility = models.CharField(
        max_length=20,
        choices=PrivacyLevel.CHOICES,
        default=PrivacyLevel.PUBLIC,
        verbose_name=_('Visibilité du profil')
    )

    # Individual field visibility
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
