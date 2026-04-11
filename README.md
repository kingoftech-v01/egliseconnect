# EgliseConnect

> **Plateforme de gestion d'eglise intelligente pour les communautes francophones du Canada.**

EgliseConnect est un systeme de gestion d'eglise (ChMS) complet construit avec une architecture moderne decouplee: un backend Django 5.x API-only, un frontend Next.js 15, et une application mobile dediee. Interface glassmorphism, authentification JWT + 2FA et multi-tenant pret pour des reseaux d'eglises.

---

## Apercu

- **12 applications Django**: `members`, `donations`, `events`, `volunteers`, `communication`, `help_requests`, `reports`, `attendance`, `payments`, `worship`, `onboarding`, `core`
- **API REST** documentee via OpenAPI / Swagger (`drf-spectacular`)
- **Suite de tests** pytest (120+ fichiers de tests repartis sur tous les apps)
- **Localisation** complete en francais canadien (`fr-ca`)

---

## Architecture

```
egliseconnect/
├── backend/          # Django 5.x API (DRF, JWT, Celery, allauth MFA)
├── web/              # Next.js 15 frontend (TypeScript, Tailwind v4)
├── mobile/           # Application mobile dediee
├── showcase/         # Site vitrine marketing
├── packages/         # Packages TypeScript partages
│   ├── types/        # @egliseconnect/types
│   ├── api-client/   # @egliseconnect/api-client (JWT auto-refresh)
│   └── utils/        # @egliseconnect/utils
├── docs/             # Documentation architecture et features
├── turbo.json        # Turborepo config
└── package.json      # Monorepo root
```

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Backend** | Django >=5.0,<6.0 ; DRF, Celery, Django Channels, PostgreSQL, Redis |
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS v4, TanStack Query, Zustand |
| **Auth** | JWT (simplejwt) avec rotation, 2FA (TOTP), RBAC 6 roles |
| **Paiements** | Stripe, Twilio SMS, Coinbase Commerce (crypto) |
| **Notifications** | Push (VAPID/pywebpush), Email (SMTP), SMS (Twilio), In-app, WebSocket |
| **Deploy** | Docker, Nginx, Gunicorn/Daphne |

---

## Demarrage rapide

### Prerequisites

- Python 3.10+, Node.js 18+, Redis (optionnel en dev)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
cp .env.example .env  # Modifier selon votre environnement
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8080
```

### Frontend

```bash
cd web
npm install
npm run dev  # Demarre sur http://localhost:3000
```

### Site vitrine

```bash
cd showcase
npm install
npm run dev  # Demarre sur http://localhost:3001
```

---

## Modules

| Module | Description |
|--------|-------------|
| **Membres** | Profils, familles, groupes, departements, enfants, import CSV, merge doublons, champs personnalises, engagement scoring |
| **Dons** | Dons multi-canaux, campagnes, pledges, recus fiscaux (ARC), import, crypto, kiosque, analytics |
| **Evenements** | CRUD, recurrence, RSVP, calendrier, salles, waitlist, templates, sondages, photos |
| **Benevoles** | Postes, schedules, disponibilites, swaps, heures, competences, reconnaissance, checklists |
| **Communication** | Newsletters, SMS (Twilio), push (VAPID), messagerie, chat, templates, automations, A/B tests |
| **Aide** | Requetes, priere, soins pastoraux, equipes de soins, benevolence, trains de repas, crise |
| **Rapports** | Dashboards, rapports planifies et sauvegardes, exports CSV/PDF |
| **Integration** | Pipeline kanban, cours, entrevues, invitations, mentorat, documents, quiz, gamification |
| **Presence** | Sessions, QR code, NFC, geofence, enfants (code securite), visiteurs, alertes, analytics |
| **Paiements** | Stripe, recurrents, campagnes, kiosques, plans, objectifs |
| **Culte** | Services, sermons, series, chants, setlists, repetitions, diffusion, demandes chants |
| **Parametres** | Branding, webhooks, campus, audit logs, login audits, preferences |

---

## Roles et permissions

| Role | Acces |
|------|-------|
| `member` | Profil personnel, evenements, dons personnels, repertoire |
| `volunteer` | + Planning, disponibilites, heures de service |
| `deacon` | + Groupes, demandes d'aide, soins pastoraux |
| `pastor` | + Tous les membres, communications, rapports etendus |
| `treasurer` | + Dons complets, rapports financiers, recus fiscaux |
| `admin` | Acces complet a tous les modules |

---

## API

- **API v1**: `/api/v1/` - Tous les endpoints CRUD par module
- **API v2**: `/api/v2/` - Auth JWT, dashboard agrege, endpoints optimises
- **Docs**: `/api/docs/` (Swagger) | `/api/redoc/` (ReDoc)

---

## Tests

```bash
# Backend (depuis /backend)
pytest apps/ -v

# Frontend TypeScript check (depuis /web)
npx tsc --noEmit
```

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Structure technique detaillee
- [Features](docs/FEATURES.md) - Inventaire complet des fonctionnalites
- [TODO](docs/TODO.md) - Etat d'avancement et prochaines etapes
- [Deployment](docs/DEPLOYMENT.md) - Guide de deploiement Docker

---

## Licence

**Proprietaire** - Tous droits reserves.

---

**EgliseConnect** - Concu avec soin pour les eglises francophones du Canada.
