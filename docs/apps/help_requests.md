# App: Help Requests (Entraide)

## Description
Systeme d'entraide complet: demandes d'aide avec categories, soins pastoraux, mur de priere, equipes de soin, fonds de benevolence, trains de repas, protocoles de crise et ressources.

## Modeles (13)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `HelpRequestCategory` | name, name_fr, description, icon, order | - |
| `HelpRequest` | request_number (HR-YYYYMM-XXXX), title, description, urgency, status, is_confidential | FK: member, category, assigned_to |
| `HelpRequestComment` | content, is_internal | FK: help_request, author |
| `PastoralCare` | care_type, date, notes, follow_up_date, status | FK: member, assigned_to, created_by |
| `PrayerRequest` | title, description, is_anonymous, is_public, status, testimony | FK: member |
| `CareTeam` | name, description | FK: leader |
| `CareTeamMember` | joined_at | FK: team, member. Unique: [team, member] |
| `BenevolenceFund` | name, total_balance, description | - |
| `BenevolenceRequest` | amount_requested, reason, status, amount_granted, disbursed_at | FK: member, fund, approved_by |
| `MealTrain` | reason, start/end_date, dietary_restrictions, status | FK: recipient |
| `MealSignup` | date, confirmed, notes | FK: meal_train, volunteer. Unique: [meal_train, volunteer, date] |
| `CrisisProtocol` | title, protocol_type, steps_json | - |
| `CrisisResource` | title, description, contact_info, url, category | - |

## API ViewSets (13)
- `HelpRequestCategoryViewSet` (ReadOnly) - Categories actives
- `HelpRequestViewSet` - Role-scoped (pasteurs=all, leaders=group non-confidentiel, membres=own). Actions: my_requests, assign, resolve, comment, comments
- `PastoralCareViewSet` - IsPastor|IsAdmin. Filtre: care_type, status, assigned_to
- `PrayerRequestViewSet` - Public+approved pour reguliers, all pour staff. Actions: mark_answered, wall
- `CareTeamViewSet`, `CareTeamMemberViewSet` - IsPastor|IsAdmin
- `BenevolenceFundViewSet` - IsPastor|IsAdmin
- `BenevolenceRequestViewSet` - Scoped: staff=all, membres=own
- `MealTrainViewSet` - Tous authentifies
- `MealSignupViewSet` - Filtre: meal_train, confirmed
- `CrisisProtocolViewSet`, `CrisisResourceViewSet` - IsPastor|IsAdmin

## Frontend Views (33 templates)
request_create/list/my_requests/detail/update/comment, category_list/create/edit/delete, care_dashboard/create/calendar/detail/update, care_team_list/create/detail/add_member/remove_member, prayer_request_create/wall, prayer_anonymous/anonymous_done, prayer_moderation/detail/answered/moderate, benevolence_list/create/detail/approve/disburse, meal_train_list/create/detail/signup, crisis_protocol_list/create/detail, crisis_resource_list/create, crisis_notify

## Forms (17)
HelpRequestForm, HelpRequestCommentForm, HelpRequestAssignForm, HelpRequestResolveForm, HelpRequestCategoryForm, PastoralCareForm, PastoralCareUpdateForm, PrayerRequestForm, AnonymousPrayerRequestForm, PrayerRequestTestimonyForm, CareTeamForm, CareTeamMemberForm, BenevolenceRequestForm, BenevolenceApprovalForm, BenevolenceFundForm, MealTrainForm, MealSignupForm, CrisisProtocolForm, CrisisResourceForm

## Points d'attention
- Categories bilingues (name + name_fr)
- Commentaires internes (staff-only) vs publics
- Demandes confidentielles visibles seulement par pasteurs/admins
- Priere anonyme accessible sans login
- Benevolence fund balance est tracked manuellement
- Protocoles de crise utilisent JSON pour les etapes

## Fichiers cles
- `apps/help_requests/models.py` - 13 modeles
- `apps/help_requests/views_api.py` - 13 ViewSets
- `apps/help_requests/views_frontend.py` - 33 templates
- `apps/help_requests/forms.py` - 17 formulaires
