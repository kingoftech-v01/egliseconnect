# Module Volunteers (Benevolat)

> **Application Django** : `apps.volunteers`
> **Chemin** : `apps/volunteers/`

---

## Vue d'ensemble

### Pour les non-techniques

Ce module coordonne le service des benevoles au sein de l'eglise. Il permet de :

- **Gerer les postes** de benevolat (accueil, louange, technique, enfants, jeunesse, etc.)
- **Planifier les horaires** de chaque dimanche ou evenement special
- **Indiquer sa disponibilite** en fonction de la frequence souhaitee (chaque semaine, aux deux semaines, mensuelle, occasionnelle)
- **Demander un echange** de quart lorsqu'un benevole ne peut pas assurer sa plage prevue

Les pasteurs et administrateurs creent les postes et assignent les horaires, tandis que les membres consultent leur propre calendrier et gerent leurs disponibilites.

### Pour les techniques

L'application est construite avec Django et Django REST Framework. Elle expose quatre ViewSets REST complets ainsi que quatre vues frontend servies par templates. Les models heritent de `BaseModel` (UUID, `created_at`, `updated_at`, `is_active`). Les constantes de l'application sont centralisees dans `apps.core.constants` (`VolunteerRole`, `ScheduleStatus`, `VolunteerFrequency`). Les permissions sont gerees par les classes `IsMember` et `IsPastorOrAdmin` du module `apps.core.permissions`.

---

## Architecture des fichiers

```
apps/volunteers/
    __init__.py
    apps.py
    models.py              # 4 models
    serializers.py          # 4 serializers
    views_api.py            # 4 ViewSets REST
    views_frontend.py       # 4 vues avec templates
    urls.py                 # Routage API + frontend
    admin.py                # Configuration Django Admin
    migrations/
        0001_initial.py
    tests/
        __init__.py
        factories.py        # 4 factories (factory_boy)
        test_views_api.py   # Tests API complets
        test_views_frontend.py
```

---

## Models

### VolunteerPosition

Represente un poste de benevolat dans un ministere de l'eglise.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | `CharField(100)` | Nom du poste (ex: "Pianiste", "Son") |
| `role_type` | `CharField(20)` | Type de ministere (`VolunteerRole.CHOICES`) |
| `description` | `TextField` | Description detaillee du poste |
| `min_volunteers` | `PositiveIntegerField` | Nombre minimum de benevoles requis (defaut: 1) |
| `max_volunteers` | `PositiveIntegerField` | Nombre maximum (optionnel, nullable) |
| `skills_required` | `TextField` | Competences necessaires |

**Valeurs possibles pour `role_type`** :

| Constante | Valeur | Libelle FR |
|-----------|--------|------------|
| `VolunteerRole.WORSHIP` | `'worship'` | Louange |
| `VolunteerRole.HOSPITALITY` | `'hospitality'` | Accueil |
| `VolunteerRole.TECHNICAL` | `'technical'` | Technique |
| `VolunteerRole.CHILDREN` | `'children'` | Enfants |
| `VolunteerRole.YOUTH` | `'youth'` | Jeunesse |
| `VolunteerRole.ADMIN` | `'admin'` | Administratif |
| `VolunteerRole.OUTREACH` | `'outreach'` | Evangelisation |
| `VolunteerRole.OTHER` | `'other'` | Autre |

**Meta** : ordonne par `name`, verbose `"Poste de benevolat"`.

---

### VolunteerAvailability

Indique la disponibilite d'un membre pour un poste specifique.

| Champ | Type | Description |
|-------|------|-------------|
| `member` | `ForeignKey(Member)` | Membre benevole |
| `position` | `ForeignKey(VolunteerPosition)` | Poste concerne |
| `is_available` | `BooleanField` | Disponible ou non (defaut: `True`) |
| `frequency` | `CharField(20)` | Frequence souhaitee (`VolunteerFrequency.CHOICES`) |
| `notes` | `TextField` | Commentaires (optionnel) |

**Contrainte unique** : `(member, position)` -- un membre ne peut avoir qu'une seule disponibilite par poste.

**Valeurs possibles pour `frequency`** :

