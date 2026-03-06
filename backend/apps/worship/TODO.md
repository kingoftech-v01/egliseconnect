# TODO - Worship App

## P1 — Critical

### CRUD Completions

- [ ] Add service delete view (create and edit exist, but no delete)
- [ ] Add section edit and delete views (currently only add section)
- [ ] Add assignment remove/unassign view

### Sermon/Message Management

- [ ] Add Sermon model (title, speaker, scripture_reference, date, series, audio_url, video_url, notes)
- [ ] Add sermon CRUD views (create, list, detail, edit, delete)
- [ ] Add sermon series model (group sermons into series)
- [ ] Add sermon media upload (audio file, video embed URL)
- [ ] Add sermon notes/outline field (rich text or markdown)
- [ ] Add sermon archive page (searchable, filterable by speaker/series/date)
- [ ] Add sermon RSS feed for podcast distribution

### Song/Setlist Management

- [ ] Add Song model (title, artist, key, bpm, lyrics, chord_chart, ccli_number)
- [ ] Add song database CRUD views (add, edit, search, browse)
- [ ] Add setlist builder (drag-and-drop songs into service order)
- [ ] Add song key transposition tool (transpose chords to match worship leader's preference)
- [ ] Add CCLI song reporting integration (track song usage for licensing)

### Frontend Refinements

- [ ] Service list: add date range filter
- [ ] Service detail: add print view for worship order (printable service program)
- [ ] Section management: add section reordering (drag & drop)
- [ ] My assignments: show confirm/decline buttons inline
- [ ] Service detail: show confirmation rate as a visual progress bar

## P2 — Important

### Worship Planning Calendar

- [ ] Add calendar view of all worship services (month/week view)
- [ ] Add drag-and-drop service builder (arrange sections, assign roles visually)
- [ ] Add service planning timeline (weeks before service: plan, rehearse, finalize, execute)
- [ ] Add planning checklist per service (all sections filled, all roles assigned, all confirmed)

### Song Usage Analytics

- [ ] Add song usage tracking (which songs played on which dates)
- [ ] Add most-played songs report (top 10/20, filterable by date range)
- [ ] Add last-played date per song (avoid repeating songs too frequently)
- [ ] Add song rotation suggestions (songs not played in X weeks)

### Chord Chart / Lead Sheet Viewer

- [ ] Add chord chart display mode (lyrics with chords above)
- [ ] Add auto-scroll for live performance (configurable scroll speed)
- [ ] Add Nashville number system toggle (for musicians who prefer numbers over chords)
- [ ] Add print-friendly chord chart layout

### Volunteer Auto-Scheduling

- [ ] Add auto-schedule generator based on availability + eligibility + rotation fairness
- [ ] Add scheduling conflict detection (member already scheduled elsewhere)
- [ ] Add schedule preview before publishing (admin reviews before sending)
- [ ] Add scheduling preferences per volunteer (preferred positions, blackout dates)

### Sidebar / Navigation

- [ ] Add "Creer un culte" link in sidebar under Cultes for staff roles
- [ ] Add "Mes assignations" link in sidebar visible to all members
- [ ] Verify "Cultes" section is visible in sidebar for all members with full access

## P3 — Nice-to-Have

### ProPresenter / EasyWorship Integration

- [ ] Add ProPresenter export (generate .pro file from service plan with lyrics)
- [ ] Add EasyWorship export (generate schedule file from service plan)
- [ ] Add import from ProPresenter/EasyWorship (sync songs from presentation software)

### Live Streaming Integration

- [ ] Add live stream embed on service detail page (YouTube Live, Facebook Live)
- [ ] Add live stream schedule management (start/stop times, platform URLs)
- [ ] Add live viewer count display during stream
- [ ] Add live stream recording archive (auto-save past streams)

### Worship Team Rehearsal Scheduling

- [ ] Add rehearsal model (date, time, location, service_link, attendees)
- [ ] Add rehearsal CRUD views
- [ ] Add rehearsal RSVP (confirm/decline attendance)
- [ ] Add rehearsal material sharing (setlist, chord charts, backing tracks)

### Congregation Song Requests

- [ ] Add song request submission form (members suggest songs)
- [ ] Add request voting system (other members upvote requests)
- [ ] Add request moderation for worship leader (approve, decline, schedule)
- [ ] Add "most requested" report

### Existing Small Fixes

- [ ] Add notification when a new assignment is created
- [ ] Service detail: add "Publish/Finalize" button
- [ ] Add eligible member list management UI
- [ ] Add service duplication (copy sections from a previous service as template)
- [ ] Service list: add calendar view alongside list view
- [ ] Add API endpoints (currently api_urlpatterns is empty)
- [ ] Upgrade admin from basic admin.site.register() to custom ModelAdmin classes
