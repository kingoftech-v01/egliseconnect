"""Centralized constants and choices for the application."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Roles:
    """Member role definitions."""
    MEMBER = 'member'
    VOLUNTEER = 'volunteer'
    GROUP_LEADER = 'group_leader'
    DEACON = 'deacon'
    PASTOR = 'pastor'
    TREASURER = 'treasurer'
    ADMIN = 'admin'

    CHOICES = [
        (MEMBER, _('Membre')),
        (VOLUNTEER, _('Volontaire')),
        (GROUP_LEADER, _('Leader de groupe')),
        (DEACON, _('Diacre')),
        (PASTOR, _('Pasteur')),
        (TREASURER, _('Trésorier')),
        (ADMIN, _('Administrateur')),
    ]

    # Permission groups for access control
    STAFF_ROLES = [DEACON, PASTOR, ADMIN]
    VIEW_ALL_ROLES = [DEACON, PASTOR, TREASURER, ADMIN]
    FINANCE_ROLES = [TREASURER, PASTOR, ADMIN]
    LEADERSHIP_ROLES = [DEACON, PASTOR, ADMIN]

    # Role hierarchy (index = power level)
    HIERARCHY = [MEMBER, VOLUNTEER, GROUP_LEADER, DEACON, TREASURER, PASTOR, ADMIN]


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


class MembershipStatus:
    """Membership lifecycle stages from registration to active member."""
    REGISTERED = 'registered'
    FORM_PENDING = 'form_pending'
    FORM_SUBMITTED = 'form_submitted'
    IN_REVIEW = 'in_review'
    APPROVED = 'approved'
    IN_TRAINING = 'in_training'
    INTERVIEW_SCHEDULED = 'interview_scheduled'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    REJECTED = 'rejected'
    EXPIRED = 'expired'

    CHOICES = [
        (REGISTERED, _('Inscrit')),
        (FORM_PENDING, _('Formulaire en attente')),
        (FORM_SUBMITTED, _('Formulaire soumis')),
        (IN_REVIEW, _('En cours de révision')),
        (APPROVED, _('Approuvé')),
        (IN_TRAINING, _('En formation')),
        (INTERVIEW_SCHEDULED, _('Interview planifiée')),
        (ACTIVE, _('Membre actif')),
        (INACTIVE, _('Inactif')),
        (SUSPENDED, _('Suspendu')),
        (REJECTED, _('Refusé')),
        (EXPIRED, _('Expiré')),
    ]

    QR_ALLOWED = [
        REGISTERED, FORM_PENDING, FORM_SUBMITTED,
        IN_REVIEW, APPROVED, IN_TRAINING,
        INTERVIEW_SCHEDULED, ACTIVE,
    ]

    FULL_ACCESS = [ACTIVE]

    IN_PROCESS = [
        REGISTERED, FORM_PENDING, FORM_SUBMITTED,
        IN_REVIEW, APPROVED, IN_TRAINING, INTERVIEW_SCHEDULED,
    ]


class InterviewStatus:
    """Interview scheduling and result states."""
    PROPOSED = 'proposed'
    ACCEPTED = 'accepted'
    COUNTER = 'counter'
    CONFIRMED = 'confirmed'
    COMPLETED_PASS = 'passed'
    COMPLETED_FAIL = 'failed'
    NO_SHOW = 'no_show'
    CANCELLED = 'cancelled'

    CHOICES = [
        (PROPOSED, _('Date proposée')),
        (ACCEPTED, _('Acceptée')),
        (COUNTER, _('Contre-proposition')),
        (CONFIRMED, _('Confirmée')),
        (COMPLETED_PASS, _('Réussie')),
        (COMPLETED_FAIL, _('Échouée')),
        (NO_SHOW, _('Absent')),
        (CANCELLED, _('Annulée')),
    ]


class LessonStatus:
    """Training lesson attendance states."""
    UPCOMING = 'upcoming'
    COMPLETED = 'completed'
    ABSENT = 'absent'
    MAKEUP = 'makeup'

    CHOICES = [
        (UPCOMING, _('À venir')),
        (COMPLETED, _('Complétée')),
        (ABSENT, _('Absent')),
        (MAKEUP, _('Rattrapage')),
    ]


class AttendanceSessionType:
    """Types of attendance check-in sessions."""
    WORSHIP = 'worship'
    EVENT = 'event'
    LESSON = 'lesson'
    OTHER = 'other'

    CHOICES = [
        (WORSHIP, _('Culte')),
        (EVENT, _('Événement')),
        (LESSON, _('Leçon de formation')),
        (OTHER, _('Autre')),
    ]


class CheckInMethod:
    """How a member was checked in."""
    QR_SCAN = 'qr_scan'
    MANUAL = 'manual'
    NFC = 'nfc'
    KIOSK = 'kiosk'
    GEO = 'geo'

    CHOICES = [
        (QR_SCAN, _('Scan QR')),
        (MANUAL, _('Manuel')),
        (NFC, _('NFC/Tap')),
        (KIOSK, _('Kiosque')),
        (GEO, _('Géolocalisation')),
    ]


class VisitorSource:
    """How a visitor heard about the church."""
    WALK_IN = 'walk_in'
    REFERRAL = 'referral'
    ONLINE = 'online'
    EVENT = 'event'
    OTHER = 'other'

    CHOICES = [
        (WALK_IN, _('Visite spontanée')),
        (REFERRAL, _('Référence')),
        (ONLINE, _('En ligne')),
        (EVENT, _('Événement')),
        (OTHER, _('Autre')),
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


class WorshipServiceStatus:
    """Worship service lifecycle states."""
    DRAFT = 'draft'
    PLANNED = 'planned'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (DRAFT, _('Brouillon')),
        (PLANNED, _('Planifié')),
        (CONFIRMED, _('Confirmé')),
        (COMPLETED, _('Terminé')),
        (CANCELLED, _('Annulé')),
    ]


class ServiceSectionType:
    """Types of sections within a worship service."""
    PRELUDE = 'prelude'
    ANNONCES = 'annonces'
    LOUANGE = 'louange'
    OFFRANDE = 'offrande'
    PREDICATION = 'predication'
    COMMUNION = 'communion'
    PRIERE = 'priere'
    BENEDICTION = 'benediction'
    OTHER = 'other'

    CHOICES = [
        (PRELUDE, _('Prélude')),
        (ANNONCES, _('Annonces')),
        (LOUANGE, _('Louange')),
        (OFFRANDE, _('Offrande')),
        (PREDICATION, _('Prédication')),
        (COMMUNION, _('Sainte Cène')),
        (PRIERE, _('Prière')),
        (BENEDICTION, _('Bénédiction')),
        (OTHER, _('Autre')),
    ]


class AssignmentStatus:
    """Status of a member's assignment to a service section."""
    ASSIGNED = 'assigned'
    CONFIRMED = 'confirmed'
    DECLINED = 'declined'

    CHOICES = [
        (ASSIGNED, _('Assigné')),
        (CONFIRMED, _('Confirmé')),
        (DECLINED, _('Non disponible')),
    ]


