# TODO - Events App

## P1 — Critical

### Facility & Room Booking

- [ ] Add Room/Facility model (name, capacity, amenities, photo, location)
- [ ] Add room availability calendar (visual display of booked vs. available time slots)
- [ ] Add booking conflict detection (prevent double-booking same room)
- [ ] Add room booking CRUD views (request, approve, reject, cancel)
- [ ] Add room booking integration with event creation (select room during event setup)
- [ ] Add facility management admin page (add/edit rooms, set availability hours)

### Calendar Sync

- [ ] Add .ics calendar export (single event + full calendar subscription feed)
- [ ] Add Google Calendar subscription URL (auto-updating iCal feed)
- [ ] Add "Add to Calendar" button on event detail (Google Calendar, Apple Calendar, Outlook links)
- [ ] Add calendar webhook for external calendar updates

### Check-In Kiosk Mode

- [ ] Add kiosk-friendly event check-in page (large buttons, no login required, auto-timeout)
- [ ] Add self-service check-in with name search or QR code scan
- [ ] Add kiosk mode toggle in event settings
- [ ] Add real-time attendee count display on kiosk

### Frontend Refinements

- [ ] Event list: add search bar for filtering by title
- [ ] Event detail: show full attendee list with RSVP status
- [ ] Event detail: add "Cancel event" button for admin/pastor
- [ ] Calendar view: add event type color coding
- [ ] Event form: add validation that end_datetime is after start_datetime
- [ ] Add past events section on event list (separate upcoming vs. past tabs)

## P2 — Important

### Event Registration with Custom Forms

- [ ] Add custom registration form builder (add fields: text, dropdown, checkbox, file upload)
- [ ] Add registration form preview before publishing
- [ ] Add registration data export (CSV of all registrants with custom field values)
- [ ] Add registration confirmation email with event details

### Event Templates

- [ ] Add event template model (save event config as reusable template)
- [ ] Add "Create from template" option on event creation page
- [ ] Add template library with common event types (Sunday service, Bible study, conference, etc.)

### Waitlist Management

- [ ] Add waitlist when event reaches max capacity
- [ ] Add auto-promotion from waitlist when spots open (RSVP cancellation)
- [ ] Add waitlist position notification (notify member of their position and when promoted)

### Event Volunteer Needs

- [ ] Add volunteer position requirements per event (e.g., "needs 3 greeters, 2 AV techs")
- [ ] Add volunteer sign-up for event positions (self-service)
- [ ] Add unfilled position alerts to event organizer

### Recurring Events

- [ ] Add recurrence rule UI (daily, weekly, biweekly, monthly, custom pattern)
- [ ] Add recurring event instance management (edit single instance vs. all future)
- [ ] Add recurring event exception handling (skip specific dates)

### Sidebar / Navigation

- [ ] Add "Creer" link in sidebar under Evenements for admin/pastors

## P3 — Nice-to-Have

### Virtual Event Support

- [ ] Add virtual event fields (meeting URL, platform, access code)
- [ ] Add embedded video player for live-streamed events (YouTube/Vimeo embed)
- [ ] Add hybrid event support (in-person + virtual attendance tracking)

### Event Photo Gallery

- [ ] Add photo upload per event (multiple images)
- [ ] Add photo gallery view on event detail page
- [ ] Add photo moderation for staff (approve before public display)

### Event Feedback & Surveys

- [ ] Add post-event survey builder (rating, multiple choice, open text)
- [ ] Add automated survey email sent X hours after event ends
- [ ] Add survey results dashboard with aggregate scores

### Multi-Campus Event Coordination

- [ ] Add campus field on event (for multi-campus churches)
- [ ] Add cross-campus event sharing (publish event to multiple campuses)
- [ ] Add campus-filtered calendar views

### Existing Small Fixes

- [ ] RSVP: add email/notification when RSVP status changes
- [ ] Event list: add filter by event type
- [ ] Event detail: add "Share event" link (copy link to clipboard)
