# Architecture v2 - React/React Native + Django API

## Vue d'ensemble

Migration de l'architecture monolithique Django (templates) vers une architecture decouplee:

```
┌─────────────────────────────────────────────────────┐
│                    MONOREPO (Turborepo)              │
├──────────┬──────────┬──────────┬────────────────────┤
│  /backend │   /web   │ /mobile  │     /packages      │
│  Django   │ Next.js  │  Expo    │  Shared code       │
│  API-only │  React   │  React   │  Types, API client │
│           │          │  Native  │  Constants, Utils   │
└──────────┴──────────┴──────────┴────────────────────┘
```

## Structure du monorepo

```
egliseconnect/
├── turbo.json                    # Turborepo config
├── package.json                  # Root workspace
├── backend/                      # Django API (contenu actuel deplace ici)
│   ├── config/
│   ├── apps/
│   ├── requirements.txt
│   ├── manage.py
│   └── Dockerfile
├── web/                          # Next.js frontend
│   ├── src/
│   │   ├── app/                  # App Router (pages)
│   │   │   ├── (auth)/           # Routes non-authentifiees
│   │   │   │   ├── login/
│   │   │   │   ├── signup/
│   │   │   │   └── forgot-password/
│   │   │   ├── (dashboard)/      # Routes authentifiees
│   │   │   │   ├── layout.tsx    # Sidebar + Header + Auth guard
│   │   │   │   ├── page.tsx      # Dashboard principal
│   │   │   │   ├── members/
│   │   │   │   ├── donations/
│   │   │   │   ├── events/
│   │   │   │   ├── volunteers/
│   │   │   │   ├── communication/
│   │   │   │   ├── help-requests/
│   │   │   │   ├── reports/
│   │   │   │   ├── onboarding/
│   │   │   │   ├── attendance/
│   │   │   │   ├── payments/
│   │   │   │   └── worship/
│   │   │   └── layout.tsx        # Root layout
│   │   ├── components/
│   │   │   ├── ui/               # Composants UI generiques
│   │   │   ├── forms/            # Composants de formulaires
│   │   │   ├── layouts/          # Sidebar, Header, Footer
│   │   │   ├── charts/           # Graphiques
│   │   │   └── [app]/            # Composants specifiques par app
│   │   ├── hooks/                # Custom React hooks
│   │   ├── lib/                  # Utilitaires
│   │   └── styles/               # CSS global + Tailwind
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── package.json
├── mobile/                       # React Native (Expo)
│   ├── app/                      # Expo Router (file-based)
│   │   ├── (auth)/
│   │   ├── (tabs)/               # Tab navigation
│   │   │   ├── index.tsx         # Dashboard
│   │   │   ├── events.tsx        # Evenements
│   │   │   ├── giving.tsx        # Dons
│   │   │   ├── profile.tsx       # Mon profil
│   │   │   └── more.tsx          # Plus (menu)
│   │   └── _layout.tsx
│   ├── components/
│   ├── hooks/
│   ├── app.json
│   └── package.json
└── packages/                     # Packages partages
    ├── api-client/               # Client API type-safe
    │   ├── src/
    │   │   ├── client.ts         # Axios/fetch wrapper + JWT
    │   │   ├── endpoints/        # Un fichier par app
    │   │   │   ├── members.ts
    │   │   │   ├── donations.ts
    │   │   │   ├── events.ts
    │   │   │   └── ...
    │   │   └── index.ts
    │   └── package.json
    ├── types/                    # Types TypeScript partages
    │   ├── src/
    │   │   ├── models/           # Types miroir des modeles Django
    │   │   │   ├── member.ts
    │   │   │   ├── donation.ts
    │   │   │   └── ...
    │   │   ├── api/              # Types requete/reponse API
    │   │   ├── constants.ts      # Miroir de constants.py
    │   │   └── index.ts
    │   └── package.json
    ├── utils/                    # Utilitaires partages
    │   ├── src/
    │   │   ├── formatting.ts     # Formatage dates, monnaie
    │   │   ├── validation.ts     # Regles de validation
    │   │   └── permissions.ts    # Logique permissions client
    │   └── package.json
    └── ui/                       # Composants UI partages (optionnel)
        └── package.json
```

