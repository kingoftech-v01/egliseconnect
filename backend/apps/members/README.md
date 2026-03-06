# Members App

## Overview

The members app is the core module of EgliseConnect. It manages church member profiles, families, groups (cell groups, ministries, committees), departments, the member directory with privacy controls, birthday tracking, disciplinary actions with an approval workflow, and profile modification requests. Every member receives an auto-generated unique number (e.g., `MBR-2026-0001`) upon registration.

### Key Features

- **Member Profiles** -- Personal information, contact details, photo, church role, join date, baptism date, onboarding status, and 2FA tracking
- **Auto-Generated Member Numbers** -- Format `MBR-YYYY-XXXX`, generated automatically with uniqueness enforcement
- **Families** -- Group members into family units with a shared address
- **Groups** -- Cell groups, ministries, committees, choirs, and classes with designated leaders and meeting schedules
- **Departments** -- Organizational units with hierarchical structure, member enrollment, and custom task types (used by the worship app)
- **Directory** -- Member directory with configurable privacy settings (public, group, private)
- **Birthdays** -- Track and display birthdays by period (today, this week, this month, specific month)
- **Disciplinary Actions** -- Punishment, exemption, and suspension workflow with role-hierarchy enforcement and dual-approval
- **Profile Modification Requests** -- Staff can request members to update their personal information
- **Multiple Roles** -- Members can hold additional roles beyond their primary role
- **CSV Export** -- Export the member list to CSV (pastor/admin only)
- **Superuser Signal** -- Auto-creates an admin Member profile for new Django superusers

## File Structure

```
apps/members/
├── __init__.py
├── admin.py                 # Django admin configuration (5 ModelAdmins, 3 inlines)
├── apps.py                  # App config
├── forms.py                 # 14 forms (all with W3CRMFormMixin)
├── models.py                # 11 models (Member, Family, Group, etc.)
├── serializers.py           # 13 DRF serializers
├── services.py              # DisciplinaryService (business logic)
├── signals.py               # Superuser auto-profile signal
├── urls.py                  # API router + frontend URL patterns
├── views_api.py             # 4 DRF ViewSets
├── views_frontend.py        # 30 frontend views
├── migrations/
│   └── ...
└── tests/
    ├── __init__.py
    ├── factories.py          # Test data factories
    ├── test_models.py        # Model tests
    ├── test_forms.py         # Form tests
    ├── test_serializers.py   # Serializer tests
    ├── test_views_api.py     # API view tests
    ├── test_views_api_extended.py  # Extended API tests
    ├── test_views_frontend.py     # Frontend view tests
    ├── test_disciplinary.py  # Disciplinary service tests
    └── test_profile.py       # Profile and modification request tests

templates/members/
├── member_list.html
├── member_detail.html
├── member_form.html
├── my_profile.html
├── birthday_list.html
├── directory.html
├── privacy_settings.html
├── group_list.html
├── group_detail.html
├── group_form.html
├── group_delete.html
├── group_add_member.html
├── family_list.html
├── family_detail.html
├── family_form.html
├── family_delete.html
├── department_delete.html
├── disciplinary_list.html
├── disciplinary_form.html
├── disciplinary_detail.html
├── request_modification.html
└── modification_request_list.html

templates/departments/
├── department_list.html
├── department_detail.html
├── department_form.html
├── department_add_member.html
└── department_task_types.html
```

## Models

### Member

The primary model of the application. Inherits from `SoftDeleteModel` (logical deletion with restore capability).

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key (from BaseModel) |
| `user` | OneToOneField -> User | No | NULL | Optional link to Django user for authentication |
| `member_number` | CharField(20) | Auto | -- | Auto-generated unique number (`MBR-YYYY-XXXX`), not editable |
| `first_name` | CharField(100) | Yes | -- | First name |
| `last_name` | CharField(100) | Yes | -- | Last name |
| `email` | EmailField | No | blank | Email address |
| `phone` | CharField(20) | No | blank | Primary phone number |
| `phone_secondary` | CharField(20) | No | blank | Secondary phone number |
| `birth_date` | DateField | No | NULL | Date of birth (for birthday tracking) |
| `address` | TextField | No | blank | Street address |
| `city` | CharField(100) | No | blank | City |
| `province` | CharField(2) | Yes | `QC` | Canadian province (choices from `Province.CHOICES`) |
| `postal_code` | CharField(10) | No | blank | Postal code |
| `photo` | ImageField | No | NULL | Profile photo, uploaded to `members/photos/%Y/%m/`, validated by `validate_image_file` |
| `role` | CharField(20) | Yes | `member` | Primary church role (choices from `Roles.CHOICES`) |
| `family_status` | CharField(20) | Yes | `single` | Marital status (choices from `FamilyStatus.CHOICES`) |
| `family` | ForeignKey -> Family | No | NULL | Family unit this member belongs to |
| `joined_date` | DateField | No | NULL | Date the member joined the church |
| `baptism_date` | DateField | No | NULL | Date of baptism |
| `notes` | TextField | No | blank | Pastoral notes (visible only to pastoral staff) |
| `membership_status` | CharField(30) | Yes | `registered` | Onboarding lifecycle status (choices from `MembershipStatus.CHOICES`), indexed |
| `registration_date` | DateTimeField | No | NULL | When the member registered |
| `form_deadline` | DateTimeField | No | NULL | Deadline for onboarding form submission |
| `form_submitted_at` | DateTimeField | No | NULL | When the onboarding form was submitted |
| `admin_reviewed_at` | DateTimeField | No | NULL | When an admin reviewed the submission |
| `admin_reviewed_by` | ForeignKey -> self | No | NULL | Which admin reviewed the submission |
| `became_active_at` | DateTimeField | No | NULL | When the member became fully active |
| `rejection_reason` | TextField | No | blank | Reason for membership rejection |
| `two_factor_enabled` | BooleanField | Yes | `False` | Whether 2FA is enabled |
| `two_factor_deadline` | DateTimeField | No | NULL | Deadline for 2FA setup |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `deleted_at` | DateTimeField | No | NULL | Inherited from SoftDeleteModel |

