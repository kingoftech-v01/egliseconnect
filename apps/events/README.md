# Application Events (Evenements)

> Module de gestion des evenements pour EgliseConnect.

---

## Table des matieres

1. [Apercu general](#apercu-general)
2. [Apercu technique](#apercu-technique)
3. [Modeles (Models)](#modeles-models)
4. [Formulaires (Forms)](#formulaires-forms)
5. [Endpoints API](#endpoints-api)
6. [URLs Frontend](#urls-frontend)
7. [Templates](#templates)
8. [Exemples d'utilisation](#exemples-dutilisation)
9. [Tests](#tests)

---

## Apercu general

### Pour les utilisateurs non techniques

Ce module gere l'ensemble des evenements de l'eglise : cultes, reunions de groupes, repas communautaires, celebrations speciales et rassemblements en ligne. Voici ce qu'il offre :

- **Calendrier des evenements** : Les membres peuvent voir tous les evenements a venir dans une vue calendrier interactive (alimentee par FullCalendar.js).
- **Details des evenements** : Chaque evenement affiche le lieu, l'horaire, le type d'evenement, et s'il est en personne ou en ligne (avec le lien de connexion).
- **Systeme de RSVP** : Les membres peuvent confirmer leur presence, decliner ou indiquer "peut-etre". Ils peuvent aussi indiquer le nombre d'invites qu'ils amenent.
- **Gestion de la capacite** : Les organisateurs peuvent definir une capacite maximale. Une fois atteinte, l'evenement est automatiquement marque comme complet.
- **Types d'evenements** : Culte, groupe, repas, special, reunion -- chaque type peut etre filtre separement.

### Qui utilise ce module ?

| Role | Acces |
|------|-------|
| **Membre** | Consulter les evenements, voir le calendrier, soumettre un RSVP |
| **Responsable de groupe (Group Leader)** | Creer et modifier des evenements |
| **Pasteur / Admin** | Gestion complete des evenements (creation, modification, suppression, consultation des participants) |
| **Organisateur** | Voir la liste des participants confirmes pour ses evenements |

---

## Apercu technique

L'application `events` est construite avec Django et Django REST Framework (DRF). Elle suit l'architecture standard d'EgliseConnect :

- **Models** : 2 modeles Django (`Event`, `EventRSVP`)
- **Forms** : 2 formulaires utilisant le mixin `W3CRMFormMixin`
- **API** : 1 ViewSet DRF avec des actions personnalisees pour le calendrier, les evenements a venir, le RSVP et la liste des participants
- **Frontend** : 4 vues basees sur des templates Django
- **Permissions** : Controle d'acces base sur les roles (`IsMember`, `IsPastorOrAdmin`)

### Architecture des fichiers

```text
apps/events/
    __init__.py
    admin.py              # Configuration Django Admin
    apps.py               # AppConfig
    forms.py              # 2 formulaires Django
    models.py             # Event, EventRSVP
    serializers.py        # 3 serializers DRF
    urls.py               # Routage API + Frontend
    views_api.py          # ViewSet DRF
    views_frontend.py     # Vues Django classiques
    migrations/
        0001_initial.py
    tests/
        __init__.py
        factories.py      # Factory Boy factories
        test_views_api.py
        test_views_frontend.py
```

Les templates se trouvent dans le repertoire global `templates/events/` (et non dans le repertoire de l'application).

---

## Modeles (Models)

### Event

Evenement d'eglise avec support pour les evenements en ligne, la gestion de la capacite et le systeme de RSVP.

Le modele herite de `BaseModel` (qui fournit `id` UUID, `created_at`, `updated_at`, `is_active`).

| Champ | Type | Description |
|-------|------|-------------|
| `title` | `CharField(200)` | Titre de l'evenement. |
| `description` | `TextField` | Description detaillee (optionnel). |
| `event_type` | `CharField(20)` | Type d'evenement. Choix : `worship`, `group`, `meal`, `special`, `meeting`. |
| `start_datetime` | `DateTimeField` | Date et heure de debut. |
| `end_datetime` | `DateTimeField` | Date et heure de fin. |
| `all_day` | `BooleanField` | Indique si l'evenement dure toute la journee. Par defaut : `False`. |
| `location` | `CharField(255)` | Nom du lieu (optionnel). |
| `location_address` | `TextField` | Adresse complete du lieu (optionnel). |
| `is_online` | `BooleanField` | Indique si l'evenement est en ligne. Par defaut : `False`. |
| `online_link` | `URLField` | Lien de connexion pour les evenements en ligne (optionnel). |
| `organizer` | `ForeignKey(Member)` | Organisateur de l'evenement. `SET_NULL` a la suppression. |
| `max_attendees` | `PositiveIntegerField` | Capacite maximale (optionnel). `null` = illimite. |
| `requires_rsvp` | `BooleanField` | Indique si un RSVP est requis. Par defaut : `False`. |
| `image` | `ImageField` | Image de l'evenement. Upload vers `events/%Y/%m/`. |
| `is_published` | `BooleanField` | Indique si l'evenement est visible publiquement. Par defaut : `True`. |
| `is_cancelled` | `BooleanField` | Indique si l'evenement est annule. Par defaut : `False`. |
| `is_recurring` | `BooleanField` | Indique si l'evenement est recurrent. Par defaut : `False`. |
| `parent_event` | `ForeignKey(self)` | Reference a l'evenement parent pour les occurrences d'evenements recurrents. |

**Proprietes calculees :**

| Propriete | Type retourne | Description |
|-----------|---------------|-------------|
| `confirmed_count` | `int` | Nombre de RSVP avec le statut `confirmed`. |
| `is_full` | `bool` | `True` si le nombre de confirmations atteint ou depasse `max_attendees`. Toujours `False` si `max_attendees` est `null`. |

**Tri par defaut :** `start_datetime` (evenements les plus proches en premier).

---

### EventRSVP

Reponse RSVP d'un membre pour un evenement. Un seul RSVP par membre par evenement (contrainte `unique_together`).

| Champ | Type | Description |
|-------|------|-------------|
| `event` | `ForeignKey(Event)` | L'evenement concerne. Suppression en cascade. |
| `member` | `ForeignKey(Member)` | Le membre qui repond. Suppression en cascade. |
| `status` | `CharField(20)` | Statut du RSVP. Choix : `pending`, `confirmed`, `declined`, `maybe`. Par defaut : `pending`. |
| `guests` | `PositiveIntegerField` | Nombre d'invites supplementaires. Par defaut : `0`. |
| `notes` | `TextField` | Notes additionnelles (optionnel). |

**Contraintes :**

```python
unique_together = ['event', 'member']  # Un seul RSVP par membre par evenement
```

---

## Formulaires (Forms)

Tous les formulaires utilisent le mixin `W3CRMFormMixin` pour un style uniforme avec le theme W3.CSS / W3CRM d'EgliseConnect.

### 1. EventForm

Formulaire complet de creation et modification d'evenements.

| Champ | Widget | Notes |
|-------|--------|-------|
| `title` | `TextInput` | Titre de l'evenement. |
| `description` | `Textarea` (rows=3) | Description detaillee. |
| `event_type` | `Select` | Type : Culte, Groupe, Repas, Special, Reunion. |
| `start_datetime` | `DateTimeInput` (type=datetime-local) | Date et heure de debut. |
| `end_datetime` | `DateTimeInput` (type=datetime-local) | Date et heure de fin. |
| `all_day` | `CheckboxInput` | Evenement toute la journee. |
| `location` | `TextInput` | Nom du lieu. |
| `location_address` | `Textarea` | Adresse complete. |
| `is_online` | `CheckboxInput` | Evenement en ligne. |
| `online_link` | `URLInput` | Lien de connexion. |
| `organizer` | `Select` | Membre organisateur. |
| `max_attendees` | `NumberInput` | Capacite maximale. |
| `requires_rsvp` | `CheckboxInput` | RSVP requis. |
| `image` | `FileInput` | Image de l'evenement. |
| `is_published` | `CheckboxInput` | Publier l'evenement. |

### 2. RSVPForm

Formulaire de soumission de RSVP pour les membres.

| Champ | Widget | Notes |
|-------|--------|-------|
| `status` | `Select` | Statut : En attente, Confirme, Decline, Peut-etre. |
| `guests` | `NumberInput` | Nombre d'invites supplementaires. |
| `notes` | `Textarea` | Notes ou commentaires. |

---

## Endpoints API

Tous les endpoints sont prefixes par `/api/v1/events/`. L'authentification est requise pour tous les endpoints.

### Evenements (Events)

| Methode | URL | Description | Permission |
|---------|-----|-------------|------------|
| `GET` | `/api/v1/events/events/` | Lister les evenements | Membre authentifie |
| `POST` | `/api/v1/events/events/` | Creer un evenement | Pasteur ou Admin |
| `GET` | `/api/v1/events/events/{uuid}/` | Detail d'un evenement | Membre authentifie |
| `PUT/PATCH` | `/api/v1/events/events/{uuid}/` | Modifier un evenement | Pasteur ou Admin |
| `DELETE` | `/api/v1/events/events/{uuid}/` | Supprimer un evenement | Pasteur ou Admin |
| `GET` | `/api/v1/events/events/upcoming/` | 10 prochains evenements | Membre authentifie |
| `GET` | `/api/v1/events/events/calendar/` | Evenements pour le calendrier | Membre authentifie |
| `POST` | `/api/v1/events/events/{uuid}/rsvp/` | Soumettre / mettre a jour un RSVP | Membre authentifie |
| `GET` | `/api/v1/events/events/{uuid}/attendees/` | Liste des participants confirmes | Organisateur ou Staff |

**Filtres disponibles :** `event_type`, `is_published`, `is_cancelled`
**Recherche :** `title`, `description`, `location`
**Tri :** `start_datetime`, `title` (par defaut : `start_datetime`)

### Parametres du endpoint `/calendar/`

| Parametre | Type | Description |
|-----------|------|-------------|
| `start` | `date` (ISO 8601) | Date de debut de la plage (optionnel) |
| `end` | `date` (ISO 8601) | Date de fin de la plage (optionnel) |

Ce endpoint est concu pour etre utilise avec FullCalendar.js, qui envoie automatiquement les parametres `start` et `end` lors du chargement des evenements.

### Serializers

L'application utilise 3 serializers :

| Serializer | Utilisation |
|------------|-------------|
| `EventListSerializer` | Liste legere des evenements (action `list`, `upcoming`, `calendar`) |
| `EventSerializer` | Detail complet d'un evenement avec proprietes calculees (`confirmed_count`, `is_full`) |
| `EventRSVPSerializer` | RSVP avec nom du membre et libelle du statut |

---

## URLs Frontend

Toutes les URLs sont prefixees par `/events/` et necessitent une connexion.

| URL | Nom de la vue | Template | Description |
|-----|---------------|----------|-------------|
| `/events/` | `event_list` | `event_list.html` | Liste paginee des evenements avec filtres par type et periode |
| `/events/calendar/` | `event_calendar` | `event_calendar.html` | Vue calendrier interactive (FullCalendar.js, donnees chargees via API) |
| `/events/{uuid}/` | `event_detail` | `event_detail.html` | Detail d'un evenement avec statut RSVP de l'utilisateur et liste des participants |
| `/events/{uuid}/rsvp/` | `event_rsvp` | *(redirect)* | Traitement du formulaire RSVP, redirige vers le detail de l'evenement |

---

## Templates

Les templates sont situes dans le repertoire global `templates/events/` du projet.

| Template | Description |
|----------|-------------|
| `event_list.html` | Liste paginee des evenements publies et non annules. Supporte le filtrage par type (`?type=worship`) et les evenements a venir (`?upcoming=1`). Pagination par 20 evenements. |
| `event_detail.html` | Affichage complet de l'evenement : titre, description, type, horaire, lieu/lien en ligne, organisateur, capacite, statut RSVP du membre connecte, et les 10 premiers participants confirmes. |
| `event_calendar.html` | Page du calendrier interactif utilisant **FullCalendar.js**. Le template charge la bibliotheque JavaScript et les donnees sont recuperees dynamiquement via l'endpoint API `/api/v1/events/events/calendar/`. |

### Integration FullCalendar.js

Le template `event_calendar.html` integre FullCalendar.js pour offrir une vue calendrier riche et interactive. Les donnees sont chargees via l'API REST :

```javascript
// Configuration typique de FullCalendar dans event_calendar.html
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'fr-ca',
        events: {
            url: '/api/v1/events/events/calendar/',
            extraParams: function() {
                return {
                    // FullCalendar envoie automatiquement start et end
                };
            }
        },
        eventClick: function(info) {
            // Redirection vers le detail de l'evenement
            window.location.href = '/events/' + info.event.id + '/';
        }
    });
    calendar.render();
});
```

---

## Exemples d'utilisation

### Creer un evenement (Python)

```python
from datetime import datetime
from django.utils import timezone
from apps.events.models import Event
from apps.core.constants import EventType

event = Event.objects.create(
    title="Culte du dimanche",
    description="Culte de louange et predication.",
    event_type=EventType.WORSHIP,
    start_datetime=timezone.make_aware(datetime(2026, 2, 8, 10, 0)),
    end_datetime=timezone.make_aware(datetime(2026, 2, 8, 12, 0)),
    location="Sanctuaire principal",
    location_address="123 rue de l'Eglise, Montreal, QC",
    max_attendees=200,
    requires_rsvp=True,
    is_published=True,
)
```

### Creer un evenement en ligne (Python)

```python
event = Event.objects.create(
    title="Etude biblique en ligne",
    event_type=EventType.GROUP,
    start_datetime=timezone.make_aware(datetime(2026, 2, 10, 19, 0)),
    end_datetime=timezone.make_aware(datetime(2026, 2, 10, 20, 30)),
    is_online=True,
    online_link="https://zoom.us/j/123456789",
    organizer=responsable_groupe,
    is_published=True,
)
```

### Soumettre un RSVP (Python)

```python
from apps.events.models import EventRSVP
from apps.core.constants import RSVPStatus

# Creer ou mettre a jour le RSVP
rsvp, created = EventRSVP.objects.update_or_create(
    event=event,
    member=membre,
    defaults={
        'status': RSVPStatus.CONFIRMED,
        'guests': 2,
        'notes': "J'amene ma famille."
    }
)
```

### Creer un evenement via l'API REST

```bash
curl -X POST /api/v1/events/events/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Repas communautaire",
    "description": "Repas partage apres le culte.",
    "event_type": "meal",
    "start_datetime": "2026-02-15T12:00:00",
    "end_datetime": "2026-02-15T14:00:00",
    "location": "Salle paroissiale",
    "max_attendees": 50,
    "requires_rsvp": true,
    "is_published": true
  }'
```

### Soumettre un RSVP via l'API REST

```bash
curl -X POST /api/v1/events/events/{uuid}/rsvp/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "confirmed",
    "guests": 2
  }'
```

### Recuperer les evenements a venir

```bash
curl /api/v1/events/events/upcoming/ \
  -H "Authorization: Bearer <token>"

# Reponse : liste des 10 prochains evenements publies et non annules
```

### Recuperer les evenements pour le calendrier

```bash
# Evenements du mois de fevrier 2026
curl "/api/v1/events/events/calendar/?start=2026-02-01&end=2026-02-28" \
  -H "Authorization: Bearer <token>"
```

### Verifier la capacite d'un evenement

```python
event = Event.objects.get(title="Repas communautaire")
print(f"Confirmes : {event.confirmed_count} / {event.max_attendees}")
print(f"Complet : {event.is_full}")
```

### Lister les participants confirmes

```bash
curl /api/v1/events/events/{uuid}/attendees/ \
  -H "Authorization: Bearer <token>"

# Reponse : liste des RSVP confirmes avec nom du membre et nombre d'invites
```

---

## Tests

L'application dispose de modules de tests couvrant les vues API et les vues frontend.

### Executer les tests

```bash
# Tous les tests de l'application events
pytest apps/events/ -v

# Tests par categorie
pytest apps/events/tests/test_views_api.py -v
pytest apps/events/tests/test_views_frontend.py -v
```

### Structure des tests

| Fichier | Couverture |
|---------|------------|
| `tests/factories.py` | Factories Factory Boy pour `Event` et `EventRSVP` |
| `tests/test_views_api.py` | Permissions par role, CRUD des evenements, endpoints custom (`upcoming`, `calendar`, `rsvp`, `attendees`), filtrage et recherche |
| `tests/test_views_frontend.py` | Acces aux pages, affichage des evenements, soumission de RSVP, pagination, filtres |

### Exemple de test

```python
import pytest
from django.utils import timezone
from apps.events.tests.factories import EventFactory, EventRSVPFactory
from apps.core.constants import RSVPStatus

@pytest.mark.django_db
def test_event_confirmed_count():
    """Le compteur de confirmations est calcule correctement."""
    event = EventFactory(max_attendees=10)
    EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
    EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
    EventRSVPFactory(event=event, status=RSVPStatus.DECLINED)
    assert event.confirmed_count == 2
    assert not event.is_full

@pytest.mark.django_db
def test_event_is_full():
    """L'evenement est marque complet quand la capacite est atteinte."""
    event = EventFactory(max_attendees=2)
    EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
    EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
    assert event.is_full

@pytest.mark.django_db
def test_rsvp_unique_per_member():
    """Un seul RSVP par membre par evenement (update_or_create)."""
    event = EventFactory()
    rsvp1, created1 = EventRSVP.objects.update_or_create(
        event=event,
        member=member,
        defaults={'status': RSVPStatus.CONFIRMED}
    )
    assert created1 is True

    rsvp2, created2 = EventRSVP.objects.update_or_create(
        event=event,
        member=member,
        defaults={'status': RSVPStatus.DECLINED}
    )
    assert created2 is False
    assert rsvp1.pk == rsvp2.pk
```

---

## Recent Additions

### EventForm
New form in `apps/events/forms.py` using W3CRMFormMixin:
- Fields: `title`, `description`, `event_type`, `start_datetime`, `end_datetime`, `all_day`, `location`, `location_address`, `is_online`, `online_link`, `organizer`, `max_attendees`, `requires_rsvp`, `image`, `is_published`
- DateTimeInput widgets for datetime fields

### RSVPForm
- Fields: `status`, `guests`, `notes`

### New Frontend Views
- `event_create` — `/events/create/` — Create new event (admin/pastor)
- `event_update` — `/events/<pk>/edit/` — Edit existing event (admin/pastor)
- `event_delete` — `/events/<pk>/delete/` — Delete event with confirmation (admin/pastor)

### New Templates
- `event_form.html` — Create/update event form (shared for create and edit)
- `event_delete.html` — Delete event confirmation page
