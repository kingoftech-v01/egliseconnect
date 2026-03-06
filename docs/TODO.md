# TODO - EgliseConnect

## Legende
- [x] Complete
- [ ] A faire
- **P0**: Critique (bloquant)
- **P1**: Important
- **P2**: Nice to have

---

## Phase 1: Preparation Backend (P0) - COMPLETE

### Authentification JWT
- [x] **P0** Installer `djangorestframework-simplejwt`
- [x] **P0** Configurer JWT dans `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`
- [x] **P0** Creer `apps/core/views_auth_v2.py` avec endpoints: login, register, refresh, logout
- [x] **P0** Endpoint `POST /api/v2/auth/login/` - retourne access + refresh + member profile
- [x] **P0** Endpoint `POST /api/v2/auth/refresh/` - rotation refresh token
- [x] **P0** Endpoint `POST /api/v2/auth/register/` - signup avec invitation code optionnel
- [x] **P0** Endpoint `POST /api/v2/auth/logout/` - blacklist refresh token
- [x] **P1** Endpoint `GET /api/v2/auth/me/` - profil utilisateur courant
- [x] **P1** Endpoint `POST /api/v2/auth/forgot-password/` - envoi email reset
- [x] **P1** Endpoint `POST /api/v2/auth/reset-password/` - confirmation reset
- [x] **P1** Endpoint `POST /api/v2/auth/change-password/` - changer mot de passe
- [ ] **P1** Endpoint `POST /api/v2/auth/google/` - OAuth Google -> JWT
- [ ] **P1** Endpoint `POST /api/v2/auth/2fa/verify/` - verification TOTP
- [ ] **P1** Middleware JWT pour WebSocket (Django Channels)

### Configuration API
- [x] **P0** Configurer CORS pour `localhost:3000` (Next.js)
- [x] **P0** Rate limiting specifique pour auth endpoints
- [x] **P0** JWT tokens (15min access, 7-day refresh, rotation + blacklist)
- [x] **P1** Generer schema OpenAPI (`drf-spectacular`)
- [ ] **P2** Pagination cursor pour mobile

---

## Phase 2: Setup Monorepo (P0) - COMPLETE

- [x] **P0** Initialiser `package.json` racine avec workspaces
- [x] **P0** Installer et configurer Turborepo (`turbo.json`)
- [x] **P0** Deplacer le code Django dans `/backend`
- [x] **P0** Initialiser `/web` avec Next.js 15 (TypeScript, Tailwind v4, App Router)
- [x] **P0** Creer `/packages/types` - types TypeScript partages
- [x] **P0** Creer `/packages/api-client` - client API type-safe avec JWT refresh
- [x] **P1** Creer `/packages/utils` - utilitaires partages
- [x] **P0** Creer `/showcase` - site vitrine marketing

---

## Phase 3: Frontend Web - Core (P0) - COMPLETE

### Layout et navigation
- [x] **P0** `DashboardLayout` - sidebar + header + content area
- [x] **P0** `Sidebar` - navigation responsive, role-aware, collapse state
- [x] **P0** `Header` - search, notifications bell, user dropdown
- [x] **P0** `AuthLayout` - layout pour pages login/signup
- [x] **P0** Auth guard (redirect via middleware si non-authentifie)
- [x] **P0** Role guard (masquer elements selon le role)

### Authentification
- [x] **P0** Page login (email + password)
- [x] **P0** Page signup (avec invitation code)
- [x] **P0** Stockage JWT (Zustand + localStorage + cookie indicator)
- [x] **P0** Auto-refresh token (interceptor dans api-client)
- [x] **P1** Page mot de passe oublie
- [x] **P1** Page reset mot de passe
- [ ] **P1** Login Google OAuth
- [ ] **P1** 2FA TOTP setup et verification

### Dashboard
- [x] **P0** Page dashboard principal avec stats cards
- [x] **P0** Quick actions par role
- [x] **P1** Events a venir
- [x] **P1** Activite recente

---

## Phase 4-5: Frontend Web - All Modules - COMPLETE

### 12 modules implementes avec tabbed UI
- [x] Members (liste, CRUD, groupes, familles, departements, enfants, import, merge, custom fields, engagement, disciplinary, background checks)
- [x] Donations (liste, CRUD, campagnes, pledges, recus, import, kiosque, crypto, analytics, rapports)
- [x] Events (liste, CRUD, RSVP, calendrier, salles, templates, waitlist, sondages, photos, kiosque)
- [x] Volunteers (positions, schedules, disponibilites, swaps, heures, competences, reconnaissance, checklists, absences)
- [x] Communication (newsletters, notifications, SMS, templates, automations, messagerie, chat groupe, push, A/B tests)
- [x] Help Requests (demandes, priere, soins pastoraux, equipes, benevolence, trains de repas, crise)
- [x] Reports (dashboard, rapports planifies, rapports sauvegardes)
- [x] Onboarding (pipeline, cours, interviews, invitations, mentors, documents, quiz, achievements, welcome sequences)
- [x] Attendance (sessions, check-in QR, visiteurs, alertes absence, enfants, geofences, NFC, analytics)
- [x] Payments (paiements, recurrents, campagnes, kiosques, plans, objectifs)
- [x] Worship (services, sections, assignations, sermons, chants, setlists, repetitions, demandes chants, diffusion, series)
- [x] Settings (profil, branding, webhooks, notifications, campus, audit logs, login audits)

### Notifications & Services (Backend fixes)
- [x] Automation email - envoie reellement via Django send_mail
- [x] Newsletter task - envoie aux destinataires via send_mass_mail
- [x] SMS Twilio - appel Twilio debloque (avec fallback ImportError)
- [x] VAPID admin email - lue depuis settings au lieu de hardcode
- [x] .env.example - toutes les cles (Stripe, Twilio, VAPID, Coinbase, Redis)
- [x] Channel layers - configurable Redis pour production

### PWA & Frontend
- [x] manifest.json dans Next.js
- [x] Service worker (push notifications, offline)
- [x] Middleware Next.js (auth redirect server-side)
- [x] Cookie auth indicator (ec-auth)
- [x] SVG app icons (192 & 512)

---

## Phase 6: Frontend Mobile (P1) - TODO

- [ ] **P0** Initialiser Expo avec TypeScript et Expo Router
- [ ] **P0** Auth flow (login, JWT, biometric, secure storage)
- [ ] **P0** Dashboard (stats rapides, prochains evenements)
- [ ] **P1** Scanner QR (camera native)
- [ ] **P1** Notifications push (Expo Notifications)
- [ ] **P1** Mon profil + carte QR
- [ ] **P1** Faire un don (Stripe mobile)

---

## Phase 7: Polish et Deploiement (P1) - PARTIAL

### Tests
- [x] **P1** Tests backend Django (1141 tests)
- [ ] **P1** Tests unitaires composants React (Vitest)
- [ ] **P1** Tests E2E web (Playwright)
- [ ] **P2** Tests E2E mobile (Detox)

### Deploiement
- [x] **P1** Docker configuration (Dockerfile, docker-compose, nginx)
- [x] **P1** Site vitrine marketing (showcase)
- [ ] **P0** CI/CD pipeline (GitHub Actions)
- [ ] **P1** Deploy web sur Vercel
- [ ] **P2** Build mobile (EAS Build)

### A ameliorer
- [ ] **P1** Google OAuth login
- [ ] **P1** 2FA setup dans frontend
- [ ] **P1** Chart library (Recharts) pour graphiques
- [ ] **P2** i18n (next-intl pour fr/en)
- [ ] **P2** Tests frontend
- [ ] **P2** Nettoyage templates Django legacy