**Properties:**

| Property | Return Type | Description |
|----------|-------------|-------------|
| `full_name` | `str` | `"first_name last_name"` |
| `full_address` | `str` | Formatted address string (address, city, province, postal code) |
| `age` | `int` or `None` | Calculated from `birth_date` |
| `days_remaining_for_form` | `int` or `None` | Days until onboarding form deadline |
| `is_form_expired` | `bool` | Whether the 30-day form deadline has passed |
| `has_full_access` | `bool` | Whether membership status grants full dashboard access |
| `can_use_qr` | `bool` | Whether membership status allows QR code attendance |
| `is_in_onboarding` | `bool` | Whether member is currently in the onboarding process |
| `is_2fa_overdue` | `bool` | Whether the 2FA setup deadline has passed without enabling |
| `all_roles` | `set` | Union of primary role and all additional `MemberRole` entries |
| `is_staff_member` | `bool` | Whether member has any role in `Roles.STAFF_ROLES` |
| `can_manage_finances` | `bool` | Whether member has any role in `Roles.FINANCE_ROLES` |

**Methods:**

| Method | Return | Description |
|--------|--------|-------------|
| `save()` | -- | Auto-generates `member_number` on first save via `generate_member_number()` |
| `has_role(role)` | `bool` | Check if member has a specific role (primary or additional) |
| `get_groups()` | `QuerySet[Group]` | Returns all active groups the member belongs to |

**Database Indexes:**

| Indexed Fields | Purpose |
|----------------|---------|
| `member_number` | Fast lookup by member number |
| `email` | Search by email |
| `last_name, first_name` | Optimized alphabetical sorting |
| `birth_date` | Birthday queries |
| `role` | Role filtering |

**Meta:** Ordered by `['last_name', 'first_name']`.

---

### Family

Family unit grouping members under a shared address. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `name` | CharField(200) | Yes | -- | Family name (e.g., "Famille Dupont") |
| `address` | TextField | No | blank | Shared street address |
| `city` | CharField(100) | No | blank | City |
| `province` | CharField(2) | Yes | `QC` | Province |
| `postal_code` | CharField(10) | No | blank | Postal code |
| `notes` | TextField | No | blank | Notes |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Properties:**

| Property | Return Type | Description |
|----------|-------------|-------------|
| `member_count` | `int` | Count of active members in this family |
| `full_address` | `str` | Formatted address string |

**Meta:** Ordered by `['name']`.

---

### Group

Church group (cell, ministry, committee, class, choir). Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `name` | CharField(200) | Yes | -- | Group name |
| `group_type` | CharField(20) | Yes | `cell` | Type: `cell`, `ministry`, `committee`, `class`, `choir`, `other` |
| `description` | TextField | No | blank | Group description |
| `leader` | ForeignKey -> Member | No | NULL | Group leader |
| `meeting_day` | CharField(20) | No | blank | Meeting day (e.g., "Wednesday") |
| `meeting_time` | TimeField | No | NULL | Meeting time |
| `meeting_location` | CharField(200) | No | blank | Meeting location |
| `email` | EmailField | No | blank | Group email address |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Properties:**

| Property | Return Type | Description |
|----------|-------------|-------------|
| `member_count` | `int` | Count of active memberships in this group |

**Meta:** Ordered by `['name']`.

---

### GroupMembership

Join table between `Member` and `Group` with role and join date. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `member` | ForeignKey -> Member | Yes | -- | The member (related_name: `group_memberships`) |
| `group` | ForeignKey -> Group | Yes | -- | The group (related_name: `memberships`) |
| `role` | CharField(20) | Yes | `member` | Role in the group: `member`, `leader`, `assistant` |
| `joined_date` | DateField | Auto | auto_now_add | Date joined the group |
| `notes` | TextField | No | blank | Notes |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Constraints:** `unique_together = ['member', 'group']`

**Meta:** Ordered by `['group__name', 'member__last_name']`.

---

### DirectoryPrivacy

Controls what information other members can see in the directory. One-to-one with `Member`. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `member` | OneToOneField -> Member | Yes | -- | The member (related_name: `privacy_settings`) |
| `visibility` | CharField(20) | Yes | `public` | Profile visibility level |
| `show_email` | BooleanField | Yes | `True` | Show email in directory |
| `show_phone` | BooleanField | Yes | `True` | Show phone in directory |
| `show_address` | BooleanField | Yes | `False` | Show address in directory |
| `show_birth_date` | BooleanField | Yes | `True` | Show birth date in directory |
| `show_photo` | BooleanField | Yes | `True` | Show photo in directory |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Visibility Levels:**

