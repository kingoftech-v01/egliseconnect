# Events App

Event management for ÉgliseConnect.

## Features
- Event creation and management
- Calendar view
- RSVP system
- Capacity management
- Online/in-person events

## API Endpoints
- GET /api/v1/events/events/ - List events
- POST /api/v1/events/events/ - Create event
- GET /api/v1/events/events/{uuid}/ - Get event
- GET /api/v1/events/events/upcoming/ - Upcoming events
- GET /api/v1/events/events/calendar/ - Calendar view
- POST /api/v1/events/events/{uuid}/rsvp/ - Submit RSVP
- GET /api/v1/events/events/{uuid}/attendees/ - Get attendees

## Frontend URLs
- /events/ - Event list
- /events/calendar/ - Calendar view
- /events/{uuid}/ - Event details
- /events/{uuid}/rsvp/ - Submit RSVP
