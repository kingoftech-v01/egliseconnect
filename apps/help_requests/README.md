# Help Requests App

> **Django application**: `apps.help_requests`
> **Path**: `apps/help_requests/`

---

## Overview

The Help Requests app provides a confidential support ticket system for the EgliseConnect church management platform. Church members can submit requests for assistance across configurable categories such as prayer support, financial aid, material needs, or pastoral counseling.

### Key Features

- **Auto-numbered tickets** -- Each request receives a unique identifier in `HR-YYYYMM-XXXX` format (e.g., `HR-202602-0001`).
- **Confidentiality flag** -- Requests marked confidential are visible only to pastors and administrators.
- **Role-based access control** -- Granular visibility rules for members, group leaders, pastors, and administrators.
- **Status workflow** -- Requests progress through `New -> In Progress -> Resolved -> Closed` states.
- **Assignment system** -- Staff can assign requests to pastor/admin members, which auto-transitions status from New to In Progress.
- **Commenting with internal notes** -- Public comments visible to the requester, plus staff-only internal notes hidden from regular members.
- **Category management** -- Full CRUD for help request categories with safe deactivation (categories with existing requests are deactivated rather than deleted).
- **Dual-layer architecture** -- Both template-based frontend views and a Django REST Framework API.

---

## File Structure

```
apps/help_requests/
    __init__.py
    apps.py                     # AppConfig
    models.py                   # 3 models: HelpRequestCategory, HelpRequest, HelpRequestComment
    forms.py                    # 5 forms
    serializers.py              # 7 serializers
    views_api.py                # 2 DRF ViewSets
    views_frontend.py           # 10 function-based views
    urls.py                     # API router + frontend URL patterns
    admin.py                    # 3 admin classes + 1 inline
    migrations/
        0001_initial.py
    tests/
        __init__.py
        factories.py            # 3 factory_boy factories
        test_forms.py           # 30 form tests
        test_models.py          # 11 model tests
        test_views_api.py       # 16 API tests
        test_views_frontend.py  # 84 frontend view tests
```

---

## Models

All models inherit from `apps.core.models.BaseModel`, which provides `id` (UUID primary key), `created_at`, `updated_at`, and `is_active` fields.

### HelpRequestCategory

Reference data model for categorizing help requests (e.g., Prayer, Financial, Material, Pastoral).

| Field | Type | Description |
|---|---|---|
| `name` | `CharField(100)` | Category name in English |
| `name_fr` | `CharField(100)` | Category name in French (optional) |
| `description` | `TextField` | Category description (optional) |
| `icon` | `CharField(50)` | Icon identifier for the UI (e.g., `'help-circle'`) |
| `order` | `PositiveIntegerField` | Display order (default: `0`) |

**Inherited fields**: `id` (UUID), `created_at`, `updated_at`, `is_active`

**Meta**: Ordered by `order`, then `name`. Uses `on_delete=PROTECT` from `HelpRequest`, so categories with associated requests cannot be deleted at the database level.

---

### HelpRequest

The primary model representing a support ticket submitted by a church member.

| Field | Type | Description |
|---|---|---|
| `request_number` | `CharField(20)` | Auto-generated unique identifier (`HR-YYYYMM-XXXX`), not editable |
| `member` | `ForeignKey(Member)` | The member who submitted the request (`on_delete=CASCADE`) |
| `category` | `ForeignKey(HelpRequestCategory)` | Request category (`on_delete=PROTECT`) |
| `title` | `CharField(200)` | Short title describing the request |
| `description` | `TextField` | Detailed description of the need |
| `urgency` | `CharField(20)` | Urgency level (choices from `HelpRequestUrgency`) |
| `status` | `CharField(20)` | Current workflow status (choices from `HelpRequestStatus`) |
| `assigned_to` | `ForeignKey(Member)` | Staff member assigned to handle the request (nullable, `on_delete=SET_NULL`) |
| `is_confidential` | `BooleanField` | When `True`, only pastors and admins can view (default: `False`) |
| `resolved_at` | `DateTimeField` | Timestamp when the request was resolved (nullable) |
| `resolution_notes` | `TextField` | Notes recorded upon resolution (optional) |

