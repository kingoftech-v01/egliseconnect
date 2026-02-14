# Volunteers App

## Overview

The Volunteers app coordinates volunteer service within the church. It manages volunteer positions (roles), member availability preferences, scheduled assignments, planned absences, shift swap requests, and automated schedule reminders via Celery tasks. The app provides both a template-based frontend (using the W3CRM/DexignZone theme) and a full Django REST Framework API with four ViewSets.

All models inherit from `BaseModel`, which provides UUID primary keys, `created_at`/`updated_at` timestamps, and an `is_active` soft-flag with `ActiveManager` as the default manager.

## File Structure

```text
apps/volunteers/
    __init__.py
    admin.py                # Django admin configuration (4 model admins)
    apps.py                 # AppConfig
    forms.py                # VolunteerPositionForm, VolunteerScheduleForm, SwapRequestForm
    models.py               # VolunteerPosition, VolunteerAvailability, VolunteerSchedule, PlannedAbsence, SwapRequest
    serializers.py          # 4 DRF serializers
    tasks.py                # Celery task for schedule reminders
    urls.py                 # Frontend + API URL routing
    views_api.py            # 4 DRF ViewSets
    views_frontend.py       # 16 template-based views
    migrations/
        0001_initial.py
    tests/
        __init__.py
        factories.py        # 5 factories (factory_boy)
        test_forms.py       # VolunteerPositionForm + VolunteerScheduleForm tests
        test_models.py      # Model __str__ tests
        test_tasks.py       # Celery reminder task tests
        test_views_api.py   # Full API endpoint coverage
        test_views_frontend.py  # Frontend view tests

templates/volunteers/
    availability_update.html      # Manage availability per position
    my_schedule.html              # Current user's schedule
    planned_absence_delete.html   # Delete absence confirmation
    planned_absence_form.html     # Create/edit planned absence
    planned_absence_list.html     # List planned absences
    position_delete.html          # Delete position confirmation
    position_form.html            # Create/edit position
    position_list.html            # List active positions
    schedule_delete.html          # Delete schedule confirmation
    schedule_form.html            # Create/edit schedule entry
    schedule_list.html            # Full volunteer schedule
    swap_request_form.html        # Create swap request
    swap_request_list.html        # List swap requests
```

## Models

### VolunteerPosition

Represents a volunteer role that members can sign up for within a specific ministry area.

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUIDField` | PK, auto-generated | Inherited from BaseModel |
| `name` | `CharField(100)` | required | Position name (e.g., "Pianist", "Sound Tech") |
| `role_type` | `CharField(20)` | choices: `VolunteerRole`, required | Ministry area category |
| `description` | `TextField` | blank | Detailed description of duties |
| `min_volunteers` | `PositiveIntegerField` | default: `1` | Minimum required volunteers |
| `max_volunteers` | `PositiveIntegerField` | nullable | Maximum volunteers (None = unlimited) |
| `skills_required` | `TextField` | blank | Skills or qualifications needed |
| `created_at` | `DateTimeField` | auto_now_add | Inherited from BaseModel |
| `updated_at` | `DateTimeField` | auto_now | Inherited from BaseModel |
| `is_active` | `BooleanField` | default: `True` | Inherited from BaseModel |

**VolunteerRole choices:**

| Constant | Value | French Label |
| --- | --- | --- |
| `VolunteerRole.WORSHIP` | `worship` | Louange |
| `VolunteerRole.HOSPITALITY` | `hospitality` | Accueil |
| `VolunteerRole.TECHNICAL` | `technical` | Technique |
| `VolunteerRole.CHILDREN` | `children` | Enfants |
| `VolunteerRole.YOUTH` | `youth` | Jeunesse |
| `VolunteerRole.ADMIN` | `admin` | Administration |
| `VolunteerRole.OUTREACH` | `outreach` | Evangelisation |
| `VolunteerRole.OTHER` | `other` | Autre |

**Computed properties:**

| Property | Return Type | Description |
| --- | --- | --- |
| `volunteer_count` | `int` | Count of `available_volunteers` (VolunteerAvailability records) |

**Meta:** ordering = `['name']`, verbose_name = "Poste de benevolat"

### VolunteerAvailability

Tracks when a member is available for a specific volunteer position, including preferred frequency.

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUIDField` | PK, auto-generated | Inherited from BaseModel |
| `member` | `ForeignKey(Member)` | `CASCADE` | The volunteer member (related_name: `volunteer_availability`) |
| `position` | `ForeignKey(VolunteerPosition)` | `CASCADE` | The position (related_name: `available_volunteers`) |
| `is_available` | `BooleanField` | default: `True` | Whether currently available |
| `frequency` | `CharField(20)` | choices: `VolunteerFrequency`, default: `monthly` | Preferred service frequency |
| `notes` | `TextField` | blank | Additional notes |
| `created_at` | `DateTimeField` | auto_now_add | Inherited from BaseModel |
| `updated_at` | `DateTimeField` | auto_now | Inherited from BaseModel |
| `is_active` | `BooleanField` | default: `True` | Inherited from BaseModel |