| Level | Description |
|-------|-------------|
| `public` | Visible to all church members |
| `group` | Visible only to members who share at least one group |
| `private` | Visible only to pastoral staff (pastors and admins) |

---

### MemberRole

Allows a member to hold multiple roles simultaneously, in addition to their primary `role` field. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `member` | ForeignKey -> Member | Yes | -- | The member (related_name: `additional_roles`) |
| `role` | CharField(20) | Yes | -- | Additional role (choices from `Roles.CHOICES`) |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Constraints:** `unique_together = ['member', 'role']`

---

### Department

Organizational department with leader, hierarchy, calendar, and custom task types. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `name` | CharField(200) | Yes | -- | Department name |
| `description` | TextField | No | blank | Description |
| `leader` | ForeignKey -> Member | No | NULL | Department leader (related_name: `led_departments`) |
| `parent_department` | ForeignKey -> self | No | NULL | Parent department for hierarchy (related_name: `sub_departments`) |
| `meeting_day` | CharField(20) | No | blank | Meeting day |
| `meeting_time` | TimeField | No | NULL | Meeting time |
| `meeting_location` | CharField(200) | No | blank | Meeting location |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Properties:**

| Property | Return Type | Description |
|----------|-------------|-------------|
| `member_count` | `int` | Count of active memberships in this department |

**Meta:** Ordered by `['name']`.

---

### DepartmentMembership

Links members to departments with a role. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `member` | ForeignKey -> Member | Yes | -- | The member (related_name: `department_memberships`) |
| `department` | ForeignKey -> Department | Yes | -- | The department (related_name: `memberships`) |
| `role` | CharField(20) | Yes | `member` | Role: `member`, `leader`, `assistant` (choices from `DepartmentRole.CHOICES`) |
| `joined_date` | DateField | Auto | auto_now_add | Date joined the department |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Constraints:** `unique_together = ['member', 'department']`

**Meta:** Ordered by `['department__name']`.

---

### DepartmentTaskType

Custom task types specific to a department, used by the worship app for section assignments. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `department` | ForeignKey -> Department | Yes | -- | Parent department (related_name: `task_types`) |
| `name` | CharField(100) | Yes | -- | Task type name |
| `description` | TextField | No | blank | Description |
| `max_assignees` | PositiveIntegerField | Yes | `1` | Maximum people assignable to this task |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Constraints:** `unique_together = ['department', 'name']`

**Meta:** Ordered by `['department', 'name']`.

---

### DisciplinaryAction

Tracks disciplinary measures (punishment, exemption, suspension) with an approval workflow. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `member` | ForeignKey -> Member | Yes | -- | Target member (related_name: `disciplinary_actions`) |
| `action_type` | CharField(20) | Yes | -- | Type: `punishment`, `exemption`, `suspension` |
| `reason` | TextField | Yes | -- | Reason for the action |
| `start_date` | DateField | Yes | -- | Start date of the action |
| `end_date` | DateField | No | NULL | End date (for temporary actions) |
| `created_by` | ForeignKey -> Member | Yes | NULL | Staff member who created the action (related_name: `created_disciplinary_actions`) |
| `approved_by` | ForeignKey -> Member | No | NULL | Staff member who approved/rejected (related_name: `approved_disciplinary_actions`) |
| `approval_status` | CharField(20) | Yes | `pending` | Status: `pending`, `approved`, `rejected` |
| `auto_suspend_membership` | BooleanField | Yes | `True` | Whether to auto-suspend the member's account on approval |
| `notes` | TextField | No | blank | Internal notes |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Properties:**

| Property | Return Type | Description |
|----------|-------------|-------------|
| `is_current` | `bool` | Whether this action is currently in effect (based on start/end dates) |

**Meta:** Ordered by `['-start_date']`.

---

### ProfileModificationRequest

Request from staff asking a member to update their personal information. Inherits from `BaseModel`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUIDField | Auto | uuid4 | Primary key |
| `target_member` | ForeignKey -> Member | Yes | -- | Member being asked to update (related_name: `modification_requests`) |
| `requested_by` | ForeignKey -> Member | Yes | NULL | Staff member who made the request (related_name: `sent_modification_requests`) |
| `message` | TextField | Yes | -- | Description of requested modifications |
| `status` | CharField(20) | Yes | `pending` | Status: `pending`, `completed`, `cancelled` |
| `completed_at` | DateTimeField | No | NULL | When the request was completed |
| `is_active` | BooleanField | Yes | `True` | Inherited from BaseModel |
| `created_at` | DateTimeField | Auto | now | Inherited from BaseModel |
| `updated_at` | DateTimeField | Auto | now | Inherited from BaseModel |

**Meta:** Ordered by `['-created_at']`.

---

## Forms

All forms use `W3CRMFormMixin` for automatic Bootstrap CSS class application.