**Inherited fields**: `id` (UUID), `created_at`, `updated_at`, `is_active`

**Urgency Choices** (`HelpRequestUrgency`):

| Constant | Value | Display Label |
|---|---|---|
| `LOW` | `'low'` | Faible |
| `MEDIUM` | `'medium'` | Moyenne |
| `HIGH` | `'high'` | Elevee |
| `URGENT` | `'urgent'` | Urgente |

**Status Choices** (`HelpRequestStatus`):

| Constant | Value | Display Label | Description |
|---|---|---|---|
| `NEW` | `'new'` | Nouvelle | Just created, awaiting attention |
| `IN_PROGRESS` | `'in_progress'` | En cours | Assigned and being handled |
| `RESOLVED` | `'resolved'` | Resolue | Successfully completed |
| `CLOSED` | `'closed'` | Fermee | Closed (with or without resolution) |

**Business Methods**:

| Method | Description |
|---|---|
| `save()` | Auto-generates `request_number` via `generate_request_number()` if not already set |
| `mark_resolved(notes='')` | Sets status to `RESOLVED`, records `resolved_at` timestamp and `resolution_notes` |
| `assign_to(member)` | Assigns the request to a staff member; auto-transitions status from `NEW` to `IN_PROGRESS` |

**Meta**: Ordered by `-created_at` (newest first).

---

### HelpRequestComment

A comment or internal staff note attached to a help request.

| Field | Type | Description |
|---|---|---|
| `help_request` | `ForeignKey(HelpRequest)` | The associated help request (`on_delete=CASCADE`) |
| `author` | `ForeignKey(Member)` | Comment author (`on_delete=CASCADE`) |
| `content` | `TextField` | Comment text |
| `is_internal` | `BooleanField` | When `True`, only visible to pastors and admins (default: `False`) |

**Inherited fields**: `id` (UUID), `created_at`, `updated_at`, `is_active`

**Business rule**: Comments with `is_internal=True` are never shown to regular members, even if they are the request owner. Only pastors and administrators can view them. If a non-staff member attempts to create an internal comment, the system forces `is_internal=False`.

**Meta**: Ordered by `created_at` (chronological).

---

## Forms

Five forms, all using `W3CRMFormMixin` for consistent styling with the DexignZone template.

### HelpRequestForm

Creates a new help request. Used by the `request_create` frontend view.

| Field | Widget | Required |
|---|---|---|
| `category` | Select | Yes |
| `title` | TextInput | Yes |
| `description` | Textarea (5 rows) | Yes |
| `urgency` | Select | Yes |
| `is_confidential` | Checkbox | No (default: `False`) |

### HelpRequestCommentForm

Adds a comment to a help request.

| Field | Widget | Required |
|---|---|---|
| `content` | Textarea (3 rows) | Yes |
| `is_internal` | Checkbox | No (default: `False`) |

### HelpRequestAssignForm

Assigns a help request to a staff member. The `assigned_to` select widget is dynamically populated with active pastor and admin members at form initialization.

| Field | Widget | Required |
|---|---|---|
| `assigned_to` | Select (filtered: active pastors + admins) | Yes |

### HelpRequestResolveForm

Resolves a help request with optional notes.

| Field | Widget | Required |
|---|---|---|
| `resolution_notes` | Textarea (3 rows) | No |

### HelpRequestCategoryForm

Creates or edits a help request category. Used by category CRUD views.

| Field | Widget | Required |
|---|---|---|
| `name` | TextInput | Yes |
| `name_fr` | TextInput | No |
| `description` | Textarea (3 rows) | No |
| `icon` | TextInput | No |
| `order` | NumberInput | No (default: `0`) |
| `is_active` | Checkbox | No (default: `True`) |