class DepartmentRole:
    """Role within a department."""
    MEMBER = 'member'
    LEADER = 'leader'
    ASSISTANT = 'assistant'

    CHOICES = [
        (MEMBER, _('Membre')),
        (LEADER, _('Leader')),
        (ASSISTANT, _('Assistant')),
    ]


class DisciplinaryType:
    """Types of disciplinary actions."""
    PUNISHMENT = 'punishment'
    EXEMPTION = 'exemption'
    SUSPENSION = 'suspension'

    CHOICES = [
        (PUNISHMENT, _('Punition')),
        (EXEMPTION, _('Exemption')),
        (SUSPENSION, _('Suspension')),
    ]


class ApprovalStatus:
    """Approval workflow states."""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    CHOICES = [
        (PENDING, _('En attente')),
        (APPROVED, _('Approuvé')),
        (REJECTED, _('Rejeté')),
    ]


class ModificationRequestStatus:
    """Profile modification request states."""
    PENDING = 'pending'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (PENDING, _('En attente')),
        (COMPLETED, _('Complété')),
        (CANCELLED, _('Annulé')),
    ]


# ─── New constants for TODO implementations ───────────────────────────────────


class PledgeStatus:
    """Pledge/commitment tracking states."""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    PAUSED = 'paused'

    CHOICES = [
        (ACTIVE, _('Actif')),
        (COMPLETED, _('Complété')),
        (CANCELLED, _('Annulé')),
        (PAUSED, _('En pause')),
    ]


