# Core App

## Overview

The core app provides the foundational infrastructure for the entire EgliseConnect system. It contains no user-facing features itself, but defines the abstract base models, constants, permissions, mixins, validators, utilities, middleware, and audit logging that every other app depends on.

### Key Features

- **Base Models**: UUID primary keys, timestamps, `is_active` flag, and soft-delete pattern used by all models
- **Constants**: 25+ constant classes defining roles, statuses, and types for the entire system
- **Permissions**: 10 DRF permission classes with role hierarchy (member → volunteer → group leader → deacon → treasurer → pastor → admin)
- **Mixins**: 12 view/form mixins for access control, context injection, form styling, and query filtering
- **Validators**: Image (5MB, JPEG/PNG/GIF/WebP) and PDF (10MB) file upload validation
- **CSV Export**: Generic queryset-to-CSV and list-to-CSV utilities with Excel UTF-8 BOM support
- **Reminder System**: Generic 5d/3d/1d/same-day notification sender used by onboarding, volunteers, and worship
- **Middleware**: 2FA enforcement and membership-based access control
- **Audit Logging**: Login attempt tracking with IP, user agent, method, and success/failure
- **PWA Support**: Service worker, manifest, and offline fallback page

## File Structure

```
apps/core/
├── __init__.py
├── admin.py                  # LoginAudit admin registration
├── allauth_forms.py          # Custom allauth signup form (with invitation code)
├── apps.py                   # App config
├── audit.py                  # LoginAudit model
├── breadcrumbs.py            # Breadcrumb helper utilities
├── constants.py              # 25+ constant classes (Roles, Statuses, Types)
├── export.py                 # CSV export utilities
├── middleware.py              # TwoFactorEnforcementMiddleware, MembershipAccessMiddleware
├── mixins.py                 # 12 view/form mixins
├── models.py                 # BaseModel, SoftDeleteModel, TimeStampedMixin, OrderedMixin
├── permissions.py             # 10 DRF permission classes + 3 helper functions
├── reminders.py               # Generic send_reminder_batch() utility
├── serializers_audit.py       # LoginAudit DRF serializer
├── signals.py                 # Signal handlers
├── utils.py                   # Utility functions (birthday lookups, etc.)
├── validators.py              # File upload validators (image, PDF)
├── views_audit.py             # LoginAuditViewSet (API)
├── views_frontend_audit.py    # Login audit list, 2FA status (frontend)
├── views_frontend_search.py   # Global search view
├── views_pwa.py               # Service worker, manifest, offline page
└── tests/
    ├── test_permissions.py
    ├── test_permissions_extended.py
    ├── test_allauth_templates.py
    └── test_reminders.py
```

## Models

### BaseModel (Abstract)

Foundation for all models in the system. Provides UUID primary keys, timestamps, and active/inactive state.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Auto-generated UUID primary key |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |
| `is_active` | BooleanField | Active flag (default: True) |

**Managers:**
- `objects` → `ActiveManager`: Returns only `is_active=True` records (default)
- `all_objects` → `AllObjectsManager`: Returns all records including inactive

**Methods:**
- `deactivate()`: Sets `is_active=False`
- `activate()`: Sets `is_active=True`

### SoftDeleteModel (Abstract)

Extends BaseModel with soft-delete support. Records are marked as deleted rather than removed from the database.

| Field | Type | Description |
|-------|------|-------------|
| `deleted_at` | DateTimeField | Timestamp of soft deletion (nullable) |

**Managers:**
- `objects` → `SoftDeleteManager`: Returns only non-deleted records
- `all_objects` → `AllObjectsManager`: Returns all records including deleted

**Properties:**
- `is_deleted` → `bool`: Whether the record has been soft-deleted

**Methods:**
- `delete()`: Soft delete (sets `deleted_at`, marks `is_active=False`)
- `restore()`: Restores a soft-deleted record
- `hard_delete()`: Permanently removes from database

### TimeStampedMixin (Abstract)

Lightweight mixin with only `created_at` and `updated_at` timestamps (no UUID, no `is_active`).

### OrderedMixin (Abstract)

Adds manual ordering via a `PositiveIntegerField` named `order`. Default ordering: `['order']`.

### LoginAudit