---

## Serializers

| Serializer | Purpose | Extra Read-Only Fields |
|---|---|---|
| `HelpRequestCategorySerializer` | Full category representation | -- |
| `HelpRequestSerializer` | Full help request with nested comments | `member_name`, `category_name`, `assigned_to_name`, `urgency_display`, `status_display`, `comments` (nested) |
| `HelpRequestCreateSerializer` | Limited fields for creation; auto-assigns `member` from `request.user.member_profile` | -- |
| `HelpRequestCommentSerializer` | Full comment representation | `author_name` |
| `HelpRequestAssignSerializer` | Assignment action payload | -- (accepts `assigned_to` UUID only) |
| `HelpRequestResolveSerializer` | Resolution action payload | -- (accepts `resolution_notes` only) |
| `CommentCreateSerializer` | Comment creation payload | -- (accepts `content` + `is_internal`) |

---

## API Endpoints

All endpoints are prefixed with `/api/v1/help-requests/`. Authentication is required for all endpoints.

### HelpRequestCategoryViewSet (Read-Only)

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/api/v1/help-requests/categories/` | List all active categories | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/categories/{id}/` | Retrieve a single category | `IsAuthenticated` |

### HelpRequestViewSet (Full CRUD + Custom Actions)

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/api/v1/help-requests/requests/` | List help requests (filtered by role) | `IsAuthenticated` |
| `POST` | `/api/v1/help-requests/requests/` | Create a new help request | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/requests/{id}/` | Retrieve a help request | `IsAuthenticated` |
| `PUT/PATCH` | `/api/v1/help-requests/requests/{id}/` | Update a help request | `IsAuthenticated` |
| `DELETE` | `/api/v1/help-requests/requests/{id}/` | Delete a help request | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/requests/my_requests/` | List the authenticated member's own requests | `IsAuthenticated` |
| `POST` | `/api/v1/help-requests/requests/{id}/assign/` | Assign request to a staff member | `IsPastor \| IsAdmin` |
| `POST` | `/api/v1/help-requests/requests/{id}/resolve/` | Mark request as resolved | `IsPastor \| IsAdmin` |
| `POST` | `/api/v1/help-requests/requests/{id}/comment/` | Add a comment to a request | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/requests/{id}/comments/` | List comments on a request | `IsAuthenticated` |

**Filtering** (via `django-filter`): `status`, `urgency`, `category`, `assigned_to`, `is_confidential`

**Search**: `title`, `description`, `request_number`

**Ordering**: `created_at`, `urgency`, `status`

**Queryset Scoping by Role**:

| Role | Visible Requests |
|---|---|
| Pastor / Admin | All requests |
| Group Leader | Own requests + group members' non-confidential requests |
| Regular Member | Own requests only |
| User without Member profile | None (empty queryset) |

---

## Frontend URLs

All frontend URLs are prefixed with `/help-requests/` and use the namespace `frontend:help_requests:`.

### Help Request Views

| Path | URL Name | View | Description |
|---|---|---|---|
| `/help-requests/` | `request_list` | `request_list` | List all requests with filters and stats (pastor/admin only) |
| `/help-requests/create/` | `request_create` | `request_create` | Form to submit a new help request (any member) |
| `/help-requests/my-requests/` | `my_requests` | `my_requests` | Paginated list of the current member's own requests |
| `/help-requests/<uuid:pk>/` | `request_detail` | `request_detail` | Full detail view with comments, assignment form, and status timeline |
| `/help-requests/<uuid:pk>/update/` | `request_update` | `request_update` | Handles assign, resolve, and close actions (POST only, redirects) |
| `/help-requests/<uuid:pk>/comment/` | `request_comment` | `request_comment` | Add a comment to a request (POST only, redirects) |

### Category Management Views