| Constante | Valeur | Libelle FR |
|-----------|--------|------------|
| `VolunteerFrequency.WEEKLY` | `'weekly'` | Chaque semaine |
| `VolunteerFrequency.BIWEEKLY` | `'biweekly'` | Aux deux semaines |
| `VolunteerFrequency.MONTHLY` | `'monthly'` | Une fois par mois |
| `VolunteerFrequency.OCCASIONAL` | `'occasional'` | Occasionnellement |

---

### VolunteerSchedule

Represente une assignation planifiee d'un benevole a un poste pour une date donnee.

| Champ | Type | Description |
|-------|------|-------------|
| `member` | `ForeignKey(Member)` | Benevole assigne |
| `position` | `ForeignKey(VolunteerPosition)` | Poste a occuper |
| `event` | `ForeignKey(Event)` | Evenement lie (optionnel, nullable) |
| `date` | `DateField` | Date du quart |
| `status` | `CharField(20)` | Statut de l'assignation (`ScheduleStatus.CHOICES`) |
| `reminder_sent` | `BooleanField` | Si un rappel a ete envoye (defaut: `False`) |
| `notes` | `TextField` | Notes additionnelles |

**Valeurs possibles pour `status`** :

| Constante | Valeur | Libelle FR |
|-----------|--------|------------|
| `ScheduleStatus.SCHEDULED` | `'scheduled'` | Planifie |
| `ScheduleStatus.CONFIRMED` | `'confirmed'` | Confirme |
| `ScheduleStatus.DECLINED` | `'declined'` | Refuse |
| `ScheduleStatus.COMPLETED` | `'completed'` | Complete |
| `ScheduleStatus.NO_SHOW` | `'no_show'` | Absent |

**Meta** : ordonne par `date`.

---

### SwapRequest

Demande d'echange de quart entre deux benevoles.

| Champ | Type | Description |
|-------|------|-------------|
| `original_schedule` | `ForeignKey(VolunteerSchedule)` | Quart original a echanger |
| `requested_by` | `ForeignKey(Member)` | Membre qui demande l'echange |
| `swap_with` | `ForeignKey(Member)` | Membre avec qui echanger (optionnel, nullable) |
| `status` | `CharField(20)` | `'pending'` / `'approved'` / `'declined'` |
| `reason` | `TextField` | Raison de la demande |

---

## Serializers

Quatre serializers `ModelSerializer` dans `serializers.py` :

| Serializer | Model | Champs supplementaires (read-only) |
|------------|-------|------------------------------------|
| `VolunteerPositionSerializer` | `VolunteerPosition` | `role_type_display` |
| `VolunteerAvailabilitySerializer` | `VolunteerAvailability` | `member_name`, `position_name` |
| `VolunteerScheduleSerializer` | `VolunteerSchedule` | `member_name`, `position_name`, `status_display` |
| `SwapRequestSerializer` | `SwapRequest` | `requested_by_name` |

Tous utilisent `fields = '__all__'`.

---

## Endpoints API REST

Tous les endpoints sont prefixes par `/api/v1/volunteers/` et utilisent le `DefaultRouter` de DRF.

### VolunteerPositionViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/volunteers/positions/` | Lister les postes | `IsMember` (authentifie) |
| `POST` | `/api/v1/volunteers/positions/` | Creer un poste | `IsPastorOrAdmin` |
| `GET` | `/api/v1/volunteers/positions/{id}/` | Detail d'un poste | `IsMember` |
| `PUT/PATCH` | `/api/v1/volunteers/positions/{id}/` | Modifier un poste | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/volunteers/positions/{id}/` | Supprimer un poste | `IsPastorOrAdmin` |

**Filtres** : `role_type`, `is_active` (via `DjangoFilterBackend`)
**Recherche** : `name` (via `SearchFilter`)

### VolunteerScheduleViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/volunteers/schedules/` | Lister tous les horaires | `IsMember` |
| `POST` | `/api/v1/volunteers/schedules/` | Creer un horaire | `IsPastorOrAdmin` |
| `GET` | `/api/v1/volunteers/schedules/{id}/` | Detail d'un horaire | `IsMember` |
| `PUT/PATCH` | `/api/v1/volunteers/schedules/{id}/` | Modifier un horaire | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/volunteers/schedules/{id}/` | Supprimer un horaire | `IsPastorOrAdmin` |
| `GET` | `/api/v1/volunteers/schedules/my-schedule/` | Mon horaire personnel | `IsMember` |
| `POST` | `/api/v1/volunteers/schedules/{id}/confirm/` | Confirmer une assignation | `IsPastorOrAdmin` |

**Filtres** : `position`, `status`, `date`, `member`
**Tri** : `date` (via `OrderingFilter`)

### VolunteerAvailabilityViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/volunteers/availability/` | Lister les disponibilites | `IsMember` |
| `POST` | `/api/v1/volunteers/availability/` | Declarer sa disponibilite | `IsMember` |
| `GET` | `/api/v1/volunteers/availability/{id}/` | Detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/volunteers/availability/{id}/` | Modifier | `IsMember` |
| `DELETE` | `/api/v1/volunteers/availability/{id}/` | Supprimer | `IsMember` |

**Portee (scoping)** : les membres ne voient que leurs propres disponibilites; le staff (`is_staff`) voit tout.

### SwapRequestViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/volunteers/swap-requests/` | Lister les demandes | `IsMember` |
| `POST` | `/api/v1/volunteers/swap-requests/` | Creer une demande | `IsMember` |
| `GET` | `/api/v1/volunteers/swap-requests/{id}/` | Detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/volunteers/swap-requests/{id}/` | Modifier | `IsMember` |
| `DELETE` | `/api/v1/volunteers/swap-requests/{id}/` | Supprimer | `IsMember` |

**Portee (scoping)** : les membres ne voient que les demandes ou ils sont `requested_by` ou `swap_with`. Le staff voit toutes les demandes.

---

## URLs frontend

| URL | Vue | Template | Description |
|-----|-----|----------|-------------|
| `/volunteers/positions/` | `position_list` | `volunteers/position_list.html` | Liste des postes actifs |
| `/volunteers/schedule/` | `schedule_list` | `volunteers/schedule_list.html` | Horaire complet de tous les benevoles |
| `/volunteers/my-schedule/` | `my_schedule` | `volunteers/my_schedule.html` | Mon horaire personnel |
| `/volunteers/availability/` | `availability_update` | `volunteers/availability_update.html` | Gerer mes disponibilites par poste |

Toutes les vues frontend necessitent `@login_required`. La vue `availability_update` gere le POST pour mettre a jour les disponibilites de chaque poste via `update_or_create`.

---

## Templates

| Template | Description |
|----------|-------------|
| `volunteers/position_list.html` | Affiche les postes actifs avec type, description et nombre requis |
| `volunteers/schedule_list.html` | Tableau des horaires (date, membre, poste, statut) |
| `volunteers/my_schedule.html` | Horaire filtre pour le membre connecte |
| `volunteers/availability_update.html` | Formulaire avec checkbox par poste + selection de frequence |

---

## Administration Django

Quatre classes d'administration enregistrees dans `admin.py` :

| Admin Class | Colonnes affichees | Filtres |
|-------------|-------------------|---------|
| `VolunteerPositionAdmin` | name, role_type, min/max_volunteers, is_active | role_type, is_active |
| `VolunteerAvailabilityAdmin` | member, position, is_available, frequency | position, is_available, frequency |
| `VolunteerScheduleAdmin` | member, position, date, status, reminder_sent | position, status, date |
| `SwapRequestAdmin` | original_schedule, requested_by, swap_with, status | status |

`VolunteerScheduleAdmin` dispose egalement de `date_hierarchy = 'date'` pour la navigation par date. Les champs `member`, `position` et `event` utilisent `autocomplete_fields`.

---

## Permissions

| Role | Consulter postes | Creer/modifier postes | Consulter horaires | Creer/modifier horaires | Gerer ses disponibilites | Demandes d'echange |
|------|------------------|-----------------------|--------------------|------------------------|--------------------------|---------------------|
| **Membre** | Oui | Non | Oui (tous) | Non | Oui (les siennes) | Oui (les siennes) |
| **Responsable de groupe** | Oui | Non | Oui | Non | Oui | Oui |
| **Pasteur / Admin** | Oui | Oui | Oui | Oui | Oui (toutes) | Oui (toutes) |
| **Staff (is_staff)** | Selon role | Selon role | Selon role | Selon role | Oui (toutes) | Oui (toutes) |

---

## Exemples d'utilisation

### API : Creer un poste de benevolat (Pasteur)

```bash
curl -X POST /api/v1/volunteers/positions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pianiste",
    "role_type": "worship",
    "description": "Accompagnement musical au piano",
    "min_volunteers": 1,
    "max_volunteers": 2,
    "skills_required": "Piano, lecture de partitions"
  }'
