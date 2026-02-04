"""
Core constants - Centralized constants and choices for ÉgliseConnect.

This module contains all the choices and constants used across the application.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


# =============================================================================
# MEMBER ROLES
# =============================================================================

class Roles:
    """Member role choices."""
    MEMBER = 'member'
    VOLUNTEER = 'volunteer'
    GROUP_LEADER = 'group_leader'
    PASTOR = 'pastor'
    TREASURER = 'treasurer'
    ADMIN = 'admin'

    CHOICES = [
        (MEMBER, _('Membre')),
        (VOLUNTEER, _('Volontaire')),
        (GROUP_LEADER, _('Leader de groupe')),
        (PASTOR, _('Pasteur')),
        (TREASURER, _('Trésorier')),
        (ADMIN, _('Administrateur')),
    ]

    # Roles that can manage other members
    STAFF_ROLES = [PASTOR, ADMIN]

    # Roles that can view all members
    VIEW_ALL_ROLES = [PASTOR, TREASURER, ADMIN]

    # Roles that can manage finances
    FINANCE_ROLES = [TREASURER, ADMIN]


# =============================================================================
# FAMILY STATUS
# =============================================================================

class FamilyStatus:
    """Family status choices."""
    SINGLE = 'single'
    MARRIED = 'married'
    WIDOWED = 'widowed'
    DIVORCED = 'divorced'

    CHOICES = [
        (SINGLE, _('Célibataire')),
        (MARRIED, _('Marié(e)')),
        (WIDOWED, _('Veuf/Veuve')),
        (DIVORCED, _('Divorcé(e)')),
    ]


# =============================================================================
# GROUP TYPES
# =============================================================================

class GroupType:
    """Group type choices."""
    CELL = 'cell'
    MINISTRY = 'ministry'
    COMMITTEE = 'committee'
    CLASS = 'class'
    CHOIR = 'choir'
    OTHER = 'other'

    CHOICES = [
        (CELL, _('Cellule')),
        (MINISTRY, _('Ministère')),
        (COMMITTEE, _('Comité')),
        (CLASS, _('Classe')),
        (CHOIR, _('Chorale')),
        (OTHER, _('Autre')),
    ]


# =============================================================================
# DIRECTORY PRIVACY
# =============================================================================

class PrivacyLevel:
    """Directory privacy level choices."""
    PUBLIC = 'public'
    GROUP = 'group'
    PRIVATE = 'private'

    CHOICES = [
        (PUBLIC, _('Public (tous les membres)')),
        (GROUP, _('Groupe (mes groupes seulement)')),
        (PRIVATE, _('Privé (équipe pastorale seulement)')),
    ]


# =============================================================================
# DONATION TYPES
# =============================================================================

class DonationType:
    """Donation type choices."""
    TITHE = 'tithe'
    OFFERING = 'offering'
    SPECIAL = 'special'
    CAMPAIGN = 'campaign'
    BUILDING = 'building'
    MISSIONS = 'missions'
    OTHER = 'other'

    CHOICES = [
        (TITHE, _('Dîme')),
        (OFFERING, _('Offrande générale')),
        (SPECIAL, _('Offrande spéciale')),
        (CAMPAIGN, _('Campagne')),
        (BUILDING, _('Bâtiment')),
        (MISSIONS, _('Missions')),
        (OTHER, _('Autre')),
    ]


# =============================================================================
# PAYMENT METHODS
# =============================================================================

class PaymentMethod:
    """Payment method choices."""
    CASH = 'cash'
    CHECK = 'check'
    CARD = 'card'
    BANK_TRANSFER = 'bank_transfer'
    ONLINE = 'online'
    OTHER = 'other'

    CHOICES = [
        (CASH, _('Espèces')),
        (CHECK, _('Chèque')),
        (CARD, _('Carte de crédit/débit')),
        (BANK_TRANSFER, _('Virement bancaire')),
        (ONLINE, _('En ligne')),
        (OTHER, _('Autre')),
    ]


# =============================================================================
# EVENT TYPES
# =============================================================================

class EventType:
    """Event type choices."""
    WORSHIP = 'worship'
    GROUP = 'group'
    MEAL = 'meal'
    SPECIAL = 'special'
    MEETING = 'meeting'
    TRAINING = 'training'
    OUTREACH = 'outreach'
    OTHER = 'other'

    CHOICES = [
        (WORSHIP, _('Culte')),
        (GROUP, _('Réunion de groupe')),
        (MEAL, _('Repas communautaire')),
        (SPECIAL, _('Événement spécial')),
        (MEETING, _('Réunion')),
        (TRAINING, _('Formation')),
        (OUTREACH, _('Évangélisation')),
        (OTHER, _('Autre')),
    ]


# =============================================================================
# RSVP STATUS
# =============================================================================

class RSVPStatus:
    """RSVP status choices."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    DECLINED = 'declined'
    MAYBE = 'maybe'

    CHOICES = [
        (PENDING, _('En attente')),
        (CONFIRMED, _('Confirmé')),
        (DECLINED, _('Refusé')),
        (MAYBE, _('Peut-être')),
    ]


# =============================================================================
# VOLUNTEER ROLES
# =============================================================================

