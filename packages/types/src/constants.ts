/** TypeScript mirror of apps/core/constants.py */

// ─── Member Roles ────────────────────────────────────────────────────────────

export const Roles = {
  MEMBER: 'member',
  VOLUNTEER: 'volunteer',
  GROUP_LEADER: 'group_leader',
  DEACON: 'deacon',
  PASTOR: 'pastor',
  TREASURER: 'treasurer',
  ADMIN: 'admin',
} as const;
export type Role = (typeof Roles)[keyof typeof Roles];

export const ROLE_LABELS: Record<Role, string> = {
  member: 'Membre',
  volunteer: 'Volontaire',
  group_leader: 'Leader de groupe',
  deacon: 'Diacre',
  pastor: 'Pasteur',
  treasurer: 'Trésorier',
  admin: 'Administrateur',
};

export const STAFF_ROLES: Role[] = [Roles.DEACON, Roles.PASTOR, Roles.ADMIN];
export const VIEW_ALL_ROLES: Role[] = [Roles.DEACON, Roles.PASTOR, Roles.TREASURER, Roles.ADMIN];
export const FINANCE_ROLES: Role[] = [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN];
export const LEADERSHIP_ROLES: Role[] = [Roles.DEACON, Roles.PASTOR, Roles.ADMIN];
export const ROLE_HIERARCHY: Role[] = [
  Roles.MEMBER, Roles.VOLUNTEER, Roles.GROUP_LEADER,
  Roles.DEACON, Roles.TREASURER, Roles.PASTOR, Roles.ADMIN,
];

// ─── Membership Status ──────────────────────────────────────────────────────

export const MembershipStatus = {
  REGISTERED: 'registered',
  FORM_PENDING: 'form_pending',
  FORM_SUBMITTED: 'form_submitted',
  IN_REVIEW: 'in_review',
  APPROVED: 'approved',
  IN_TRAINING: 'in_training',
  INTERVIEW_SCHEDULED: 'interview_scheduled',
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  SUSPENDED: 'suspended',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
} as const;
export type MembershipStatusType = (typeof MembershipStatus)[keyof typeof MembershipStatus];

export const MEMBERSHIP_STATUS_LABELS: Record<MembershipStatusType, string> = {
  registered: 'Inscrit',
  form_pending: 'Formulaire en attente',
  form_submitted: 'Formulaire soumis',
  in_review: 'En cours de révision',
  approved: 'Approuvé',
  in_training: 'En formation',
  interview_scheduled: 'Interview planifiée',
  active: 'Membre actif',
  inactive: 'Inactif',
  suspended: 'Suspendu',
  rejected: 'Refusé',
  expired: 'Expiré',
};

// ─── Family Status ───────────────────────────────────────────────────────────

export const FamilyStatus = {
  SINGLE: 'single',
  MARRIED: 'married',
  WIDOWED: 'widowed',
  DIVORCED: 'divorced',
} as const;
export type FamilyStatusType = (typeof FamilyStatus)[keyof typeof FamilyStatus];

// ─── Group Type ──────────────────────────────────────────────────────────────

export const GroupType = {
  CELL: 'cell',
  MINISTRY: 'ministry',
  COMMITTEE: 'committee',
  CLASS: 'class',
  CHOIR: 'choir',
  OTHER: 'other',
} as const;
export type GroupTypeValue = (typeof GroupType)[keyof typeof GroupType];

// ─── Privacy Level ───────────────────────────────────────────────────────────

export const PrivacyLevel = {
  PUBLIC: 'public',
  GROUP: 'group',
  PRIVATE: 'private',
} as const;
export type PrivacyLevelType = (typeof PrivacyLevel)[keyof typeof PrivacyLevel];

// ─── Donation Type ───────────────────────────────────────────────────────────

export const DonationType = {
  TITHE: 'tithe',
  OFFERING: 'offering',
  SPECIAL: 'special',
  CAMPAIGN: 'campaign',
  BUILDING: 'building',
  MISSIONS: 'missions',
  OTHER: 'other',
} as const;
export type DonationTypeValue = (typeof DonationType)[keyof typeof DonationType];

export const DONATION_TYPE_LABELS: Record<DonationTypeValue, string> = {
  tithe: 'Dîme',
  offering: 'Offrande générale',
  special: 'Offrande spéciale',
  campaign: 'Campagne',
  building: 'Bâtiment',
  missions: 'Missions',
  other: 'Autre',
};

// ─── Payment Method ──────────────────────────────────────────────────────────

export const PaymentMethod = {
  CASH: 'cash',
  CHECK: 'check',
  CARD: 'card',
  BANK_TRANSFER: 'bank_transfer',
  ONLINE: 'online',
  OTHER: 'other',
} as const;
export type PaymentMethodType = (typeof PaymentMethod)[keyof typeof PaymentMethod];