| Form | Model | Fields | Description |
|------|-------|--------|-------------|
| `MemberRegistrationForm` | Member | `first_name`, `last_name`, `email`, `phone`, `birth_date`, `address`, `city`, `province`, `postal_code`, `family_status` + `create_account`, `password`, `password_confirm` | Public registration with optional user account creation. Validates email uniqueness, password strength, and match. On save: creates Member, optionally creates Django User, creates DirectoryPrivacy. |
| `MemberProfileForm` | Member | `first_name`, `last_name`, `email`, `phone`, `phone_secondary`, `birth_date`, `address`, `city`, `province`, `postal_code`, `photo`, `family_status` | Self-service profile update. Excludes sensitive fields (role, notes, is_active, family, joined_date, baptism_date). |
| `MemberAdminForm` | Member | All profile fields + `role`, `family`, `joined_date`, `baptism_date`, `notes`, `is_active` | Full admin form with all fields including role and pastoral notes. |
| `MemberStaffForm` | Member | `role`, `family`, `joined_date`, `baptism_date`, `membership_status`, `notes`, `is_active` | Staff form for editing only administrative fields (no personal info). Used when staff edits another member's profile. |
| `ProfileModificationRequestForm` | ProfileModificationRequest | `message` | Form for staff to request a member to update their info. |
| `FamilyForm` | Family | `name`, `address`, `city`, `province`, `postal_code`, `notes` | Create/edit families. |
| `GroupForm` | Group | `name`, `group_type`, `description`, `leader`, `meeting_day`, `meeting_time`, `meeting_location`, `email` | Create/edit groups. The `leader` field is filtered to members with role `group_leader`, `pastor`, or `admin`. |
| `GroupMembershipForm` | GroupMembership | `member`, `group`, `role`, `notes` | Add a member to a group. When passed a `group` kwarg, hides the group field and excludes members already in the group. |
| `DirectoryPrivacyForm` | DirectoryPrivacy | `visibility`, `show_email`, `show_phone`, `show_address`, `show_birth_date`, `show_photo` | Manage directory privacy settings. |
| `MemberSearchForm` | -- (Form) | `search`, `role`, `family_status`, `group`, `birth_month` | Search and filter form for the member list view. |
| `DepartmentForm` | Department | `name`, `description`, `leader`, `parent_department`, `meeting_day`, `meeting_time`, `meeting_location` | Create/edit departments. Leader filtered to active members with staff-level roles. |
| `DepartmentTaskTypeForm` | DepartmentTaskType | `name`, `description`, `max_assignees` | Create/edit task types within a department. |
| `DepartmentMembershipForm` | DepartmentMembership | `member`, `role` | Add a member to a department. When passed a `department` kwarg, excludes already-enrolled members. |
| `DisciplinaryActionForm` | DisciplinaryAction | `member`, `action_type`, `reason`, `start_date`, `end_date`, `auto_suspend_membership`, `notes` | Create disciplinary actions. Member field filtered to active members. |

## Services

### DisciplinaryService

Located in `apps/members/services.py`. Manages the disciplinary action lifecycle with role-hierarchy enforcement.

**Role Hierarchy** (ascending authority): `member` < `volunteer` < `group_leader` < `deacon` < `treasurer` < `pastor` < `admin`

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `can_discipline(actor, target)` | Two Member instances | `bool` | Checks if actor can create a disciplinary action against target. Actor must be in `STAFF_ROLES` and have strictly higher hierarchy than target. |
| `can_approve(approver, action)` | Member, DisciplinaryAction | `bool` | Checks if approver can approve an action. Must be different from creator and at least pastor level. |
| `create_action(actor, target, action_type, reason, start_date, end_date, notes, auto_suspend)` | Various | `DisciplinaryAction` | Creates a pending action and sends notifications to all pastors/admins (excluding the actor). Raises `ValueError` if hierarchy check fails. |
| `approve_action(approver, action)` | Member, DisciplinaryAction | `DisciplinaryAction` | Approves the action. If `auto_suspend_membership` is True and action type is `suspension`, sets the member's `membership_status` to `SUSPENDED` and notifies them. Notifies the action creator. Raises `ValueError` if unauthorized. |
| `reject_action(approver, action)` | Member, DisciplinaryAction | `DisciplinaryAction` | Rejects the action and notifies the creator. Raises `ValueError` if unauthorized. |
| `lift_suspension(actor, action)` | Member, DisciplinaryAction | `DisciplinaryAction` | Sets end date to today, reactivates the member if suspended, and notifies them. Only works on approved suspensions. Raises `ValueError` otherwise. |

## Serializers

