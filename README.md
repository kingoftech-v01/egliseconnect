# EgliseConnect - Systeme de gestion d'eglise

> **Une solution complete de gestion pour les eglises francophones du Canada.**
> EgliseConnect est un systeme de gestion d'eglise construit avec Django 5.2, concu pour aider les eglises
> franco-canadiennes a gerer leurs membres, dons, evenements, benevoles, communications et demandes d'aide
> -- le tout dans une interface moderne en francais.

---

## Table des matieres

- [Apercu du projet](#apercu-du-projet)
- [Captures d'ecran](#captures-decran)
- [Fonctionnalites](#fonctionnalites)
- [Architecture](#architecture)
- [Pile technologique (Tech Stack)](#pile-technologique-tech-stack)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Configuration](#configuration)
- [Lancement du projet](#lancement-du-projet)
- [Apercu des URLs](#apercu-des-urls)
- [Roles et permissions](#roles-et-permissions)
- [Theme frontend (W3CRM)](#theme-frontend-w3crm)
- [Tests](#tests)
- [Contribution](#contribution)
- [Licence](#licence)

---

## Apercu du projet

### Pour les utilisateurs non techniques

EgliseConnect est une application web qui permet a votre eglise de :

- **Gerer les membres** : Tenir a jour un repertoire complet de vos membres et de leurs familles, avec photos et coordonnees.
- **Suivre les dons** : Enregistrer les dons, gerer les campagnes de financement et generer les recus fiscaux conformes a l'ARC (Agence du revenu du Canada).
- **Organiser les evenements** : Planifier des evenements, gerer les inscriptions (RSVP) et consulter un calendrier.
- **Coordonner les benevoles** : Creer des postes de benevolat, gerer les horaires et permettre les echanges de quarts.
- **Communiquer** : Envoyer des infolettres et des notifications aux membres.
- **Gerer les demandes d'aide** : Recevoir et traiter les demandes de priere, d'aide financiere, materielle ou pastorale.
- **Consulter des rapports** : Voir des statistiques, des tableaux de bord et des rapports detailles.

### Pour les developpeurs

EgliseConnect est une application Django 5.2 modulaire composee de 8 apps Django, avec une architecture a double couche (frontend + API REST). Le systeme est entierement localise en francais canadien (`fr-ca`) et utilise le fuseau horaire `America/Toronto`.

---

## Captures d'ecran

> _Section a venir -- les captures d'ecran seront ajoutees prochainement._

| Page | Apercu |
|------|--------|
| Tableau de bord (Dashboard) | ![Dashboard](docs/screenshots/dashboard.png) |
| Gestion des membres | ![Membres](docs/screenshots/members.png) |
| Suivi des dons | ![Dons](docs/screenshots/donations.png) |
| Calendrier des evenements | ![Evenements](docs/screenshots/events.png) |
| Gestion des benevoles | ![Benevoles](docs/screenshots/volunteers.png) |
| Communications | ![Communications](docs/screenshots/communication.png) |

---

## Fonctionnalites

### Gestion des membres (`members`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Repertoire complet des membres avec photos et coordonnees | Modeles `Member`, `Family`, `Group` avec numeros de membre auto-generes |
| Regroupement par famille et par groupes/ministeres | Relations many-to-many, recherche et filtrage avances |
| Parametres de confidentialite pour chaque membre | Systeme de privacy granulaire au niveau du profil |
| Repertoire consultable par les membres autorises | Vue repertoire avec controle d'acces base sur les roles |

### Suivi des dons (`donations`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Enregistrement des dons (en ligne et physiques) | Modele `Donation` avec support multi-type (cheque, virement, especes, en ligne) |
| Campagnes de financement avec suivi de progression | Modele `Campaign` avec objectifs et dates |
| Generation de recus fiscaux conformes a l'ARC | Generation automatique de recus conformes aux normes de l'Agence du revenu du Canada (CRA) |
| Rapports financiers detailles | Agregation et filtrage via l'app `reports` |

### Gestion des evenements (`events`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Calendrier des evenements de l'eglise | Integration FullCalendar dans le frontend |
| Inscription en ligne (RSVP) aux evenements | Systeme RSVP avec confirmation |
| Evenements recurrents (hebdomadaires, mensuels) | Gestion de la recurrence au niveau du modele |

### Coordination des benevoles (`volunteers`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Creation de postes de benevolat | Modele `Position` avec descriptions et exigences |
| Horaires et planification des quarts | Modele `Schedule` avec gestion de rotation |
| Demandes d'echange de quarts entre benevoles | Modele `SwapRequest` avec workflow d'approbation |
| Gestion de la disponibilite | Modele `Availability` par benevole |

### Communications (`communication`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Envoi d'infolettres aux membres | Modele `Newsletter` avec editeur de contenu (nettoyage via Bleach) |
| Notifications personnalisees | Modele `Notification` avec preferences par membre |
| Preferences de communication par membre | Gestion des abonnements et canaux preferes (courriel, SMS) |

### Demandes d'aide (`help_requests`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Systeme de billetterie pour les demandes d'aide | Modele `HelpRequest` avec types : priere, financier, materiel, pastoral |
| Suivi des demandes et commentaires | Modele `Comment` avec historique |
| Attribution des demandes a des responsables | Systeme d'assignation avec notifications |

### Rapports et tableau de bord (`reports`)

| Pour l'eglise | Detail technique |
|----------------|-----------------|
| Tableau de bord principal avec indicateurs cles | Dashboard avec widgets Chart.js et ApexCharts |
| Rapports sur les membres, dons, presence, benevoles | Vues de rapport dediees avec filtres avances |
| Statistiques visuelles et exportables | Agregation Django ORM, graphiques interactifs |

---

## Architecture

### Explication simple

EgliseConnect fonctionne sur deux niveaux :

1. **Le site web (frontend)** : C'est l'interface que vos membres et administrateurs voient dans leur navigateur. Elle est construite avec des pages HTML elegantes utilisant le theme W3CRM.
2. **L'API REST** : C'est un service en arriere-plan qui permet a d'autres applications (ou une future application mobile) de communiquer avec EgliseConnect pour lire ou modifier des donnees.

Les deux niveaux partagent les memes donnees et les memes regles de securite.

### Detail technique : architecture a double couche (Dual-Layer)

Chaque app Django contient deux fichiers de vues separes :

```text
apps/members/
├── views_frontend.py   # Vues Django classiques (templates HTML, session-based auth)
├── views_api.py        # Vues DRF (serializers JSON, session-based auth)
├── serializers.py      # Serializers Django REST Framework
├── urls_frontend.py    # Routes frontend (namespace: frontend:members:*)
├── urls_api.py         # Routes API (namespace: v1:members:*)
├── models.py           # Modeles de donnees
├── forms.py            # Formulaires Django
├── permissions.py      # Permissions personnalisees
└── ...
```

**Flux des requetes :**

```text
Navigateur ──► urls_frontend.py ──► views_frontend.py ──► templates/ ──► Reponse HTML
Client API ──► urls_api.py ──► views_api.py ──► serializers.py ──► Reponse JSON
```

**Namespaces d'URL :**

| Couche | Format du namespace | Exemple |
|--------|---------------------|---------|
| Frontend | `frontend:app_name:view_name` | `frontend:members:member_list` |
| API | `v1:app_name:resource` | `v1:members:member-list` |

---

## Pile technologique (Tech Stack)

| Categorie | Technologie | Role |
|-----------|-------------|------|
| **Framework web** | Django 5.2 | Framework principal |
| **API REST** | Django REST Framework >= 3.14 | Endpoints API |
| **Documentation API** | drf-spectacular >= 0.27 | Swagger / ReDoc auto-generee |
| **Base de donnees (dev)** | SQLite | Developpement local |
| **Base de donnees (prod)** | PostgreSQL (psycopg2-binary >= 2.9) | Production |
| **Taches asynchrones** | Celery >= 5.3 + Redis >= 5.0 | Envoi de courriels, rapports differees |
| **Taches planifiees** | django-celery-beat >= 2.5 | Taches recurrentes (cron) |
| **Theme frontend** | W3CRM par DexignZone (Bootstrap 5) | Interface d'administration |
| **Filtrage** | django-filter >= 23.5 | Filtres sur les vues et l'API |
| **CORS** | django-cors-headers >= 4.3 | Gestion des origines croisees pour l'API |
| **Images** | Pillow >= 10.0 | Traitement des photos de profil |
| **Securite contenu** | Bleach >= 6.0 | Nettoyage HTML (infolettres) |
| **Dates** | python-dateutil >= 2.8 | Manipulation avancee des dates |
| **Variables d'env** | django-environ >= 0.11 | Gestion du fichier `.env` |
| **Serveur WSGI (prod)** | Gunicorn >= 21.2 | Serveur de production |
| **Tests** | pytest >= 7.4, pytest-django >= 4.7, factory-boy >= 3.3 | Suite de tests |
| **Couverture** | pytest-cov >= 4.1 | Rapport de couverture de code |
| **Qualite de code** | flake8 >= 6.1, black >= 23.12, isort >= 5.13 | Linting et formatage |

---

## Structure du projet

```text
egliseconnect/
├── manage.py                        # Point d'entree Django
├── requirements.txt                 # Dependances Python
├── dz.py                            # Configuration des assets du theme W3CRM
├── custom_context_processor.py      # Injecte dz_array dans les templates
├── config/
│   ├── settings/
│   │   ├── base.py                  # Parametres communs (apps, middleware, i18n)
│   │   ├── development.py           # Dev : DEBUG=True, SQLite, console email
│   │   └── production.py            # Prod : PostgreSQL, securite renforcee
│   ├── urls.py                      # Configuration racine des URLs avec namespaces
│   └── wsgi.py                      # Point d'entree WSGI
├── apps/
│   ├── core/                        # Modeles de base, permissions, mixins, utilitaires,
│   │                                #   constantes, validateurs
│   ├── members/                     # Membres, familles, groupes, repertoire, confidentialite
│   ├── donations/                   # Dons, campagnes, recus fiscaux (ARC/CRA)
│   ├── events/                      # Evenements, calendrier, RSVP
│   ├── volunteers/                  # Postes, horaires, disponibilite, echanges de quarts
│   ├── communication/               # Infolettres, notifications, preferences
│   ├── help_requests/               # Systeme de demandes d'aide, commentaires, assignation
│   └── reports/                     # Tableau de bord, statistiques, rapports
├── templates/
│   ├── base.html                    # Layout de base (sidebar W3CRM, en-tete, pied de page)
│   ├── elements/                    # Composants : nav-header, sidebar, header, footer
│   ├── registration/                # login.html
│   ├── members/                     # 9 templates pour la gestion des membres
│   ├── events/                      # 3 templates
│   ├── volunteers/                  # 4 templates
│   ├── communication/               # 5 templates
│   ├── help_requests/               # 4 templates
│   └── reports/                     # 5 templates
├── static/
│   └── w3crm/                       # Tous les assets statiques du theme
│       ├── css/style.css            # Feuille de style principale
│       ├── js/
│       │   ├── custom.min.js        # Scripts personnalises
│       │   └── deznav-init.js       # Initialisation de la navigation
│       ├── vendor/                  # Librairies tierces :
│       │   ├── bootstrap/           #   Bootstrap 5
│       │   ├── datatables/          #   DataTables (tableaux interactifs)
│       │   ├── chart.js/            #   Chart.js (graphiques)
│       │   ├── apexchart/           #   ApexCharts (graphiques avances)
│       │   └── fullcalendar/        #   FullCalendar (calendrier)
│       └── images/                  # Images du theme
├── locale/                          # Fichiers de traduction i18n (fr-ca)
└── media/                           # Fichiers uploades (photos, recus, etc.)
```

---

## Installation

### Prerequis

- **Python 3.10+**
- **pip** (gestionnaire de paquets Python)
- **Redis** (requis pour Celery en production ; optionnel en developpement)
- **PostgreSQL** (requis en production ; SQLite est utilise en developpement)
- **Git**

### Etape par etape

#### 1. Cloner le depot

```bash
git clone https://github.com/votre-organisation/egliseconnect.git
cd egliseconnect
```

#### 2. Creer et activer un environnement virtuel

```bash
# Linux / macOS
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate
```

#### 3. Installer les dependances

```bash
pip install -r requirements.txt
```

#### 4. Creer le fichier de configuration `.env`

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Puis modifiez le fichier `.env` selon votre environnement (voir la section [Configuration](#configuration) ci-dessous).

#### 5. Appliquer les migrations de la base de donnees

```bash
python manage.py migrate
```

#### 6. Creer un compte administrateur

```bash
python manage.py createsuperuser
```

Suivez les instructions pour definir le nom d'utilisateur, le courriel et le mot de passe.

#### 7. Collecter les fichiers statiques (production seulement)

```bash
python manage.py collectstatic --noinput
```

#### 8. Lancer le serveur de developpement

```bash
python manage.py runserver
```

Ouvrez votre navigateur a l'adresse [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Configuration

Le fichier `.env` a la racine du projet contient les variables de configuration. Voici les variables principales :

### Variables d'environnement

| Variable | Description | Exemple | Requis |
|----------|-------------|---------|--------|
| `DJANGO_SETTINGS_MODULE` | Module de parametres a utiliser | `config.settings.development` | Oui |
| `SECRET_KEY` | Cle secrete Django (generez-en une unique!) | `votre-cle-secrete-ici` | Oui |
| `DEBUG` | Mode debogage (jamais `True` en production) | `True` | Oui |
| `ALLOWED_HOSTS` | Hotes autorises, separes par des virgules | `localhost,127.0.0.1` | Oui (prod) |
| `DATABASE_URL` | URL de connexion PostgreSQL (production) | `postgres://user:pass@localhost:5432/egliseconnect` | Prod |
| `REDIS_URL` | URL de connexion Redis (pour Celery) | `redis://localhost:6379/0` | Prod |
| `EMAIL_BACKEND` | Backend d'envoi de courriels | `django.core.mail.backends.smtp.EmailBackend` | Non |
| `EMAIL_HOST` | Serveur SMTP | `smtp.gmail.com` | Non |
| `EMAIL_PORT` | Port SMTP | `587` | Non |
| `EMAIL_HOST_USER` | Utilisateur SMTP | `eglise@example.com` | Non |
| `EMAIL_HOST_PASSWORD` | Mot de passe SMTP | `mot-de-passe` | Non |
| `EMAIL_USE_TLS` | Utiliser TLS pour le courriel | `True` | Non |
| `DEFAULT_FROM_EMAIL` | Adresse d'envoi par defaut | `EgliseConnect <noreply@example.com>` | Non |
| `CORS_ALLOWED_ORIGINS` | Origines autorisees pour l'API (CORS) | `http://localhost:3000` | Non |

### Exemple de fichier `.env` pour le developpement

```env
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=dev-secret-key-changez-moi-en-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Exemple de fichier `.env` pour la production

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=une-tres-longue-cle-secrete-aleatoire
DEBUG=False
ALLOWED_HOSTS=egliseconnect.example.com
DATABASE_URL=postgres://eglise_user:mot_de_passe@localhost:5432/egliseconnect
REDIS_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=eglise@example.com
EMAIL_HOST_PASSWORD=mot-de-passe-app
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=EgliseConnect <noreply@egliseconnect.example.com>
```

---

## Lancement du projet

### Serveur de developpement

```bash
# Assurez-vous que l'environnement virtuel est active
python manage.py runserver
```

Le site sera accessible a [http://127.0.0.1:8000](http://127.0.0.1:8000).
La page d'accueil (`/`) redirige automatiquement vers le tableau de bord (`/reports/`).

### Worker Celery (taches asynchrones)

Pour les taches en arriere-plan (envoi de courriels, generation de rapports), lancez le worker Celery :

```bash
# Lancer le worker Celery
celery -A config worker --loglevel=info

# Lancer le scheduler Celery Beat (taches planifiees)
celery -A config beat --loglevel=info
```

> **Note :** Redis doit etre en marche pour que Celery fonctionne. En developpement, vous pouvez ignorer Celery si vous n'avez pas besoin des taches asynchrones.

### Serveur de production (Gunicorn)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Apercu des URLs

### URLs du frontend (interface web)

| URL | Description | Authentification |
|-----|-------------|------------------|
| `/` | Redirection vers `/reports/` (tableau de bord) | Oui |
| `/accounts/login/` | Page de connexion | Non |
| `/admin/` | Interface d'administration Django | Superutilisateur |
| `/members/` | Gestion des membres, familles, groupes | Oui |
| `/donations/` | Gestion des dons, campagnes, recus fiscaux | Oui |
| `/events/` | Evenements et calendrier | Oui |
| `/volunteers/` | Gestion des benevoles et horaires | Oui |
| `/communication/` | Infolettres et notifications | Oui |
| `/help-requests/` | Demandes d'aide | Oui |
| `/reports/` | Tableau de bord et rapports | Oui |

### URLs de l'API REST

| URL | Description | Format |
|-----|-------------|--------|
| `/api/v1/members/` | API des membres | JSON |
| `/api/v1/donations/` | API des dons | JSON |
| `/api/v1/events/` | API des evenements | JSON |
| `/api/v1/volunteers/` | API des benevoles | JSON |
| `/api/v1/communication/` | API des communications | JSON |
| `/api/v1/help-requests/` | API des demandes d'aide | JSON |
| `/api/v1/reports/` | API des rapports | JSON |
| `/api/docs/` | Documentation Swagger (interactive) | HTML |
| `/api/redoc/` | Documentation ReDoc (reference) | HTML |

> **Authentification API :** L'API utilise l'authentification par session Django. Les clients doivent d'abord se connecter via `/accounts/login/` ou envoyer les credentials dans la requete.

---

## Roles et permissions

EgliseConnect utilise un systeme de roles pour controler l'acces aux fonctionnalites. Chaque utilisateur se voit attribuer un ou plusieurs roles.

### Explication simple des roles

| Role | Qui est-ce? | Ce qu'il peut faire |
|------|-------------|---------------------|
| **member** | Un membre regulier de l'eglise | Consulter son profil, voir le repertoire (selon confidentialite), s'inscrire aux evenements, faire des dons |
| **volunteer** | Un benevole actif | Tout ce qu'un membre peut faire + gerer sa disponibilite, voir ses horaires, demander des echanges de quarts |
| **group_leader** | Un responsable de groupe ou ministere | Tout ce qu'un benevole peut faire + gerer les membres de son groupe, voir les rapports de son groupe |
| **pastor** | Un membre du personnel pastoral | Acces elargi aux informations des membres, gestion des demandes d'aide pastorales, communications |
| **treasurer** | L'administrateur financier | Gestion complete des dons, campagnes, recus fiscaux, rapports financiers |
| **admin** | L'administrateur systeme | Acces complet a toutes les fonctionnalites, gestion des utilisateurs et des parametres |

### Matrice des permissions detaillee

| Fonctionnalite | member | volunteer | group_leader | pastor | treasurer | admin |
|----------------|--------|-----------|--------------|--------|-----------|-------|
| Voir son profil | Oui | Oui | Oui | Oui | Oui | Oui |
| Modifier son profil | Oui | Oui | Oui | Oui | Oui | Oui |
| Voir le repertoire | Limite | Limite | Oui | Oui | Limite | Oui |
| Gerer les membres | -- | -- | Son groupe | Oui | -- | Oui |
| Faire un don | Oui | Oui | Oui | Oui | Oui | Oui |
| Gerer les dons | -- | -- | -- | -- | Oui | Oui |
| Generer des recus fiscaux | -- | -- | -- | -- | Oui | Oui |
| S'inscrire aux evenements | Oui | Oui | Oui | Oui | Oui | Oui |
| Gerer les evenements | -- | -- | Oui | Oui | -- | Oui |
| Voir ses horaires benevole | -- | Oui | Oui | Oui | -- | Oui |
| Gerer les horaires | -- | -- | Oui | Oui | -- | Oui |
| Envoyer des communications | -- | -- | Son groupe | Oui | -- | Oui |
| Gerer les demandes d'aide | -- | -- | -- | Oui | -- | Oui |
| Voir les rapports | -- | -- | Son groupe | Oui | Financiers | Oui |
| Administration systeme | -- | -- | -- | -- | -- | Oui |

---

## Theme frontend (W3CRM)

### A propos du theme

EgliseConnect utilise **W3CRM** par **DexignZone**, un template d'administration professionnel base sur **Bootstrap 5**. Ce theme fournit une interface moderne avec sidebar, en-tete, tableaux de donnees, graphiques et composants interactifs.

Tous les assets statiques du theme se trouvent dans `static/w3crm/`.

### Chargement des assets : le pipeline de configuration

Le theme W3CRM utilise un pipeline de configuration en trois etapes pour charger dynamiquement les fichiers CSS et JavaScript dans les templates :

```text
dz.py  ──►  custom_context_processor.py  ──►  custom_tags.py (filtre)  ──►  Templates
```

**Etape 1 : `dz.py`** (configuration)

Le fichier `dz.py` a la racine du projet definit un dictionnaire `dz_array` qui contient la configuration du theme : les fichiers CSS a charger, les fichiers JS, les options de layout (sidebar, en-tete, couleurs), etc.

**Etape 2 : `custom_context_processor.py`** (injection dans le contexte)

Le context processor lit `dz_array` depuis `dz.py` et l'injecte dans le contexte de chaque template Django. Ainsi, chaque page a acces a la configuration du theme.

**Etape 3 : `custom_tags.py`** (filtre de template)

Un filtre de template personnalise (`templatetags/custom_tags.py`) permet aux templates d'acceder aux valeurs de `dz_array` de facon propre, par exemple pour generer dynamiquement les balises `<link>` et `<script>`.

### Structure des templates

```text
templates/
├── base.html              # Layout principal : charge les CSS/JS, definit la structure
│   ├── elements/
│   │   ├── nav-header.html    # Logo et bouton toggle
│   │   ├── sidebar.html       # Menu lateral de navigation
│   │   ├── header.html        # Barre d'en-tete (recherche, notifications, profil)
│   │   └── footer.html        # Pied de page
│   └── [blocs de contenu]     # {% block content %} rempli par chaque page
├── registration/
│   └── login.html             # Page de connexion
├── members/                   # Templates de l'app membres (9 fichiers)
├── events/                    # Templates de l'app evenements (3 fichiers)
├── volunteers/                # Templates de l'app benevoles (4 fichiers)
├── communication/             # Templates de l'app communications (5 fichiers)
├── help_requests/             # Templates de l'app demandes d'aide (4 fichiers)
└── reports/                   # Templates de l'app rapports (5 fichiers)
```

> **Note :** Les templates de l'app `donations` se trouvent dans `apps/donations/templates/donations/` (au sein de l'app elle-meme).

---

## Tests

EgliseConnect dispose d'une suite de **1152 tests** couvrant l'ensemble des fonctionnalites.

### Lancer tous les tests

```bash
pytest apps/ -v
```

### Lancer les tests d'une app specifique

```bash
# Tests de l'app membres
pytest apps/members/ -v

# Tests de l'app dons
pytest apps/donations/ -v

# Tests de l'app evenements
pytest apps/events/ -v
```

### Lancer les tests avec rapport de couverture

```bash
pytest apps/ --cov=apps --cov-report=html -v
```

Le rapport HTML sera genere dans le dossier `htmlcov/`. Ouvrez `htmlcov/index.html` dans votre navigateur pour consulter la couverture ligne par ligne.

### Lancer les tests avec un rapport de couverture en terminal

```bash
pytest apps/ --cov=apps --cov-report=term-missing -v
```

### Verifier la qualite du code

```bash
# Linting avec flake8
flake8 apps/

# Formatage avec black (verification sans modification)
black --check apps/

# Verification de l'ordre des imports
isort --check-only apps/
```

### Corriger automatiquement le formatage

```bash
# Formater le code avec black
black apps/

# Trier les imports avec isort
isort apps/
```

---

## Contribution

Merci de votre interet a contribuer a EgliseConnect! Voici les etapes a suivre :

### 1. Preparer votre environnement

```bash
# Forker et cloner le depot
git clone https://github.com/votre-compte/egliseconnect.git
cd egliseconnect

# Creer un environnement virtuel et installer les dependances
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Creer une branche

```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
```

Nommez votre branche selon la convention :

- `feature/description` pour une nouvelle fonctionnalite
- `fix/description` pour une correction de bogue
- `docs/description` pour la documentation
- `refactor/description` pour du refactoring

### 3. Ecrire du code de qualite

- Respectez le style de code existant (Python PEP 8)
- Utilisez `black` pour le formatage et `isort` pour les imports
- Ecrivez des tests pour toute nouvelle fonctionnalite ou correction
- Tous les textes visibles par l'utilisateur doivent etre en francais canadien
- Les commentaires de code et docstrings peuvent etre en anglais ou en francais

### 4. Verifier avant de soumettre

```bash
# Lancer les tests
pytest apps/ -v

# Verifier le formatage
black --check apps/
isort --check-only apps/
flake8 apps/
```

### 5. Soumettre une pull request

- Assurez-vous que tous les tests passent (1152 tests actuellement)
- Decrivez clairement les changements dans la description de la PR
- Referencez les issues pertinentes le cas echeant

### Conventions de code

| Element | Convention |
|---------|-----------|
| Langue de l'interface | Francais canadien (`fr-ca`) |
| Formatage Python | `black` (longueur de ligne par defaut) |
| Ordre des imports | `isort` (compatible avec `black`) |
| Linting | `flake8` |
| Tests | `pytest` avec `factory-boy` pour les fixtures |
| Modeles | Heritage depuis les modeles de base dans `apps/core/` |
| Vues frontend | Dans `views_frontend.py` |
| Vues API | Dans `views_api.py` |
| URLs frontend | Dans `urls_frontend.py` |
| URLs API | Dans `urls_api.py` |

---

## Licence

**Proprietaire** -- Tous droits reserves.

Ce logiciel est la propriete exclusive de ses auteurs. Toute reproduction, distribution ou modification sans autorisation prealable est interdite.

---

**EgliseConnect** -- Concu avec soin pour les eglises francophones du Canada.
Django 5.2 | Django REST Framework | Bootstrap 5 (W3CRM) | Celery | PostgreSQL
