# App: Volunteers (Benevolat)

## Description
Gestion complete du benevolat: positions, planification, disponibilites, echanges de quarts, heures de service, competences, milestones, cross-training, annonces d'equipe et checklists d'integration.

## Modeles (16)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `VolunteerPosition` | name, role_type, description, min/max_volunteers, skills_required | - |
| `VolunteerAvailability` | is_available, frequency, notes | FK: member, position. Unique: [member, position] |
| `VolunteerSchedule` | date, status, reminder_*_sent flags (5j/3j/1j/jour) | FK: member, position, event |
| `PlannedAbsence` | start/end_date, reason | FK: member, approved_by |
| `SwapRequest` | status, reason | FK: original_schedule, requested_by, swap_with |
| `VolunteerHours` | date, hours_worked, description, approved_at | FK: member, position, approved_by |
| `VolunteerBackgroundCheck` | status, check/expiry_date | FK: member, position |
| `TeamAnnouncement` | title, body, sent_at | FK: position, author |
| `PositionChecklist` | title, description, order, is_required | FK: position |
| `ChecklistProgress` | completed_at | FK: member, checklist_item, verified_by. Unique: [member, checklist_item] |
| `Skill` | name (unique), category, description | - |
| `VolunteerSkill` | proficiency_level, certified_at | FK: member, skill, verified_by. Unique: [member, skill] |
| `Milestone` | name, milestone_type, threshold, badge_icon | Unique: [milestone_type, threshold] |
| `MilestoneAchievement` | achieved_at, notified | FK: member, milestone. Unique: [member, milestone] |
| `AvailabilitySlot` | day_of_week, time_start, time_end, is_available | FK: member |
| `CrossTraining` | certified_at, notes | FK: member, original_position, trained_position. Unique: [member, orig, trained] |

## API ViewSets (4)
- `VolunteerPositionViewSet` - Filtre: role_type, is_active. Search: name
- `VolunteerScheduleViewSet` - Filtre: position, status, date, member. Actions: my-schedule, confirm
- `VolunteerAvailabilityViewSet` - Scoped: own unless staff
- `SwapRequestViewSet` - Scoped: staff sees all, members see own

## Frontend Views (30+)
Positions CRUD, checklist management, schedule CRUD + bulk, my-schedule, mobile-schedule, availability update/slots/heatmap/calendar, planned absences CRUD, swap requests list/create/detail, hours log/my-summary/admin-report, background checks CRUD, announcements list/create, onboarding checklist, skills list/profile, milestones page, volunteer of month, cross-training list/create/suggestions

## Forms (13)
VolunteerPositionForm, VolunteerScheduleForm, SwapRequestForm, VolunteerHoursForm, VolunteerHoursSelfForm, VolunteerBackgroundCheckForm, TeamAnnouncementForm, PositionChecklistForm, SkillForm, VolunteerSkillForm, VolunteerSkillSelfForm, AvailabilitySlotForm, CrossTrainingForm

## Points d'attention
- Vue mobile dediee (`mobile_schedule.html`) pour planning sur telephone
- Rappels multiples: 5 jours, 3 jours, 1 jour, jour meme (flags booleen dans le modele)
- Auto-scheduling existe en preview mais algorithme basique
- Cross-training suggere des positions basees sur les competences du volontaire

## Fichiers cles
- `apps/volunteers/models.py` - 16 modeles
- `apps/volunteers/views_api.py` - 4 ViewSets
- `apps/volunteers/views_frontend.py` - 30+ vues
- `apps/volunteers/forms.py` - 13 formulaires
