# Attendance App

## Overview

The attendance app provides a complete QR-code-based check-in system for church services, events, and training sessions. Members receive a unique, rotating QR code that can be scanned at sessions by authorized staff. The system also tracks member inactivity and generates absence alerts for pastoral follow-up.

### Key Features

- **Personal QR Codes**: Each member gets a unique, HMAC-signed QR code that rotates weekly
- **Session Management**: Create, edit, open/close, and delete attendance sessions
- **QR Scanner**: Real-time QR scanning interface for admins/pastors/group leaders
- **Manual Check-in**: Add attendance records manually for members without QR codes
- **Attendance History**: Members can view their own check-in history
- **Inactivity Tracking**: Celery tasks automatically mark members as inactive/expired based on attendance
- **Absence Alerts**: Automatic alerts when members miss 3+ worship sessions in 30 days
- **Onboarding Integration**: QR check-ins at training lessons automatically mark lesson attendance

## File Structure

```
apps/attendance/
├── __init__.py
├── admin.py                 # Django admin configuration
├── apps.py                  # App config
├── models.py                # MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert
├── serializers.py           # DRF serializers + CheckInSerializer
├── tasks.py                 # Celery tasks (inactivity check, absence alerts)
├── urls.py                  # Frontend + API URL patterns
├── views_api.py             # DRF ViewSets (QR, sessions, check-in, alerts)
├── views_frontend.py        # Template-based views (12 views)
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_attendancesession_duration_minutes.py
└── tests/
    ├── __init__.py
    ├── factories.py          # Test factories
    ├── test_models.py        # Model tests
    ├── test_views_api.py     # API endpoint tests
    ├── test_views_frontend.py # Frontend view tests
    └── test_tasks.py         # Celery task tests
```

## Models

### MemberQRCode

Unique rotating QR code for each member. Uses HMAC-SHA256 for tamper-proof code generation.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | OneToOneField → Member | The member who owns this QR code |
| `code` | CharField(100) | Unique HMAC-signed code (format: `EC-{uuid[:8]}-{signature[:16]}`) |
| `generated_at` | DateTimeField | Auto-set on creation |
| `expires_at` | DateTimeField | Expiration date (default: 7 days from generation) |
| `qr_image` | ImageField | Generated PNG image stored in `qrcodes/%Y/%m/` |

**Properties:**
- `is_valid` → `bool`: Returns `True` if the QR code has not expired

**Methods:**
- `regenerate()`: Generates a new code, image, and resets expiration to 7 days

### AttendanceSession

A check-in session for a service, event, or training lesson.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `name` | CharField(200) | Session name (e.g., "Culte du 15 mars 2025") |
| `session_type` | CharField(30) | One of: `worship`, `prayer`, `bible_study`, `youth`, `training`, `event`, `other` |
| `event` | ForeignKey → Event | Optional linked event |
| `scheduled_lesson` | ForeignKey → ScheduledLesson | Optional linked onboarding lesson |
| `date` | DateField | Session date |
| `start_time` | TimeField | Start time (optional) |
| `end_time` | TimeField | End time (optional) |
| `duration_minutes` | PositiveIntegerField | Planned duration in minutes (optional) |
| `opened_by` | ForeignKey → Member | Staff member who opened the session |
| `is_open` | BooleanField | Whether check-in is currently accepted (default: True) |

**Properties:**
- `attendee_count` → `int`: Number of attendance records in this session

**Meta:**
- Ordering: `['-date', '-start_time']`

### AttendanceRecord

Individual check-in record for a member at a session.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `session` | ForeignKey → AttendanceSession | The session |
| `member` | ForeignKey → Member | The checked-in member |
| `checked_in_at` | DateTimeField | Auto-set timestamp |
| `checked_in_by` | ForeignKey → Member | Staff member who performed the scan |
| `method` | CharField(20) | `qr_scan` or `manual` |
| `notes` | TextField | Optional notes |

**Constraints:**
- `unique_together = ['session', 'member']` — a member can only check in once per session

### AbsenceAlert

Alert generated when a member misses multiple worship sessions.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | ForeignKey → Member | The absent member |
| `consecutive_absences` | PositiveIntegerField | Number of missed sessions |
| `last_attendance_date` | DateField | Last known attendance date (nullable) |
| `alert_sent` | BooleanField | Whether the alert notification was sent |
| `alert_sent_at` | DateTimeField | When the alert was sent |
| `acknowledged_by` | ForeignKey → Member | Leader who acknowledged the alert |
| `notes` | TextField | Follow-up notes |

## Serializers

| Serializer | Model | Extra Fields |
|------------|-------|-------------|
| `MemberQRCodeSerializer` | MemberQRCode | `member_name`, `is_valid` (read-only) |
| `AttendanceSessionSerializer` | AttendanceSession | `attendee_count`, nested `records` |
| `AttendanceRecordSerializer` | AttendanceRecord | `member_name` (read-only) |
| `AbsenceAlertSerializer` | AbsenceAlert | `member_name` (read-only) |
| `CheckInSerializer` | — (plain Serializer) | `qr_code` (CharField), `session_id` (UUIDField) |

## API Endpoints

Base path: `/api/v1/attendance/`

### MemberQRCodeViewSet (ReadOnly)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/qr/` | List own QR code(s) | Authenticated |
| GET | `/qr/{id}/` | Retrieve own QR code | Authenticated |
| POST | `/qr/regenerate/` | Regenerate QR code | Authenticated |

### AttendanceSessionViewSet (ModelViewSet)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/sessions/` | List sessions | Pastor/Admin |
| POST | `/sessions/` | Create session | Pastor/Admin |
| GET | `/sessions/{id}/` | Retrieve session | Pastor/Admin |
| PUT | `/sessions/{id}/` | Update session | Pastor/Admin |
| DELETE | `/sessions/{id}/` | Delete session | Pastor/Admin |

