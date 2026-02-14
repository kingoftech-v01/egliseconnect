# Reports App

> **Django application**: `apps.reports`
> **Path**: `apps/reports/`

---

## 1. Overview

The Reports app provides church leadership with a centralized analytics and reporting hub for the EgliseConnect system. It is a **read-only** module -- it does not define any Django models of its own. Instead, it aggregates data from every other app in the project (members, donations, events, volunteers, help requests, attendance) and presents it through dashboards, detailed reports, and CSV exports.

### Key Features

- **Main dashboard** -- at-a-glance KPIs: total members, recent donations, upcoming events, volunteer activity, open help requests, and upcoming birthdays.
- **Onboarding pipeline widget** -- counts of members in each membership-status stage (registered, form submitted, in training, interview scheduled).
- **Financial summary widget** -- six-month giving trend rendered as a Chart.js line chart.
- **Member growth trend** -- twelve-month new-registration chart.
- **Member statistics page** -- breakdown by role, active vs. inactive, new this month/year.
- **Donation report** -- monthly and yearly analysis, year-over-year comparison, breakdown by donation type and payment method, anonymized top-donor ranking, campaign totals.
- **Attendance report** -- per-event RSVP statistics (confirmed, declined, guest count) plus attendance-session analytics (check-in counts, by type, by method).
- **Volunteer report** -- shifts completed vs. no-shows, breakdown by position, top-10 most active volunteers.
- **Birthday calendar** -- upcoming birthdays within a configurable day range (accessible to all authenticated members).
- **CSV exports** -- one-click download of members, donations, attendance, and volunteer data as CSV files (BOM-prefixed for Excel compatibility).
- **REST API** -- full programmatic access to all dashboard and report data via DRF ViewSets and an additional treasurer-specific endpoint.

---

## 2. File Structure

```
apps/reports/
    __init__.py
    apps.py                     # AppConfig (name='apps.reports')
    services.py                 # DashboardService + ReportService
    serializers.py              # 10 non-model serializers
    views_api.py                # 2 ViewSets + 1 APIView (DRF)
    views_frontend.py           # 10 frontend views (6 pages + 4 CSV exports)
    urls.py                     # URL routing (API + frontend)
    migrations/
        __init__.py             # No migrations (no models)
    tests/
        __init__.py
        test_services.py        # 9 tests  -- service-layer aggregation logic
        test_views_api.py       # 68 tests -- API endpoints, permissions, edge cases
        test_views_frontend.py  # 127 tests -- frontend views, context, CSV exports
```

---

## 3. Models

This app defines **no models**. It is purely a reporting layer that queries models from other apps:

| Model | Source App |
|-------|-----------|
| `Member` | `apps.members` |
| `Donation` | `apps.donations` |
| `Event`, `EventRSVP` | `apps.events` |
| `AttendanceSession`, `AttendanceRecord` | `apps.attendance` |
| `VolunteerPosition`, `VolunteerSchedule`, `VolunteerAvailability` | `apps.volunteers` |
| `HelpRequest` | `apps.help_requests` |

---

## 4. Services

All business logic lives in two static service classes in `services.py`.

### DashboardService

Aggregates quick-look statistics for the dashboard and individual stat widgets.

| Method | Description | Return Keys |
|--------|-------------|-------------|
| `get_member_stats()` | Member totals and role breakdown | `total`, `active`, `inactive`, `new_this_month`, `new_this_year`, `role_breakdown` |
| `get_donation_stats(year=None)` | Donation totals for a given year | `year`, `total_amount`, `total_count`, `average_amount`, `monthly_breakdown`, `by_type`, `by_payment_method` |
| `get_event_stats(year=None)` | Event totals and RSVP counts | `year`, `total_events`, `upcoming`, `cancelled`, `by_type`, `total_rsvps`, `confirmed_rsvps` |
| `get_volunteer_stats()` | Volunteer position and schedule stats | `total_positions`, `volunteers_by_position`, `upcoming_schedules`, `confirmed_this_month`, `pending_this_month` |
| `get_help_request_stats()` | Help-request totals by status, urgency, and category | `total`, `open`, `resolved_this_month`, `by_urgency`, `by_category` |
| `get_upcoming_birthdays(days=7)` | Members with birthdays in the next N days | List of `{member_id, member_name, birthday, age, email}` |
| `get_dashboard_summary()` | Combines all of the above into one payload | `members`, `donations`, `events`, `volunteers`, `help_requests`, `upcoming_birthdays`, `generated_at` |
| `get_onboarding_pipeline_stats()` | Counts members in each onboarding stage | `registered`, `form_submitted`, `in_training`, `interview_scheduled`, `total_in_process` |
| `get_financial_summary()` | Six-month giving trend | `monthly_trend`, `labels`, `values` |
| `get_member_growth_trend()` | Twelve-month new-member registration counts | `labels`, `counts` |

