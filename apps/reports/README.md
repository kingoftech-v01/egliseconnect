# Module Reports (Rapports et Tableau de bord)

> **Application Django** : `apps.reports`
> **Chemin** : `apps/reports/`

---

## Vue d'ensemble

### Pour les non-techniques

Ce module fournit a la direction de l'eglise une vue d'ensemble de toutes les activites. Il comprend :

- **Tableau de bord principal** : affiche les statistiques cles en un coup d'oeil -- nombre total de membres, dons recents, evenements a venir, activite des benevoles, demandes d'aide ouvertes et prochains anniversaires.
- **Rapport des membres** : ventilation par role, nouveaux membres ce mois-ci et cette annee, membres actifs vs inactifs.
- **Rapport des dons** : analyse mensuelle et annuelle des dons, ventilation par type et methode de paiement, donateurs les plus genereux (anonymises par rang), suivi des campagnes.
- **Rapport de presence** : suivi des RSVP par evenement, taux de confirmation, nombre d'invites.
- **Rapport des benevoles** : quarts completes vs absences, repartition par poste, top 10 des benevoles les plus actifs.
- **Calendrier des anniversaires** : permet a la communaute de celebrer ensemble les anniversaires a venir.

Ce module est **en lecture seule** -- il ne cree aucune donnee, il agrege les informations des autres modules pour les presenter sous forme de tableaux et graphiques.

### Pour les techniques

L'application ne contient aucun model Django. Elle utilise deux services (`DashboardService` et `ReportService`) qui effectuent des queries d'aggregation (`Count`, `Sum`, `Avg`, `TruncMonth`, etc.) sur les models des autres applications. Les resultats sont serialises avec des serializers non-model (`Serializer`) plutot que `ModelSerializer`. Le frontend utilise Chart.js, ApexCharts et DataTables pour le rendu des graphiques et tableaux. Les ViewSets sont de type `viewsets.ViewSet` (sans model) et les permissions sont granulaires par role.

---

## Architecture des fichiers

```
apps/reports/
    __init__.py
    apps.py
    services.py            # DashboardService + ReportService
    serializers.py          # 9 serializers (non-model)
    views_api.py            # 2 ViewSets + 1 APIView
    views_frontend.py       # 6 vues avec templates
    urls.py                 # Routage API + frontend
    migrations/
        __init__.py         # Pas de migrations (pas de models)
    tests/
        __init__.py
        test_services.py    # Tests des services d'aggregation
        test_views_api.py   # Tests API
        test_views_frontend.py
```

---

## Services

### DashboardService

Service statique qui agrege les statistiques de chaque module pour le tableau de bord.

| Methode | Description | Donnees retournees |
|---------|-------------|---------------------|
| `get_member_stats()` | Statistiques des membres | total, active, inactive, new_this_month, new_this_year, role_breakdown |
| `get_donation_stats(year)` | Statistiques des dons | total_amount, total_count, average_amount, monthly_breakdown, by_type, by_payment_method |
| `get_event_stats(year)` | Statistiques des evenements | total_events, upcoming, cancelled, by_type, total_rsvps, confirmed_rsvps |
| `get_volunteer_stats()` | Statistiques des benevoles | total_positions, volunteers_by_position, upcoming_schedules, confirmed/pending_this_month |
| `get_help_request_stats()` | Statistiques des demandes d'aide | total, open, resolved_this_month, by_urgency, by_category |
| `get_upcoming_birthdays(days)` | Anniversaires a venir | Liste de {member_id, member_name, birthday, age} |
| `get_dashboard_summary()` | Agregation complete | Combine toutes les methodes ci-dessus + generated_at |

**Exemple de retour de `get_member_stats()`** :
```python
{
    'total': 150,
    'active': 142,
    'inactive': 8,
    'new_this_month': 3,
    'new_this_year': 12,
    'role_breakdown': [
        {'role': 'member', 'count': 120},
        {'role': 'group_leader', 'count': 15},
        {'role': 'pastor', 'count': 5},
        {'role': 'admin', 'count': 2},
    ]
}
```

### ReportService

Service statique qui genere des rapports detailles avec filtres de dates.

| Methode | Parametres | Description |
|---------|------------|-------------|
| `get_attendance_report(start_date, end_date)` | Dates optionnelles (defaut: 90 derniers jours) | RSVP par evenement : confirmed, declined, total_guests |
| `get_donation_report(year)` | Annee (obligatoire) | Ventilation mensuelle, top donateurs (anonymises par rang), campagnes |
| `get_volunteer_report(start_date, end_date)` | Dates optionnelles (defaut: 30 derniers jours) | Quarts par poste, completed vs no_show, top 10 benevoles |

