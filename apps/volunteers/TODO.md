# TODO - Volunteers App

## P1 — Critical

### CRUD Completions

- [ ] Swap request: add frontend views (list + create) for members to request schedule swaps (currently API only)
- [ ] Planned absence: add edit and delete views (currently only list + create)

### Volunteer Hour Tracking

- [ ] Add VolunteerHours model (member, position, date, hours_worked, notes, approved_by)
- [ ] Add hour logging form (volunteer self-reports or staff enters)
- [ ] Add hours summary per volunteer (total hours by period: week, month, year)
- [ ] Add hours report for admin (all volunteers, filterable by position/date range)
- [ ] Add CSV export for volunteer hour reports

### Background Check Status

- [ ] Add background check status per volunteer (pending, approved, expired, not_required)
- [ ] Add expiry date tracking with automated renewal alerts
- [ ] Add background check status indicator on volunteer profile and position assignment
- [ ] Block scheduling for volunteers with expired background checks

### Team Communication

- [ ] Add group messaging within position/team (send message to all volunteers in a position)
- [ ] Add team announcement board per position
- [ ] Add shift reminder notifications (auto-notify X hours before scheduled shift)

### Frontend Refinements

- [ ] My schedule: add confirm/decline buttons directly on schedule items
- [ ] Schedule list: add date range filter
- [ ] Position list: show volunteer count per position
- [ ] Planned absence list: add status indicator (pending/approved)
- [ ] Schedule form: add member autocomplete search

## P2 — Important

### Volunteer Onboarding Checklist

- [ ] Add per-position onboarding checklist (required training, policy acknowledgment, orientation)
- [ ] Add checklist progress tracking per volunteer
- [ ] Add training completion certificates
- [ ] Block scheduling until onboarding checklist is complete

### Volunteer Recognition System

- [ ] Add milestone tracking (100 hours, 500 hours, 1 year, 5 years)
- [ ] Add milestone notifications and congratulations messages
- [ ] Add volunteer appreciation page (leaderboard, milestones achieved)
- [ ] Add volunteer of the month/quarter nomination system

### Skills Matrix Matching

- [ ] Add skills/qualifications model (skill name, proficiency level, certification date)
- [ ] Add skills profile per volunteer (self-reported + admin-verified)
- [ ] Add auto-suggest volunteers for positions based on skills match
- [ ] Add skill gap analysis per position (required skills vs. available volunteers)

### Sidebar / Navigation

- [ ] Verify "Absences planifiees" link is in sidebar under Volontaires section
- [ ] Add "Echanges" link in sidebar when swap request frontend views are implemented

## P3 — Nice-to-Have

### Volunteer Mobile Experience

- [ ] Add mobile-optimized schedule view (swipe between days)
- [ ] Add push notification for schedule changes and reminders
- [ ] Add one-tap check-in for volunteer shifts (confirm arrival)
- [ ] Add mobile hour logging (quick entry from phone)

### Volunteer Availability Heatmap

- [ ] Add availability submission form (mark available/unavailable per day/time slot)
- [ ] Add visual heatmap calendar showing team availability
- [ ] Add smart scheduling suggestions based on availability data

### Cross-Training Tracking

- [ ] Add cross-training records (volunteer A trained in position B)
- [ ] Add cross-trained volunteer suggestions for unfilled shifts
- [ ] Add training wish list (volunteers request to learn new positions)

### Existing Small Fixes

- [ ] Add notification when a new schedule is assigned to a volunteer
- [ ] Position detail: show current volunteers assigned to the position
- [ ] Add volunteer availability calendar view
- [ ] Schedule list: add bulk actions (assign multiple members at once)