## Backend - Modifications requises

### 1. Authentification JWT

Remplacer `SessionAuthentication` par JWT via `djangorestframework-simplejwt`:

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # garder pour admin
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

Nouveaux endpoints:
```
POST /api/v2/auth/login/          → {access, refresh, member}
POST /api/v2/auth/refresh/        → {access}
POST /api/v2/auth/register/       → {access, refresh, member}
POST /api/v2/auth/logout/         → blacklist refresh token
POST /api/v2/auth/password-reset/ → envoie email
POST /api/v2/auth/verify-email/   → verifie token
POST /api/v2/auth/google/         → OAuth Google → JWT
POST /api/v2/auth/2fa/verify/     → verifie TOTP code
GET  /api/v2/auth/me/             → profil utilisateur courant
```

### 2. API v2 - Ameliorations

L'API v1 existe deja et couvre ~95% des fonctionnalites. API v2 ajoutera:

- **Serializers optimises**: Nested serializers pour reduire les appels (ex: `MemberDetail` inclut `groups`, `family`, `privacy_settings`)
- **Endpoints agrege**: `/api/v2/dashboard/` retourne toutes les stats en un seul appel
- **Pagination cursor**: Pour le scroll infini mobile
- **Filtres avances**: Date ranges, recherche full-text
- **Bulk operations**: Ajout/suppression en masse
- **WebSocket**: Notifications temps reel via `/ws/notifications/`
- **Upload presigne**: Pour photos/documents (S3 compatible)

### 3. CORS Configuration

```python
# config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',      # Next.js dev
    'http://localhost:8081',      # Expo dev
    'https://app.egliseconnect.ca',  # Prod web
]
CORS_ALLOW_CREDENTIALS = True
```

### 4. Suppression progressive des templates

Phase 1: Construire le frontend React complet
Phase 2: Supprimer `templates/`, `static/w3crm/`, `dz.py`, `custom_context_processor.py`, `custom_tags.py`, et toutes les `views_frontend.py`
Phase 3: Django devient purement API-only

## Frontend Web (Next.js)

### Stack technique

| Technologie | Role |
|-------------|------|
| Next.js 14+ | Framework React (App Router, SSR) |
| TypeScript | Typage statique |
| Tailwind CSS | Styling utilitaire |
| shadcn/ui | Composants UI accessibles |
| TanStack Query | Cache, fetch, mutations |
| Zustand | State management global |
| React Hook Form + Zod | Formulaires + validation |
| Recharts | Graphiques et charts |
| FullCalendar React | Calendrier |
| next-intl | Internationalisation (fr/en) |
| next-auth | Auth helper (stockage JWT) |

### Mapping pages actuelles → Next.js

| Django Template | Next.js Route |
|----------------|---------------|
| `reports/dashboard.html` | `/` (dashboard) |
| `member_list.html` | `/members` |
| `member_detail.html` | `/members/[id]` |
| `member_form.html` | `/members/new`, `/members/[id]/edit` |
| `group_list.html` | `/members/groups` |
| `donation_admin_list.html` | `/donations` |
| `event_list.html` | `/events` |
| `event_calendar.html` | `/events/calendar` |
| `scanner.html` | `/attendance/scanner` |
| `my_qr.html` | `/attendance/my-qr` |
| `newsletter_list.html` | `/communication/newsletters` |
| `admin_pipeline.html` | `/onboarding/pipeline` |
| `service_list.html` | `/worship/services` |
| ... | ... |

### Architecture des composants

