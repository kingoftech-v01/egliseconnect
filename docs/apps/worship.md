# App: Worship (Planification du culte)

## Description
Planification complete des services de culte: services avec sections et assignments, sermons, bibliotheque de chants, setlists, live streams, rehearsals, song requests et exports (ProPresenter, EasyWorship).

## Modeles (15)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `WorshipService` | date, start/end_time, duration_minutes, status, theme, validation_deadline (auto 14j avant) | FK: created_by, event |
| `ServiceSection` | name, order, duration_minutes, section_type, notes | FK: service, department. Unique: [service, order] |
| `ServiceAssignment` | status (assigned/confirmed/declined), reminder_*_sent flags | FK: section, member, task_type |
| `EligibleMemberList` | section_type (unique) | M2M: members. FK: department |
| `SermonSeries` | title, description, start/end_date, image | - |
| `Sermon` | title, scripture_reference, date, audio/video_url, status, duration_minutes | FK: speaker, series, service |
| `Song` | title, artist, song_key, bpm, lyrics, chord_chart, ccli_number, tags, last_played, play_count | - |
| `Setlist` | notes | OneToOne: WorshipService |
| `SetlistSong` | order, key_override, notes | FK: setlist, song. Unique: [setlist, order] |
| `VolunteerPreference` | preferred_positions, blackout_dates (JSON), max_services_per_month | OneToOne: Member |
| `LiveStream` | platform, stream_url, start/end_time, viewer_count, recording_url | FK: service |
| `Rehearsal` | date, start/end_time, location, notes | FK: service |
| `RehearsalAttendee` | status (invited/confirmed/declined) | FK: rehearsal, member. Unique: [rehearsal, member] |
| `SongRequest` | song_title, artist, notes, votes, status, scheduled_date | FK: requested_by |
| `SongRequestVote` | - | FK: song_request, member. Unique: [song_request, member] |

## Proprietes calculees
- `WorshipService.confirmation_rate` → pourcentage d'assignments confirmes
- `WorshipService.planning_checklist` → liste de verification planification
- `Song.play_count` / `last_played` → analytics d'utilisation

## API ViewSets (13)
services, sections, assignments, eligible, sermons, sermon-series, songs, setlists, setlist-songs, preferences, livestreams, rehearsals, song-requests

## Frontend Views (50+ templates)
Service CRUD + sections + assignments + eligible lists, sermon CRUD + series + RSS feed + archive, songs CRUD + chord charts (affichage + impression) + search, setlist builder, CCLI report, calendar + planning timeline, most played/rotation analytics, auto-schedule preview, live streams CRUD, rehearsals CRUD + attendees, song requests submit/vote/moderate, duplicate service, print service order, ProPresenter export, EasyWorship export, volunteer preferences

## Forms (14)
WorshipServiceForm, ServiceSectionForm, ServiceAssignmentForm, EligibleMemberListForm, ServiceDateRangeFilterForm, SermonForm, SermonSeriesForm, SermonFilterForm, SongForm, SetlistForm, SetlistSongForm, SongSearchForm, VolunteerPreferenceForm, LiveStreamForm, RehearsalForm, SongRequestForm, SongRequestModerationForm

## Points d'attention
- `validation_deadline` auto-set a 14 jours avant le service dans `save()`
- Section types pre-definis: prelude, annonces, louange, offrande, predication, communion, priere, benediction
- Assignments workflow: assigned → confirmed/declined avec rappels multi-niveaux
- Chord chart: affichage monospace, version imprimable
- CCLI number tracking pour reporting de licence
- Setlist: chants ordonnes avec override de tonalite possible
- Exports: ProPresenter et EasyWorship formats
- Song requests: systeme de vote democratique + moderation staff
- Sermons: RSS feed pour distribution podcast

## Fichiers cles
- `apps/worship/models.py` - 15 modeles
- `apps/worship/views_api.py` - 13 ViewSets
- `apps/worship/views_frontend.py` - 50+ vues (app avec le plus de templates)
- `apps/worship/forms.py` - 14 formulaires