Filterset fields: `session_type`, `date`, `is_open`

### CheckInViewSet
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/checkin/` | Process QR check-in | Authenticated |

Request body: `{ "qr_code": "EC-...", "session_id": "uuid" }`

### AbsenceAlertViewSet (ReadOnly)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/alerts/` | List absence alerts | Pastor/Admin |
| GET | `/alerts/{id}/` | Retrieve alert details | Pastor/Admin |

Filterset fields: `alert_sent`

## Frontend URLs

Base path: `/attendance/`

| URL | View | Name | Roles |
|-----|------|------|-------|
| `/attendance/my-qr/` | `my_qr` | `attendance:my_qr` | All members (with valid membership) |
| `/attendance/scanner/` | `scanner` | `attendance:scanner` | Admin, Pastor, Group Leader |
| `/attendance/scanner/checkin/` | `process_checkin` | `attendance:process_checkin` | Admin, Pastor, Group Leader |
| `/attendance/sessions/` | `session_list` | `attendance:session_list` | Admin, Pastor |
| `/attendance/sessions/create/` | `create_session` | `attendance:create_session` | Admin, Pastor |
| `/attendance/sessions/<uuid>/` | `session_detail` | `attendance:session_detail` | Admin, Pastor |
| `/attendance/sessions/<uuid>/edit/` | `edit_session` | `attendance:edit_session` | Admin, Pastor |
| `/attendance/sessions/<uuid>/toggle/` | `toggle_session` | `attendance:toggle_session` | Admin, Pastor |
| `/attendance/sessions/<uuid>/delete/` | `delete_session` | `attendance:delete_session` | Admin, Pastor |
| `/attendance/sessions/<uuid>/add-record/` | `add_manual_record` | `attendance:add_manual_record` | Admin, Pastor, Group Leader |
| `/attendance/records/<uuid>/delete/` | `delete_record` | `attendance:delete_record` | Admin, Pastor |
| `/attendance/my-history/` | `my_history` | `attendance:my_history` | All members |

## Templates

All templates are in `templates/attendance/` and extend `base.html`.

| Template | View | Description |
|----------|------|-------------|
| `my_qr.html` | `my_qr` | Display member's personal QR code |
| `scanner.html` | `scanner` | QR code scanning interface with session selector |
| `create_session.html` | `create_session` | Form to create a new attendance session |
| `edit_session.html` | `edit_session` | Form to edit an existing session |
| `delete_session.html` | `delete_session` | Confirmation page for session deletion |
| `session_list.html` | `session_list` | Paginated list of all sessions |
| `session_detail.html` | `session_detail` | Session details with attendance records and manual add form |
| `my_history.html` | `my_history` | Member's personal attendance history with pagination |

## Celery Tasks

### `check_member_inactivity`

Periodic task that updates member status based on attendance:
- **2 months** without attendance → `INACTIVE` (only for members with some attendance history)
- **6 months** inactive → `EXPIRED` (account deactivated, must redo onboarding)

### `check_absence_alerts`

Periodic task that monitors worship session attendance:
- Checks attendance over the last 30 days
- Creates `AbsenceAlert` for members who missed 3+ worship sessions
- Updates existing unacknowledged alerts if absences increase
- Sends `Notification` to all admin/pastor members with link to sessions page

## Admin Configuration

All 4 models are registered in Django admin:

- **MemberQRCodeAdmin**: list by member/code/dates, search by member name/code
- **AttendanceSessionAdmin**: list by name/type/date/status/count, filter by type/open/date, inline attendance records
- **AttendanceRecordAdmin**: list by member/session/method/time, filter by method/session type
- **AbsenceAlertAdmin**: list by member/absences/sent/date, filter by alert_sent

## Permissions Matrix

| Action | Member | Volunteer | Group Leader | Deacon | Pastor | Admin |
|--------|--------|-----------|-------------|--------|--------|-------|
| View own QR code | Yes* | Yes* | Yes* | Yes* | Yes* | Yes* |
| View own history | Yes | Yes | Yes | Yes | Yes | Yes |
| Scan QR codes | — | — | Yes | — | Yes | Yes |
| Manual check-in | — | — | Yes | — | Yes | Yes |
| Create session | — | — | — | — | Yes | Yes |
| Edit/delete session | — | — | — | — | Yes | Yes |
| Toggle session open/close | — | — | — | — | Yes | Yes |
| Delete attendance record | — | — | — | — | Yes | Yes |
| View session list | — | — | — | — | Yes | Yes |
| View session detail | — | — | — | — | Yes | Yes |
| API: Manage sessions | — | — | — | — | Yes | Yes |
| API: View alerts | — | — | — | — | Yes | Yes |

\* Requires `can_use_qr` property on member (valid membership status)

## Dependencies

- **members**: Member model (QR code owner, attendance records, alerts)
- **events**: Event model (optional session link)
- **onboarding**: ScheduledLesson model (lesson attendance integration), OnboardingService
- **communication**: Notification model (absence alert notifications)
- **core**: BaseModel, constants (Roles, CheckInMethod, AttendanceSessionType, MembershipStatus), permissions (IsPastorOrAdmin)
- **External**: `qrcode` library (QR image generation), Celery (periodic tasks)

## Tests

Test files in `apps/attendance/tests/`:
- `factories.py` — Test data factories
- `test_models.py` — Model creation, QR generation, validation, regeneration
- `test_views_api.py` — API endpoint tests (CRUD, check-in flow, permissions)
- `test_views_frontend.py` — Frontend view tests (access control, form submissions, pagination)
- `test_tasks.py` — Celery task tests (inactivity detection, absence alert creation)