| Path | URL Name | View | Description |
|---|---|---|---|
| `/help-requests/categories/` | `category_list` | `category_list` | List all categories including inactive (pastor/admin only) |
| `/help-requests/categories/create/` | `category_create` | `category_create` | Form to create a new category (pastor/admin only) |
| `/help-requests/categories/<uuid:pk>/edit/` | `category_edit` | `category_edit` | Form to edit an existing category (pastor/admin only) |
| `/help-requests/categories/<uuid:pk>/delete/` | `category_delete` | `category_delete` | Confirmation page and delete/deactivate action (pastor/admin only) |

**View Details**:

- **`request_list`**: Supports query parameter filters for `status`, `urgency`, `category`, and `q` (text search on title and description). Provides a `stats` context with counts for open, in-progress, and resolved requests.
- **`request_detail`**: Shows a status timeline, comment list (internal comments hidden for non-staff), comment form, and assignment form (staff only). Provides `can_manage` and `can_close` flags for conditional template rendering. Owners can close their own resolved requests.
- **`request_update`**: Dispatches based on the `action` POST field: `assign` (assign to staff), `resolve` (mark resolved with notes), or `close` (close the request).
- **`category_delete`**: If the category has associated requests, it deactivates the category instead of deleting it.

---

## Templates

All templates are located in `templates/help_requests/`.

| Template | Description |
|---|---|
| `request_list.html` | Staff dashboard listing all requests with status/urgency/category filters, search, and summary statistics |
| `request_create.html` | Form for submitting a new help request with category selection |
| `request_detail.html` | Full request detail with status timeline, comments section, assignment form (staff), and comment form |
| `my_requests.html` | Paginated list of the current member's own requests with status and urgency indicators |
| `category_list.html` | Admin table of all categories (active and inactive) with edit/delete actions |
| `category_form.html` | Shared form template for creating and editing categories |
| `category_delete.html` | Delete confirmation page showing associated request count and deactivation warning |

---

## Admin Configuration

Three model admin classes registered with the Django admin, all inheriting from `apps.core.admin.BaseModelAdmin`.

### HelpRequestCategoryAdmin

- **List display**: `name`, `name_fr`, `icon`, `is_active`, `order`
- **List filters**: `is_active`
- **Search fields**: `name`, `name_fr`
- **Ordering**: `order`, `name`

### HelpRequestAdmin

- **List display**: `request_number`, `title`, `member`, `category`, `urgency`, `status`, `assigned_to`, `created_at`
- **List filters**: `status`, `urgency`, `category`, `is_confidential`, `created_at`
- **Search fields**: `request_number`, `title`, `description`, `member__first_name`, `member__last_name`
- **Read-only fields**: `request_number`, `created_at`, `updated_at`, `resolved_at`
- **Raw ID fields**: `member`, `assigned_to`
- **Inline**: `HelpRequestCommentInline` (TabularInline, extra=0, read-only `author` and `created_at`)

**Fieldsets**:

| Section | Fields | Collapsed |
|---|---|---|
| (default) | `request_number`, `member`, `category`, `title`, `description` | No |
| Status | `status`, `urgency`, `assigned_to`, `is_confidential` | No |
| Resolution | `resolved_at`, `resolution_notes` | Yes |
| Timestamps | `created_at`, `updated_at` | Yes |

### HelpRequestCommentAdmin

- **List display**: `help_request`, `author`, `is_internal`, `created_at`
- **List filters**: `is_internal`, `created_at`
- **Search fields**: `content`, `help_request__request_number`
- **Raw ID fields**: `help_request`, `author`

---

## Permissions Matrix

| Role | Create Request | View Own | View Group Members' | View All | Assign | Resolve / Close | Internal Notes | View Confidential |
|---|---|---|---|---|---|---|---|---|
| **Member** | Yes | Yes | No | No | No | No | No | No |
| **Group Leader** | Yes | Yes | Yes (non-confidential only) | No | No | No | No | No |
| **Pastor** | Yes | Yes | Yes | Yes | Yes | Yes | Read + Write | Yes |
| **Admin** | Yes | Yes | Yes | Yes | Yes | Yes | Read + Write | Yes |