Login attempt tracking for security monitoring. Located in `apps/core/audit.py`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `user` | ForeignKey → User | The user who attempted login (nullable) |
| `email_attempted` | EmailField | Email address used |
| `ip_address` | GenericIPAddressField | Client IP address |
| `user_agent` | TextField | Browser user agent string |
| `success` | BooleanField | Whether login succeeded |
| `failure_reason` | CharField(100) | Reason for failure (optional) |
| `method` | CharField(30) | `password`, `totp`, `social`, or `code` |

**Indexes:** `[user, -created_at]`, `[-created_at]`, `[ip_address]`

## Constants

All defined in `apps/core/constants.py`. Each class provides a `CHOICES` list for Django model fields.

### Role System

| Class | Values |
|-------|--------|
| `Roles` | `member`, `volunteer`, `group_leader`, `deacon`, `pastor`, `treasurer`, `admin` |

Groups: `STAFF_ROLES`, `VIEW_ALL_ROLES`, `FINANCE_ROLES`, `LEADERSHIP_ROLES`, `HIERARCHY`

### Status & Type Classes

| Class | Values |
|-------|--------|
| `MembershipStatus` | `registered`, `form_pending`, `form_submitted`, `in_review`, `approved`, `in_training`, `interview_scheduled`, `active`, `inactive`, `suspended`, `rejected`, `expired` |
| `FamilyStatus` | `single`, `married`, `widowed`, `divorced` |
| `Province` | All 13 Canadian provinces/territories |
| `DepartmentRole` | `member`, `leader`, `assistant` |
| `DisciplinaryType` | `punishment`, `exemption`, `suspension` |
| `ApprovalStatus` | `pending`, `approved`, `rejected` |
| `ModificationRequestStatus` | `pending`, `completed`, `cancelled` |
| `DonationType` | `tithe`, `offering`, `special`, `campaign`, `building`, `missions`, `other` |
| `PaymentMethod` | `cash`, `check`, `card`, `bank_transfer`, `online`, `other` |
| `EventType` | `worship`, `group`, `meal`, `special`, `meeting`, `training`, `outreach`, `other` |
| `RSVPStatus` | `pending`, `confirmed`, `declined`, `maybe` |
| `GroupType` | `cell`, `ministry`, `committee`, `class`, `choir`, `other` |
| `PrivacyLevel` | `public`, `group`, `private` |
| `VolunteerRole` | `worship`, `hospitality`, `technical`, `children`, `youth`, `admin`, `outreach`, `other` |
| `ScheduleStatus` | `scheduled`, `confirmed`, `declined`, `completed`, `no_show` |
| `VolunteerFrequency` | `weekly`, `biweekly`, `monthly`, `occasional` |
| `HelpRequestCategory` | `prayer`, `financial`, `material`, `pastoral`, `transport`, `medical`, `other` |
| `HelpRequestUrgency` | `low`, `medium`, `high`, `urgent` |
| `HelpRequestStatus` | `new`, `in_progress`, `resolved`, `closed` |
| `NewsletterStatus` | `draft`, `scheduled`, `sending`, `sent`, `failed` |
| `NotificationType` | `birthday`, `event`, `volunteer`, `help_request`, `donation`, `general` |
| `InterviewStatus` | `proposed`, `accepted`, `counter`, `confirmed`, `passed`, `failed`, `no_show`, `cancelled` |
| `LessonStatus` | `upcoming`, `completed`, `absent`, `makeup` |
| `AttendanceSessionType` | `worship`, `event`, `lesson`, `other` |
| `CheckInMethod` | `qr_scan`, `manual` |
| `WorshipServiceStatus` | `draft`, `planned`, `confirmed`, `completed`, `cancelled` |
| `ServiceSectionType` | `prelude`, `annonces`, `louange`, `offrande`, `predication`, `communion`, `priere`, `benediction`, `other` |
| `AssignmentStatus` | `assigned`, `confirmed`, `declined` |

## Permissions (DRF)

10 permission classes in `apps/core/permissions.py`:

| Class | Access Level | Description |
|-------|-------------|-------------|
| `IsMember` | Any authenticated | Basic access |
| `IsVolunteer` | Volunteer+ | Volunteer role or higher |
| `IsGroupLeader` | Group Leader+ | Group leader or higher |
| `IsDeacon` | Deacon+ | Deacon, pastor, or admin |
| `IsPastor` | Pastor+ | Pastor or admin |
| `IsTreasurer` | Treasurer+ | Treasurer, pastor, or admin |
| `IsAdmin` | Admin | Admin, pastor, or superuser |
| `IsPastorOrAdmin` | Staff | Any staff role |
| `IsFinanceStaff` | Finance | Finance roles or delegated access |
| `IsOwnerOrStaff` | Object-level | Object owner or staff member |
| `IsOwnerOrReadOnly` | Object-level | Owner writes, others read |
| `CanViewMember` | Object-level | Privacy-aware member viewing |