class PledgeFrequency:
    """Pledge payment frequency."""
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    ANNUALLY = 'annually'
    ONE_TIME = 'one_time'

    CHOICES = [
        (WEEKLY, _('Hebdomadaire')),
        (BIWEEKLY, _('Aux deux semaines')),
        (MONTHLY, _('Mensuel')),
        (QUARTERLY, _('Trimestriel')),
        (ANNUALLY, _('Annuel')),
        (ONE_TIME, _('Unique')),
    ]


class CareType:
    """Pastoral care visit types."""
    HOSPITAL_VISIT = 'hospital_visit'
    HOME_VISIT = 'home_visit'
    PHONE_CALL = 'phone_call'
    COUNSELING = 'counseling'
    PRAYER_MEETING = 'prayer_meeting'
    OTHER = 'other'

    CHOICES = [
        (HOSPITAL_VISIT, _('Visite à l\'hôpital')),
        (HOME_VISIT, _('Visite à domicile')),
        (PHONE_CALL, _('Appel téléphonique')),
        (COUNSELING, _('Counseling')),
        (PRAYER_MEETING, _('Rencontre de prière')),
        (OTHER, _('Autre')),
    ]


class CareStatus:
    """Pastoral care case states."""
    OPEN = 'open'
    FOLLOW_UP = 'follow_up'
    CLOSED = 'closed'

    CHOICES = [
        (OPEN, _('Ouvert')),
        (FOLLOW_UP, _('Suivi')),
        (CLOSED, _('Fermé')),
    ]


class PrayerRequestStatus:
    """Prayer request lifecycle states."""
    ACTIVE = 'active'
    ANSWERED = 'answered'
    CLOSED = 'closed'

    CHOICES = [
        (ACTIVE, _('Active')),
        (ANSWERED, _('Exaucée')),
        (CLOSED, _('Fermée')),
    ]


class BackgroundCheckStatus:
    """Background check verification states."""
    NOT_REQUIRED = 'not_required'
    PENDING = 'pending'
    APPROVED = 'approved'
    EXPIRED = 'expired'
    FAILED = 'failed'

    CHOICES = [
        (NOT_REQUIRED, _('Non requis')),
        (PENDING, _('En attente')),
        (APPROVED, _('Approuvé')),
        (EXPIRED, _('Expiré')),
        (FAILED, _('Échoué')),
    ]


class GroupLifecycleStage:
    """Small group lifecycle stages."""
    LAUNCHING = 'launching'
    ACTIVE = 'active'
    MULTIPLYING = 'multiplying'
    CLOSED = 'closed'

    CHOICES = [
        (LAUNCHING, _('En lancement')),
        (ACTIVE, _('Actif')),
        (MULTIPLYING, _('En multiplication')),
        (CLOSED, _('Fermé')),
    ]


class DocumentStatus:
    """Digital document signing states."""
    PENDING = 'pending'
    SIGNED = 'signed'
    EXPIRED = 'expired'

    CHOICES = [
        (PENDING, _('En attente')),
        (SIGNED, _('Signé')),
        (EXPIRED, _('Expiré')),
    ]


class BenevolenceStatus:
    """Benevolence fund request states."""
    SUBMITTED = 'submitted'
    REVIEWING = 'reviewing'
    APPROVED = 'approved'
    DENIED = 'denied'
    DISBURSED = 'disbursed'

    CHOICES = [
        (SUBMITTED, _('Soumise')),
        (REVIEWING, _('En révision')),
        (APPROVED, _('Approuvée')),
        (DENIED, _('Refusée')),
        (DISBURSED, _('Déboursée')),
    ]


class MealTrainStatus:
    """Meal train coordination states."""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (ACTIVE, _('Actif')),
        (COMPLETED, _('Complété')),
        (CANCELLED, _('Annulé')),
    ]


class SermonStatus:
    """Sermon publication states."""
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

    CHOICES = [
        (DRAFT, _('Brouillon')),
        (PUBLISHED, _('Publié')),
        (ARCHIVED, _('Archivé')),
    ]


