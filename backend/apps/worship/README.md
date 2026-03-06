# Worship App

## Overview

The worship app handles the planning and coordination of worship services (cultes). It supports building a service order with typed sections, assigning members to sections based on department and task types, tracking assignment confirmations, and providing members with a view of their upcoming assignments.

### Key Features

- **Service Planning**: Create worship services with date, time, theme, and validation deadline
- **Service Sections**: Build a service order with typed, ordered sections (worship, prayer, preaching, etc.)
- **Department Integration**: Link sections to departments and filter eligible members by department task types
- **Member Assignments**: Assign members to sections with notification and confirm/decline workflow
- **Eligibility Lists**: Define which members are eligible for specific section types
- **Confirmation Tracking**: Track assignment responses with confirmation rate per service
- **My Assignments**: Members see their upcoming and past worship assignments

## File Structure

```
apps/worship/
├── __init__.py
├── admin.py                 # Django admin (basic registration)
├── apps.py                  # App config
├── forms.py                 # WorshipServiceForm, ServiceSectionForm, ServiceAssignmentForm
├── models.py                # WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList
├── services.py              # WorshipServiceManager (business logic)
├── urls.py                  # Frontend URL patterns (no API yet)
├── views_frontend.py        # Template-based views (8 views)
├── migrations/
│   └── 0001_initial.py
└── tests/
    ├── __init__.py
    ├── factories.py          # Test factories
    ├── test_models.py        # Model tests
    ├── test_services.py      # Service tests
    ├── test_views_frontend.py # Frontend view tests
    └── test_tasks.py         # Task tests
```

## Models

### WorshipService

A planned worship service (culte).

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `date` | DateField | Service date |
| `start_time` | TimeField | Start time |
| `end_time` | TimeField | End time (optional) |
| `duration_minutes` | PositiveIntegerField | Duration in minutes (default: 120) |
| `status` | CharField(20) | `draft`, `planned`, `confirmed`, `completed`, `cancelled` |
| `theme` | CharField(300) | Service theme (optional) |
| `notes` | TextField | Additional notes |
| `created_by` | ForeignKey → Member | Staff member who created the service |
| `validation_deadline` | DateField | Auto-set to 14 days before service date |
| `event` | ForeignKey → Event | Optional linked event |

**Properties:**
- `confirmation_rate` → `int`: Percentage of confirmed assignments (0-100)
- `total_assignments` → `int`: Total number of member assignments
- `confirmed_assignments` → `int`: Number of confirmed assignments

**Auto-save behavior:**
- `validation_deadline` defaults to `date - 14 days` if not set

### ServiceSection

A section/segment within a worship service.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `service` | ForeignKey → WorshipService | Parent service |
| `name` | CharField(200) | Section name |
| `order` | PositiveIntegerField | Display order |
| `duration_minutes` | PositiveIntegerField | Duration (default: 15) |
| `section_type` | CharField(30) | Type: `worship`, `prayer`, `preaching`, `announcements`, `offering`, `testimony`, `special_music`, `reading`, `communion`, `other` |
| `department` | ForeignKey → Department | Responsible department (optional) |
| `notes` | TextField | Additional notes |

**Constraints:**
- `unique_together = ['service', 'order']`

### ServiceAssignment

Assignment of a member to a section of a worship service.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `section` | ForeignKey → ServiceSection | The section |
| `member` | ForeignKey → Member | Assigned member |
| `task_type` | ForeignKey → DepartmentTaskType | Specific task within the department (optional) |
| `status` | CharField(20) | `assigned`, `confirmed`, `declined` |
| `responded_at` | DateTimeField | When the member responded |
| `notes` | TextField | Additional notes |
| `reminder_5days_sent` | BooleanField | Reminder tracking flags |
| `reminder_3days_sent` | BooleanField | |
| `reminder_1day_sent` | BooleanField | |
| `reminder_sameday_sent` | BooleanField | |

**Constraints:**
- `unique_together = ['section', 'member']`

### EligibleMemberList

Defines which members are eligible for a specific section type.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `section_type` | CharField(30) | Section type (unique) |
| `members` | ManyToManyField → Member | Eligible members |
| `department` | ForeignKey → Department | Associated department (optional) |

## Forms