```
Components/
├── ui/                    # Primitives (Button, Input, Card, Modal, Badge, etc.)
├── layouts/
│   ├── DashboardLayout    # Sidebar + Header + Content + Footer
│   ├── AuthLayout         # Layout pour pages non-authentifiees
│   ├── Sidebar            # Navigation role-aware
│   └── Header             # Search, notifications, user menu
├── data-display/
│   ├── DataTable          # Remplacement DataTables (sorting, filtering, pagination)
│   ├── StatCard           # Carte statistique dashboard
│   ├── KPIGrid            # Grille de metriques
│   └── Calendar           # Wrapper FullCalendar
├── forms/
│   ├── FormField          # Champ generique (label, erreur, aide)
│   ├── MemberForm         # Formulaire membre
│   ├── DonationForm       # Formulaire don
│   └── [AppName]Form      # Un formulaire par entite majeure
├── features/
│   ├── members/           # Composants specifiques membres
│   ├── donations/         # Composants specifiques dons
│   ├── attendance/        # Scanner QR, carte QR
│   ├── worship/           # Setlist builder, chord chart
│   └── onboarding/        # Pipeline kanban, journey map
└── common/
    ├── RoleGuard          # Wrapper conditionnel par role
    ├── NotificationBell   # Cloche notifications temps reel
    └── SearchBar          # Recherche globale avec autocomplete
```

## Frontend Mobile (React Native / Expo)

### Navigation

```
Tab Navigator
├── Dashboard (Home)
│   ├── Stats rapides
│   ├── Prochains evenements
│   └── Notifications recentes
├── Evenements
│   ├── Liste des evenements
│   ├── Detail evenement
│   └── RSVP
├── Dons
│   ├── Faire un don (Stripe)
│   ├── Historique
│   └── Recus fiscaux
├── Profil
│   ├── Mon profil
│   ├── Ma carte QR
│   ├── Mon planning benevolat
│   └── Parametres
└── Plus
    ├── Annuaire
    ├── Groupes
    ├── Demandes d'aide
    ├── Mur de priere
    ├── Sermons (audio/video)
    └── Parametres app
```

### Fonctionnalites mobiles specifiques

| Feature | Description |
|---------|-------------|
| **QR Scanner** | Camera native pour scan QR (presence) |
| **Push Notifications** | Expo Notifications (remplace VAPID) |
| **Offline Mode** | Cache local pour consultation hors-ligne |
| **Biometric Auth** | Touch ID / Face ID pour login rapide |
| **Deep Linking** | Liens `egliseconnect://` pour navigation |
| **Share** | Partage evenements, sermons via share sheet |
| **Maps** | Carte pour localiser l'eglise et evenements |
| **Audio Player** | Lecteur audio pour sermons |

## Authentification - Flow JWT

```
┌─────────┐     ┌──────────┐     ┌─────────┐
│  Client  │────>│  /login/  │────>│ Django  │
│ (React)  │     │  (email + │     │ Backend │
│          │     │  password)│     │         │
│          │<────│           │<────│ JWT pair│
│          │     └──────────┘     └─────────┘
│          │
│ Stocke:  │
│ - access │ (memoire / httpOnly cookie)
│ - refresh│ (httpOnly cookie)
│          │
│ Requetes:│
│ Authorization: Bearer <access_token>
│          │
│ Quand access expire (15min):
│ POST /auth/refresh/ avec refresh token
│ → nouveau access token
└──────────┘
```

### Strategie de stockage des tokens

**Web (Next.js)**:
- Access token: en memoire (variable React) + httpOnly cookie (SSR)
- Refresh token: httpOnly cookie uniquement
- CSRF: Double-submit cookie pattern

**Mobile (React Native)**:
- Access token: SecureStore (Expo)
- Refresh token: SecureStore (Expo)
- Biometric lock optionnel

## WebSocket - Notifications temps reel

Le systeme WebSocket existant (Django Channels) sera conserve. Les clients React/RN se connecteront au meme endpoint:

```
ws://api.egliseconnect.ca/ws/notifications/
```