**Additional rules**:

- A user without a `member_profile` is redirected away from all views and receives empty querysets from the API.
- Regular members who attempt to create internal comments have `is_internal` silently forced to `False`.
- Group leaders can view request details for their group members but cannot view confidential requests, even for their own group members.
- Owners can close their own requests only when the status is `RESOLVED`.

---

## Dependencies

| Dependency | Usage |
|---|---|
| `apps.core.models.BaseModel` | Base model providing UUID PK, `created_at`, `updated_at`, `is_active` |
| `apps.core.constants.HelpRequestUrgency` | Urgency level choices for `HelpRequest.urgency` |
| `apps.core.constants.HelpRequestStatus` | Status choices for `HelpRequest.status` |
| `apps.core.permissions.IsPastor` | DRF permission class for pastor-only API actions |
| `apps.core.permissions.IsAdmin` | DRF permission class for admin-only API actions |
| `apps.core.mixins.W3CRMFormMixin` | Form mixin for DexignZone template styling |
| `apps.core.utils.generate_request_number` | Generates unique `HR-YYYYMM-XXXX` request numbers |
| `apps.core.admin.BaseModelAdmin` | Base admin class for all registered models |
| `apps.members.Member` | FK target for `member` and `assigned_to` fields |
| `apps.members.GroupMembership` | Used for group leader queryset filtering |
| `django-filter` | DRF filter backend for API endpoint filtering |
| `djangorestframework` | API ViewSets, serializers, permissions |

---

## Tests

Tests use `pytest` with `pytest-django` and `factory_boy`. There are **141 tests** across 4 test modules.

### Test Breakdown

| Module | Tests | Coverage |
|---|---|---|
| `tests/test_models.py` | 11 | Model creation, `__str__`, `request_number` generation, `mark_resolved`, `assign_to`, confidential flag |
| `tests/test_forms.py` | 30 | Validation for all 4 forms, required fields, max length, widget attrs, labels, urgency choices, staff filtering |
| `tests/test_views_api.py` | 16 | CRUD operations, `my_requests`, `assign`, `resolve`, `comment`/`comments` actions, role-based queryset filtering, internal comment enforcement, confidential hiding, edge cases (no profile, nonexistent member) |
| `tests/test_views_frontend.py` | 84 | All 10 frontend views, authentication checks, role-based access, filters, search, pagination, timeline, close permissions, category CRUD, deactivation on delete, group leader visibility |

### Factories

| Factory | Model | Key Defaults |
|---|---|---|
| `HelpRequestCategoryFactory` | `HelpRequestCategory` | `icon='help-circle'`, `is_active=True`, sequential `name` and `order` |
| `HelpRequestFactory` | `HelpRequest` | `urgency='medium'`, `status='new'`, `is_confidential=False`, auto `member` and `category` sub-factories |
| `HelpRequestCommentFactory` | `HelpRequestComment` | `is_internal=False`, auto `help_request` and `author` sub-factories |

### Running Tests

```bash
# All help_requests tests
pytest apps/help_requests/ -v

# By module
pytest apps/help_requests/tests/test_models.py -v
pytest apps/help_requests/tests/test_forms.py -v
pytest apps/help_requests/tests/test_views_api.py -v
pytest apps/help_requests/tests/test_views_frontend.py -v
```

---

## Request Lifecycle

```
1. Member submits a help request
       |
       v
   [NEW] Request created with auto-generated number (HR-YYYYMM-XXXX)
       |
       v
2. Pastor/Admin assigns the request to a staff member (assign_to)
       |
       v
   [IN_PROGRESS] Being handled; comments (public + internal) can be added
       |
       v
3. Pastor/Admin resolves the request (mark_resolved)
       |
       v
   [RESOLVED] Completed (resolved_at timestamp + resolution_notes recorded)
       |
       v
4. Staff or owner closes the request
       |
       v
   [CLOSED] Archived
```
