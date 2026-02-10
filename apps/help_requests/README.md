# Module Help Requests (Demandes d'aide)

> **Application Django** : `apps.help_requests`
> **Chemin** : `apps/help_requests/`

---

## Vue d'ensemble

### Pour les non-techniques

Ce module offre un systeme confidentiel de demandes d'aide. Les membres de l'eglise peuvent soumettre des demandes pour :

- **Priere** : demande de soutien en priere pour une situation personnelle ou familiale
- **Aide financiere** : besoin d'assistance financiere ponctuelle
- **Aide materielle** : besoin de biens materiels (vetements, meubles, nourriture, etc.)
- **Accompagnement pastoral** : demande de rencontre avec un pasteur

Chaque demande recoit automatiquement un numero unique (ex: `HR-202602-0001`), peut etre marquee comme **confidentielle** (visible uniquement par les pasteurs et administrateurs), et suit un workflow complet : nouvelle -> en cours -> resolue -> fermee.

Le personnel de l'eglise peut assigner les demandes, suivre leur progression, et ajouter des notes internes invisibles pour le demandeur. Les responsables de groupe peuvent voir les demandes non-confidentielles de leurs membres.

### Pour les techniques

L'application suit le patron de conception "ticket/support". Elle expose un ViewSet REST principal avec des actions custom (`assign`, `resolve`, `comment`, `comments`, `my_requests`) et un ViewSet en lecture seule pour les categories. Les permissions sont granulaires : le `get_queryset()` filtre dynamiquement selon le role du membre (pasteur/admin voient tout, responsable de groupe voit les demandes de son groupe sauf les confidentielles, membre voit les siennes). Le model `HelpRequest` genere automatiquement un numero de demande via `save()`. Quatre formulaires Django avec `W3CRMFormMixin` couvrent la creation, les commentaires, l'assignation et la resolution.

---

## Architecture des fichiers

```
apps/help_requests/
    __init__.py
    apps.py
    models.py              # 3 models
    forms.py               # 4 formulaires
    serializers.py          # 7 serializers
    views_api.py            # 2 ViewSets REST
    views_frontend.py       # 6 vues avec templates
    urls.py                 # Routage API + frontend
    admin.py                # Configuration Django Admin (avec inlines)
    migrations/
        0001_initial.py
    tests/
        __init__.py
        factories.py        # 3 factories
        test_forms.py       # Tests des formulaires
        test_models.py      # Tests des models
        test_views_api.py   # Tests API
        test_views_frontend.py
```

---

## Models

### HelpRequestCategory

Categories de demandes d'aide (donnees de reference).

| Champ | Type | Description |
|-------|------|-------------|
| `name` | `CharField(100)` | Nom en anglais |
| `name_fr` | `CharField(100)` | Nom en francais (optionnel) |
| `description` | `TextField` | Description de la categorie |
| `icon` | `CharField(50)` | Nom d'icone pour l'interface (ex: `'help-circle'`) |
| `order` | `PositiveIntegerField` | Ordre d'affichage (defaut: 0) |

**Categories typiques** : Priere, Financier, Materiel, Pastoral.

**Meta** : ordonne par `order` puis `name`, protege par `on_delete=PROTECT` (ne peut pas supprimer une categorie utilisee).

---

### HelpRequest

Demande d'aide soumise par un membre. C'est le model principal du module.

| Champ | Type | Description |
|-------|------|-------------|
| `request_number` | `CharField(20)` | Numero unique auto-genere (`HR-YYYYMM-XXXX`) |
| `member` | `ForeignKey(Member)` | Membre demandeur |
| `category` | `ForeignKey(HelpRequestCategory)` | Categorie de la demande |
| `title` | `CharField(200)` | Titre court |
| `description` | `TextField` | Description detaillee du besoin |
| `urgency` | `CharField(20)` | Niveau d'urgence (`HelpRequestUrgency.choices`) |
| `status` | `CharField(20)` | Statut de la demande (`HelpRequestStatus.choices`) |
| `assigned_to` | `ForeignKey(Member)` | Membre du personnel assigne (nullable) |
| `is_confidential` | `BooleanField` | Visible uniquement par pasteurs/admins (defaut: `False`) |
| `resolved_at` | `DateTimeField` | Date de resolution (nullable) |
| `resolution_notes` | `TextField` | Notes de resolution (optionnel) |

**Valeurs possibles pour `urgency`** :

| Constante | Valeur | Libelle FR |
|-----------|--------|------------|
| `HelpRequestUrgency.LOW` | `'low'` | Faible |
| `HelpRequestUrgency.MEDIUM` | `'medium'` | Moyenne |
| `HelpRequestUrgency.HIGH` | `'high'` | Elevee |
| `HelpRequestUrgency.URGENT` | `'urgent'` | Urgente |