class SongKey:
    """Musical key options for songs."""
    C = 'C'
    C_SHARP = 'C#'
    D = 'D'
    D_SHARP = 'D#'
    E = 'E'
    F = 'F'
    F_SHARP = 'F#'
    G = 'G'
    G_SHARP = 'G#'
    A = 'A'
    A_SHARP = 'A#'
    B = 'B'

    CHOICES = [
        (C, 'C'), (C_SHARP, 'C#'), (D, 'D'), (D_SHARP, 'D#'),
        (E, 'E'), (F, 'F'), (F_SHARP, 'F#'), (G, 'G'),
        (G_SHARP, 'G#'), (A, 'A'), (A_SHARP, 'A#'), (B, 'B'),
    ]


class SwapRequestStatus:
    """Volunteer swap request states."""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    CHOICES = [
        (PENDING, _('En attente')),
        (APPROVED, _('Approuvé')),
        (REJECTED, _('Rejeté')),
    ]


class RecurrenceFrequency:
    """Event recurrence frequency."""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'

    CHOICES = [
        (DAILY, _('Quotidien')),
        (WEEKLY, _('Hebdomadaire')),
        (BIWEEKLY, _('Aux deux semaines')),
        (MONTHLY, _('Mensuel')),
        (YEARLY, _('Annuel')),
    ]


class BookingStatus:
    """Room booking status."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'

    CHOICES = [
        (PENDING, _('En attente')),
        (CONFIRMED, _('Confirmée')),
        (CANCELLED, _('Annulée')),
        (REJECTED, _('Rejetée')),
    ]


class VolunteerSignupStatus:
    """Event volunteer signup status."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (PENDING, _('En attente')),
        (CONFIRMED, _('Confirmé')),
        (CANCELLED, _('Annulé')),
    ]


class VirtualPlatform:
    """Virtual event platform options."""
    ZOOM = 'zoom'
    GOOGLE_MEET = 'google_meet'
    TEAMS = 'teams'
    YOUTUBE = 'youtube'
    FACEBOOK = 'facebook'
    OTHER = 'other'

    CHOICES = [
        (ZOOM, _('Zoom')),
        (GOOGLE_MEET, _('Google Meet')),
        (TEAMS, _('Microsoft Teams')),
        (YOUTUBE, _('YouTube Live')),
        (FACEBOOK, _('Facebook Live')),
        (OTHER, _('Autre')),
    ]


class AutomationTrigger:
    """Communication automation trigger types."""
    MEMBER_CREATED = 'member_created'
    FIRST_VISIT = 'first_visit'
    BIRTHDAY = 'birthday'
    ANNIVERSARY = 'anniversary'
    DONATION_RECEIVED = 'donation_received'
    EVENT_RSVP = 'event_rsvp'
    CUSTOM = 'custom'

    CHOICES = [
        (MEMBER_CREATED, _('Nouveau membre créé')),
        (FIRST_VISIT, _('Première visite')),
        (BIRTHDAY, _('Anniversaire')),
        (ANNIVERSARY, _('Anniversaire d\'adhésion')),
        (DONATION_RECEIVED, _('Don reçu')),
        (EVENT_RSVP, _('Inscription événement')),
        (CUSTOM, _('Personnalisé')),
    ]


class ReportFrequency:
    """Scheduled report frequency."""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'

    CHOICES = [
        (DAILY, _('Quotidien')),
        (WEEKLY, _('Hebdomadaire')),
        (MONTHLY, _('Mensuel')),
        (QUARTERLY, _('Trimestriel')),
    ]


class ReportType:
    """Available report types for scheduled and saved reports."""
    MEMBER_STATS = 'member_stats'
    DONATION_SUMMARY = 'donation_summary'
    EVENT_ATTENDANCE = 'event_attendance'
    VOLUNTEER_HOURS = 'volunteer_hours'
    HELP_REQUESTS = 'help_requests'
    COMMUNICATION = 'communication'
    CUSTOM = 'custom'

    CHOICES = [
        (MEMBER_STATS, _('Statistiques des membres')),
        (DONATION_SUMMARY, _('Sommaire des dons')),
        (EVENT_ATTENDANCE, _('Presence aux evenements')),
        (VOLUNTEER_HOURS, _('Heures de benevolat')),
        (HELP_REQUESTS, _('Demandes d\'aide')),
        (COMMUNICATION, _('Communications')),
        (CUSTOM, _('Personnalise')),
    ]