**Helper functions:** `get_user_role(user)`, `is_staff_member(user)`, `can_manage_finances(user)`

## Mixins

12 mixins in `apps/core/mixins.py`:

### Access Control Mixins

| Mixin | Required Role |
|-------|--------------|
| `MemberRequiredMixin` | Any member profile |
| `VolunteerRequiredMixin` | Volunteer+ |
| `GroupLeaderRequiredMixin` | Group Leader+ |
| `PastorRequiredMixin` | Pastor+ |
| `TreasurerRequiredMixin` | Treasurer+ |
| `AdminRequiredMixin` | Admin/superuser |
| `FinanceStaffRequiredMixin` | Finance roles |
| `OwnerOrStaffRequiredMixin` | Object owner or staff |

### Context & Form Mixins

| Mixin | Description |
|-------|-------------|
| `ChurchContextMixin` | Adds `current_user_role`, `current_member`, `today_birthdays` |
| `PageTitleMixin` | Adds `page_title` to context |
| `BreadcrumbMixin` | Adds breadcrumb trail `[(label, url), ...]` |
| `FormMessageMixin` | Success/error messages on form submission |
| `SetOwnerMixin` | Auto-sets `member`/`user`/`created_by` on save |
| `FilterByMemberMixin` | Filters queryset to current user (staff see all) |
| `W3CRMFormMixin` | Auto-applies Bootstrap CSS classes to all form widgets |

## Validators

| Function | Allowed Types | Max Size |
|----------|--------------|----------|
| `validate_image_file` | JPEG, PNG, GIF, WebP | 5 MB |
| `validate_pdf_file` | PDF | 10 MB |

## Export Utilities

| Function | Description |
|----------|-------------|
| `export_queryset_csv(queryset, fields, filename, headers)` | Export queryset to CSV with choice field display support |
| `export_list_csv(data, headers, filename)` | Export list of dicts to CSV |

Both include UTF-8 BOM for Excel compatibility.

## Reminder System

`send_reminder_batch(items, get_date, get_member, make_message, link)`:
- Checks `reminder_5days_sent`, `reminder_3days_sent`, `reminder_1day_sent`, `reminder_sameday_sent` flags
- Creates `Notification` objects at each interval
- Used by: onboarding (lessons, interviews), volunteers (schedules), worship (assignments)

## Middleware

### TwoFactorEnforcementMiddleware
Forces 2FA setup when member's deadline has passed. Redirects to `/accounts/2fa/`. Exempt paths: `/accounts/`, `/api/`, `/static/`, `/media/`, `/admin/`.

### MembershipAccessMiddleware
Restricts non-active members from full dashboard pages (`/donations/`, `/events/`, `/members/`, etc.). Staff roles bypass.

## PWA Support

| View | URL | Description |
|------|-----|-------------|
| `service_worker` | `/sw.js` | Service worker JavaScript |
| `manifest` | `/manifest.json` | PWA manifest (standalone, fr-CA) |
| `offline` | `/offline/` | Offline fallback page |

## Audit Views

**API:** `LoginAuditViewSet` at `/api/v1/audit/login-audits/` (ReadOnly, Pastor/Admin)

**Frontend:**

| URL | View | Description |
|-----|------|-------------|
| `/audit/logins/` | `login_audit_list` | Login history with filters |
| `/audit/logins/2fa-status/` | `two_factor_status` | 2FA enrollment status |

## Dependencies

- **Django**: auth, middleware, forms, signals
- **DRF**: permission classes, ViewSets
- **django-allauth**: custom signup forms, 2FA
- **communication**: Notification model (reminders)
- **donations**: FinanceDelegation (IsFinanceStaff check)

## Tests

- `test_permissions.py` — All permission classes + helper functions
- `test_permissions_extended.py` — Object-level permissions
- `test_allauth_templates.py` — Allauth template rendering
- `test_reminders.py` — Reminder batch with various date scenarios