| Serializer | Model | Purpose | Key Fields |
|------------|-------|---------|------------|
| `MemberListSerializer` | Member | Lightweight list/search results | `id`, `member_number`, `first_name`, `last_name`, `full_name`, `email`, `phone`, `role`, `role_display`, `photo`, `age`, `is_active` |
| `MemberSerializer` | Member | Full detail with related data | All fields + `full_name`, `full_address`, `age`, `role_display`, `family_status_display`, `province_display`, `family_name`, `groups` (method field) |
| `MemberCreateSerializer` | Member | Member creation | `first_name`, `last_name`, `email`, `phone`, `phone_secondary`, `birth_date`, `address`, `city`, `province`, `postal_code`, `photo`, `family_status`, `family`. On create: also creates `DirectoryPrivacy`. |
| `MemberProfileSerializer` | Member | Self-service profile update | `first_name`, `last_name`, `email`, `phone`, `phone_secondary`, `birth_date`, `address`, `city`, `province`, `postal_code`, `photo`, `family_status` |
| `MemberAdminSerializer` | Member | Admin updates with all fields | All writable fields + `full_name`, `notes`, `role`, `is_active`. Read-only: `member_number`, `created_at`, `updated_at` |
| `BirthdaySerializer` | Member | Birthday-focused data | `id`, `member_number`, `full_name`, `birth_date`, `birth_day` (method), `birth_month` (method), `age`, `photo`, `phone`, `email` |
| `DirectoryMemberSerializer` | Member | Directory listing with privacy | `id`, `member_number`, `full_name`, `email`, `phone`, `photo`. Applies privacy settings in `to_representation()`: nulls out email/phone/photo based on member's `DirectoryPrivacy` settings. |
| `FamilySerializer` | Family | Full family with members | `id`, `name`, `address`, `city`, `province`, `postal_code`, `full_address`, `notes`, `member_count`, `members` (nested `MemberListSerializer`), `is_active`, `created_at`, `updated_at` |
| `FamilyListSerializer` | Family | Lightweight family list | `id`, `name`, `city`, `member_count` |
| `GroupSerializer` | Group | Full group details | `id`, `name`, `group_type`, `group_type_display`, `description`, `leader`, `leader_name`, `meeting_day`, `meeting_time`, `meeting_location`, `email`, `member_count`, `is_active`, `created_at`, `updated_at` |
| `GroupListSerializer` | Group | Lightweight group list | `id`, `name`, `group_type`, `group_type_display`, `member_count` |
| `GroupMembershipSerializer` | GroupMembership | Membership details | `id`, `member`, `member_name`, `group`, `group_name`, `role`, `role_display`, `joined_date`, `notes`, `is_active` |
| `DirectoryPrivacySerializer` | DirectoryPrivacy | Privacy settings | `id`, `visibility`, `visibility_display`, `show_email`, `show_phone`, `show_address`, `show_birth_date`, `show_photo` |

**Serializer Selection by Action (MemberViewSet):**

| Action | Serializer |
|--------|------------|
| `list` | `MemberListSerializer` |
| `create` | `MemberCreateSerializer` |
| `retrieve` | `MemberSerializer` |
| `update`/`partial_update` (staff) | `MemberAdminSerializer` |
| `update`/`partial_update` (member) | `MemberProfileSerializer` |
| `birthdays` | `BirthdaySerializer` |
| `directory` | `DirectoryMemberSerializer` |

## API Endpoints

The REST API is built with Django REST Framework using ViewSets with an automatic router.

### Members (`MemberViewSet`)

Base path: `/api/v1/members/members/`

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/members/members/` | List members (filtered by user's role) | `IsMember` |
| `POST` | `/api/v1/members/members/` | Register a new member | Public (none) |
| `GET` | `/api/v1/members/members/{uuid}/` | Member detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/members/{uuid}/` | Update a member | `IsOwnerOrStaff` |
| `DELETE` | `/api/v1/members/members/{uuid}/` | Delete a member | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/members/me/` | Current user's profile | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/members/me/` | Update own profile | `IsMember` |
| `GET` | `/api/v1/members/members/birthdays/` | Birthdays (`?period=today/week/month&month=1-12`) | `IsMember` |
| `GET` | `/api/v1/members/members/directory/` | Directory with privacy applied (`?search=...`) | `IsMember` |

**Filters:** `role`, `family_status`, `family`, `is_active`
**Search:** `first_name`, `last_name`, `email`, `member_number`, `phone`
**Ordering:** `last_name`, `first_name`, `created_at`, `birth_date`

**Data Visibility by Role:**

| Role | Visible Members |
|------|-----------------|
| Admin / Pastor | All members |
| Group Leader | Self + members of groups they lead |
| Member / Volunteer | Self only |

### Families (`FamilyViewSet`)

Base path: `/api/v1/members/families/`

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/members/families/` | List families | `IsMember` |
| `POST` | `/api/v1/members/families/` | Create a family | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/families/{uuid}/` | Family detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/families/{uuid}/` | Update a family | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/members/families/{uuid}/` | Delete a family | `IsPastorOrAdmin` |

**Search:** `name`, `city`
**Ordering:** `name`, `created_at`

### Groups (`GroupViewSet`)

Base path: `/api/v1/members/groups/`

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/members/groups/` | List groups | `IsMember` |
| `POST` | `/api/v1/members/groups/` | Create a group | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/groups/{uuid}/` | Group detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/groups/{uuid}/` | Update a group | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/members/groups/{uuid}/` | Delete a group | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/groups/{uuid}/members/` | List active group members | `IsMember` |
| `POST` | `/api/v1/members/groups/{uuid}/add-member/` | Add member to group (`{"member": "uuid", "role": "member"}`) | `IsPastorOrAdmin` |
| `POST` | `/api/v1/members/groups/{uuid}/remove-member/` | Remove member from group (`{"member": "uuid"}`) | `IsPastorOrAdmin` |

**Filters:** `group_type`, `leader`, `is_active`
**Search:** `name`, `description`
**Ordering:** `name`, `created_at`

### Directory Privacy (`DirectoryPrivacyViewSet`)

Base path: `/api/v1/members/privacy/`

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/members/privacy/` | List privacy settings (staff sees all, members see own) | `IsMember` |
| `GET` | `/api/v1/members/privacy/{uuid}/` | Privacy settings detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/privacy/{uuid}/` | Update privacy settings | `IsMember` |
| `GET` | `/api/v1/members/privacy/me/` | Current user's privacy settings | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/privacy/me/` | Update own privacy settings | `IsMember` |