**Valeurs possibles pour `status`** :

| Constante | Valeur | Libelle FR | Description |
|-----------|--------|------------|-------------|
| `HelpRequestStatus.NEW` | `'new'` | Nouvelle | Vient d'etre creee |
| `HelpRequestStatus.IN_PROGRESS` | `'in_progress'` | En cours | Assignee et en traitement |
| `HelpRequestStatus.RESOLVED` | `'resolved'` | Resolue | Terminee avec succes |
| `HelpRequestStatus.CLOSED` | `'closed'` | Fermee | Fermee (avec ou sans resolution) |

**Methodes metier** :

| Methode | Description |
|---------|-------------|
| `save()` | Genere automatiquement le `request_number` si absent |
| `mark_resolved(notes)` | Passe le statut a RESOLVED, enregistre la date et les notes |
| `assign_to(member)` | Assigne a un membre; auto-transition de NEW a IN_PROGRESS |

**Meta** : ordonne par `-created_at`.

---

### HelpRequestComment

Commentaire ou note interne sur une demande d'aide.

| Champ | Type | Description |
|-------|------|-------------|
| `help_request` | `ForeignKey(HelpRequest)` | Demande associee |
| `author` | `ForeignKey(Member)` | Auteur du commentaire |
| `content` | `TextField` | Contenu du commentaire |
| `is_internal` | `BooleanField` | Note interne (visible uniquement par le staff) |

**Meta** : ordonne par `created_at` (chronologique).

**Regle metier** : les commentaires marques `is_internal=True` ne sont jamais affiches aux membres reguliers, meme s'ils sont le demandeur. Seuls les pasteurs et administrateurs les voient.

---

## Formulaires

Quatre formulaires, tous utilisant `W3CRMFormMixin` pour le style :

### HelpRequestForm

Formulaire de creation d'une nouvelle demande.

| Champ | Widget | Label FR |
|-------|--------|----------|
| `category` | Select | Categorie |
| `title` | TextInput | Titre |
| `description` | Textarea (5 lignes) | Description |
| `urgency` | Select | Urgence |
| `is_confidential` | Checkbox | Confidentiel (visible uniquement par les pasteurs) |

### HelpRequestCommentForm

Ajout d'un commentaire sur une demande.

| Champ | Widget | Label FR |
|-------|--------|----------|
| `content` | Textarea (3 lignes) | Commentaire |
| `is_internal` | Checkbox | Note interne (visible uniquement par le staff) |

### HelpRequestAssignForm

Assignation d'une demande a un membre du personnel.

| Champ | Widget | Label FR |
|-------|--------|----------|
| `assigned_to` | Select (filtre: pasteurs + admins actifs) | Assigner a |

Le choix du select est construit dynamiquement a l'initialisation du formulaire :
```python
staff = Member.objects.filter(
    role__in=['pastor', 'admin'],
    is_active=True
).order_by('last_name', 'first_name')
```

### HelpRequestResolveForm

Resolution d'une demande avec notes optionnelles.

| Champ | Widget | Label FR |
|-------|--------|----------|
| `resolution_notes` | Textarea (3 lignes) | Notes de resolution |

---

## Serializers

| Serializer | Utilisation | Champs supplementaires (read-only) |
|------------|-------------|-------------------------------------|
| `HelpRequestCategorySerializer` | Categories (CRUD) | -- |
| `HelpRequestSerializer` | Detail complet d'une demande | `member_name`, `category_name`, `assigned_to_name`, `urgency_display`, `status_display`, `comments` (nested) |
| `HelpRequestCreateSerializer` | Creation (champs limites) | -- (assigne automatiquement le `member` depuis `request.user`) |
| `HelpRequestCommentSerializer` | Detail d'un commentaire | `author_name` |
| `HelpRequestAssignSerializer` | Action assign | -- (`assigned_to` UUID seulement) |
| `HelpRequestResolveSerializer` | Action resolve | -- (`resolution_notes` seulement) |
| `CommentCreateSerializer` | Action comment | -- (`content` + `is_internal`) |

---

## Endpoints API REST

Tous les endpoints sont prefixes par `/api/v1/help-requests/`.

### HelpRequestCategoryViewSet (ReadOnly)

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/help-requests/categories/` | Lister les categories actives | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/categories/{id}/` | Detail d'une categorie | `IsAuthenticated` |

### HelpRequestViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/help-requests/requests/` | Lister les demandes (filtrees par role) | `IsAuthenticated` |
| `POST` | `/api/v1/help-requests/requests/` | Creer une demande | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/requests/{id}/` | Detail d'une demande | `IsAuthenticated` (avec filtrage) |
| `PUT/PATCH` | `/api/v1/help-requests/requests/{id}/` | Modifier | `IsAuthenticated` |
| `DELETE` | `/api/v1/help-requests/requests/{id}/` | Supprimer | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/requests/my_requests/` | Mes demandes | `IsAuthenticated` |
| `POST` | `/api/v1/help-requests/requests/{id}/assign/` | Assigner a un membre staff | `IsPastor \| IsAdmin` |
| `POST` | `/api/v1/help-requests/requests/{id}/resolve/` | Marquer comme resolue | `IsPastor \| IsAdmin` |
| `POST` | `/api/v1/help-requests/requests/{id}/comment/` | Ajouter un commentaire | `IsAuthenticated` |
| `GET` | `/api/v1/help-requests/requests/{id}/comments/` | Lister les commentaires | `IsAuthenticated` |

**Filtres** : `status`, `urgency`, `category`, `assigned_to`, `is_confidential`
**Recherche** : `title`, `description`, `request_number`
**Tri** : `created_at`, `urgency`, `status`

**Logique de filtrage du queryset (scoping)** :

```
Pasteur/Admin     -> Toutes les demandes
Responsable       -> Ses propres demandes + celles de ses membres de groupe (non-confidentielles)
Membre regulier   -> Ses propres demandes seulement
```

**Regles pour les commentaires internes** : si un membre non-staff tente de creer un commentaire avec `is_internal=True`, le systeme force automatiquement `is_internal=False`. Les commentaires internes sont filtres dans l'action `comments` pour les non-staff.

---

## URLs frontend

| URL | Vue | Template | Description |
|-----|-----|----------|-------------|
| `/help-requests/` | `request_list` | `help_requests/request_list.html` | Liste de toutes les demandes (Pasteur/Admin) |
| `/help-requests/create/` | `request_create` | `help_requests/request_create.html` | Creer une nouvelle demande |
| `/help-requests/my-requests/` | `my_requests` | `help_requests/my_requests.html` | Mes demandes personnelles |
| `/help-requests/<uuid:pk>/` | `request_detail` | `help_requests/request_detail.html` | Detail avec commentaires + formulaires |
| `/help-requests/<uuid:pk>/update/` | `request_update` | -- (redirect) | Actions : assign, resolve, close |
| `/help-requests/<uuid:pk>/comment/` | `request_comment` | -- (redirect) | Ajouter un commentaire (POST) |

**Logique de la vue `request_list`** : filtres par `status`, `urgency`, et `category` via query parameters.

**Logique de la vue `request_detail`** : affiche le formulaire d'assignation et le formulaire de commentaire. Les commentaires internes sont masques pour les non-staff. La variable `can_manage` est passee au template pour le rendu conditionnel.

**Logique de la vue `request_update`** : gere trois actions via le champ POST `action` :
- `assign` : assigne la demande a un membre staff
- `resolve` : marque la demande comme resolue avec notes
- `close` : ferme la demande directement

---

## Templates

| Template | Description |
|----------|-------------|
| `help_requests/request_list.html` | Liste avec filtres (statut, urgence, categorie), colonnes : numero, titre, demandeur, categorie, urgence, statut, date |
| `help_requests/request_create.html` | Formulaire de creation avec selection de categorie |
| `help_requests/request_detail.html` | Detail complet avec section commentaires, formulaire d'assignation (si pasteur/admin), formulaire de commentaire |
| `help_requests/my_requests.html` | Liste des demandes du membre connecte avec statut et urgence |

---

## Administration Django

Trois classes d'administration avec configuration avancee :

| Admin Class | Caracteristiques |
|-------------|-----------------|
| `HelpRequestCategoryAdmin` | list_display, list_filter par is_active, search, ordering par order+name |
| `HelpRequestAdmin` | Fieldsets organises (info, statut, resolution, timestamps), HelpRequestCommentInline, raw_id_fields, readonly request_number/timestamps |
| `HelpRequestCommentAdmin` | list_filter par is_internal et created_at, raw_id_fields |

**Fieldsets de `HelpRequestAdmin`** :

| Section | Champs |
|---------|--------|
| (defaut) | request_number, member, category, title, description |
| Status | status, urgency, assigned_to, is_confidential |
| Resolution (collapse) | resolved_at, resolution_notes |
| Timestamps (collapse) | created_at, updated_at |

---

## Permissions

| Role | Creer | Voir les siennes | Voir celles du groupe | Voir toutes | Assigner | Resoudre/Fermer | Notes internes | Voir confidentielles |
|------|-------|-------------------|-----------------------|-------------|----------|-----------------|----------------|---------------------|
| **Membre** | Oui | Oui | Non | Non | Non | Non | Non | Non |
| **Responsable de groupe** | Oui | Oui | Oui (non-confid.) | Non | Non | Non | Non | Non |
| **Pasteur / Admin** | Oui | Oui | Oui | Oui | Oui | Oui | Oui (lecture + ecriture) | Oui |