| Form | Type | Description |
|------|------|-------------|
| `WorshipServiceForm` | ModelForm | Create/edit services (date, times, duration, theme, notes) |
| `ServiceSectionForm` | ModelForm | Create sections (name, order, type, duration, department, notes) |
| `ServiceAssignmentForm` | Form | Assign member to section (member select, task type filtered by section department, notes) |

All forms use `W3CRMFormMixin` for automatic CSS class application.

## Services

### WorshipServiceManager

| Method | Description |
|--------|-------------|
| `create_service(date, start_time, created_by, ...)` | Create a new worship service with DRAFT status |
| `add_section(service, name, order, section_type, ...)` | Add a section to a service |
| `assign_member(section, member, task_type, notes)` | Assign member + send notification |
| `member_respond(assignment, accepted)` | Confirm or decline assignment; notify admins on decline |
| `update_service_status(service, new_status)` | Update service status |

## API Endpoints

Currently `api_urlpatterns = []` — no API endpoints defined yet. All operations are through frontend views.

## Frontend URLs

Base path: `/worship/`

| URL | View | Name | Access |
|-----|------|------|--------|
| `/worship/services/` | `service_list` | `worship:service_list` | All members |
| `/worship/services/create/` | `service_create` | `worship:service_create` | Staff roles |
| `/worship/services/<uuid>/` | `service_detail` | `worship:service_detail` | All members |
| `/worship/services/<uuid>/edit/` | `service_edit` | `worship:service_edit` | Staff roles |
| `/worship/services/<uuid>/sections/` | `section_manage` | `worship:section_manage` | Staff roles |
| `/worship/sections/<uuid>/assign/` | `assign_members` | `worship:assign_members` | Staff roles |
| `/worship/my-assignments/` | `my_assignments` | `worship:my_assignments` | All members |
| `/worship/assignments/<uuid>/respond/` | `assignment_respond` | `worship:assignment_respond` | Assigned member |

**Staff roles** are determined by `Roles.STAFF_ROLES` checked via `member.all_roles`.

## Templates

All templates are in `templates/worship/` and extend `base.html`.

| Template | View | Description |
|----------|------|-------------|
| `service_list.html` | `service_list` | Paginated service list with status filter and upcoming filter |
| `service_detail.html` | `service_detail` | Service details with sections and assignments |
| `service_form.html` | `service_create` / `service_edit` | Service create/edit form |
| `section_form.html` | `section_manage` | Add section form |
| `assign_members.html` | `assign_members` | Assign member to section with existing assignments list |
| `my_assignments.html` | `my_assignments` | Member's upcoming and past worship assignments |

## Admin Configuration

All 4 models are registered with basic `admin.site.register()` (no custom admin classes).

## Permissions Matrix

| Action | Member | Volunteer | Group Leader | Deacon | Pastor | Admin |
|--------|--------|-----------|-------------|--------|--------|-------|
| View service list | Yes | Yes | Yes | Yes | Yes | Yes |
| View service detail | Yes | Yes | Yes | Yes | Yes | Yes |
| Create/edit service | — | — | — | Yes* | Yes | Yes |
| Add sections | — | — | — | Yes* | Yes | Yes |
| Assign members | — | — | — | Yes* | Yes | Yes |
| View own assignments | Yes | Yes | Yes | Yes | Yes | Yes |
| Confirm/decline assignment | Yes** | Yes** | Yes** | Yes** | Yes** | Yes** |

\* If included in `Roles.STAFF_ROLES`
\** Only for their own assignments

## Dependencies

- **members**: Member model (assignments, created_by), Department model (section responsibility), DepartmentTaskType model (specific tasks)
- **events**: Event model (optional service link)
- **communication**: Notification model (assignment and decline notifications)
- **core**: BaseModel, constants (WorshipServiceStatus, ServiceSectionType, AssignmentStatus, Roles), mixins (W3CRMFormMixin)

## Tests

Test files in `apps/worship/tests/`:
- `factories.py` — Test data factories
- `test_models.py` — Model creation, properties, constraints, auto-save behavior
- `test_services.py` — WorshipServiceManager business logic tests
- `test_views_frontend.py` — Frontend view tests (access control, form submissions)
- `test_tasks.py` — Celery task tests (reminder sending)