### ReportService

Generates detailed, date-filtered reports for display or export.

| Method | Parameters | Description | Return Keys |
|--------|------------|-------------|-------------|
| `get_attendance_report(start_date, end_date)` | Optional dates (default: last 90 days) | Per-event RSVP breakdown | `start_date`, `end_date`, `total_events`, `events` |
| `get_attendance_session_stats(start_date, end_date)` | Optional dates (default: last 90 days) | Session-level check-in analytics | `total_sessions`, `total_checkins`, `avg_per_session`, `by_type`, `by_method` |
| `get_donation_report(year)` | Year (required) | Monthly breakdown, anonymized top donors, campaign totals | `year`, `total`, `total_count`, `unique_donors`, `monthly`, `top_donors`, `campaigns` |
| `get_volunteer_report(start_date, end_date)` | Optional dates (default: last 30 days) | Shifts by position, completed vs. no-show, top volunteers | `start_date`, `end_date`, `total_shifts`, `completed`, `no_shows`, `by_position`, `top_volunteers` |

**Privacy note**: Top donors are anonymized -- only rank and amount are returned, never the member's identity.

---

## 5. Serializers

All serializers are non-model (`serializers.Serializer`) since there are no app-specific models. Defined in `serializers.py`:

| Serializer | Fields |
|------------|--------|
| `MemberStatsSerializer` | `total`, `active`, `inactive`, `new_this_month`, `new_this_year`, `role_breakdown` |
| `DonationStatsSerializer` | `year`, `total_amount`, `total_count`, `average_amount`, `monthly_breakdown`, `by_type`, `by_payment_method` |
| `EventStatsSerializer` | `year`, `total_events`, `upcoming`, `cancelled`, `by_type`, `total_rsvps`, `confirmed_rsvps` |
| `VolunteerStatsSerializer` | `total_positions`, `volunteers_by_position`, `upcoming_schedules`, `confirmed_this_month`, `pending_this_month` |
| `HelpRequestStatsSerializer` | `total`, `open`, `resolved_this_month`, `by_urgency`, `by_category` |
| `BirthdaySerializer` | `member_id` (UUID), `member_name`, `birthday` (Date), `age` (nullable Int) |
| `DashboardSummarySerializer` | `members`, `donations`, `events`, `volunteers`, `help_requests`, `upcoming_birthdays`, `generated_at` |
| `AttendanceReportSerializer` | `start_date`, `end_date`, `total_events`, `events` |
| `DonationReportSerializer` | `year`, `total`, `total_count`, `unique_donors`, `monthly`, `top_donors`, `campaigns` |
| `VolunteerReportSerializer` | `start_date`, `end_date`, `total_shifts`, `completed`, `no_shows`, `by_position`, `top_volunteers` |

---

## 6. API Endpoints

All API endpoints are prefixed with `/api/v1/reports/`.

### DashboardViewSet

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/reports/dashboard/` | Full dashboard summary | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/members/` | Member statistics | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/donations/` | Donation statistics | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/events/` | Event statistics | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/volunteers/` | Volunteer statistics | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/help_requests/` | Help-request statistics | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/birthdays/` | Upcoming birthdays | `IsPastor \| IsAdmin` |

**Query parameters**:
- `donations` and `events`: `?year=2026` (optional, defaults to current year)
- `birthdays`: `?days=7` (optional, defaults to 7)

### ReportViewSet

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/reports/reports/attendance/` | Attendance report | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/reports/donations/{year}/` | Annual donation report | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/reports/volunteers/` | Volunteer report | `IsPastor \| IsAdmin` |

**Query parameters** for `attendance` and `volunteers`:
- `?start_date=2026-01-01` (ISO format, optional)
- `?end_date=2026-02-13` (ISO format, optional)