class PaymentPlanStatus:
    """Payment plan lifecycle states."""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    DEFAULTED = 'defaulted'
    CANCELLED = 'cancelled'

    CHOICES = [
        (ACTIVE, _('Actif')),
        (COMPLETED, _('Complété')),
        (DEFAULTED, _('En défaut')),
        (CANCELLED, _('Annulé')),
    ]


class CustomFieldType:
    """Custom field data types for church-configurable forms."""
    TEXT = 'text'
    TEXTAREA = 'textarea'
    NUMBER = 'number'
    DATE = 'date'
    DROPDOWN = 'dropdown'
    CHECKBOX = 'checkbox'
    FILE = 'file'

    CHOICES = [
        (TEXT, _('Texte court')),
        (TEXTAREA, _('Texte long')),
        (NUMBER, _('Nombre')),
        (DATE, _('Date')),
        (DROPDOWN, _('Liste déroulante')),
        (CHECKBOX, _('Case à cocher')),
        (FILE, _('Fichier')),
    ]


class OnboardingTrack:
    """Multi-track onboarding paths."""
    NEW_BELIEVER = 'new_believer'
    TRANSFER = 'transfer'
    YOUTH = 'youth'
    FAMILY = 'family'
    DEFAULT = 'default'

    CHOICES = [
        (NEW_BELIEVER, _('Nouveau croyant')),
        (TRANSFER, _('Transfert d\'église')),
        (YOUTH, _('Jeunesse')),
        (FAMILY, _('Famille')),
        (DEFAULT, _('Standard')),
    ]


class SMSStatus:
    """SMS delivery states."""
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    UNDELIVERED = 'undelivered'

    CHOICES = [
        (PENDING, _('En attente')),
        (SENT, _('Envoyé')),
        (DELIVERED, _('Livré')),
        (FAILED, _('Échec')),
        (UNDELIVERED, _('Non livré')),
    ]


class ABTestStatus:
    """A/B test lifecycle states."""
    DRAFT = 'draft'
    RUNNING = 'running'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (DRAFT, _('Brouillon')),
        (RUNNING, _('En cours')),
        (COMPLETED, _('Terminé')),
        (CANCELLED, _('Annulé')),
    ]


class AutomationStepChannel:
    """Channel for an automation step."""
    EMAIL = 'email'
    SMS = 'sms'
    PUSH = 'push'
    IN_APP = 'in_app'

    CHOICES = [
        (EMAIL, _('Courriel')),
        (SMS, _('SMS')),
        (PUSH, _('Notification push')),
        (IN_APP, _('Notification in-app')),
    ]


class AutomationStatus:
    """Automation enrollment states."""
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (ACTIVE, _('Actif')),
        (PAUSED, _('En pause')),
        (COMPLETED, _('Complété')),
        (CANCELLED, _('Annulé')),
    ]


class EmailTemplateCategory:
    """Email template categories."""
    WELCOME = 'welcome'
    EVENT_REMINDER = 'event_reminder'
    BIRTHDAY = 'birthday'
    GIVING_RECEIPT = 'giving_receipt'
    FOLLOW_UP = 'follow_up'
    GENERAL = 'general'

    CHOICES = [
        (WELCOME, _('Bienvenue')),
        (EVENT_REMINDER, _('Rappel d\'événement')),
        (BIRTHDAY, _('Anniversaire')),
        (GIVING_RECEIPT, _('Reçu de don')),
        (FOLLOW_UP, _('Suivi')),
        (GENERAL, _('Général')),
    ]


class SkillProficiency:
    """Volunteer skill proficiency levels."""
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'

    CHOICES = [
        (BEGINNER, _('Débutant')),
        (INTERMEDIATE, _('Intermédiaire')),
        (ADVANCED, _('Avancé')),
        (EXPERT, _('Expert')),
    ]