## Frontend URLs

Base path: `/members/`

### Member Management

| URL | View | Name | Access |
|-----|------|------|--------|
| `/members/` | `member_list` | `members:member_list` | Pastor, Admin |
| `/members/register/` | `member_create` | `members:member_create` | Public |
| `/members/my-profile/` | `my_profile` | `members:my_profile` | Authenticated (own profile) |
| `/members/export/` | `member_list_export` | `members:member_list_export` | Pastor, Admin |
| `/members/birthdays/` | `birthday_list` | `members:birthday_list` | Authenticated |
| `/members/directory/` | `directory` | `members:directory` | Authenticated |
| `/members/privacy-settings/` | `privacy_settings` | `members:privacy_settings` | Authenticated (own settings) |
| `/members/<uuid:pk>/` | `member_detail` | `members:member_detail` | Owner, Staff, Group Leader (if in their group) |
| `/members/<uuid:pk>/edit/` | `member_update` | `members:member_update` | Owner (profile fields), Staff (admin fields) |
| `/members/<uuid:pk>/request-modification/` | `request_modification` | `members:request_modification` | Staff |

### Modification Requests

| URL | View | Name | Access |
|-----|------|------|--------|
| `/members/modification-requests/` | `modification_request_list` | `members:modification_request_list` | Staff |
| `/members/modification-requests/<uuid:pk>/complete/` | `complete_modification_request` | `members:complete_modification_request` | Target member only (POST) |

### Groups

| URL | View | Name | Access |
|-----|------|------|--------|
| `/members/groups/` | `group_list` | `members:group_list` | Authenticated |
| `/members/groups/create/` | `group_create` | `members:group_create` | Staff |
| `/members/groups/<uuid:pk>/` | `group_detail` | `members:group_detail` | Authenticated |
| `/members/groups/<uuid:pk>/edit/` | `group_edit` | `members:group_edit` | Staff |
| `/members/groups/<uuid:pk>/delete/` | `group_delete` | `members:group_delete` | Staff |
| `/members/groups/<uuid:pk>/add-member/` | `group_add_member` | `members:group_add_member` | Staff, Group Leader |
| `/members/groups/<uuid:pk>/remove-member/<uuid:membership_pk>/` | `group_remove_member` | `members:group_remove_member` | Staff, Group Leader (POST) |

### Families

| URL | View | Name | Access |
|-----|------|------|--------|
| `/members/families/` | `family_list` | `members:family_list` | Authenticated |
| `/members/families/create/` | `family_create` | `members:family_create` | Staff |
| `/members/families/<uuid:pk>/` | `family_detail` | `members:family_detail` | Authenticated |
| `/members/families/<uuid:pk>/edit/` | `family_edit` | `members:family_edit` | Staff |
| `/members/families/<uuid:pk>/delete/` | `family_delete` | `members:family_delete` | Staff |

### Departments

| URL | View | Name | Access |
|-----|------|------|--------|
| `/members/departments/` | `department_list` | `members:department_list` | Authenticated |
| `/members/departments/create/` | `department_create` | `members:department_create` | Pastor, Admin |
| `/members/departments/<uuid:pk>/` | `department_detail` | `members:department_detail` | Authenticated |
| `/members/departments/<uuid:pk>/edit/` | `department_edit` | `members:department_edit` | Pastor, Admin |
| `/members/departments/<uuid:pk>/delete/` | `department_delete` | `members:department_delete` | Pastor, Admin |
| `/members/departments/<uuid:pk>/add-member/` | `department_add_member` | `members:department_add_member` | Pastor, Admin, Dept Leader |
| `/members/departments/<uuid:pk>/remove-member/<uuid:membership_pk>/` | `department_remove_member` | `members:department_remove_member` | Pastor, Admin, Dept Leader (POST) |
| `/members/departments/<uuid:pk>/task-types/` | `department_task_types` | `members:department_task_types` | Pastor, Admin, Dept Leader |

### Disciplinary Actions

| URL | View | Name | Access |
|-----|------|------|--------|
| `/members/disciplinary/` | `disciplinary_list` | `members:disciplinary_list` | Staff (`STAFF_ROLES`) |
| `/members/disciplinary/create/` | `disciplinary_create` | `members:disciplinary_create` | Staff (`STAFF_ROLES`) |
| `/members/disciplinary/<uuid:pk>/` | `disciplinary_detail` | `members:disciplinary_detail` | Staff (`STAFF_ROLES`) |
| `/members/disciplinary/<uuid:pk>/approve/` | `disciplinary_approve` | `members:disciplinary_approve` | Pastor, Admin (POST) |

## Templates

### `templates/members/`

