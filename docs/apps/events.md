# App: Events (Evenements)

## Description
Gestion complete des evenements: creation, RSVP, calendrier, salles et reservations, templates, waitlist, besoins volontaires, galerie photos, sondages post-evenement et formulaires d'inscription.

## Modeles (13)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `Event` | title, event_type, start/end_datetime, all_day, location, is_online, online_link, max_attendees, requires_rsvp, is_recurring, recurrence_rule (RRULE), kiosk_mode_enabled | FK: organizer, parent_event(self) |
| `EventRSVP` | status, guests, notes | FK: event, member. Unique: [event, member] |
| `Room` | name, capacity, location, amenities_json, photo | - |
| `RoomBooking` | start/end_datetime, status | FK: room, event, booked_by |
| `RegistrationForm` | title, fields_json | FK: event |
| `RegistrationEntry` | data_json, submitted_at | FK: form, member. Unique: [form, member] |
| `EventTemplate` | name, event_type, default_duration/description/capacity/location, requires_rsvp | - |
| `EventWaitlist` | position, added_at, promoted_at | FK: event, member. Unique: [event, member] |
| `EventVolunteerNeed` | position_name, required_count, description | FK: event |
| `EventVolunteerSignup` | status | FK: need, member. Unique: [need, member] |
| `EventPhoto` | image, caption, is_approved | FK: event, uploaded_by |
| `EventSurvey` | title, questions_json, send_after_hours | FK: event |
| `SurveyResponse` | answers_json, submitted_at | FK: survey, member. Unique: [survey, member] |

## Proprietes calculees
- `Event.confirmed_count` → RSVPs confirmees
- `Event.is_full` → confirmed_count >= max_attendees
- `Event.available_spots` → max_attendees - confirmed_count
- `Event.waitlist_count` → nombre en waitlist
- `EventVolunteerNeed.filled_count` → signups confirmes
- `EventVolunteerNeed.is_filled` → filled >= required

## API ViewSets (7)
- `EventViewSet` - Filtre: type, published, cancelled, campus. Actions: upcoming, calendar, rsvp, attendees
- `RoomViewSet` - CRUD salles
- `RoomBookingViewSet` - Filtre: room, status
- `EventTemplateViewSet` - Search: name
- `EventVolunteerNeedViewSet` - Filtre: event
- `EventPhotoViewSet` - Filtre: event, is_approved
- `EventSurveyViewSet` - Filtre: event

## Frontend Views (21+ templates)
event_list, event_calendar, event_create, event_detail, event_update, event_delete, event_cancel, event_rsvp, event_ics_download, event_ics_feed, room_list/create/update/delete/calendar, booking_list/create/action, kiosk_checkin, template_list/create, event_create_from_template, waitlist_view/join/promote, volunteer_needs_view/create/signup, photo_gallery/upload/approve, survey_builder/respond/results

## Forms (9)
EventForm, RSVPForm, RoomForm, RoomBookingForm, EventTemplateForm, EventFromTemplateForm, RegistrationFormForm, EventVolunteerNeedForm, EventPhotoForm, EventSurveyForm

## Points d'attention
- Support recurrence iCal RRULE mais generation auto d'occurrences non implementee
- Export iCal disponible (par evenement + feed complet)
- FullCalendar utilise pour l'affichage calendrier
- Kiosk mode par evenement pour check-in self-service
- Sondages et formulaires d'inscription utilisent JSON pour la structure des champs

## Fichiers cles
- `apps/events/models.py` - 13 modeles
- `apps/events/views_api.py` - 7 ViewSets
- `apps/events/views_frontend.py` - Vues template
- `apps/events/forms.py` - 9 formulaires