**Exemple de retour de `get_donation_report(2026)`** :
```python
{
    'year': 2026,
    'total': Decimal('45000.00'),
    'total_count': 312,
    'unique_donors': 89,
    'monthly': [
        {'month': 1, 'total': Decimal('5200.00'), 'count': 35},
        {'month': 2, 'total': Decimal('4800.00'), 'count': 28},
        # ... 12 mois
    ],
    'top_donors': [
        {'rank': 1, 'total': Decimal('3500.00')},
        {'rank': 2, 'total': Decimal('2800.00')},
        # ... jusqu'a 10
    ],
    'campaigns': [
        {'campaign__name': 'Construction', 'total': Decimal('12000.00'), 'count': 45},
    ]
}
```

**Note importante** : les top donateurs sont anonymises -- seul le rang et le montant sont retournes, pas le nom du membre. Ceci protege la confidentialite des dons.

---

## Serializers

Serializers non-model (`serializers.Serializer`) pour valider et formater les donnees des services :

| Serializer | Champs |
|------------|--------|
| `MemberStatsSerializer` | total, active, inactive, new_this_month, new_this_year, role_breakdown |
| `DonationStatsSerializer` | year, total_amount, total_count, average_amount, monthly_breakdown, by_type, by_payment_method |
| `EventStatsSerializer` | year, total_events, upcoming, cancelled, by_type, total_rsvps, confirmed_rsvps |
| `VolunteerStatsSerializer` | total_positions, volunteers_by_position, upcoming_schedules, confirmed/pending_this_month |
| `HelpRequestStatsSerializer` | total, open, resolved_this_month, by_urgency, by_category |
| `BirthdaySerializer` | member_id (UUID), member_name, birthday (Date), age (nullable) |
| `DashboardSummarySerializer` | members, donations, events, volunteers, help_requests, upcoming_birthdays, generated_at |
| `AttendanceReportSerializer` | start_date, end_date, total_events, events (list) |
| `DonationReportSerializer` | year, total, total_count, unique_donors, monthly, top_donors, campaigns |
| `VolunteerReportSerializer` | start_date, end_date, total_shifts, completed, no_shows, by_position, top_volunteers |

---

## Endpoints API REST

Tous les endpoints sont prefixes par `/api/v1/reports/`.

### DashboardViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/reports/dashboard/` | Tableau de bord complet | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/members/` | Statistiques des membres | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/donations/` | Statistiques des dons | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/events/` | Statistiques des evenements | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/volunteers/` | Statistiques des benevoles | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/help_requests/` | Statistiques des demandes d'aide | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/dashboard/birthdays/` | Anniversaires a venir | `IsPastor \| IsAdmin` |

**Parametres de query pour `donations` et `events`** : `?year=2026` (optionnel, defaut: annee en cours)

**Parametre de query pour `birthdays`** : `?days=7` (nombre de jours a venir, defaut: 7)

### ReportViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/reports/reports/attendance/` | Rapport de presence | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/reports/donations/{year}/` | Rapport annuel des dons | `IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/reports/volunteers/` | Rapport des benevoles | `IsPastor \| IsAdmin` |

**Parametres de query pour `attendance` et `volunteers`** :
- `?start_date=2026-01-01` (format ISO, optionnel)
- `?end_date=2026-02-06` (format ISO, optionnel)