### TreasurerDonationReportView (APIView)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/api/v1/reports/treasurer/donations/` | Donation report (current year) | `IsTreasurer \| IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/treasurer/donations/{year}/` | Donation report (specific year) | `IsTreasurer \| IsPastor \| IsAdmin` |

This endpoint allows treasurers to access donation reports without requiring full admin/pastor dashboard access.

---

## 7. Frontend URLs

All frontend routes are prefixed with `/reports/` and use the `frontend:reports:` namespace.

### Report Pages

| Path | View Function | Name | Description |
|------|---------------|------|-------------|
| `/reports/` | `dashboard` | `dashboard` | Main dashboard with KPI cards, onboarding pipeline, financial trend, and growth chart |
| `/reports/members/` | `member_stats` | `member_stats` | Member statistics with role breakdown and 12-month growth chart |
| `/reports/donations/` | `donation_report` | `donation_report` | Donation report with year selector, YoY comparison, and monthly chart |
| `/reports/attendance/` | `attendance_report` | `attendance_report` | Attendance analytics with date-range filtering and session statistics |
| `/reports/volunteers/` | `volunteer_report` | `volunteer_report` | Volunteer activity report with date-range filtering |
| `/reports/birthdays/` | `birthday_report` | `birthday_report` | Upcoming birthday list (configurable via `?days=` parameter, default 30) |

### CSV Export Endpoints

| Path | View Function | Name | Description |
|------|---------------|------|-------------|
| `/reports/export/members/` | `export_members_csv` | `export_members_csv` | Download active members as CSV |
| `/reports/export/donations/` | `export_donations_csv` | `export_donations_csv` | Download donations for a year as CSV (`?year=`) |
| `/reports/export/attendance/` | `export_attendance_csv` | `export_attendance_csv` | Download attendance/RSVP data as CSV |
| `/reports/export/volunteers/` | `export_volunteers_csv` | `export_volunteers_csv` | Download top volunteers as CSV |

All CSV files include a UTF-8 BOM for seamless opening in Microsoft Excel.

---

## 8. Templates

All templates live in `templates/reports/` and extend the project's `base.html`.

| Template | Description | JS Libraries |
|----------|-------------|-------------|
| `reports/dashboard.html` | Dashboard with stat cards, onboarding pipeline, financial trend, and growth chart | Chart.js, ApexCharts, DataTables |
| `reports/member_stats.html` | Member breakdown by role, active/inactive, new registrations, 12-month growth chart | Chart.js |
| `reports/donation_report.html` | Monthly donation chart, year selector, YoY comparison, type/method breakdown | Chart.js, ApexCharts |
| `reports/attendance_report.html` | Event RSVP table, attendance session stats, date-range filter | DataTables |
| `reports/volunteer_report.html` | Shifts by position, completion rate, top volunteers, date-range filter | Chart.js |
| `reports/birthday_report.html` | Upcoming birthdays list with age and configurable day range | -- |

---

## 9. Admin Configuration

This app has **no `admin.py` file** and registers nothing in the Django admin. Since the app defines no models, there is nothing to register.

---

## 10. Permissions Matrix

### Frontend Views

| Role | Dashboard | Member Stats | Donation Report | Attendance Report | Volunteer Report | Birthday Report | CSV Exports (Members/Attendance/Volunteers) | CSV Export (Donations) |
|------|-----------|-------------|-----------------|-------------------|------------------|-----------------|---------------------------------------------|----------------------|
| **Member** | No | No | No | No | No | Yes | No | No |
| **Group Leader** | No | No | No | No | No | Yes | No | No |
| **Treasurer** | Yes | No | Yes | No | No | Yes | No | Yes |
| **Pastor** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Admin** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

### API Endpoints

| Role | DashboardViewSet | ReportViewSet | TreasurerDonationReportView |
|------|-----------------|---------------|-----------------------------|
| **Member** | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| **Group Leader** | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| **Treasurer** | 403 Forbidden | 403 Forbidden | 200 OK |
| **Pastor** | 200 OK | 200 OK | 200 OK |
| **Admin** | 200 OK | 200 OK | 200 OK |

**Notes**:
- All views and endpoints require authentication (`@login_required` or `IsAuthenticated`).
- The `birthday_report` frontend view is the only report page accessible to all authenticated members with a member profile.
- The `dashboard` and `donation_report` frontend views additionally accept the `treasurer` role.
- API permissions use DRF permission classes from `apps.core.permissions`: `IsPastor`, `IsAdmin`, `IsTreasurer`.