| Template | View(s) | Description |
|----------|---------|-------------|
| `member_list.html` | `member_list` | Paginated member table with search, role/status filters, and sorting |
| `member_detail.html` | `member_detail` | Full member profile page with groups and family |
| `member_form.html` | `member_create`, `member_update` | Shared create/edit form (adapts based on form type) |
| `my_profile.html` | `my_profile` | Self-service profile page with pending modification requests |
| `birthday_list.html` | `birthday_list` | Birthday listing by period (today/week/month) |
| `directory.html` | `directory` | Member directory with privacy-filtered results |
| `privacy_settings.html` | `privacy_settings` | Privacy settings form |
| `group_list.html` | `group_list` | List of all active groups with type filter |
| `group_detail.html` | `group_detail` | Group details with member list |
| `group_form.html` | `group_create`, `group_edit` | Group create/edit form |
| `group_delete.html` | `group_delete` | Group delete confirmation |
| `group_add_member.html` | `group_add_member` | Add member to group form |
| `family_list.html` | `family_list` | List of all families with search |
| `family_detail.html` | `family_detail` | Family details with member list |
| `family_form.html` | `family_create`, `family_edit` | Family create/edit form |
| `family_delete.html` | `family_delete` | Family delete confirmation |
| `department_delete.html` | `department_delete` | Department delete confirmation |
| `disciplinary_list.html` | `disciplinary_list` | Paginated disciplinary action list with status/type/date filters |
| `disciplinary_form.html` | `disciplinary_create` | Disciplinary action creation form |
| `disciplinary_detail.html` | `disciplinary_detail` | Disciplinary action details with approve/reject/lift buttons |
| `request_modification.html` | `request_modification` | Profile modification request form |
| `modification_request_list.html` | `modification_request_list` | List of all profile modification requests with status filter |

### `templates/departments/`

| Template | View(s) | Description |
|----------|---------|-------------|
| `department_list.html` | `department_list` | List of all active departments |
| `department_detail.html` | `department_detail` | Department details with members and task types |
| `department_form.html` | `department_create`, `department_edit` | Department create/edit form |
| `department_add_member.html` | `department_add_member` | Add member to department form |
| `department_task_types.html` | `department_task_types` | Task type management for a department |

## Signals

### `create_member_for_superuser`

| Signal | Sender | Trigger | Behavior |
|--------|--------|---------|----------|
| `post_save` | `User` | New superuser created | Auto-creates a `Member` profile with `role=ADMIN`, `membership_status=ACTIVE`. Uses `first_name` / `last_name` from the User (or defaults to "Admin" / capitalized username). Skips if the user already has a `member_profile`. |

Located in `apps/members/signals.py`.

## Admin Configuration

### Registered Models and Admin Classes

| Model | Admin Class | Parent | Features |
|-------|-------------|--------|----------|
| `Member` | `MemberAdmin` | `SoftDeleteModelAdmin` | Full fieldsets (Identification, Personal Info, Address, Church, Notes, Status, Metadata), inlines for DirectoryPrivacy and GroupMembership |
| `Family` | `FamilyAdmin` | `BaseModelAdmin` | Fieldsets (Name, Address, Notes, Status, Metadata), inline for family members |
| `Group` | `GroupAdmin` | `BaseModelAdmin` | Fieldsets (Info, Meetings, Contact, Status, Metadata), inline for GroupMembership |
| `GroupMembership` | `GroupMembershipAdmin` | `BaseModelAdmin` | List display with member, group, role, joined_date, is_active |
| `DirectoryPrivacy` | `DirectoryPrivacyAdmin` | `BaseModelAdmin` | List display with member, visibility, and show_* fields |

### Inlines

| Inline | Type | Used In | Description |
|--------|------|---------|-------------|
| `GroupMembershipInline` | TabularInline | `MemberAdmin`, `GroupAdmin` | Manage member-group assignments with autocomplete |
| `DirectoryPrivacyInline` | StackedInline | `MemberAdmin` | Edit privacy settings (cannot delete) |
| `FamilyMemberInline` | TabularInline | `FamilyAdmin` | View/add family members (member_number readonly) |

### MemberAdmin Detail

- **list_display:** `member_number`, `full_name`, `email`, `phone`, `role`, `family_status`, `is_active`
- **list_filter:** `role`, `family_status`, `province`, `is_active`, `created_at`
- **search_fields:** `member_number`, `first_name`, `last_name`, `email`, `phone`
- **readonly_fields:** `id`, `member_number`, `created_at`, `updated_at`, `deleted_at`
- **autocomplete_fields:** `user`, `family`

## Permissions Matrix

### Frontend Views