class VolunteerRole:
    """Volunteer role type choices."""
    WORSHIP = 'worship'
    HOSPITALITY = 'hospitality'
    TECHNICAL = 'technical'
    CHILDREN = 'children'
    YOUTH = 'youth'
    ADMIN = 'admin'
    OUTREACH = 'outreach'
    OTHER = 'other'

    CHOICES = [
        (WORSHIP, _('Louange')),
        (HOSPITALITY, _('Accueil')),
        (TECHNICAL, _('Technique')),
        (CHILDREN, _('Enfants')),
        (YOUTH, _('Jeunesse')),
        (ADMIN, _('Administration')),
        (OUTREACH, _('Évangélisation')),
        (OTHER, _('Autre')),
    ]


# =============================================================================
# VOLUNTEER SCHEDULE STATUS
# =============================================================================

class ScheduleStatus:
    """Volunteer schedule status choices."""
    SCHEDULED = 'scheduled'
    CONFIRMED = 'confirmed'
    DECLINED = 'declined'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'

    CHOICES = [
        (SCHEDULED, _('Planifié')),
        (CONFIRMED, _('Confirmé')),
        (DECLINED, _('Refusé')),
        (COMPLETED, _('Complété')),
        (NO_SHOW, _('Absent')),
    ]


# =============================================================================
# VOLUNTEER FREQUENCY
# =============================================================================

class VolunteerFrequency:
    """Volunteer availability frequency choices."""
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    MONTHLY = 'monthly'
    OCCASIONAL = 'occasional'

    CHOICES = [
        (WEEKLY, _('Chaque semaine')),
        (BIWEEKLY, _('Aux deux semaines')),
        (MONTHLY, _('Une fois par mois')),
        (OCCASIONAL, _('Occasionnellement')),
    ]


# =============================================================================
# HELP REQUEST CATEGORIES
# =============================================================================

class HelpRequestCategory:
    """Help request category choices."""
    PRAYER = 'prayer'
    FINANCIAL = 'financial'
    MATERIAL = 'material'
    PASTORAL = 'pastoral'
    TRANSPORT = 'transport'
    MEDICAL = 'medical'
    OTHER = 'other'

    CHOICES = [
        (PRAYER, _('Prière')),
        (FINANCIAL, _('Aide financière')),
        (MATERIAL, _('Aide matérielle')),
        (PASTORAL, _('Conseil pastoral')),
        (TRANSPORT, _('Transport')),
        (MEDICAL, _('Médical')),
        (OTHER, _('Autre')),
    ]


# =============================================================================
# HELP REQUEST URGENCY
# =============================================================================

class HelpRequestUrgency(models.TextChoices):
    """Help request urgency choices."""
    LOW = 'low', _('Faible')
    MEDIUM = 'medium', _('Moyenne')
    HIGH = 'high', _('Élevée')
    URGENT = 'urgent', _('Urgente')


# Alias for backwards compatibility
Urgency = HelpRequestUrgency


# =============================================================================
# HELP REQUEST STATUS
# =============================================================================

class HelpRequestStatus(models.TextChoices):
    """Help request status choices."""
    NEW = 'new', _('Nouvelle')
    IN_PROGRESS = 'in_progress', _('En cours')
    RESOLVED = 'resolved', _('Résolue')
    CLOSED = 'closed', _('Fermée')


# Alias for backwards compatibility
RequestStatus = HelpRequestStatus


# =============================================================================
# NEWSLETTER STATUS
# =============================================================================

class NewsletterStatus:
    """Newsletter status choices."""
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    SENDING = 'sending'
    SENT = 'sent'
    FAILED = 'failed'

    CHOICES = [
        (DRAFT, _('Brouillon')),
        (SCHEDULED, _('Planifiée')),
        (SENDING, _('En cours d\'envoi')),
        (SENT, _('Envoyée')),
        (FAILED, _('Échec')),
    ]


# =============================================================================
# NOTIFICATION TYPES
# =============================================================================

class NotificationType:
    """Notification type choices."""
    BIRTHDAY = 'birthday'
    EVENT = 'event'
    VOLUNTEER = 'volunteer'
    HELP_REQUEST = 'help_request'
    DONATION = 'donation'
    GENERAL = 'general'

    CHOICES = [
        (BIRTHDAY, _('Anniversaire')),
        (EVENT, _('Rappel d\'événement')),
        (VOLUNTEER, _('Rappel de bénévolat')),
        (HELP_REQUEST, _('Mise à jour de requête')),
        (DONATION, _('Reçu de don')),
        (GENERAL, _('Général')),
    ]


# =============================================================================
# CANADIAN PROVINCES
# =============================================================================

class Province:
    """Canadian province choices."""
    AB = 'AB'
    BC = 'BC'
    MB = 'MB'
    NB = 'NB'
    NL = 'NL'
    NS = 'NS'
    NT = 'NT'
    NU = 'NU'
    ON = 'ON'
    PE = 'PE'
    QC = 'QC'
    SK = 'SK'
    YT = 'YT'

    CHOICES = [
        (AB, _('Alberta')),
        (BC, _('Colombie-Britannique')),
        (MB, _('Manitoba')),
        (NB, _('Nouveau-Brunswick')),
        (NL, _('Terre-Neuve-et-Labrador')),
        (NS, _('Nouvelle-Écosse')),
        (NT, _('Territoires du Nord-Ouest')),
        (NU, _('Nunavut')),
        (ON, _('Ontario')),
        (PE, _('Île-du-Prince-Édouard')),
        (QC, _('Québec')),
        (SK, _('Saskatchewan')),
        (YT, _('Yukon')),
    ]