Avec authentification JWT dans le handshake:
```javascript
const ws = new WebSocket(`wss://api.example.com/ws/notifications/?token=${accessToken}`);
```

## Plan de migration

### Phase 1: Preparation backend (2-3 semaines)
1. Ajouter `djangorestframework-simplejwt`
2. Creer endpoints auth v2 (login, register, refresh, 2FA)
3. Optimiser serializers pour v2 (nested, aggregated)
4. Configurer CORS pour Next.js et Expo
5. Ajouter pagination cursor pour mobile
6. Generer types TypeScript depuis schema OpenAPI

### Phase 2: Setup monorepo (1 semaine)
1. Initialiser Turborepo
2. Deplacer backend dans `/backend`
3. Creer `/web` (Next.js), `/mobile` (Expo), `/packages`
4. Setup CI/CD (lint, type-check, test)
5. Creer `api-client` et `types` packages

### Phase 3: Frontend web - Core (3-4 semaines)
1. Layout system (Sidebar, Header, Auth guards)
2. Dashboard principal
3. Module membres (CRUD, directory, groups, families)
4. Module dons (CRUD, campaigns, receipts)
5. Auth complet (login, signup, 2FA, reset, Google)

### Phase 4: Frontend web - Features (3-4 semaines)
1. Module evenements (CRUD, calendrier, RSVP)
2. Module benevolat (planification, schedule, hours)
3. Module communication (newsletters, SMS, notifications)
4. Module presence (scanner QR, sessions, kiosk)
5. Module onboarding (pipeline, formation, interviews)

### Phase 5: Frontend web - Avance (2-3 semaines)
1. Module culte (services, sermons, chants, setlists)
2. Module aide (requetes, priere, equipes de soin)
3. Module rapports (dashboard, analytics, exports)
4. Module paiements (Stripe, recurrents, statements)
5. Module parametres (branding, webhooks, audit)

### Phase 6: Mobile (4-5 semaines)
1. Auth + navigation de base
2. Dashboard + notifications push
3. Dons (Stripe mobile)
4. Evenements + RSVP
5. QR code + scanner
6. Profil + annuaire
7. Sermons (lecteur audio)
8. Mode offline

### Phase 7: Polish et deploiement (2 semaines)
1. Tests E2E (Playwright web, Detox mobile)
2. Performance (Lighthouse, bundle analysis)
3. Accessibilite (a11y audit)
4. Deploiement (Vercel web, EAS mobile, Docker backend)
5. Suppression templates Django

## Deploiement cible

```
┌─────────────────┐     ┌──────────────────┐
│   Vercel         │     │  App Store       │
│   (Next.js web)  │     │  Google Play     │
│   CDN + Edge     │     │  (React Native)  │
└────────┬────────┘     └────────┬─────────┘
         │                        │
         │    HTTPS / JWT         │
         ▼                        ▼
┌─────────────────────────────────────────┐
│          API Gateway / Nginx             │
├─────────────────────────────────────────┤
│  Django (Gunicorn)  │  Daphne (ASGI)    │
│  REST API           │  WebSocket        │
├─────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Celery Workers │
└──────────────┴─────────┴────────────────┘
```

## Decisions techniques cles

| Decision | Choix | Raison |
|----------|-------|--------|
| Monorepo | Turborepo | Types partages, atomic commits, CI unifiee |
| Web framework | Next.js | SSR, routing fichier, ecosystem React |
| Mobile | Expo | Dev experience, OTA updates, pas besoin native modules custom |
| Auth | JWT | Stateless, fonctionne mobile + web, standard industrie |
| State | Zustand + TanStack Query | Simple, performant, separation server/client state |
| Styling web | Tailwind + shadcn/ui | Rapide, accessible, composants headless |
| Styling mobile | NativeWind | Tailwind syntax pour React Native |
| Forms | React Hook Form + Zod | Performance, validation type-safe |
| API client | Auto-genere depuis OpenAPI | Type-safety, sync avec backend |
| i18n | next-intl | ICU message format, SSR support |