| Action | Member | Volunteer | Group Leader | Deacon | Treasurer | Pastor | Admin |
|--------|--------|-----------|-------------|--------|-----------|--------|-------|
| View member list | -- | -- | -- | Yes | -- | Yes | Yes |
| View member detail (own) | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View member detail (other) | -- | -- | Own group* | Yes | -- | Yes | Yes |
| Edit own profile | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Edit other's admin fields | -- | -- | -- | Yes | -- | Yes | Yes |
| Register (public) | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Export member list CSV | -- | -- | -- | -- | -- | Yes | Yes |
| View birthdays | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View directory | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Manage own privacy | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View group list | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View group detail | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Create/edit/delete group | -- | -- | -- | Yes | -- | Yes | Yes |
| Add/remove group member | -- | -- | Own group* | Yes | -- | Yes | Yes |
| View family list | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View family detail | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Create/edit/delete family | -- | -- | -- | Yes | -- | Yes | Yes |
| View department list | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View department detail | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Create/edit/delete department | -- | -- | -- | -- | -- | Yes | Yes |
| Add/remove dept member | -- | -- | Dept leader* | -- | -- | Yes | Yes |
| Manage dept task types | -- | -- | Dept leader* | -- | -- | Yes | Yes |
| View disciplinary list | -- | -- | -- | Yes | -- | Yes | Yes |
| Create disciplinary action | -- | -- | -- | Yes | -- | Yes | Yes |
| Approve/reject/lift | -- | -- | -- | -- | -- | Yes | Yes |
| Request profile modification | -- | -- | -- | Yes | -- | Yes | Yes |
| View modification requests | -- | -- | -- | Yes | -- | Yes | Yes |
| Complete modification request | Target member only | | | | | | |
| View own profile (my_profile) | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

\* Only for groups/departments they lead

### API Endpoints

| Action | Permission Class | Description |
|--------|-----------------|-------------|
| Create member | None (public) | Anyone can register |
| List members | `IsMember` | Must be authenticated with a member profile |
| Retrieve member | `IsMember` | Role-based queryset filtering applies |
| Update member | `IsOwnerOrStaff` | Own profile or staff |
| Delete member | `IsPastorOrAdmin` | Pastor or admin only |
| `/me/` | `IsMember` | Authenticated members |
| `/birthdays/` | `IsMember` | Authenticated members |
| `/directory/` | `IsMember` | Privacy settings applied to results |
| List/retrieve family | `IsMember` | Authenticated members |
| Create/update/delete family | `IsPastorOrAdmin` | Pastor or admin only |
| List/retrieve group | `IsMember` | Authenticated members |
| Create/update/delete group | `IsPastorOrAdmin` | Pastor or admin only |
| Group `/members/` | `IsMember` | Authenticated members |
| Group `/add-member/`, `/remove-member/` | `IsPastorOrAdmin` | Pastor or admin only |
| Privacy settings | `IsMember` | Members see only their own; staff sees all |

## Dependencies

- **core**: `BaseModel`, `SoftDeleteModel`, constants (`Roles`, `FamilyStatus`, `GroupType`, `PrivacyLevel`, `Province`, `MembershipStatus`, `DepartmentRole`, `DisciplinaryType`, `ApprovalStatus`, `ModificationRequestStatus`), `validate_image_file`, `generate_member_number`, `get_today_birthdays`, `get_week_birthdays`, `get_month_birthdays`, `export_queryset_csv`, permissions (`IsMember`, `IsPastor`, `IsAdmin`, `IsPastorOrAdmin`, `IsOwnerOrStaff`, `CanViewMember`), mixins (`W3CRMFormMixin`, `PastorRequiredMixin`, `MemberRequiredMixin`, `ChurchContextMixin`, `OwnerOrStaffRequiredMixin`), admin (`SoftDeleteModelAdmin`, `BaseModelAdmin`)
- **communication**: `Notification` model (used by `DisciplinaryService` for approval notifications, suspension notifications, and action result notifications)
- **django.contrib.auth**: `User` model (one-to-one link from Member, superuser signal)

## Tests

**345 tests** across 8 test files, located in `apps/members/tests/`.

| File | Description |
|------|-------------|
| `factories.py` | Test data factories for Member, Family, Group, GroupMembership, DirectoryPrivacy, Department, DepartmentMembership, DepartmentTaskType, DisciplinaryAction, ProfileModificationRequest |
| `test_models.py` | Model creation, auto-generated member numbers, soft delete/restore, property calculations (age, full_name, full_address), constraints (unique_together), member_count properties |
| `test_forms.py` | Form validation (registration with account creation, password validation, email uniqueness), leader field filtering in GroupForm/DepartmentForm, GroupMembershipForm exclusion of existing members, W3CRMFormMixin CSS application |
| `test_serializers.py` | Serializer output verification, privacy-respecting directory serializer, birthday serializer computed fields, read-only field enforcement |
| `test_views_api.py` | API CRUD operations, role-based queryset filtering, permission enforcement, custom actions (me, birthdays, directory), group member management endpoints |
| `test_views_api_extended.py` | Extended API tests for edge cases and additional scenarios |
| `test_views_frontend.py` | Frontend view access control, form rendering and submission, pagination, search/filter functionality, redirect behavior for unauthorized access |
| `test_disciplinary.py` | DisciplinaryService hierarchy enforcement, create/approve/reject/lift workflows, notification creation, auto-suspension on approval, error handling for invalid operations |
| `test_profile.py` | Profile modification request workflow (create, complete), my_profile view, staff-only access to modification request list |

Run tests:

```bash
# All members tests
pytest apps/members/ -v

# By category
pytest apps/members/tests/test_models.py -v
pytest apps/members/tests/test_forms.py -v
pytest apps/members/tests/test_views_api.py -v
pytest apps/members/tests/test_views_frontend.py -v
pytest apps/members/tests/test_disciplinary.py -v
pytest apps/members/tests/test_profile.py -v

# With coverage
pytest apps/members/ -v --cov=apps.members --cov-report=html
```