class MilestoneType:
    """Volunteer milestone trigger types."""
    HOURS = 'hours'
    YEARS = 'years'

    CHOICES = [
        (HOURS, _('Heures de service')),
        (YEARS, _('Années de service')),
    ]


class DayOfWeek:
    """Days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    CHOICES = [
        (MONDAY, _('Lundi')),
        (TUESDAY, _('Mardi')),
        (WEDNESDAY, _('Mercredi')),
        (THURSDAY, _('Jeudi')),
        (FRIDAY, _('Vendredi')),
        (SATURDAY, _('Samedi')),
        (SUNDAY, _('Dimanche')),
    ]


class MentorAssignmentStatus:
    """Mentor/buddy assignment states."""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (ACTIVE, _('Actif')),
        (COMPLETED, _('Complété')),
        (CANCELLED, _('Annulé')),
    ]


class WelcomeStepChannel:
    """Welcome sequence step delivery channel."""
    EMAIL = 'email'
    SMS = 'sms'
    BOTH = 'both'

    CHOICES = [
        (EMAIL, _('Courriel')),
        (SMS, _('SMS')),
        (BOTH, _('Courriel et SMS')),
    ]


class DocumentType:
    """Onboarding document types."""
    COVENANT = 'covenant'
    POLICY = 'policy'
    CONSENT = 'consent'
    WAIVER = 'waiver'
    OTHER = 'other'

    CHOICES = [
        (COVENANT, _('Alliance')),
        (POLICY, _('Politique')),
        (CONSENT, _('Consentement')),
        (WAIVER, _('Décharge')),
        (OTHER, _('Autre')),
    ]


class AchievementTrigger:
    """Gamification achievement trigger types."""
    FORM_SUBMITTED = 'form_submitted'
    TRAINING_STARTED = 'training_started'
    LESSON_COMPLETED = 'lesson_completed'
    TRAINING_COMPLETED = 'training_completed'
    INTERVIEW_PASSED = 'interview_passed'
    BECAME_ACTIVE = 'became_active'
    FIRST_ATTENDANCE = 'first_attendance'
    MENTOR_ASSIGNED = 'mentor_assigned'
    DOCUMENT_SIGNED = 'document_signed'
    CUSTOM = 'custom'

    CHOICES = [
        (FORM_SUBMITTED, _('Formulaire soumis')),
        (TRAINING_STARTED, _('Formation commencée')),
        (LESSON_COMPLETED, _('Leçon complétée')),
        (TRAINING_COMPLETED, _('Formation complétée')),
        (INTERVIEW_PASSED, _('Interview réussie')),
        (BECAME_ACTIVE, _('Devenu membre actif')),
        (FIRST_ATTENDANCE, _('Première présence')),
        (MENTOR_ASSIGNED, _('Mentor assigné')),
        (DOCUMENT_SIGNED, _('Document signé')),
        (CUSTOM, _('Personnalisé')),
    ]


class VisitorFollowUpStatus:
    """Visitor follow-up assignment states."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (PENDING, _('En attente')),
        (IN_PROGRESS, _('En cours')),
        (COMPLETED, _('Complété')),
        (CANCELLED, _('Annulé')),
    ]


class SongRequestStatus:
    """Song request lifecycle states."""
    PENDING = 'pending'
    APPROVED = 'approved'
    DECLINED = 'declined'
    SCHEDULED = 'scheduled'

    CHOICES = [
        (PENDING, _('En attente')),
        (APPROVED, _('Approuvée')),
        (DECLINED, _('Refusée')),
        (SCHEDULED, _('Planifiée')),
    ]


class LiveStreamPlatform:
    """Live streaming platform choices."""
    YOUTUBE = 'youtube'
    FACEBOOK = 'facebook'
    OTHER = 'other'

    CHOICES = [
        (YOUTUBE, _('YouTube Live')),
        (FACEBOOK, _('Facebook Live')),
        (OTHER, _('Autre')),
    ]


class RehearsalAttendeeStatus:
    """Rehearsal RSVP states."""
    INVITED = 'invited'
    CONFIRMED = 'confirmed'
    DECLINED = 'declined'

    CHOICES = [
        (INVITED, _('Invité')),
        (CONFIRMED, _('Confirmé')),
        (DECLINED, _('Décliné')),
    ]