---

## Exemples d'utilisation

### API : Creer une demande d'aide

```bash
curl -X POST /api/v1/help-requests/requests/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "<category-uuid>",
    "title": "Besoin de priere pour une situation familiale",
    "description": "Ma famille traverse une periode difficile...",
    "urgency": "medium",
    "is_confidential": true
  }'
```

**Reponse** (`201 Created`) :
```json
{
  "id": "...",
  "request_number": "HR-202602-0001",
  "member": "...",
  "member_name": "Marie Dupont",
  "category": "...",
  "category_name": "Prayer",
  "title": "Besoin de priere pour une situation familiale",
  "urgency": "medium",
  "urgency_display": "Moyenne",
  "status": "new",
  "status_display": "Nouvelle",
  "is_confidential": true,
  "assigned_to": null,
  "created_at": "2026-02-06T14:30:00Z"
}
```

### API : Assigner une demande (Pasteur/Admin)

```bash
curl -X POST /api/v1/help-requests/requests/<id>/assign/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"assigned_to": "<staff-member-uuid>"}'
```

Le statut passe automatiquement de `'new'` a `'in_progress'` lors de l'assignation.

### API : Resoudre une demande

```bash
curl -X POST /api/v1/help-requests/requests/<id>/resolve/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"resolution_notes": "Rencontre effectuee, priere en groupe realisee."}'
```

### API : Ajouter un commentaire avec note interne

```bash
curl -X POST /api/v1/help-requests/requests/<id>/comment/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Situation suivie de pres, prochaine rencontre mardi.",
    "is_internal": true
  }'
```

### API : Consulter mes demandes

```bash
curl -X GET /api/v1/help-requests/requests/my_requests/ \
  -H "Authorization: Bearer <token>"
```

### API : Filtrer les demandes ouvertes urgentes

```bash
curl -X GET "/api/v1/help-requests/requests/?status=new&urgency=urgent" \
  -H "Authorization: Bearer <token>"
```

---

## Tests

Les tests utilisent `pytest` avec `pytest-django` et `factory_boy`.

### Factories disponibles

| Factory | Model | Valeurs par defaut |
|---------|-------|--------------------|
| `HelpRequestCategoryFactory` | `HelpRequestCategory` | icon='help-circle', is_active=True |
| `HelpRequestFactory` | `HelpRequest` | urgency='medium', status='new', is_confidential=False |
| `HelpRequestCommentFactory` | `HelpRequestComment` | is_internal=False |

### Executer les tests

```bash
# Tous les tests du module
pytest apps/help_requests/ -v

# Tests des models (request_number, mark_resolved, assign_to)
pytest apps/help_requests/tests/test_models.py -v

# Tests des formulaires
pytest apps/help_requests/tests/test_forms.py -v

# Tests API (CRUD, permissions, actions custom)
pytest apps/help_requests/tests/test_views_api.py -v

# Tests frontend
pytest apps/help_requests/tests/test_views_frontend.py -v
```

---

## Workflow de traitement d'une demande

```
1. Membre soumet une demande
       |
       v
   [NEW] Nouvelle demande creee (HR-YYYYMM-XXXX)
       |
       v
2. Pasteur/Admin assigne la demande (assign_to)
       |
       v
   [IN_PROGRESS] En cours de traitement
       |
       |--- Commentaires (publics + internes)
       |
       v
3. Pasteur/Admin resout la demande (mark_resolved)
       |
       v
   [RESOLVED] Resolue (resolved_at, resolution_notes)
       |
       v
4. (Optionnel) Fermeture definitive
       |
       v
   [CLOSED] Fermee
```

---

## Dependances

| Dependance | Utilisation |
|------------|-------------|
| `apps.core.models.BaseModel` | Heritage des models (UUID, timestamps, is_active) |
| `apps.core.constants` | `HelpRequestUrgency`, `HelpRequestStatus` |
| `apps.core.permissions` | `IsPastor`, `IsAdmin` |
| `apps.core.mixins` | `W3CRMFormMixin`, `PastorRequiredMixin` |
| `apps.core.utils` | `generate_request_number()` |
| `apps.members.Member` | FK vers le membre demandeur et le personnel assigne |
| `apps.members.GroupMembership` | Pour le filtrage des demandes par groupe |
| `django-filter` | Filtrage des endpoints API |

---

## Recent Additions

No major model or view additions since initial README. The help requests app remains stable with the existing HelpRequestCategory, HelpRequest, and HelpRequestComment models.
