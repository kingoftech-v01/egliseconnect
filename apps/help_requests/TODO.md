# TODO - Help Requests App

## P1 — Critical

### Pastoral Care Tracking

- [x] Add PastoralCare model (care_type, member, assigned_to, date, notes, follow_up_date, status)
- [x] Add care types: hospital visit, home visit, phone call, counseling, prayer meeting
- [x] Add care visit CRUD views (log visit, update notes, set follow-up)
- [x] Add care dashboard for pastors (open cases, upcoming follow-ups, overdue items)
- [x] Add care visit history on member detail page (visible to staff)

### Prayer Request Management

- [x] Add PrayerRequest model (title, description, member, is_anonymous, is_public, status, answered_at)
- [x] Add prayer request submission form (logged-in members)
- [x] Add prayer wall (public display of non-anonymous requests)
- [x] Add prayer team notification (alert prayer team members of new requests)
- [x] Add "Mark as answered" with optional testimony

### Care Team Assignment & Workflow

- [x] Add care team model (team name, members, leader)
- [x] Add automatic care team assignment based on request type/urgency
- [x] Add care team dashboard (assigned cases, workload balance)
- [x] Add case handoff workflow (reassign between team members)

### CRUD Completions

- [x] Category: add frontend CRUD for admin (currently only manageable via Django admin)

### Frontend Refinements

- [x] Request list: add search bar for filtering by title/description
- [x] Request detail: add explicit "Close request" button
- [x] My requests: add pagination (currently shows all requests)
- [x] Request list: add filter by urgency level

## P2 — Important

### Automated Follow-Up Reminders

- [x] Add follow-up reminder system (auto-notify when follow-up date arrives)
- [x] Add escalation rules (if no follow-up after X days, escalate to supervisor)
- [x] Add reminder snooze (postpone follow-up by 1 day, 3 days, 1 week)
- [x] Add follow-up completion logging (what was discussed, next steps)

### Anonymous Prayer Request Submission

- [x] Add public-facing prayer request form (no login required)
- [x] Add CAPTCHA or rate limiting to prevent spam
- [x] Add moderation queue for anonymous requests (admin approves before public display)
- [x] Add anonymous request notification routing (to prayer team, not specific pastor)

### Care Ministry Dashboard

- [x] Add aggregate care statistics (open cases, closed this month, average resolution time)
- [x] Add care calendar view (scheduled visits, follow-ups by date)
- [x] Add care category breakdown (how many hospital visits vs. home visits vs. counseling)
- [x] Add care team performance metrics (cases per team member, response time)

### Sidebar / Navigation

- [x] Verify help request links are visible in sidebar for all roles that can create requests

## P3 — Nice-to-Have

### Benevolence Fund Management

- [x] Add BenevolenceRequest model (amount_requested, reason, status, approved_by, amount_granted)
- [x] Add benevolence request submission form (member or anonymous)
- [x] Add approval workflow (submit, review, approve/deny, disburse)
- [x] Add fund balance tracking (total fund, disbursed, remaining)
- [x] Add benevolence report for finance committee

### Meal Train Coordination

- [x] Add MealTrain model (recipient_member, reason, start_date, end_date, dietary_restrictions)
- [x] Add meal sign-up calendar (volunteers pick dates to deliver meals)
- [x] Add meal delivery confirmation and thank-you notification
- [x] Add dietary restriction display for meal providers

### Grief & Crisis Response

- [x] Add crisis response protocol templates (death, hospitalization, natural disaster)
- [x] Add crisis notification broadcast (alert all care team members immediately)
- [x] Add crisis resource library (grief support materials, community resources, referral contacts)
- [x] Add crisis follow-up timeline (structured check-ins at 1 week, 1 month, 3 months)

### Existing Small Fixes

- [x] Add email/notification when request status changes (assigned, resolved, closed)
- [x] Request detail: show timeline of status changes (created, assigned, resolved)
- [x] Add request statistics summary on list page (total open, assigned, resolved)
- [x] My requests: add "New request" button prominently on the page