### TreasurerDonationReportView (APIView)

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/reports/treasurer/donations/` | Rapport des dons (annee en cours) | `IsTreasurer \| IsPastor \| IsAdmin` |
| `GET` | `/api/v1/reports/treasurer/donations/{year}/` | Rapport des dons (annee specifique) | `IsTreasurer \| IsPastor \| IsAdmin` |

Cet endpoint permet aux tresoriers d'acceder aux rapports de dons sans avoir acces complet au tableau de bord administratif.

---

## URLs frontend

| URL | Vue | Template | Description |
|-----|-----|----------|-------------|
| `/reports/` | `dashboard` | `reports/dashboard.html` | Tableau de bord principal |
| `/reports/members/` | `member_stats` | `reports/member_stats.html` | Statistiques des membres |
| `/reports/donations/` | `donation_report` | `reports/donation_report.html` | Rapport des dons (avec selecteur d'annee) |
| `/reports/attendance/` | `attendance_report` | `reports/attendance_report.html` | Rapport de presence |
| `/reports/volunteers/` | `volunteer_report` | `reports/volunteer_report.html` | Rapport des benevoles |
| `/reports/birthdays/` | `birthday_report` | `reports/birthday_report.html` | Calendrier des anniversaires |

**Note** : la page d'accueil de l'application (`/`) redirige vers `/reports/` pour les utilisateurs autorises.

**Logique de la vue `donation_report`** : combine les donnees de `ReportService.get_donation_report()` et `DashboardService.get_donation_stats()`. Propose un selecteur d'annee couvrant les 5 dernieres annees.

**Logique de la vue `birthday_report`** : parametre `?days=30` (defaut: 30 jours). Accessible a tous les membres authentifies.

---

## Templates

| Template | Description | Librairies JS |
|----------|-------------|---------------|
| `reports/dashboard.html` | Tableau de bord avec cartes de statistiques et graphiques | Chart.js, ApexCharts, DataTables |
| `reports/member_stats.html` | Ventilation des membres par role, nouveaux membres, tendances | Chart.js |
| `reports/donation_report.html` | Graphique mensuel, ventilation par type et methode, selecteur d'annee | Chart.js, ApexCharts |
| `reports/attendance_report.html` | Tableau des evenements avec RSVP, taux de confirmation | DataTables |
| `reports/volunteer_report.html` | Repartition par poste, taux de completion, top benevoles | Chart.js |
| `reports/birthday_report.html` | Liste des anniversaires a venir avec age | -- |

---

## Permissions

| Role | Tableau de bord | Stats membres | Rapport dons | Rapport presence | Rapport benevoles | Anniversaires |
|------|----------------|---------------|--------------|------------------|-------------------|---------------|
| **Membre** | Non | Non | Non | Non | Non | Oui |
| **Responsable de groupe** | Non | Non | Non | Non | Non | Oui |
| **Tresorier** | Oui (frontend) | Non | Oui | Non | Non | Oui |
| **Pasteur** | Oui | Oui | Oui | Oui | Oui | Oui |
| **Admin** | Oui | Oui | Oui | Oui | Oui | Oui |

**Note sur l'API** : les endpoints du `DashboardViewSet` et `ReportViewSet` exigent `IsPastor | IsAdmin`. Le `TreasurerDonationReportView` ajoute `IsTreasurer` comme permission supplementaire.

**Note sur le frontend** : la vue `dashboard` accepte egalement le role `'treasurer'`. La vue `birthday_report` est accessible a tout membre authentifie.

---

## Exemples d'utilisation

### API : Obtenir le tableau de bord complet

```bash
curl -X GET /api/v1/reports/dashboard/ \
  -H "Authorization: Bearer <token>"
```

**Reponse** (`200 OK`) :
```json
{
  "members": {
    "total": 150,
    "active": 142,
    "inactive": 8,
    "new_this_month": 3,
    "new_this_year": 12,
    "role_breakdown": [
      {"role": "member", "count": 120}
    ]
  },
  "donations": {
    "year": 2026,
    "total_amount": "45000.00",
    "total_count": 312,
    "average_amount": "144.23",
    "monthly_breakdown": [...],
    "by_type": [...],
    "by_payment_method": [...]
  },
  "events": {
    "year": 2026,
    "total_events": 24,
    "upcoming": 8,
    "cancelled": 1
  },
  "volunteers": {
    "total_positions": 12,
    "upcoming_schedules": 35,
    "confirmed_this_month": 28,
    "pending_this_month": 7
  },
  "help_requests": {
    "total": 45,
    "open": 5,
    "resolved_this_month": 3
  },
  "upcoming_birthdays": [
    {
      "member_id": "...",
      "member_name": "Sophie Bergeron",
      "birthday": "2026-02-10",
      "age": 35
    }
  ],
  "generated_at": "2026-02-06T15:00:00Z"
}
```

### API : Rapport des dons pour une annee specifique

```bash
curl -X GET /api/v1/reports/reports/donations/2025/ \
  -H "Authorization: Bearer <token>"
```

### API : Rapport de presence avec dates personnalisees

```bash
curl -X GET "/api/v1/reports/reports/attendance/?start_date=2026-01-01&end_date=2026-02-06" \
  -H "Authorization: Bearer <token>"
```

### API : Rapport des benevoles (30 derniers jours)

```bash
curl -X GET /api/v1/reports/reports/volunteers/ \
  -H "Authorization: Bearer <token>"
```

**Reponse** :
```json
{
  "start_date": "2026-01-07",
  "end_date": "2026-02-06",
  "total_shifts": 120,
  "completed": 105,
  "no_shows": 8,
  "by_position": [
    {
      "position__name": "Accueil",
      "total": 40,
      "completed": 38,
      "no_show": 1
    }
  ],
  "top_volunteers": [
    {"member__first_name": "Jean", "member__last_name": "Tremblay", "count": 8}
  ]
}
```

### API : Rapport des dons pour le tresorier

```bash
curl -X GET /api/v1/reports/treasurer/donations/2026/ \
  -H "Authorization: Bearer <token>"