**VolunteerFrequency choices:**

| Constant | Value | French Label |
| --- | --- | --- |
| `VolunteerFrequency.WEEKLY` | `weekly` | Chaque semaine |
| `VolunteerFrequency.BIWEEKLY` | `biweekly` | Aux deux semaines |
| `VolunteerFrequency.MONTHLY` | `monthly` | Une fois par mois |
| `VolunteerFrequency.OCCASIONAL` | `occasional` | Occasionnellement |

**Constraints:** `unique_together = ['member', 'position']` -- one availability record per member per position.

**Meta:** verbose_name = "Disponibilite"

### VolunteerSchedule

A scheduled volunteer assignment for a specific date, optionally linked to an event.

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUIDField` | PK, auto-generated | Inherited from BaseModel |
| `member` | `ForeignKey(Member)` | `CASCADE` | Assigned volunteer (related_name: `volunteer_schedules`) |
| `position` | `ForeignKey(VolunteerPosition)` | `CASCADE` | Position to fill (related_name: `schedules`) |
| `event` | `ForeignKey(Event)` | nullable, `CASCADE` | Optional linked event (related_name: `volunteer_schedules`) |
| `date` | `DateField` | required | Date of the assignment |
| `status` | `CharField(20)` | choices: `ScheduleStatus`, default: `scheduled` | Assignment status |
| `reminder_sent` | `BooleanField` | default: `False` | Legacy flag -- set to `True` when any reminder is sent |
| `reminder_5days_sent` | `BooleanField` | default: `False` | 5-day reminder tracking flag |
| `reminder_3days_sent` | `BooleanField` | default: `False` | 3-day reminder tracking flag |
| `reminder_1day_sent` | `BooleanField` | default: `False` | 1-day reminder tracking flag |
| `reminder_sameday_sent` | `BooleanField` | default: `False` | Same-day reminder tracking flag |
| `notes` | `TextField` | blank | Additional notes |
| `created_at` | `DateTimeField` | auto_now_add | Inherited from BaseModel |
| `updated_at` | `DateTimeField` | auto_now | Inherited from BaseModel |
| `is_active` | `BooleanField` | default: `True` | Inherited from BaseModel |

**ScheduleStatus choices:**

| Constant | Value | French Label |
| --- | --- | --- |
| `ScheduleStatus.SCHEDULED` | `scheduled` | Planifie |
| `ScheduleStatus.CONFIRMED` | `confirmed` | Confirme |
| `ScheduleStatus.DECLINED` | `declined` | Refuse |
| `ScheduleStatus.COMPLETED` | `completed` | Complete |
| `ScheduleStatus.NO_SHOW` | `no_show` | Absent |

**Meta:** ordering = `['date']`, verbose_name = "Horaire"

### PlannedAbsence

Pre-declared absence period to prevent scheduling a member during that time.

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUIDField` | PK, auto-generated | Inherited from BaseModel |
| `member` | `ForeignKey(Member)` | `CASCADE` | Member declaring absence (related_name: `planned_absences`) |
| `start_date` | `DateField` | required | Absence start date |
| `end_date` | `DateField` | required | Absence end date |
| `reason` | `TextField` | blank | Reason for absence |
| `approved_by` | `ForeignKey(Member)` | nullable, `SET_NULL` | Staff member who approved (related_name: `approved_absences`) |
| `created_at` | `DateTimeField` | auto_now_add | Inherited from BaseModel |
| `updated_at` | `DateTimeField` | auto_now | Inherited from BaseModel |
| `is_active` | `BooleanField` | default: `True` | Inherited from BaseModel |