// ─── Event Type ──────────────────────────────────────────────────────────────

export const EventType = {
  WORSHIP: 'worship',
  GROUP: 'group',
  MEAL: 'meal',
  SPECIAL: 'special',
  MEETING: 'meeting',
  TRAINING: 'training',
  OUTREACH: 'outreach',
  OTHER: 'other',
} as const;
export type EventTypeValue = (typeof EventType)[keyof typeof EventType];

// ─── RSVP Status ─────────────────────────────────────────────────────────────

export const RSVPStatus = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  DECLINED: 'declined',
  MAYBE: 'maybe',
} as const;
export type RSVPStatusType = (typeof RSVPStatus)[keyof typeof RSVPStatus];

// ─── Volunteer Role ──────────────────────────────────────────────────────────

export const VolunteerRole = {
  WORSHIP: 'worship',
  HOSPITALITY: 'hospitality',
  TECHNICAL: 'technical',
  CHILDREN: 'children',
  YOUTH: 'youth',
  ADMIN: 'admin',
  OUTREACH: 'outreach',
  OTHER: 'other',
} as const;
export type VolunteerRoleType = (typeof VolunteerRole)[keyof typeof VolunteerRole];

// ─── Help Request ────────────────────────────────────────────────────────────

export const HelpRequestCategory = {
  PRAYER: 'prayer',
  FINANCIAL: 'financial',
  MATERIAL: 'material',
  PASTORAL: 'pastoral',
  TRANSPORT: 'transport',
  MEDICAL: 'medical',
  OTHER: 'other',
} as const;
export type HelpRequestCategoryType = (typeof HelpRequestCategory)[keyof typeof HelpRequestCategory];

export const HelpRequestUrgency = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
} as const;
export type HelpRequestUrgencyType = (typeof HelpRequestUrgency)[keyof typeof HelpRequestUrgency];

export const HelpRequestStatus = {
  NEW: 'new',
  IN_PROGRESS: 'in_progress',
  RESOLVED: 'resolved',
  CLOSED: 'closed',
} as const;
export type HelpRequestStatusType = (typeof HelpRequestStatus)[keyof typeof HelpRequestStatus];

// ─── Newsletter ──────────────────────────────────────────────────────────────

export const NewsletterStatus = {
  DRAFT: 'draft',
  SCHEDULED: 'scheduled',
  SENDING: 'sending',
  SENT: 'sent',
  FAILED: 'failed',
} as const;
export type NewsletterStatusType = (typeof NewsletterStatus)[keyof typeof NewsletterStatus];

// ─── Attendance ──────────────────────────────────────────────────────────────

export const AttendanceSessionType = {
  WORSHIP: 'worship',
  EVENT: 'event',
  LESSON: 'lesson',
  OTHER: 'other',
} as const;
export type AttendanceSessionTypeValue = (typeof AttendanceSessionType)[keyof typeof AttendanceSessionType];

export const CheckInMethod = {
  QR_SCAN: 'qr_scan',
  MANUAL: 'manual',
  NFC: 'nfc',
  KIOSK: 'kiosk',
  GEO: 'geo',
} as const;
export type CheckInMethodType = (typeof CheckInMethod)[keyof typeof CheckInMethod];

// ─── Worship ─────────────────────────────────────────────────────────────────

export const WorshipServiceStatus = {
  DRAFT: 'draft',
  PLANNED: 'planned',
  CONFIRMED: 'confirmed',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const;
export type WorshipServiceStatusType = (typeof WorshipServiceStatus)[keyof typeof WorshipServiceStatus];

export const SermonStatus = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  ARCHIVED: 'archived',
} as const;
export type SermonStatusType = (typeof SermonStatus)[keyof typeof SermonStatus];

// ─── Province ────────────────────────────────────────────────────────────────

export const Province = {
  AB: 'AB', BC: 'BC', MB: 'MB', NB: 'NB', NL: 'NL', NS: 'NS',
  NT: 'NT', NU: 'NU', ON: 'ON', PE: 'PE', QC: 'QC', SK: 'SK', YT: 'YT',
} as const;
export type ProvinceType = (typeof Province)[keyof typeof Province];

export const PROVINCE_LABELS: Record<ProvinceType, string> = {
  AB: 'Alberta', BC: 'Colombie-Britannique', MB: 'Manitoba',
  NB: 'Nouveau-Brunswick', NL: 'Terre-Neuve-et-Labrador', NS: 'Nouvelle-Écosse',
  NT: 'Territoires du Nord-Ouest', NU: 'Nunavut', ON: 'Ontario',
  PE: 'Île-du-Prince-Édouard', QC: 'Québec', SK: 'Saskatchewan', YT: 'Yukon',
};
