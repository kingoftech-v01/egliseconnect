# EgliseConnect - Church Management System

## Vue d'ensemble

EgliseConnect est un systeme de gestion d'eglise complet developpe en Django 5.2, concu pour les eglises francophones canadiennes. Le systeme couvre la gestion des membres, les dons, les evenements, le benevolat, la communication, l'aide mutuelle, les rapports, l'integration, la presence, les paiements et la planification du culte.

## Architecture actuelle

- **Backend**: Django 5.2 + Django REST Framework
- **Frontend actuel**: Templates Django + W3CRM (DexignZone) Bootstrap 5
- **Base de donnees**: SQLite (dev) / PostgreSQL 16 (prod)
- **Taches async**: Celery + Redis
- **Temps reel**: Django Channels (WebSocket)
- **Auth**: django-allauth (email, Google OAuth, TOTP 2FA)
- **Paiements**: Stripe, Coinbase Commerce
- **SMS**: Twilio
- **Push**: VAPID Web Push
- **PWA**: Service Worker + manifest.json

## Architecture cible (v2)

Migration vers une architecture decouplee:

- **Backend**: Django 5.2 (API-only) + JWT auth
- **Frontend Web**: Next.js 14+ (React)
- **Frontend Mobile**: React Native (Expo)
- **Monorepo**: Turborepo avec packages partages

Voir [ARCHITECTURE.md](./ARCHITECTURE.md) pour les details complets.

## Applications (12 apps)

| App | Description | Modeles | Endpoints API |
|-----|-------------|---------|---------------|
| **core** | Infrastructure partagee, permissions, audit | 5 | 3 |
| **members** | Gestion des membres, groupes, familles, departements | 19 | 4 ViewSets |
| **donations** | Dons, campagnes, recus fiscaux, pledges | 12 | 10 ViewSets |
| **events** | Evenements, RSVP, salles, sondages | 13 | 7 ViewSets |
| **volunteers** | Planification, quarts, heures, competences | 16 | 4 ViewSets |
| **communication** | Newsletters, SMS, push, automations, chat | 16 | 15 ViewSets |
| **help_requests** | Demandes d'aide, priere, equipes de soin | 13 | 13 ViewSets |
| **reports** | Tableaux de bord, rapports planifies | 2 | 4 ViewSets |
| **onboarding** | Parcours d'integration, formation, mentors | 22 | 20+ ViewSets |
| **attendance** | QR check-in, kiosque, enfants, NFC, geo | 10 | 12 ViewSets |
| **payments** | Stripe, recurrents, kiosque, crypto | 10 | 9 ViewSets |
| **worship** | Services, sermons, chants, setlists, livestream | 15 | 13 ViewSets |

**Total**: ~153 modeles, ~114 ViewSets API, ~300+ templates, 1141 tests

## Stack technique

### Backend (Python)
```
Django 5.2           - Framework web
DRF 3.14+            - API REST
django-allauth       - Auth (email, Google, 2FA TOTP)
django-filter        - Filtrage API
drf-spectacular      - Documentation OpenAPI
celery + redis       - Taches asynchrones
django-celery-beat   - Taches periodiques
channels + daphne    - WebSocket temps reel
stripe               - Paiements en ligne
twilio               - SMS
pywebpush            - Notifications push
xhtml2pdf            - Generation PDF
openpyxl             - Export Excel
icalendar            - Export iCal
django-waffle        - Feature flags
django-oauth-toolkit - OAuth2 (futur)
coinbase-commerce    - Crypto donations
bleach               - Sanitization HTML
qrcode               - Generation QR
```

### Frontend actuel
```
Bootstrap 5          - Framework CSS
jQuery               - Manipulation DOM
MetisMenu            - Navigation sidebar
DataTables           - Tableaux interactifs
FullCalendar         - Calendrier
Chart.js + ApexCharts - Graphiques
html5-qrcode         - Scanner QR
CKEditor             - Editeur rich text
```

### Frontend cible (v2)
```
Next.js 14+          - Framework React SSR
React Native (Expo)  - Mobile iOS/Android
TypeScript           - Typage statique
TanStack Query       - Gestion cache/data
Zustand              - State management
Tailwind CSS         - Styling (web)
NativeWind           - Styling (mobile)
Turborepo            - Monorepo workspace
```

## Demarrage rapide

### Prerequisites
- Python 3.12+
- Node.js 20+ (pour v2)
- Redis (pour Celery)

### Installation
```bash
# Cloner le repo
git clone <repo-url>
cd egliseconnect

# Environnement Python
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
# Editer .env avec vos cles

# Base de donnees
python manage.py migrate
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver 8080
```

### Production (Docker)
```bash
docker-compose up -d
```

Services: PostgreSQL 16, Redis 7, Gunicorn, Nginx, Celery Worker, Celery Beat

## Structure du projet

```
egliseconnect/
├── config/                    # Configuration Django
│   ├── settings/
│   │   ├── base.py           # Settings communs
│   │   ├── development.py    # Dev (SQLite, CORS all)
│   │   └── production.py     # Prod (PostgreSQL, HTTPS)
│   ├── urls.py               # Routing principal
│   ├── celery.py             # Config Celery
│   └── wsgi.py / asgi.py
├── apps/                      # 12 applications Django
│   ├── core/                 # Infrastructure partagee
│   ├── members/              # Gestion des membres
│   ├── donations/            # Dons et finances
│   ├── events/               # Evenements
│   ├── volunteers/           # Benevolat
│   ├── communication/        # Communications
│   ├── help_requests/        # Entraide
│   ├── reports/              # Rapports
│   ├── onboarding/           # Integration
│   ├── attendance/           # Presence
│   ├── payments/             # Paiements
│   └── worship/              # Culte
├── templates/                 # Templates Django (frontend actuel)
├── static/w3crm/             # Assets statiques (CSS, JS)
├── docs/                      # Documentation
├── docker/                    # Fichiers Docker
├── requirements.txt           # Dependances Python
└── manage.py
```

## API

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- Schema OpenAPI: `/api/schema/`
- Base URL: `/api/v1/`
- Auth actuelle: Session cookies
- Auth cible: JWT (access + refresh tokens)

## Systeme de roles

Hierarchie (du plus bas au plus eleve):
```
member → volunteer → group_leader → deacon → treasurer → pastor → admin
```

Support multi-roles via `MemberRole` + propriete `all_roles` (set).

## Documentation supplementaire

- [Architecture v2](./ARCHITECTURE.md) - Design de la nouvelle architecture
- [TODO](./TODO.md) - Liste des taches de migration
- [Features](./FEATURES.md) - Inventaire des fonctionnalites
- [Improvements](./IMPROVEMENTS.md) - Ameliorations proposees
- [Apps](./apps/) - Documentation par application

## Licence

Proprietary - Tous droits reserves
