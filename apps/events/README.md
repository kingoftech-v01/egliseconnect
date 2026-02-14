# Events App

> Event management module for the EgliseConnect church management system.

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Models](#models)
4. [Forms](#forms)
5. [Serializers](#serializers)
6. [API Endpoints](#api-endpoints)
7. [Frontend URLs](#frontend-urls)
8. [Templates](#templates)
9. [Admin Configuration](#admin-configuration)
10. [Permissions Matrix](#permissions-matrix)
11. [Dependencies](#dependencies)
12. [Tests](#tests)

---

## Overview

The `events` app handles the full lifecycle of church events: creation, publishing, RSVP management, calendar visualization, and attendee tracking. It serves as the central scheduling hub for the congregation.

### Key Features

- **Event CRUD** -- Staff users (pastors, admins) can create, edit, cancel, and delete events.
- **Event Types** -- Eight categories (worship, group, meal, special, meeting, training, outreach, other) with color-coded calendar display.
- **RSVP System** -- Members can confirm, decline, or mark "maybe" for events, with optional guest counts.
- **Capacity Management** -- Optional maximum attendee limits; events are automatically marked full when capacity is reached.
- **Interactive Calendar** -- FullCalendar.js-powered monthly/weekly view, loaded via REST API.
- **Online Events** -- Support for virtual events with meeting links.
- **Recurring Events** -- Parent-child event relationship for recurring occurrences.
- **Auto Attendance Sessions** -- Creating an event automatically creates a linked AttendanceSession for attendance tracking.
- **Kiosk + Attendance Integration** -- Kiosk check-ins create both EventRSVP and AttendanceRecord when a session exists.
- **Search and Filters** -- Filter by event type, upcoming/past, and full-text search on title and description.
- **Pagination** -- Event list paginated at 20 items per page.

### Architecture

The app follows EgliseConnect's dual-layer pattern:

- **Frontend layer** -- Django template-based views served under `/events/`
- **API layer** -- Django REST Framework ViewSet served under `/api/v1/events/events/`

All models inherit from `BaseModel`, which provides UUID primary keys, `created_at`/`updated_at` timestamps, and an `is_active` soft-delete flag with `ActiveManager` as the default manager.

---

## File Structure

```text
apps/events/
    __init__.py
    admin.py                  # Django admin configuration
    apps.py                   # AppConfig (name: apps.events)
    forms.py                  # EventForm, RSVPForm (W3CRMFormMixin)
    models.py                 # Event, EventRSVP
    serializers.py            # EventSerializer, EventListSerializer, EventRSVPSerializer
    urls.py                   # Frontend + API URL routing
    views_api.py              # DRF ViewSet with custom actions
    views_frontend.py         # Template-based function views
    migrations/
        __init__.py
        0001_initial.py
        0002_alter_event_image.py
    tests/
        __init__.py
        factories.py          # EventFactory, EventRSVPFactory (factory_boy)
        test_forms.py         # EventForm + RSVPForm tests
        test_models.py        # Model __str__, is_full, confirmed_count tests
        test_views_api.py     # Full API endpoint coverage
        test_views_frontend.py  # Frontend view tests

templates/events/             # (project-level templates directory)
    event_calendar.html       # FullCalendar.js interactive calendar
    event_delete.html         # Delete confirmation page
    event_detail.html         # Single event view with RSVP + attendees
    event_form.html           # Create/edit form (shared template)
    event_list.html           # Paginated event listing with filters
```

---

## Models

### BaseModel Fields (inherited)

Both models inherit from `apps.core.models.BaseModel`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` (PK) | Auto-generated UUID primary key |
| `created_at` | `DateTimeField` | Auto-set on creation (`auto_now_add`) |
| `updated_at` | `DateTimeField` | Auto-set on every save (`auto_now`) |
| `is_active` | `BooleanField` | Soft-delete flag (default: `True`) |

### Event

Represents a church event with scheduling, location, RSVP, and recurrence support.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `title` | `CharField(200)` | Yes | -- | Event title |
| `description` | `TextField` | No | `""` | Detailed description |
| `event_type` | `CharField(20)` | Yes | `worship` | Category of event (see choices below) |
| `start_datetime` | `DateTimeField` | Yes | -- | Start date and time |
| `end_datetime` | `DateTimeField` | Yes | -- | End date and time |
| `all_day` | `BooleanField` | No | `False` | Whether the event spans the entire day |
| `location` | `CharField(255)` | No | `""` | Venue name |
| `location_address` | `TextField` | No | `""` | Full physical address |
| `is_online` | `BooleanField` | No | `False` | Whether the event is virtual |
| `online_link` | `URLField` | No | `""` | Video conference or streaming link |
| `organizer` | `FK(Member)` | No | `null` | Organizing member (`SET_NULL` on delete, related_name: `organized_events`) |
| `max_attendees` | `PositiveIntegerField` | No | `null` | Capacity limit (`null` means unlimited) |
| `requires_rsvp` | `BooleanField` | No | `False` | Whether members must RSVP to attend |
| `image` | `ImageField` | No | `null` | Event banner image; uploads to `events/%Y/%m/`; validated by `validate_image_file` |
| `is_published` | `BooleanField` | No | `True` | Controls visibility in public listings |
| `is_cancelled` | `BooleanField` | No | `False` | Marks the event as cancelled |
| `is_recurring` | `BooleanField` | No | `False` | Whether this is a recurring event |
| `parent_event` | `FK(self)` | No | `null` | Parent event for recurring occurrences (`CASCADE` on delete, related_name: `occurrences`) |

**Event Type Choices (`EventType`):**

| Constant | Value | Label (French) |
|----------|-------|----------------|
| `WORSHIP` | `worship` | Culte |
| `GROUP` | `group` | Reunion de groupe |
| `MEAL` | `meal` | Repas communautaire |
| `SPECIAL` | `special` | Evenement special |
| `MEETING` | `meeting` | Reunion |
| `TRAINING` | `training` | Formation |
| `OUTREACH` | `outreach` | Evangelisation |
| `OTHER` | `other` | Autre |

**Computed Properties:**

| Property | Return Type | Description |
|----------|-------------|-------------|
| `confirmed_count` | `int` | Count of RSVPs with status `confirmed` |
| `is_full` | `bool` | `True` if `confirmed_count >= max_attendees`; always `False` when `max_attendees` is `None` |

**Meta:** `ordering = ['start_datetime']` (soonest first)

**String Representation:** `"{title} ({start_date})"`

**Relationships:**

- `rsvps` -- Reverse FK from `EventRSVP`
- `occurrences` -- Reverse FK from child `Event` records (recurring)
- `organizer` -- FK to `members.Member`

---

### EventRSVP

Tracks a member's attendance response for a specific event. Enforces one RSVP per member per event.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `event` | `FK(Event)` | Yes | -- | The event being RSVP'd to (`CASCADE` on delete, related_name: `rsvps`) |
| `member` | `FK(Member)` | Yes | -- | The responding member (`CASCADE` on delete, related_name: `event_rsvps`) |
| `status` | `CharField(20)` | Yes | `pending` | Response status (see choices below) |
| `guests` | `PositiveIntegerField` | No | `0` | Number of additional guests |
| `notes` | `TextField` | No | `""` | Optional notes from the member |

**RSVP Status Choices (`RSVPStatus`):**

| Constant | Value | Label (French) |
|----------|-------|----------------|
| `PENDING` | `pending` | En attente |
| `CONFIRMED` | `confirmed` | Confirme |
| `DECLINED` | `declined` | Refuse |
| `MAYBE` | `maybe` | Peut-etre |

**Constraints:**

```python
unique_together = ['event', 'member']  # One RSVP per member per event
```

**String Representation:** `"{member_full_name} - {event_title}"`

---

## Forms

Both forms use the `W3CRMFormMixin` for consistent styling with the DexignZone W3CRM template theme.

### EventForm

Full create/update form for events. Includes custom validation ensuring the end datetime is after the start datetime.

| Field | Widget | Notes |
|-------|--------|-------|
| `title` | `TextInput` | Required |
| `description` | `Textarea` (rows=3) | Optional |
| `event_type` | `Select` | Choices from `EventType.CHOICES` |
| `start_datetime` | `DateTimeInput` (type=datetime-local) | Required |
| `end_datetime` | `DateTimeInput` (type=datetime-local) | Required; must be after start |
| `all_day` | `CheckboxInput` | Optional |
| `location` | `TextInput` | Optional |
| `location_address` | `Textarea` | Optional |
| `is_online` | `CheckboxInput` | Optional |
| `online_link` | `URLInput` | Optional |
| `organizer` | `Select` | FK to Member; optional |
| `max_attendees` | `NumberInput` | Optional |
| `requires_rsvp` | `CheckboxInput` | Optional |
| `image` | `FileInput` | Optional; validated by `validate_image_file` |
| `is_published` | `CheckboxInput` | Optional |

**Custom Validation:**

- `clean()` raises `ValidationError` if `end_datetime <= start_datetime`.

### RSVPForm

Member RSVP submission form.

| Field | Widget | Notes |
|-------|--------|-------|
| `status` | `Select` | Choices from `RSVPStatus.CHOICES` |
| `guests` | `NumberInput` | Default: `0` |
| `notes` | `Textarea` | Optional |

---

## Serializers

### EventListSerializer

Compact serializer used for list, upcoming, and calendar endpoints. Omits detail-only fields like `is_full` and `organizer_name`.

| Field | Type | Read-Only | Source |
|-------|------|-----------|--------|
| `id` | UUID | -- | Model PK |
| `title` | string | No | Model field |
| `event_type` | string | No | Model field |
| `event_type_display` | string | Yes | `get_event_type_display` |
| `start_datetime` | datetime | No | Model field |
| `end_datetime` | datetime | No | Model field |
| `location` | string | No | Model field |
| `is_online` | boolean | No | Model field |
| `confirmed_count` | integer | Yes | Model property |
| `max_attendees` | integer | No | Model field |
| `is_published` | boolean | No | Model field |
| `is_cancelled` | boolean | No | Model field |

### EventSerializer

Full detail serializer with all model fields. Used for retrieve, create, and update actions.

| Extra Field | Type | Read-Only | Source |
|-------------|------|-----------|--------|
| `event_type_display` | string | Yes | `get_event_type_display` |
| `organizer_name` | string (nullable) | Yes | `organizer.full_name` |
| `confirmed_count` | integer | Yes | Model property |
| `is_full` | boolean | Yes | Model property |

Uses `fields = '__all__'`. Read-only fields: `created_at`, `updated_at`.

### EventRSVPSerializer

RSVP serializer with denormalized member name and human-readable status label.

| Field | Type | Read-Only | Source |
|-------|------|-----------|--------|
| `id` | UUID | -- | Model PK |
| `event` | UUID | No | FK |
| `member` | UUID | No | FK |
| `member_name` | string | Yes | `member.full_name` |
| `status` | string | No | Model field |
| `status_display` | string | Yes | `get_status_display` |
| `guests` | integer | No | Model field |
| `notes` | string | No | Model field |
| `created_at` | datetime | -- | Model field |

---

## API Endpoints

Base path: `/api/v1/events/events/`

The `EventViewSet` is a `ModelViewSet` registered on the DRF `DefaultRouter` with basename `event`.

### Standard CRUD

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/events/events/` | List all events (paginated) | `IsMember` |
| `POST` | `/api/v1/events/events/` | Create a new event | `IsPastorOrAdmin` |
| `GET` | `/api/v1/events/events/{id}/` | Retrieve event detail | `IsMember` |
| `PUT` | `/api/v1/events/events/{id}/` | Full update | `IsPastorOrAdmin` |
| `PATCH` | `/api/v1/events/events/{id}/` | Partial update | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/events/events/{id}/` | Delete event | `IsPastorOrAdmin` |

### Custom Actions

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/events/events/upcoming/` | Next 10 published, non-cancelled future events | `IsMember` |
| `GET` | `/api/v1/events/events/calendar/` | Events within optional `start`/`end` date range (published only) | `IsMember` |
| `POST` | `/api/v1/events/events/{id}/rsvp/` | Create or update RSVP for current user | `IsPastorOrAdmin` |
| `GET` | `/api/v1/events/events/{id}/attendees/` | List confirmed attendees for the event | `IsPastorOrAdmin` |

### Calendar Endpoint Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start` | ISO 8601 date | No | Filter events starting on or after this date |
| `end` | ISO 8601 date | No | Filter events starting on or before this date |

This endpoint is designed for FullCalendar.js, which automatically sends `start` and `end` parameters when loading events.

### Filtering, Search, and Ordering

| Feature | Fields |
|---------|--------|
| **Filter backends** | `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` |
| **Filterset fields** | `event_type`, `is_published`, `is_cancelled` |
| **Search fields** | `title`, `description`, `location` |
| **Ordering fields** | `start_datetime`, `title` |
| **Default ordering** | `start_datetime` ascending |

### Serializer Selection

- `list` action uses `EventListSerializer` (compact -- excludes `is_full`, `organizer_name`)
- All other actions use `EventSerializer` (full detail including all model fields)

---

## Frontend URLs

Base path: `/events/` (namespace: `frontend:events`)

All views require authentication (`@login_required`).

| URL Pattern | View Function | Name | Description |
|-------------|---------------|------|-------------|
| `/events/` | `event_list` | `event_list` | Paginated event listing (20 per page) with search and filters |
| `/events/calendar/` | `event_calendar` | `event_calendar` | FullCalendar.js interactive calendar |
| `/events/create/` | `event_create` | `event_create` | New event form (admin/pastor only) |
| `/events/<uuid:pk>/` | `event_detail` | `event_detail` | Event detail with RSVP status and attendees |
| `/events/<uuid:pk>/edit/` | `event_update` | `event_update` | Edit existing event (admin/pastor only) |
| `/events/<uuid:pk>/delete/` | `event_delete` | `event_delete` | Delete confirmation page (admin/pastor only) |
| `/events/<uuid:pk>/cancel/` | `event_cancel` | `event_cancel` | Cancel event via POST (admin/pastor only) |
| `/events/<uuid:pk>/rsvp/` | `event_rsvp` | `event_rsvp` | Submit/update RSVP via POST |

### View Details

**event_list** -- Displays published, non-cancelled events with:
- Text search (`q` parameter) across title and description
- Event type filter (`type` parameter)
- Upcoming/past toggle (`upcoming`/`past` parameters)
- Pagination at 20 items per page
- Context includes `upcoming_count` and `past_count` for UI badges

**event_detail** -- Shows full event information plus:
- Current user's RSVP status (if any)
- Full list of confirmed attendees (no limit)
- Staff flag (`is_staff`) set for admin/pastor users

**event_rsvp** -- POST-only handler that creates or updates an RSVP via `update_or_create`. Defaults to `status=confirmed` and `guests=0`. Invalid guests values (non-numeric) default to `0`. Requires a member profile; redirects with error if missing. Redirects to event detail.

**event_create** -- Admin/pastor only. Renders `EventForm` on GET, creates event on valid POST. Automatically creates a linked `AttendanceSession` for the new event. For recurring events, each generated child event also gets its own session. Redirects to `/events/` on success. Redirects to `/` for unauthorized users.

**event_update** -- Admin/pastor only. Pre-populates `EventForm` with existing event on GET. Saves changes on valid POST. Redirects to event detail on success.

**event_delete** -- Admin/pastor only. Shows confirmation page on GET. Performs hard delete on POST. Redirects to `/events/`.

**event_cancel** -- Admin/pastor only. POST-only. Sets `is_cancelled=True` on the event. Redirects to event detail.

**event_calendar** -- Renders the FullCalendar.js page. Passes `event_type_colors` map and `event_type_choices` for the legend/filter UI.

### Event Type Color Map (Calendar)

Events are color-coded by type on the calendar view:

| Type | Color Name | Hex |
|------|------------|-----|
| `worship` | Violet | `#6a5acd` |
| `group` | Green | `#28a745` |
| `meal` | Orange | `#fd7e14` |
| `special` | Red | `#dc3545` |
| `meeting` | Cyan | `#17a2b8` |
| `training` | Blue | `#007bff` |
| `outreach` | Yellow | `#ffc107` |
| `other` | Gray | `#6c757d` |

---

## Templates

All templates are located in the project-level `templates/events/` directory (not inside the app directory). They extend `base.html` and use the W3CRM/DexignZone template system.

| Template | Used By | Description |
|----------|---------|-------------|
| `event_list.html` | `event_list` | Paginated list with search bar, type filter dropdown, and upcoming/past tabs |
| `event_detail.html` | `event_detail` | Full event view with RSVP form, attendee list, and staff action buttons |
| `event_form.html` | `event_create`, `event_update` | Shared create/edit form rendering `EventForm` with DexignZone styling |
| `event_delete.html` | `event_delete` | Delete confirmation dialog with POST form |
| `event_calendar.html` | `event_calendar` | FullCalendar.js calendar with color-coded event types, data loaded from `/api/v1/events/events/calendar/` |

---

## Admin Configuration

### EventAdmin

- **Registered Model:** `Event`
- **Extends:** `BaseModelAdmin`
- **list_display:** `title`, `event_type`, `start_datetime`, `location`, `is_published`, `is_cancelled`
- **list_filter:** `event_type`, `is_published`, `is_cancelled`, `start_datetime`
- **search_fields:** `title`, `description`, `location`
- **date_hierarchy:** `start_datetime`

### EventRSVPAdmin

- **Registered Model:** `EventRSVP`
- **Extends:** `BaseModelAdmin`
- **list_display:** `event`, `member`, `status`, `guests`, `created_at`
- **list_filter:** `status`, `event`
- **autocomplete_fields:** `event`, `member`

---

## Permissions Matrix

### Frontend Views

| View | Unauthenticated | Member | Pastor | Admin |
|------|:---------------:|:------:|:------:|:-----:|
| `event_list` | Redirect to login | Yes | Yes | Yes |
| `event_detail` | Redirect to login | Yes | Yes | Yes |
| `event_calendar` | Redirect to login | Yes | Yes | Yes |
| `event_rsvp` | Redirect to login | Yes (requires member profile) | Yes | Yes |
| `event_create` | Redirect to login | Denied (redirect to `/`) | Yes | Yes |
| `event_update` | Redirect to login | Denied (redirect to `/`) | Yes | Yes |
| `event_delete` | Redirect to login | Denied (redirect to `/`) | Yes | Yes |
| `event_cancel` | Redirect to login | Denied (redirect to `/`) | Yes | Yes |

### API Actions

| Action | Unauthenticated | Member (`IsMember`) | Pastor/Admin (`IsPastorOrAdmin`) |
|--------|:---------------:|:-------------------:|:--------------------------------:|
| `list` | 403 | Yes | Yes |
| `retrieve` | 403 | Yes | Yes |
| `upcoming` | 403 | Yes | Yes |
| `calendar` | 403 | Yes | Yes |
| `create` | 403 | 403 | Yes |
| `update` / `partial_update` | 403 | 403 | Yes |
| `destroy` | 403 | 403 | Yes |
| `rsvp` | 403 | 403 | Yes |
| `attendees` | 403 | 403 | Yes |

**Permission Details:**
- `IsMember` -- Allows any authenticated user (does not require a member profile).
- `IsPastorOrAdmin` -- Requires an authenticated user whose member profile has a role in `Roles.STAFF_ROLES` (deacon, pastor, admin) or has Django `is_staff`/`is_superuser` set to `True`.

---

## Dependencies

### Internal (EgliseConnect apps)

| Module | Usage |
|--------|-------|
| `apps.core.models.BaseModel` | Model inheritance (UUID PK, timestamps, `is_active`) |
| `apps.core.constants.EventType` | Event type choices |
| `apps.core.constants.RSVPStatus` | RSVP status choices |
| `apps.core.constants.Roles` | Role constants for permission checks in frontend views |
| `apps.core.validators.validate_image_file` | Image upload validator for `Event.image` |
| `apps.core.permissions.IsMember` | DRF permission: any authenticated user |
| `apps.core.permissions.IsPastorOrAdmin` | DRF permission: pastor/admin role required |
| `apps.core.mixins.W3CRMFormMixin` | Form styling mixin for DexignZone template |
| `apps.core.admin.BaseModelAdmin` | Base admin class |
| `apps.members.Member` | FK target for `organizer` (Event) and `member` (EventRSVP) |

### External (Python packages)

| Package | Usage |
|---------|-------|
| `django` | Core framework (models, views, forms, admin, auth decorators, pagination) |
| `djangorestframework` | API ViewSet, serializers, permissions, filters |
| `django-filter` | `DjangoFilterBackend` for API filtering |
| `factory-boy` | Test data factories |
| `pytest` / `pytest-django` | Test runner |

### Client-Side

| Library | Usage |
|---------|-------|
| FullCalendar.js | Interactive calendar rendering in `event_calendar.html` |

---

## Tests

**Total: 118 tests** across 4 test modules plus a factory module.

Test framework: **pytest** with `pytest-django` and `factory_boy`.

### Test Breakdown

| File | Test Count | Coverage Area |
|------|:----------:|---------------|
| `tests/factories.py` | -- | `EventFactory` and `EventRSVPFactory` for test data generation |
| `tests/test_models.py` | 5 | `Event.__str__`, `is_full` (max reached, not reached, no limit), `EventRSVP.__str__` |
| `tests/test_forms.py` | 22 | `EventForm` validation (required fields, optional fields, all event types, datetime validation, save, update); `RSVPForm` validation (all statuses, guests, notes, save, update, decline, maybe) |
| `tests/test_views_api.py` | 41 | List (auth, unauth, serializer fields, filters, search, ordering); Retrieve (auth, detail serializer, unauth, 404); Create (pastor, member forbidden, unauth); Update (full, partial, member forbidden); Delete (pastor, member forbidden); Upcoming (future/past/cancelled/unpublished/limit-10); Calendar (published, start/end params, combined, no params); RSVP (create, update, defaults, no profile, member forbidden, declined); Attendees (confirmed only, member forbidden, empty); Access without profile |
| `tests/test_views_frontend.py` | 50 | Event list (auth, unauth, context, type filter, upcoming filter, exclusion, pagination); Event detail (auth, unauth, context, user RSVP with/without profile, confirmed attendees, 404); RSVP (create, update, defaults, invalid guests, GET redirect, no profile, unauth, 404); Calendar (auth, context, unauth); Create (login, no profile, member denied, admin/pastor GET, POST valid/invalid, context); Update (login, no profile, member denied, admin/pastor GET, POST valid/invalid, 404); Delete (login, no profile, member denied, admin/pastor GET, POST, GET-no-delete, 404) |

### Test Fixtures

Defined in test files using `@pytest.fixture`:

| Fixture | Description |
|---------|-------------|
| `api_client` | DRF `APIClient` instance |
| `client` | Django `Client` instance |
| `member_user` | Authenticated user with `MEMBER` role |
| `pastor_user` | Authenticated user with `PASTOR` role |
| `admin_user` | Authenticated user with `ADMIN` role |
| `user_no_profile` | Authenticated user without a member profile |
| `staff_user_no_profile` | Staff user (Django `is_staff=True`) without a member profile |

### Key Test Scenarios

- **Authentication** -- All views and endpoints redirect/reject unauthenticated users
- **Role-based access** -- Regular members cannot create/update/delete events; admin/pastor can
- **No member profile** -- Users without `member_profile` are handled gracefully (redirects or error messages)
- **RSVP behavior** -- Create and update via `update_or_create`; defaults to `confirmed` status and `0` guests; invalid guest values default to `0`
- **Pagination** -- Event list paginates at 20 items per page
- **Filtering** -- Event type filter, text search across title/description, upcoming/past separation
- **Calendar** -- Date range filtering with `start`/`end` parameters; returns only published events
- **Attendees** -- Returns only confirmed RSVPs
- **Serializer selection** -- List action uses compact `EventListSerializer`; detail uses full `EventSerializer`
- **404 handling** -- Nonexistent UUIDs return 404

### Running Tests

```bash
# All events tests
pytest apps/events/ -v

# By module
pytest apps/events/tests/test_models.py -v
pytest apps/events/tests/test_forms.py -v
pytest apps/events/tests/test_views_frontend.py -v
pytest apps/events/tests/test_views_api.py -v

# Specific test class
pytest apps/events/tests/test_views_api.py::TestEventUpcoming -v
```