---

## 11. Dependencies

### Python / Django Dependencies

| Dependency | Usage |
|------------|-------|
| `apps.core.permissions` | `IsPastor`, `IsAdmin`, `IsTreasurer` permission classes |
| `apps.core.mixins` | `PastorRequiredMixin` (imported but used only indirectly) |
| `apps.core.utils` | `get_upcoming_birthdays()` utility function |
| `apps.core.constants` | `MembershipStatus`, `AttendanceSessionType` |
| `apps.members.models` | `Member` -- aggregation queries for member stats |
| `apps.donations.models` | `Donation` -- aggregation queries for donation stats |
| `apps.events.models` | `Event`, `EventRSVP` -- aggregation queries for event/attendance stats |
| `apps.attendance.models` | `AttendanceSession`, `AttendanceRecord` -- session-level attendance analytics |
| `apps.volunteers.models` | `VolunteerPosition`, `VolunteerSchedule`, `VolunteerAvailability` -- volunteer stats |
| `apps.help_requests.models` | `HelpRequest` -- help-request stats |
| `djangorestframework` | API ViewSets, serializers, permissions |

### Frontend Libraries (loaded in templates)

| Library | Usage |
|---------|-------|
| Chart.js | Line/bar/doughnut charts on dashboard, members, donations, volunteers |
| ApexCharts | Advanced charts on dashboard and donation report |
| DataTables | Interactive sortable/searchable tables on dashboard and attendance report |

---

## 12. Tests

Tests use `pytest` with `pytest-django` and `factory_boy`. The test suite contains **204 tests** across three modules.

### Test Files

| File | Tests | Coverage Area |
|------|-------|---------------|
| `tests/test_services.py` | 9 | DashboardService and ReportService aggregation logic |
| `tests/test_views_api.py` | 68 | API endpoint responses, permission enforcement, query parameter edge cases, year/date fallbacks |
| `tests/test_views_frontend.py` | 127 | Frontend view access control, context variables, CSV export content and headers, redirect behavior |

### Running Tests

```bash
# All reports tests
pytest apps/reports/ -v

# Service layer only
pytest apps/reports/tests/test_services.py -v

# API tests only
pytest apps/reports/tests/test_views_api.py -v

# Frontend tests only
pytest apps/reports/tests/test_views_frontend.py -v
```

### Test Coverage Highlights

**Service tests** (`test_services.py`):
- `DashboardService`: member totals, donation totals, event counts, volunteer positions, help-request open/resolved counts, full dashboard summary structure, onboarding pipeline, financial summary, member growth trend, birthday email inclusion.
- `ReportService`: attendance report events/RSVPs, donation report monthly breakdown, volunteer shifts/no-shows, attendance session stats (empty, with data, by type, default dates).

**API tests** (`test_views_api.py`):
- Authentication required (401/403 for unauthenticated requests).
- Role-based access: pastor and admin allowed; regular member denied; treasurer allowed only on treasurer-specific endpoint.
- Query parameter handling: valid year, invalid year fallback, custom days, valid/invalid date ranges.
- Response field validation for every endpoint.
- Edge cases: `None` year, non-numeric year strings, both invalid dates.

**Frontend tests** (`test_views_frontend.py`):
- Login required redirects.
- Role-based access for every view (pastor, admin, treasurer, regular member, volunteer, user without profile).
- Context variable presence (summary, stats, report, growth data JSON, onboarding pipeline, financial summary, YoY comparison, session stats).
- CSV export: content type, disposition header, filename, BOM presence, header row, data rows.
- Date/year parameter handling: valid, invalid, missing, defaults.
- Redirect destinations for unauthorized users.

### Factories Used (from other apps)

| Factory | Source |
|---------|--------|
| `UserFactory`, `MemberFactory`, `PastorFactory`, `TreasurerFactory`, `AdminMemberFactory` | `apps.members.tests.factories` |
| `DonationFactory` | `apps.donations.tests.factories` |
| `EventFactory`, `EventRSVPFactory` | `apps.events.tests.factories` |
| `VolunteerPositionFactory`, `VolunteerScheduleFactory` | `apps.volunteers.tests.factories` |
| `HelpRequestFactory` | `apps.help_requests.tests.factories` |
| `AttendanceSessionFactory`, `AttendanceRecordFactory` | `apps.attendance.tests.factories` |