**Meta:** ordering = `['-start_date']`, verbose_name = "Absence prevue"

### SwapRequest

Request to swap a scheduled shift with another volunteer.

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUIDField` | PK, auto-generated | Inherited from BaseModel |
| `original_schedule` | `ForeignKey(VolunteerSchedule)` | `CASCADE` | The shift to swap (related_name: `swap_requests`) |
| `requested_by` | `ForeignKey(Member)` | `CASCADE` | Member requesting the swap (related_name: `swap_requests_made`) |
| `swap_with` | `ForeignKey(Member)` | nullable, `SET_NULL` | Target member for the swap (related_name: `swap_requests_received`) |
| `status` | `CharField(20)` | choices: `pending`/`approved`/`declined`, default: `pending` | Request status |
| `reason` | `TextField` | blank | Reason for the swap request |
| `created_at` | `DateTimeField` | auto_now_add | Inherited from BaseModel |
| `updated_at` | `DateTimeField` | auto_now | Inherited from BaseModel |
| `is_active` | `BooleanField` | default: `True` | Inherited from BaseModel |

**Meta:** verbose_name = "Demande d'echange"

## Forms

### VolunteerPositionForm

- **Mixin:** `W3CRMFormMixin` (applies DexignZone CSS classes)
- **Model:** `VolunteerPosition`
- **Fields:** `name`, `role_type`, `description`, `min_volunteers`, `max_volunteers`, `skills_required`
- **Widgets:**
  - `description`: `Textarea` with `rows=3`
  - `skills_required`: `Textarea` with `rows=3`

### VolunteerScheduleForm

- **Mixin:** `W3CRMFormMixin`
- **Model:** `VolunteerSchedule`
- **Fields:** `member`, `position`, `event`, `date`, `status`, `notes`
- **Widgets:**
  - `date`: `DateInput` with `type="date"`
  - `notes`: `Textarea` with `rows=3`
  - `member`: `Select` with `data-search="true"` attribute

### SwapRequestForm

- **Mixin:** `W3CRMFormMixin`
- **Model:** `SwapRequest`
- **Display fields:** `requesting_schedule`, `target_member`, `target_schedule`, `reason`
- **Custom `__init__`:** Accepts a `member` keyword argument to scope the `requesting_schedule` queryset to the member's future active schedules. The `target_schedule` queryset is dynamically populated based on the selected `target_member` from POST data.
- **Custom `save`:** Maps form fields to model fields:
  - `requesting_schedule` -> `original_schedule`
  - `requesting_schedule.member` -> `requested_by`
  - `target_member` -> `swap_with`

## Serializers

All serializers use `fields = '__all__'`.

### VolunteerPositionSerializer

| Extra Field | Source | Read-only |
| --- | --- | --- |
| `role_type_display` | `get_role_type_display` | yes |

### VolunteerAvailabilitySerializer

| Extra Field | Source | Read-only |
| --- | --- | --- |
| `member_name` | `member.full_name` | yes |
| `position_name` | `position.name` | yes |

### VolunteerScheduleSerializer

| Extra Field | Source | Read-only |
| --- | --- | --- |
| `member_name` | `member.full_name` | yes |
| `position_name` | `position.name` | yes |
| `status_display` | `get_status_display` | yes |

### SwapRequestSerializer

| Extra Field | Source | Read-only |
| --- | --- | --- |
| `requested_by_name` | `requested_by.full_name` | yes |

## API Endpoints

All API endpoints are prefixed with `/api/v1/volunteers/` and use the DRF `DefaultRouter`.

### VolunteerPositionViewSet

Base path: `/api/v1/volunteers/positions/`

| Method | Endpoint | Action | Permission |
| --- | --- | --- | --- |
| `GET` | `/api/v1/volunteers/positions/` | List positions | `IsMember` |
| `POST` | `/api/v1/volunteers/positions/` | Create position | `IsPastorOrAdmin` |
| `GET` | `/api/v1/volunteers/positions/{id}/` | Retrieve position | `IsMember` |
| `PUT` | `/api/v1/volunteers/positions/{id}/` | Full update | `IsPastorOrAdmin` |
| `PATCH` | `/api/v1/volunteers/positions/{id}/` | Partial update | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/volunteers/positions/{id}/` | Delete position | `IsPastorOrAdmin` |