```

### API : Anniversaires des 14 prochains jours

```bash
curl -X GET "/api/v1/reports/dashboard/birthdays/?days=14" \
  -H "Authorization: Bearer <token>"
```

### API : Statistiques des dons pour une annee specifique

```bash
curl -X GET "/api/v1/reports/dashboard/donations/?year=2025" \
  -H "Authorization: Bearer <token>"
```

---

## Tests

Les tests utilisent `pytest` avec `pytest-django` et `factory_boy`.

### Executer les tests

```bash
# Tous les tests du module reports
pytest apps/reports/ -v

# Tests des services (logique d'aggregation)
pytest apps/reports/tests/test_services.py -v

# Tests API (permissions, endpoints)
pytest apps/reports/tests/test_views_api.py -v

# Tests frontend
pytest apps/reports/tests/test_views_frontend.py -v
```

### Couverture des tests de services

Les tests couvrent les scenarios suivants :

- **DashboardService** :
  - `get_member_stats()` : total, actifs, inactifs
  - `get_donation_stats()` : total, montant, compte
  - `get_event_stats()` : total, annules
  - `get_volunteer_stats()` : nombre de postes
  - `get_help_request_stats()` : total, ouverts (new + in_progress)
  - `get_dashboard_summary()` : verification de la structure complete

- **ReportService** :
  - `get_attendance_report()` : evenements avec RSVP
  - `get_donation_report()` : montant total, compte, 12 mois
  - `get_volunteer_report()` : quarts completes, absences

### Factories utilisees (d'autres modules)

Les tests du module reports utilisent les factories des autres modules pour generer les donnees d'aggregation :

| Factory | Module source |
|---------|--------------|
| `MemberFactory` | `apps.members` |
| `DonationFactory` | `apps.donations` |
| `EventFactory`, `EventRSVPFactory` | `apps.events` |
| `VolunteerPositionFactory`, `VolunteerScheduleFactory` | `apps.volunteers` |
| `HelpRequestFactory` | `apps.help_requests` |

---

## Dependances

| Dependance | Utilisation |
|------------|-------------|
| `apps.core.permissions` | `IsPastor`, `IsAdmin`, `IsTreasurer` |
| `apps.core.utils` | `get_upcoming_birthdays()` |
| `apps.members.models` | Queries d'aggregation sur `Member` |
| `apps.donations.models` | Queries d'aggregation sur `Donation` |
| `apps.events.models` | Queries d'aggregation sur `Event`, `EventRSVP` |
| `apps.volunteers.models` | Queries d'aggregation sur `VolunteerPosition`, `VolunteerSchedule`, `VolunteerAvailability` |
| `apps.help_requests.models` | Queries d'aggregation sur `HelpRequest` |
| Chart.js | Graphiques (frontend) |
| ApexCharts | Graphiques avances (frontend) |
| DataTables | Tableaux interactifs (frontend) |

---

## Notes techniques

### Performance

Les services effectuent des queries d'aggregation directement en base de donnees (via les ORM `annotate`, `aggregate`, `values`), ce qui est performant meme avec de grands volumes de donnees. Le `get_dashboard_summary()` execute cependant plusieurs queries en serie -- si la performance devient un enjeu, un systeme de cache (Redis) ou de pre-calcul pourrait etre envisage.

### Confidentialite des dons

Les rapports de dons affichent les top donateurs par **rang uniquement** (1er, 2eme, 3eme...) sans reveler l'identite du membre. Ceci respecte la confidentialite des dons tout en fournissant des metriques utiles a la direction.

### Module en lecture seule

Ce module ne possede aucun model propre et n'effectue aucune ecriture en base de donnees. Il est purement oriente lecture et aggregation. Toutes les donnees proviennent des autres modules de l'application.

---

## Recent Additions

### New Frontend Views

- **`attendance_report`** — `/reports/attendance/` — Attendance analytics with date range filtering. Uses `ReportService.get_attendance_report()` and `DashboardService.get_event_stats()`. Requires pastor/admin.
- **`volunteer_report`** — `/reports/volunteers/` — Volunteer activity report with date range filtering. Uses `ReportService.get_volunteer_report()` and `DashboardService.get_volunteer_stats()`. Requires pastor/admin.

### New Templates

- `attendance_report.html` — Attendance analytics dashboard
- `volunteer_report.html` — Volunteer activity report