```

**Reponse** (`201 Created`) :
```json
{
  "id": "a1b2c3d4-...",
  "name": "Pianiste",
  "role_type": "worship",
  "role_type_display": "Louange",
  "description": "Accompagnement musical au piano",
  "min_volunteers": 1,
  "max_volunteers": 2,
  "skills_required": "Piano, lecture de partitions",
  "is_active": true,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

### API : Consulter mon horaire

```bash
curl -X GET /api/v1/volunteers/schedules/my-schedule/ \
  -H "Authorization: Bearer <token>"
```

**Reponse** (`200 OK`) :
```json
[
  {
    "id": "...",
    "member": "...",
    "member_name": "Jean Tremblay",
    "position": "...",
    "position_name": "Pianiste",
    "date": "2026-02-09",
    "status": "scheduled",
    "status_display": "Planifie",
    "reminder_sent": false,
    "notes": ""
  }
]
```

### API : Creer une demande d'echange

```bash
curl -X POST /api/v1/volunteers/swap-requests/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "original_schedule": "<schedule-uuid>",
    "requested_by": "<member-uuid>",
    "swap_with": "<autre-member-uuid>",
    "reason": "Conflit avec un rendez-vous medical"
  }'
```

### API : Filtrer les postes par type

```bash
# Postes d'accueil uniquement
curl -X GET "/api/v1/volunteers/positions/?role_type=hospitality" \
  -H "Authorization: Bearer <token>"

# Recherche par nom
curl -X GET "/api/v1/volunteers/positions/?search=Piano" \
  -H "Authorization: Bearer <token>"
```

### API : Confirmer une assignation (Pasteur)

```bash
curl -X POST /api/v1/volunteers/schedules/<schedule-id>/confirm/ \
  -H "Authorization: Bearer <token>"
```

---

## Tests

Les tests utilisent `pytest` avec le plugin `pytest-django` et `factory_boy` pour la generation de donnees.

### Factories disponibles

| Factory | Model | Valeurs par defaut |
|---------|-------|--------------------|
| `VolunteerPositionFactory` | `VolunteerPosition` | role_type=WORSHIP, min_volunteers=1 |
| `VolunteerAvailabilityFactory` | `VolunteerAvailability` | is_available=True, frequency=MONTHLY |
| `VolunteerScheduleFactory` | `VolunteerSchedule` | date=aujourd'hui+7 jours, status=SCHEDULED |
| `SwapRequestFactory` | `SwapRequest` | status='pending' |

### Executer les tests

```bash
# Tous les tests du module volunteers
pytest apps/volunteers/ -v

# Tests API seulement
pytest apps/volunteers/tests/test_views_api.py -v

# Tests frontend seulement
pytest apps/volunteers/tests/test_views_frontend.py -v

# Un test specifique
pytest apps/volunteers/tests/test_views_api.py::TestVolunteerPositionCreate -v
```

### Couverture des tests API

Les tests couvrent les scenarios suivants :

- **VolunteerPositionViewSet** : list, retrieve, create, update, delete, filtrage par `role_type`, recherche par `name`, verification des permissions (membre vs pasteur)
- **VolunteerScheduleViewSet** : list, retrieve, create, update, delete, `my-schedule`, `confirm`, filtrage par `status`, tri par `date`, gestion du profil manquant
- **VolunteerAvailabilityViewSet** : CRUD complet, scoping (membre voit les siennes, staff voit tout), utilisateur sans profil
- **SwapRequestViewSet** : CRUD complet, scoping (`requested_by` + `swap_with`), staff voit tout

---

## Dependances

| Dependance | Utilisation |
|------------|-------------|
| `apps.core.models.BaseModel` | Heritage des models (UUID, timestamps, is_active) |
| `apps.core.constants` | `VolunteerRole`, `ScheduleStatus`, `VolunteerFrequency` |
| `apps.core.permissions` | `IsMember`, `IsPastorOrAdmin` |
| `apps.members.Member` | FK vers le membre benevole |
| `apps.events.Event` | FK optionnelle vers l'evenement lie |
| `django-filter` | Filtrage des endpoints API |