- **Filter backends:** `DjangoFilterBackend`, `SearchFilter`
- **Filterset fields:** `role_type`, `is_active`
- **Search fields:** `name`

### VolunteerScheduleViewSet

Base path: `/api/v1/volunteers/schedules/`

| Method | Endpoint | Action | Permission |
| --- | --- | --- | --- |
| `GET` | `/api/v1/volunteers/schedules/` | List all schedules | `IsMember` |
| `POST` | `/api/v1/volunteers/schedules/` | Create schedule entry | `IsPastorOrAdmin` |
| `GET` | `/api/v1/volunteers/schedules/{id}/` | Retrieve schedule | `IsMember` |
| `PUT` | `/api/v1/volunteers/schedules/{id}/` | Full update | `IsPastorOrAdmin` |
| `PATCH` | `/api/v1/volunteers/schedules/{id}/` | Partial update | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/volunteers/schedules/{id}/` | Delete schedule | `IsPastorOrAdmin` |
| `GET` | `/api/v1/volunteers/schedules/my-schedule/` | Current user's schedules | `IsMember` |
| `POST` | `/api/v1/volunteers/schedules/{id}/confirm/` | Set status to `confirmed` | `IsPastorOrAdmin` |

- **Filter backends:** `DjangoFilterBackend`, `OrderingFilter`
- **Filterset fields:** `position`, `status`, `date`, `member`
- **Ordering fields:** `date`
- **Default ordering:** `date` ascending
- **my-schedule:** Returns 404 with `{'error': 'Profil requis'}` if user has no `member_profile`

### VolunteerAvailabilityViewSet

Base path: `/api/v1/volunteers/availability/`

| Method | Endpoint | Action | Permission |
| --- | --- | --- | --- |
| `GET` | `/api/v1/volunteers/availability/` | List availability | `IsMember` |
| `POST` | `/api/v1/volunteers/availability/` | Create availability | `IsMember` |
| `GET` | `/api/v1/volunteers/availability/{id}/` | Retrieve | `IsMember` |
| `PUT` | `/api/v1/volunteers/availability/{id}/` | Full update | `IsMember` |
| `PATCH` | `/api/v1/volunteers/availability/{id}/` | Partial update | `IsMember` |
| `DELETE` | `/api/v1/volunteers/availability/{id}/` | Delete | `IsMember` |

**Queryset scoping:** Django `is_staff` users see all records. Members see only their own availability. Users without a `member_profile` see an empty queryset.

### SwapRequestViewSet

Base path: `/api/v1/volunteers/swap-requests/`

| Method | Endpoint | Action | Permission |
| --- | --- | --- | --- |
| `GET` | `/api/v1/volunteers/swap-requests/` | List swap requests | `IsMember` |
| `POST` | `/api/v1/volunteers/swap-requests/` | Create swap request | `IsMember` |
| `GET` | `/api/v1/volunteers/swap-requests/{id}/` | Retrieve | `IsMember` |
| `PUT` | `/api/v1/volunteers/swap-requests/{id}/` | Full update | `IsMember` |
| `PATCH` | `/api/v1/volunteers/swap-requests/{id}/` | Partial update | `IsMember` |
| `DELETE` | `/api/v1/volunteers/swap-requests/{id}/` | Delete | `IsMember` |

**Queryset scoping:** Django `is_staff` users see all requests. Members see only requests where they are `requested_by` or `swap_with`. Users without a `member_profile` see an empty queryset.

## Frontend URLs

Base path: `/volunteers/` (namespace: `frontend:volunteers`)

### Position Management

| URL Pattern | View Function | Name | Description |
| --- | --- | --- | --- |
| `/volunteers/positions/` | `position_list` | `position_list` | List active positions with volunteer counts |
| `/volunteers/positions/create/` | `position_create` | `position_create` | Create new position (admin/pastor) |
| `/volunteers/positions/<uuid:pk>/edit/` | `position_update` | `position_update` | Edit position (admin/pastor) |
| `/volunteers/positions/<uuid:pk>/delete/` | `position_delete` | `position_delete` | Delete position confirmation (admin/pastor) |

### Schedule Management

| URL Pattern | View Function | Name | Description |
| --- | --- | --- | --- |
| `/volunteers/schedule/` | `schedule_list` | `schedule_list` | Full schedule with date range filter |
| `/volunteers/schedule/create/` | `schedule_create` | `schedule_create` | Create schedule entry (admin/pastor) |
| `/volunteers/schedule/<uuid:pk>/edit/` | `schedule_update` | `schedule_update` | Edit schedule entry (admin/pastor) |
| `/volunteers/schedule/<uuid:pk>/delete/` | `schedule_delete` | `schedule_delete` | Delete schedule confirmation (admin/pastor) |
| `/volunteers/my-schedule/` | `my_schedule` | `my_schedule` | Current user's schedule |

### Availability

| URL Pattern | View Function | Name | Description |
| --- | --- | --- | --- |
| `/volunteers/availability/` | `availability_update` | `availability_update` | Update availability for each position (GET + POST) |

### Planned Absences

| URL Pattern | View Function | Name | Description |
| --- | --- | --- | --- |
| `/volunteers/planned-absences/` | `planned_absence_list` | `planned_absence_list` | List absences (own or all for leaders) |
| `/volunteers/planned-absences/create/` | `planned_absence_create` | `planned_absence_create` | Declare a new absence |
| `/volunteers/planned-absences/<uuid:pk>/edit/` | `planned_absence_edit` | `planned_absence_edit` | Edit absence (owner or staff) |
| `/volunteers/planned-absences/<uuid:pk>/delete/` | `planned_absence_delete` | `planned_absence_delete` | Delete absence (owner or staff) |

### Swap Requests

| URL Pattern | View Function | Name | Description |
| --- | --- | --- | --- |
| `/volunteers/swap-requests/` | `swap_request_list` | `swap_request_list` | List swap requests (own or all for staff) |
| `/volunteers/swap-requests/create/` | `swap_request_create` | `swap_request_create` | Create new swap request |

### View Details

**position_list** -- Displays active positions annotated with `num_volunteers` (count of available volunteers per position).

**schedule_list** -- Displays all active schedules ordered by date. Supports optional `date_from` and `date_to` GET parameters for date range filtering.

**my_schedule** -- Displays the current user's volunteer schedule entries. Requires `member_profile`.

**availability_update** -- GET renders all active positions with the current user's existing availability records. POST iterates over all positions and uses `update_or_create` to set `is_available` (checkbox) and `frequency` (select) per position. Default frequency is `monthly`. Redirects to `my_schedule` on success.

**planned_absence_list** -- Regular members see only their own absences. Users with roles `admin`, `pastor`, `deacon`, or `group_leader` see all active absences.

**planned_absence_create** -- Manual form (no Django Form class). Validates that both dates are provided and `end_date >= start_date`. Creates `PlannedAbsence` for the current member.

**planned_absence_edit** -- Allows the absence owner or staff (`Roles.STAFF_ROLES`) to edit. Same validation as create.

**planned_absence_delete** -- Allows the absence owner or staff to delete. GET shows confirmation, POST performs hard delete.

**swap_request_list** -- Staff sees all active swap requests. Regular members see only requests where they are `requested_by` or `swap_with`.

**swap_request_create** -- Renders `SwapRequestForm` scoped to the current member's future schedules.

## Templates

| Template | Used By | Description |
| --- | --- | --- |
| `templates/volunteers/position_list.html` | `position_list` | Active positions with role type, description, and volunteer count |
| `templates/volunteers/position_form.html` | `position_create`, `position_update` | Shared create/edit form for positions |
| `templates/volunteers/position_delete.html` | `position_delete` | Delete position confirmation |
| `templates/volunteers/schedule_list.html` | `schedule_list` | Full schedule table (date, member, position, status) with date filters |
| `templates/volunteers/schedule_form.html` | `schedule_create`, `schedule_update` | Shared create/edit form for schedule entries |
| `templates/volunteers/schedule_delete.html` | `schedule_delete` | Delete schedule confirmation |
| `templates/volunteers/my_schedule.html` | `my_schedule` | Current user's schedule entries |
| `templates/volunteers/availability_update.html` | `availability_update` | Checkbox per position + frequency dropdown |
| `templates/volunteers/planned_absence_list.html` | `planned_absence_list` | List of planned absences with dates and reason |
| `templates/volunteers/planned_absence_form.html` | `planned_absence_create`, `planned_absence_edit` | Shared create/edit absence form |
| `templates/volunteers/planned_absence_delete.html` | `planned_absence_delete` | Delete absence confirmation |
| `templates/volunteers/swap_request_list.html` | `swap_request_list` | List of swap requests with status |
| `templates/volunteers/swap_request_form.html` | `swap_request_create` | Swap request creation form |

All templates extend `base.html` and use the W3CRM/DexignZone template system. Templates are located in the global `templates/volunteers/` directory, not inside the app directory.

## Celery Tasks

### send_volunteer_schedule_reminders

Located in `apps/volunteers/tasks.py`. A `@shared_task` that sends progressive reminders for upcoming volunteer schedules.

**Reminder windows:**

| Days Until Schedule | Flag Set | Message Content |
| --- | --- | --- |
| <= 5 days | `reminder_5days_sent` | "dans 5 jours" |
| <= 3 days | `reminder_3days_sent` | "dans 3 jours" |
| <= 1 day | `reminder_1day_sent` | "DEMAIN" |
| 0 (same day) | `reminder_sameday_sent` | "C'est aujourd'hui!" |

**Behavior:**

- Queries `VolunteerSchedule` records with `date >= today` and status in `[SCHEDULED, CONFIRMED]`
- Checks each reminder flag in order (5d, 3d, 1d, same-day) and sends the first unsent one
- Creates a `Notification` record (from `apps.communication.models`) with:
  - `notification_type = 'volunteer'`
  - `link = '/volunteers/'`
  - `title = 'Rappel de benevolat'`
- Sets `reminder_sent = True` (legacy flag) along with the specific window flag
- Returns the total count of reminders sent
- Skips `DECLINED`, `COMPLETED`, and `NO_SHOW` statuses
- Skips schedules with dates in the past

## Admin Configuration

### VolunteerPositionAdmin

- **Extends:** `BaseModelAdmin`
- **list_display:** `name`, `role_type`, `min_volunteers`, `max_volunteers`, `is_active`
- **list_filter:** `role_type`, `is_active`
- **search_fields:** `name`

### VolunteerAvailabilityAdmin

- **Extends:** `BaseModelAdmin`
- **list_display:** `member`, `position`, `is_available`, `frequency`
- **list_filter:** `position`, `is_available`, `frequency`
- **autocomplete_fields:** `member`, `position`

### VolunteerScheduleAdmin

- **Extends:** `BaseModelAdmin`
- **list_display:** `member`, `position`, `date`, `status`, `reminder_sent`
- **list_filter:** `position`, `status`, `date`
- **autocomplete_fields:** `member`, `position`, `event`
- **date_hierarchy:** `date`

### SwapRequestAdmin

- **Extends:** `BaseModelAdmin`
- **list_display:** `original_schedule`, `requested_by`, `swap_with`, `status`
- **list_filter:** `status`

## Permissions Matrix

### Frontend Views

| View | Authentication | Role Required | Notes |
| --- | --- | --- | --- |
| `position_list` | `@login_required` | Any authenticated | Shows active positions only |
| `position_create` | `@login_required` | Admin or Pastor | Redirects others to `/` |
| `position_update` | `@login_required` | Admin or Pastor | Redirects others to `/` |
| `position_delete` | `@login_required` | Admin or Pastor | Redirects others to `/` |
| `schedule_list` | `@login_required` | Any authenticated | Shows active schedules |
| `schedule_create` | `@login_required` | Admin or Pastor | Redirects others to `/` |
| `schedule_update` | `@login_required` | Admin or Pastor | Redirects others to `/` |
| `schedule_delete` | `@login_required` | Admin or Pastor | Redirects others to `/` |
| `my_schedule` | `@login_required` | Any with member profile | Requires `member_profile` |
| `availability_update` | `@login_required` | Any with member profile | Requires `member_profile` |
| `planned_absence_list` | `@login_required` | Any with member profile | Leaders see all; members see own |
| `planned_absence_create` | `@login_required` | Any with member profile | Creates for current member |
| `planned_absence_edit` | `@login_required` | Owner or Staff | `Roles.STAFF_ROLES` can edit any |
| `planned_absence_delete` | `@login_required` | Owner or Staff | `Roles.STAFF_ROLES` can delete any |
| `swap_request_list` | `@login_required` | Any with member profile | Staff sees all; members see own |
| `swap_request_create` | `@login_required` | Any with member profile | Scoped to member's schedules |

### API Views

| ViewSet | Read Actions | Write Actions |
| --- | --- | --- |
| `VolunteerPositionViewSet` | `IsMember` (list, retrieve) | `IsPastorOrAdmin` (create, update, delete) |
| `VolunteerScheduleViewSet` | `IsMember` (list, retrieve, my_schedule) | `IsPastorOrAdmin` (create, update, delete, confirm) |
| `VolunteerAvailabilityViewSet` | `IsMember` (all CRUD, scoped by user) | `IsMember` (all CRUD, scoped by user) |
| `SwapRequestViewSet` | `IsMember` (all CRUD, scoped by user) | `IsMember` (all CRUD, scoped by user) |

**Note:** `IsMember` only checks `request.user.is_authenticated`. `IsPastorOrAdmin` checks for membership in `Roles.STAFF_ROLES` (deacon, pastor, admin) or Django `is_staff`/`is_superuser`.

## Dependencies

| Dependency | Usage |
| --- | --- |
| `apps.core.models.BaseModel` | Model inheritance (UUID PK, timestamps, `is_active`) |
| `apps.core.constants` | `VolunteerRole`, `ScheduleStatus`, `VolunteerFrequency`, `Roles` |
| `apps.core.permissions` | `IsMember`, `IsPastorOrAdmin` |
| `apps.core.mixins` | `W3CRMFormMixin` (for form styling) |
| `apps.members.Member` | Foreign key target for all member references |
| `apps.events.Event` | Optional FK in `VolunteerSchedule` |
| `apps.communication.models.Notification` | Created by the Celery reminder task |
| `djangorestframework` | API ViewSets, serializers, permissions |
| `django-filter` | `DjangoFilterBackend` for API filtering |
| `celery` | `@shared_task` for schedule reminders |

## Tests

Test framework: **pytest** with `pytest-django` and `factory_boy`.

### Test Files

| File | Test Classes | Coverage Area |
| --- | --- | --- |
| `tests/factories.py` | `VolunteerPositionFactory`, `VolunteerAvailabilityFactory`, `VolunteerScheduleFactory`, `PlannedAbsenceFactory`, `SwapRequestFactory` | Factory Boy factories for all 5 models |
| `tests/test_models.py` | `TestVolunteerPositionStr` (2 tests), `TestVolunteerScheduleStr` (2 tests), `TestPlannedAbsenceStr` (1 test) | `__str__` methods for Position, Schedule, and PlannedAbsence |
| `tests/test_forms.py` | `TestVolunteerPositionForm` (6 tests), `TestVolunteerScheduleForm` (7 tests) | Validation, required fields, optional fields, save/update |
| `tests/test_views_frontend.py` | `TestPositionList` (5 tests), `TestScheduleList` (5 tests), `TestMySchedule` (4 tests), `TestAvailabilityUpdate` (9 tests), `TestPlannedAbsenceList` (5 tests), `TestPlannedAbsenceCreate` (5 tests), `TestPositionCreate` (7 tests), `TestPositionUpdate` (7 tests), `TestPositionDelete` (7 tests), `TestScheduleCreate` (6 tests), `TestScheduleUpdate` (7 tests), `TestScheduleDelete` (7 tests) | Auth enforcement, role-based permissions, CRUD, filtering, scoping, 404 handling |
| `tests/test_views_api.py` | `TestVolunteerPositionList` (4 tests), `TestVolunteerPositionRetrieve` (2 tests), `TestVolunteerPositionCreate` (2 tests), `TestVolunteerPositionUpdate` (2 tests), `TestVolunteerPositionDelete` (2 tests), `TestVolunteerScheduleList` (4 tests), `TestVolunteerScheduleRetrieve` (1 test), `TestVolunteerScheduleCreate` (2 tests), `TestVolunteerScheduleMySchedule` (3 tests), `TestVolunteerScheduleConfirm` (2 tests), `TestVolunteerScheduleUpdateDelete` (3 tests), `TestVolunteerAvailabilityList` (4 tests), `TestVolunteerAvailabilityCRUD` (4 tests), `TestSwapRequestList` (6 tests), `TestSwapRequestCRUD` (4 tests) | Full API coverage: CRUD, filters, search, ordering, custom actions, scoping, permissions |
| `tests/test_tasks.py` | `TestSendVolunteerScheduleReminders` (15 tests) | All reminder windows (5d, 3d, 1d, same-day), duplicate prevention, status filtering, notification content, past schedule exclusion, multi-schedule processing |

### Key Test Scenarios

- **Authentication:** All views and endpoints redirect unauthenticated users to `/accounts/login/` or return 403
- **Role-based access:** Regular members cannot create/update/delete positions or schedules; admin/pastor can
- **No member profile:** Users without `member_profile` are redirected to `/` on frontend or return appropriate errors on API
- **Queryset scoping:** Members see only their own availability and swap requests; staff sees all
- **Availability update:** Checkbox-based `update_or_create` pattern correctly sets `is_available` and `frequency` per position
- **Planned absence validation:** Missing dates and `end_date < start_date` are rejected
- **Planned absence ownership:** Only the owner or staff roles can edit/delete
- **Swap request scoping:** Members see requests where they are `requested_by` or `swap_with`
- **Schedule confirm:** POST to `confirm` action sets status to `confirmed`
- **Only active records shown:** `is_active=False` positions and schedules are excluded from frontend lists
- **Reminder task:** Sends correct messages at each window, prevents duplicate sends, skips declined/completed/past schedules, creates Notification records with correct type and link
- **404 handling:** Nonexistent UUIDs return 404

### Running Tests

```bash
# All volunteers tests
pytest apps/volunteers/ -v

# By category
pytest apps/volunteers/tests/test_models.py -v
pytest apps/volunteers/tests/test_forms.py -v
pytest apps/volunteers/tests/test_views_frontend.py -v
pytest apps/volunteers/tests/test_views_api.py -v
pytest apps/volunteers/tests/test_tasks.py -v

# Specific test class
pytest apps/volunteers/tests/test_tasks.py::TestSendVolunteerScheduleReminders -v
```
