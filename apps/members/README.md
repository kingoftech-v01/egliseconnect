# Application Members

Gestion des membres, familles et groupes pour le systeme **EgliseConnect**.

---

## Vue d'ensemble

> **Pour les non-techniciens :** L'application `members` est le coeur fonctionnel d'EgliseConnect. C'est ici que l'on gere les profils des membres de l'eglise, les familles, les groupes (cellules de maison, ministeres, comites), le repertoire de l'eglise et le suivi des anniversaires. Chaque membre recoit automatiquement un numero unique (par exemple `MBR-2026-0001`) lors de son inscription.

### Fonctionnalites principales

- **Profils de membres** -- Informations personnelles, coordonnees, photo, role dans l'eglise, dates d'adhesion et de bapteme.
- **Numeros de membre auto-generes** -- Format `MBR-YYYY-XXXX`, generes automatiquement et proteges contre les doublons.
- **Familles** -- Regroupement de membres par famille avec adresse partagee.
- **Groupes** -- Cellules, ministeres, comites, chorales et classes avec leaders designes et horaires de reunions.
- **Repertoire** -- Annuaire des membres avec parametres de confidentialite (public, groupe, prive).
- **Anniversaires** -- Suivi et affichage des anniversaires (aujourd'hui, semaine, mois, a venir).

---

## Modeles

### Member

Le modele principal de l'application. Herite de `SoftDeleteModel` (suppression logique avec possibilite de restauration).

> **Pour les non-techniciens :** Le profil d'un membre contient toutes ses informations personnelles. La suppression d'un membre ne detruit pas ses donnees -- elles sont conservees et peuvent etre restaurees en cas d'erreur.

#### Champs

| Champ | Type | Requis | Description |
| ----- | ---- | ------ | ----------- |
| `member_number` | `CharField(20)` | Auto | Numero unique genere automatiquement (`MBR-YYYY-XXXX`) |
| `user` | `OneToOneField(User)` | Non | Lien optionnel vers un compte Django pour l'authentification |
| `first_name` | `CharField(100)` | Oui | Prenom du membre |
| `last_name` | `CharField(100)` | Oui | Nom de famille |
| `email` | `EmailField` | Non | Adresse courriel |
| `phone` | `CharField(20)` | Non | Telephone principal |
| `phone_secondary` | `CharField(20)` | Non | Telephone secondaire |
| `birth_date` | `DateField` | Non | Date de naissance (pour le suivi des anniversaires) |
| `address` | `TextField` | Non | Adresse postale |
| `city` | `CharField(100)` | Non | Ville |
| `province` | `CharField(2)` | Oui | Province canadienne (defaut : `QC`) |
| `postal_code` | `CharField(10)` | Non | Code postal |
| `photo` | `ImageField` | Non | Photo de profil (max 5 Mo, JPEG/PNG/GIF/WebP) |
| `role` | `CharField(20)` | Oui | Role dans l'eglise (defaut : `member`) |
| `family_status` | `CharField(20)` | Oui | Etat civil (defaut : `single`) |
| `family` | `ForeignKey(Family)` | Non | Famille d'appartenance |
| `joined_date` | `DateField` | Non | Date d'adhesion a l'eglise |
| `baptism_date` | `DateField` | Non | Date de bapteme |
| `notes` | `TextField` | Non | Notes pastorales (visibles uniquement par l'equipe pastorale) |
| `is_active` | `BooleanField` | Oui | Herite de `BaseModel` (defaut : `True`) |

#### Proprietes

| Propriete | Retour | Description |
| --------- | ------ | ----------- |
| `full_name` | `str` | Prenom + Nom (ex : `"Jean Dupont"`) |
| `full_address` | `str` | Adresse formatee complete (adresse, ville, province, code postal) |
| `age` | `int` ou `None` | Age calcule a partir de la date de naissance |
| `is_staff_member` | `bool` | `True` si le role est Pastor ou Admin |
| `can_manage_finances` | `bool` | `True` si le role est Treasurer ou Admin |

#### Methodes

| Methode | Retour | Description |
| ------- | ------ | ----------- |
| `save()` | -- | Auto-genere `member_number` au premier enregistrement via `generate_member_number()` |
| `get_groups()` | `QuerySet[Group]` | Retourne tous les groupes actifs dont le membre fait partie |
| `delete()` | `tuple` | Suppression logique (heritee de `SoftDeleteModel`) |
| `restore()` | -- | Restauration d'un membre supprime logiquement |

#### Indexes de base de donnees

| Champs indexes | Utilisation |
| -------------- | ----------- |
| `member_number` | Recherche rapide par numero de membre |
| `email` | Recherche par courriel |
| `last_name, first_name` | Tri alphabetique optimise |
| `birth_date` | Requetes d'anniversaires |
| `role` | Filtrage par role |

```python
from apps.members.models import Member

# Creation (le numero est genere automatiquement)
membre = Member.objects.create(
    first_name='Marie',
    last_name='Tremblay',
    email='marie@example.com',
    phone='514-555-0199',
    province='QC',
)
print(membre.member_number)  # MBR-2026-0001
print(membre.full_name)      # Marie Tremblay

# Suppression logique et restauration
membre.delete()              # Soft delete
print(membre.is_deleted)     # True
membre.restore()             # Restauration
print(membre.is_deleted)     # False
```

---

### Family

Unite familiale regroupant des membres sous une adresse commune. Herite de `BaseModel`.

> **Pour les non-techniciens :** Une famille permet de regrouper les membres qui vivent ensemble et partagent la meme adresse. Cela evite de saisir l'adresse plusieurs fois et facilite le suivi des dons familiaux.

#### Champs de Family

| Champ | Type | Requis | Description |
| ----- | ---- | ------ | ----------- |
| `name` | `CharField(200)` | Oui | Nom de la famille (ex : `"Famille Dupont"`) |
| `address` | `TextField` | Non | Adresse partagee |
| `city` | `CharField(100)` | Non | Ville |
| `province` | `CharField(2)` | Oui | Province (defaut : `QC`) |
| `postal_code` | `CharField(10)` | Non | Code postal |
| `notes` | `TextField` | Non | Notes |

#### Proprietes de Family

| Propriete | Retour | Description |
| --------- | ------ | ----------- |
| `member_count` | `int` | Nombre de membres actifs dans la famille |
| `full_address` | `str` | Adresse formatee complete |

```python
from apps.members.models import Family, Member

famille = Family.objects.create(
    name='Famille Dupont',
    address='123 rue Principale',
    city='Montreal',
    province='QC',
    postal_code='H2X 1Y4',
)

# Associer un membre a la famille
membre = Member.objects.create(
    first_name='Jean',
    last_name='Dupont',
    family=famille,
)

print(famille.member_count)  # 1
print(famille.full_address)  # 123 rue Principale, Montreal, QC, H2X 1Y4
```

---

### Group

Groupe d'eglise (cellule, ministere, comite, classe, chorale). Herite de `BaseModel`.

> **Pour les non-techniciens :** Un groupe represente toute forme de rassemblement regulier au sein de l'eglise : cellule de maison, equipe de louange, comite de jeunesse, etc. Chaque groupe peut avoir un leader designe, un jour et lieu de reunion.

#### Champs de Group

| Champ | Type | Requis | Description |
| ----- | ---- | ------ | ----------- |
| `name` | `CharField(200)` | Oui | Nom du groupe |
| `group_type` | `CharField(20)` | Oui | Type : `cell`, `ministry`, `committee`, `class`, `choir`, `other` |
| `description` | `TextField` | Non | Description du groupe |
| `leader` | `ForeignKey(Member)` | Non | Leader du groupe (doit avoir le role `group_leader`, `pastor` ou `admin`) |
| `meeting_day` | `CharField(20)` | Non | Jour de reunion (ex : `"Mercredi"`) |
| `meeting_time` | `TimeField` | Non | Heure de reunion |
| `meeting_location` | `CharField(200)` | Non | Lieu de reunion |
| `email` | `EmailField` | Non | Courriel du groupe |

#### Proprietes de Group

| Propriete | Retour | Description |
| --------- | ------ | ----------- |
| `member_count` | `int` | Nombre de membres actifs dans le groupe |

```python
from apps.members.models import Group, Member

leader = Member.objects.get(last_name='Dupont', role='group_leader')

groupe = Group.objects.create(
    name='Cellule Centre-Ville',
    group_type='cell',
    leader=leader,
    meeting_day='Mercredi',
    meeting_time='19:00',
    meeting_location='Salle communautaire',
)
```

---

### GroupMembership

Table de jointure entre `Member` et `Group` avec role et date d'adhesion. Herite de `BaseModel`.

> **Pour les non-techniciens :** Ce modele enregistre l'appartenance d'un membre a un groupe, incluant son role dans le groupe (membre, leader, assistant) et la date a laquelle il a rejoint.

#### Champs de GroupMembership

| Champ | Type | Requis | Description |
| ----- | ---- | ------ | ----------- |
| `member` | `ForeignKey(Member)` | Oui | Le membre |
| `group` | `ForeignKey(Group)` | Oui | Le groupe |
| `role` | `CharField(20)` | Oui | Role dans le groupe : `member`, `leader`, `assistant` |
| `joined_date` | `DateField` | Auto | Date d'adhesion au groupe (auto) |
| `notes` | `TextField` | Non | Notes |

**Contrainte :** Un membre ne peut appartenir qu'une seule fois au meme groupe (`unique_together = ['member', 'group']`).

```python
from apps.members.models import GroupMembership

# Ajouter un membre a un groupe
GroupMembership.objects.create(
    member=membre,
    group=groupe,
    role='member',
)
```

---

### DirectoryPrivacy

Parametres de confidentialite controlant la visibilite des informations dans le repertoire. Herite de `BaseModel`. Relation `OneToOneField` avec `Member`.

> **Pour les non-techniciens :** Chaque membre peut choisir quelles informations les autres peuvent voir dans l'annuaire de l'eglise. Par exemple, un membre peut decider de rendre son profil visible uniquement aux personnes de ses groupes, et de masquer son adresse.

#### Champs de DirectoryPrivacy

| Champ | Type | Defaut | Description |
| ----- | ---- | ------ | ----------- |
| `member` | `OneToOneField(Member)` | -- | Le membre concerne |
| `visibility` | `CharField(20)` | `public` | Niveau de visibilite : `public`, `group`, `private` |
| `show_email` | `BooleanField` | `True` | Afficher le courriel dans le repertoire |
| `show_phone` | `BooleanField` | `True` | Afficher le telephone |
| `show_address` | `BooleanField` | `False` | Afficher l'adresse |
| `show_birth_date` | `BooleanField` | `True` | Afficher la date de naissance |
| `show_photo` | `BooleanField` | `True` | Afficher la photo |

#### Niveaux de visibilite

| Niveau | Description |
| ------ | ----------- |
| `public` | Visible par tous les membres de l'eglise |
| `group` | Visible uniquement par les membres qui partagent au moins un groupe |
| `private` | Visible uniquement par l'equipe pastorale (pasteurs et administrateurs) |

```python
from apps.members.models import DirectoryPrivacy

# Configurer la confidentialite d'un membre
DirectoryPrivacy.objects.create(
    member=membre,
    visibility='group',
    show_email=True,
    show_phone=True,
    show_address=False,
    show_birth_date=True,
    show_photo=True,
)
```

---

## Formulaires

Tous les formulaires utilisent le `W3CRMFormMixin` (voir `apps/core/README.md`) pour appliquer automatiquement les classes CSS Bootstrap aux widgets.

### Vue d'ensemble des formulaires

| Formulaire | Modele | Utilisation | Utilisateurs cibles |
| ---------- | ------ | ----------- | ------------------- |
| `MemberRegistrationForm` | `Member` | Inscription publique avec creation de compte optionnelle | Nouveaux membres |
| `MemberProfileForm` | `Member` | Mise a jour du profil par le membre lui-meme | Membres connectes |
| `MemberAdminForm` | `Member` | Edition complete par le personnel pastoral | Pasteurs, admins |
| `FamilyForm` | `Family` | Creation et edition de familles | Pasteurs, admins |
| `GroupForm` | `Group` | Creation et edition de groupes | Pasteurs, admins |
| `GroupMembershipForm` | `GroupMembership` | Ajout de membres a un groupe | Pasteurs, admins |
| `DirectoryPrivacyForm` | `DirectoryPrivacy` | Parametres de confidentialite du repertoire | Membres connectes |
| `MemberSearchForm` | -- (Form) | Recherche et filtrage de la liste des membres | Tous les utilisateurs autorises |

### Details des formulaires

#### MemberRegistrationForm

Formulaire d'inscription publique. Collecte les informations essentielles et peut optionnellement creer un compte utilisateur Django.

**Champs du formulaire :**
`first_name`, `last_name`, `email`, `phone`, `birth_date`, `address`, `city`, `province`, `postal_code`, `family_status`

**Champs supplementaires :**

- `create_account` (`BooleanField`, defaut : `True`) -- Option pour creer un compte de connexion
- `password` / `password_confirm` -- Requis si `create_account` est coche

**Logique de sauvegarde :**

1. Cree le profil `Member` (le `member_number` est genere automatiquement)
2. Si `create_account` est coche : cree un `User` Django avec le courriel comme nom d'utilisateur
3. Cree automatiquement un enregistrement `DirectoryPrivacy` par defaut

**Validations :**

- Unicite du courriel si un compte est cree
- Validation du mot de passe via les validateurs Django standard
- Concordance des deux mots de passe

```python
from apps.members.forms import MemberRegistrationForm

form = MemberRegistrationForm(data={
    'first_name': 'Marie',
    'last_name': 'Tremblay',
    'email': 'marie@eglise.ca',
    'phone': '514-555-0199',
    'birth_date': '1990-05-15',
    'province': 'QC',
    'family_status': 'single',
    'create_account': True,
    'password': 'MotDePasse123!',
    'password_confirm': 'MotDePasse123!',
})

if form.is_valid():
    member = form.save()
    # member.member_number == 'MBR-2026-0001'
    # member.user est cree avec email comme username
    # DirectoryPrivacy cree automatiquement
```

#### MemberProfileForm

Formulaire en libre-service pour que les membres mettent a jour leur propre profil. Exclut les champs sensibles (`role`, `notes`, `is_active`, `family`, `joined_date`, `baptism_date`).

**Champs :** `first_name`, `last_name`, `email`, `phone`, `phone_secondary`, `birth_date`, `address`, `city`, `province`, `postal_code`, `photo`, `family_status`

#### MemberAdminForm

Formulaire complet pour le personnel pastoral et administratif. Inclut tous les champs, y compris le role, les notes pastorales et le drapeau actif.

**Champs :** Tous les champs de `MemberProfileForm` + `role`, `family`, `joined_date`, `baptism_date`, `notes`, `is_active`

#### GroupForm

Formulaire de creation/edition de groupes. Le champ `leader` est filtre pour n'afficher que les membres ayant le role `group_leader`, `pastor` ou `admin`.

**Champs :** `name`, `group_type`, `description`, `leader`, `meeting_day`, `meeting_time`, `meeting_location`, `email`

```python
from apps.members.forms import GroupForm

form = GroupForm()
# form.fields['leader'].queryset contient uniquement les members
# avec role in ['group_leader', 'pastor', 'admin']
```

#### MemberSearchForm

Formulaire de recherche et filtrage (basee sur `forms.Form`, pas `ModelForm`).

**Champs de filtre :**

| Champ | Type | Description |
| ----- | ---- | ----------- |
| `search` | `CharField` | Recherche textuelle (nom, courriel, numero) |
| `role` | `ChoiceField` | Filtrer par role (avec option "Tous les roles") |
| `family_status` | `ChoiceField` | Filtrer par etat civil |
| `group` | `ModelChoiceField` | Filtrer par appartenance a un groupe |
| `birth_month` | `ChoiceField` | Filtrer par mois de naissance (janvier a decembre) |

---

## Endpoints API

L'API REST est construite avec Django REST Framework et utilise des ViewSets avec routeur automatique.

### Membres (`MemberViewSet`)

| Methode | URL | Description | Permission |
| ------- | --- | ----------- | ---------- |
| `GET` | `/api/v1/members/members/` | Liste des membres (filtree par role) | `IsMember` (authentifie) |
| `POST` | `/api/v1/members/members/` | Inscription d'un nouveau membre | Public (aucune) |
| `GET` | `/api/v1/members/members/{uuid}/` | Detail d'un membre | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/members/{uuid}/` | Mise a jour d'un membre | `IsOwnerOrStaff` |
| `DELETE` | `/api/v1/members/members/{uuid}/` | Supprimer un membre | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/members/me/` | Profil du membre connecte | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/members/me/` | Modifier son propre profil | `IsMember` |
| `GET` | `/api/v1/members/members/birthdays/` | Anniversaires (filtre `?period=today/week/month`) | `IsMember` |
| `GET` | `/api/v1/members/members/directory/` | Repertoire avec confidentialite appliquee | `IsMember` |

**Filtres disponibles :** `role`, `family_status`, `family`, `is_active`
**Recherche :** `first_name`, `last_name`, `email`, `member_number`, `phone`
**Tri :** `last_name`, `first_name`, `created_at`, `birth_date`

#### Visibilite des donnees selon le role

| Role | Donnees visibles dans la liste |
| ---- | ------------------------------ |
| Admin / Pastor | Tous les membres |
| Group Leader | Ses propres donnees + les membres de ses groupes |
| Membre / Volontaire | Ses propres donnees uniquement |

#### Serializers utilises selon l'action

| Action | Serializer |
| ------ | ---------- |
| `list` | `MemberListSerializer` (resume) |
| `create` | `MemberCreateSerializer` |
| `retrieve` | `MemberSerializer` (complet) |
| `update/partial_update` (staff) | `MemberAdminSerializer` |
| `update/partial_update` (membre) | `MemberProfileSerializer` |
| `birthdays` | `BirthdaySerializer` |
| `directory` | `DirectoryMemberSerializer` |

### Familles (`FamilyViewSet`)

| Methode | URL | Description | Permission |
| ------- | --- | ----------- | ---------- |
| `GET` | `/api/v1/members/families/` | Liste des familles | `IsMember` |
| `POST` | `/api/v1/members/families/` | Creer une famille | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/families/{uuid}/` | Detail d'une famille | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/families/{uuid}/` | Modifier une famille | `IsPastorOrAdmin` |

**Recherche :** `name`, `city`
**Tri :** `name`, `created_at`

### Groupes (`GroupViewSet`)

| Methode | URL | Description | Permission |
| ------- | --- | ----------- | ---------- |
| `GET` | `/api/v1/members/groups/` | Liste des groupes | `IsMember` |
| `POST` | `/api/v1/members/groups/` | Creer un groupe | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/groups/{uuid}/` | Detail d'un groupe | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/groups/{uuid}/` | Modifier un groupe | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/members/groups/{uuid}/` | Supprimer un groupe | `IsPastorOrAdmin` |
| `GET` | `/api/v1/members/groups/{uuid}/members/` | Membres du groupe | `IsMember` |
| `POST` | `/api/v1/members/groups/{uuid}/add-member/` | Ajouter un membre au groupe | `IsPastorOrAdmin` |
| `POST` | `/api/v1/members/groups/{uuid}/remove-member/` | Retirer un membre du groupe | `IsPastorOrAdmin` |

**Filtres :** `group_type`, `leader`, `is_active`
**Recherche :** `name`, `description`
**Tri :** `name`, `created_at`

### Confidentialite (`DirectoryPrivacyViewSet`)

| Methode | URL | Description | Permission |
| ------- | --- | ----------- | ---------- |
| `GET` | `/api/v1/members/privacy/` | Parametres de confidentialite | `IsMember` |
| `GET` | `/api/v1/members/privacy/me/` | Mes parametres | `IsMember` |
| `PUT/PATCH` | `/api/v1/members/privacy/me/` | Modifier mes parametres | `IsMember` |

> **Note :** Les membres reguliers ne voient que leurs propres parametres. Le personnel (staff) voit tous les parametres.

---

## URLs frontend

Les pages HTML du frontend accessibles par les utilisateurs.

| URL | Vue | Description | Acces |
| --- | --- | ----------- | ----- |
| `/members/` | `member_list` | Liste de tous les membres | Personnel pastoral |
| `/members/register/` | `member_create` | Formulaire d'inscription | Public |
| `/members/{uuid}/` | `member_detail` | Profil detaille d'un membre | Membre concerne ou staff |
| `/members/{uuid}/edit/` | `member_update` | Modifier un profil | Membre concerne ou staff |
| `/members/birthdays/` | `birthday_list` | Liste des anniversaires | Membres connectes |
| `/members/directory/` | `directory` | Repertoire des membres | Membres connectes |
| `/members/privacy-settings/` | `privacy_settings` | Parametres de confidentialite | Membre connecte |
| `/members/groups/` | `group_list` | Liste des groupes | Membres connectes |
| `/members/groups/{uuid}/` | `group_detail` | Detail d'un groupe | Membres connectes |
| `/members/families/{uuid}/` | `family_detail` | Detail d'une famille | Membres connectes |

---

## Templates

Les fichiers de templates HTML se trouvent dans `templates/members/`.

| Template | Description | Contexte principal |
| -------- | ----------- | ------------------ |
| `member_list.html` | Tableau des membres avec recherche et filtres | Liste de `Member`, formulaire `MemberSearchForm` |
| `member_detail.html` | Page de profil detaille d'un membre | Instance `Member`, groupes, famille |
| `member_form.html` | Formulaire de creation et d'edition (partage) | `MemberRegistrationForm`, `MemberProfileForm` ou `MemberAdminForm` |
| `birthday_list.html` | Liste des anniversaires par periode | Membres avec anniversaires |
| `directory.html` | Repertoire des membres avec confidentialite | Membres filtres selon la confidentialite |
| `privacy_settings.html` | Formulaire de parametres de confidentialite | `DirectoryPrivacyForm` |
| `group_list.html` | Liste de tous les groupes | Liste de `Group` |
| `group_detail.html` | Detail d'un groupe avec ses membres | Instance `Group`, memberships |
| `family_detail.html` | Detail d'une famille avec ses membres | Instance `Family`, membres associes |

---

## Exemples d'utilisation complets

### Inscription d'un nouveau membre via l'API

```python
import requests

response = requests.post('http://localhost:8000/api/v1/members/members/', json={
    'first_name': 'Pierre',
    'last_name': 'Martin',
    'email': 'pierre@example.com',
    'phone': '514-555-0100',
    'birth_date': '1985-03-22',
    'province': 'QC',
    'family_status': 'married',
})

# Reponse : 201 Created
# {
#     "id": "a1b2c3d4-...",
#     "member_number": "MBR-2026-0003",
#     "first_name": "Pierre",
#     "last_name": "Martin",
#     ...
# }
```

### Gestion des groupes via l'API

```python
import requests

headers = {'Authorization': 'Token pastor_token_ici'}

# Creer un groupe
response = requests.post(
    'http://localhost:8000/api/v1/members/groups/',
    headers=headers,
    json={
        'name': 'Cellule Rive-Sud',
        'group_type': 'cell',
        'leader': 'uuid-du-leader',
        'meeting_day': 'Jeudi',
        'meeting_time': '19:30',
    },
)

# Ajouter un membre au groupe
group_id = response.json()['id']
requests.post(
    f'http://localhost:8000/api/v1/members/groups/{group_id}/add-member/',
    headers=headers,
    json={'member': 'uuid-du-membre', 'role': 'member'},
)
```

### Consulter les anniversaires

```python
import requests

headers = {'Authorization': 'Token mon_token'}

# Anniversaires de la semaine
response = requests.get(
    'http://localhost:8000/api/v1/members/members/birthdays/?period=week',
    headers=headers,
)

# Anniversaires d'un mois specifique
response = requests.get(
    'http://localhost:8000/api/v1/members/members/birthdays/?period=month&month=12',
    headers=headers,
)
```

### Utilisation du repertoire avec confidentialite

```python
import requests

headers = {'Authorization': 'Token mon_token'}

# Rechercher dans le repertoire
response = requests.get(
    'http://localhost:8000/api/v1/members/members/directory/?search=Dupont',
    headers=headers,
)
# Seuls les membres dont la confidentialite autorise la visibilite seront retournes
```

### Creer une vue frontend avec mixins

```python
from django.views.generic import ListView
from apps.core.mixins import (
    PastorRequiredMixin,
    ChurchContextMixin,
    PageTitleMixin,
    BreadcrumbMixin,
)
from apps.members.models import Member

class ListeMembresView(
    PastorRequiredMixin,
    ChurchContextMixin,
    PageTitleMixin,
    BreadcrumbMixin,
    ListView,
):
    model = Member
    template_name = 'members/member_list.html'
    context_object_name = 'members'
    page_title = "Liste des membres"

    def get_breadcrumbs(self):
        return [
            ('Accueil', '/'),
            ('Membres', None),
        ]
```

---

## Tests

Lancer les tests de l'application `members` :

```bash
# Tous les tests members
pytest apps/members/ -v

# Tests specifiques par categorie
pytest apps/members/ -v -k "test_member_model"
pytest apps/members/ -v -k "test_member_api"
pytest apps/members/ -v -k "test_group"
pytest apps/members/ -v -k "test_family"
pytest apps/members/ -v -k "test_privacy"
pytest apps/members/ -v -k "test_forms"

# Avec couverture de code
pytest apps/members/ -v --cov=apps.members --cov-report=html
```

### Scenarios de tests recommandes

#### Tests des modeles

- Creation de membre avec generation automatique du numero
- Suppression logique et restauration
- Calcul de l'age et des proprietes
- Contrainte d'unicite `member_number`
- Contrainte `unique_together` sur `GroupMembership`

#### Tests de l'API

- Inscription publique (POST sans authentification)
- Visibilite des donnees par role (admin voit tout, membre voit seulement lui-meme)
- Endpoint `/me/` pour le profil de l'utilisateur connecte
- Filtres, recherche et tri
- Gestion des groupes (ajout/retrait de membres)
- Confidentialite du repertoire (public, group, private)
- Gestion des anniversaires par periode

#### Tests des formulaires

- Validation de `MemberRegistrationForm` avec creation de compte
- Validation des mots de passe (concordance, force)
- Filtrage du champ `leader` dans `GroupForm`
- Application automatique des classes CSS par `W3CRMFormMixin`

---

## Arborescence des fichiers

```text
apps/members/
    __init__.py
    admin.py               # Configuration Django admin
    forms.py               # 8 formulaires (tous avec W3CRMFormMixin)
    models.py              # Member, Family, Group, GroupMembership, DirectoryPrivacy
    serializers.py         # Serializers DRF (Member*, Family*, Group*, etc.)
    urls.py                # Routeur API + URLs frontend
    views_api.py           # ViewSets DRF (Member, Family, Group, DirectoryPrivacy)
    views_frontend.py      # Vues frontend (templates HTML)

templates/members/
    birthday_list.html
    directory.html
    family_detail.html
    group_detail.html
    group_list.html
    member_detail.html
    member_form.html
    member_list.html
    privacy_settings.html
```
