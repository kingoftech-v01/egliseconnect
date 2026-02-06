"""Centralized constants and choices for the application."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Roles:
    """Member role definitions."""
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

    # Permission groups for access control
    STAFF_ROLES = [PASTOR, ADMIN]
    VIEW_ALL_ROLES = [PASTOR, TREASURER, ADMIN]
    FINANCE_ROLES = [TREASURER, ADMIN]


class FamilyStatus:
    """Marital/family status options."""
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


class GroupType:
    """Church group categories."""
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


class PrivacyLevel:
    """Directory visibility settings."""
    PUBLIC = 'public'
    GROUP = 'group'
    PRIVATE = 'private'

    CHOICES = [
        (PUBLIC, _('Public (tous les membres)')),
        (GROUP, _('Groupe (mes groupes seulement)')),
        (PRIVATE, _('Privé (équipe pastorale seulement)')),
    ]


class DonationType:
    """Donation categories for financial tracking."""
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


class PaymentMethod:
    """Accepted payment methods."""
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


class EventType:
    """Church event categories."""
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


class RSVPStatus:
    """Event attendance response states."""
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


class VolunteerRole:
    """Volunteer ministry areas."""
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


class ScheduleStatus:
    """Volunteer assignment states."""
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


class VolunteerFrequency:
    """Volunteer availability preferences."""
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


class HelpRequestCategory:
    """Types of assistance requests."""
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


class HelpRequestUrgency(models.TextChoices):
    """Priority levels for help requests."""
    LOW = 'low', _('Faible')
    MEDIUM = 'medium', _('Moyenne')
    HIGH = 'high', _('Élevée')
    URGENT = 'urgent', _('Urgente')


Urgency = HelpRequestUrgency  # Backwards compatibility alias


class HelpRequestStatus(models.TextChoices):
    """Workflow states for help requests."""
    NEW = 'new', _('Nouvelle')
    IN_PROGRESS = 'in_progress', _('En cours')
    RESOLVED = 'resolved', _('Résolue')
    CLOSED = 'closed', _('Fermée')


RequestStatus = HelpRequestStatus  # Backwards compatibility alias


class NewsletterStatus:
    """Newsletter delivery states."""
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


class NotificationType:
    """System notification categories."""
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


class Province:
    """Canadian provinces and territories."""
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
