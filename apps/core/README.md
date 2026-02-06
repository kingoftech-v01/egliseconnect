# Application Core

Infrastructure de base pour le systeme de gestion d'eglise **EgliseConnect**.

---

## Vue d'ensemble

> **Pour les non-techniciens :** L'application `core` est la fondation sur laquelle repose tout le systeme EgliseConnect. Elle ne contient aucune fonctionnalite visible directement par les utilisateurs, mais elle fournit les outils et les regles communes que toutes les autres applications (membres, dons, evenements, etc.) utilisent. Pensez-y comme le "code de construction" d'un edifice : on ne le voit pas, mais il assure que tout est solide et uniforme.

### Ce que `core` fournit :

- **Modeles de base** -- Chaque enregistrement dans la base de donnees recoit automatiquement un identifiant unique (UUID), des horodatages de creation/modification, et un drapeau actif/inactif.
- **Constantes centralisees** -- Toutes les listes de choix (roles, statuts, provinces, etc.) sont definies a un seul endroit pour garantir la coherence.
- **Permissions** -- Regles de controle d'acces basees sur les roles (membre, volontaire, pasteur, tresorier, admin).
- **Mixins de vues** -- Composants reutilisables pour les pages web (verification de role, messages de succes/erreur, titre de page, fil d'Ariane).
- **Utilitaires** -- Fonctions d'aide pour la generation de numeros, le suivi des anniversaires, le formatage de donnees.
- **Validateurs** -- Validation de fichiers (images, PDF) avec limites de taille et types acceptes.

---

## Composants detailles

### 1. Modeles (`models.py`)

Les modeles abstraits fournissent les champs communs herites par tous les modeles concrets du projet.

#### Managers

| Manager | Description | Utilisation |
|---------|-------------|-------------|
| `ActiveManager` | Retourne uniquement les objets actifs (`is_active=True`) | Manager par defaut de `BaseModel` |
| `SoftDeleteManager` | Retourne uniquement les objets non supprimes (`deleted_at IS NULL`) | Manager par defaut de `SoftDeleteModel` |
| `AllObjectsManager` | Retourne tous les objets, incluant les inactifs et supprimes | Utilise pour l'admin, les rapports, la recuperation |

#### BaseModel

Modele abstrait de base utilise par la majorite des entites du systeme.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` (PK) | Identifiant unique genere automatiquement (UUID v4) |
| `created_at` | `DateTimeField` | Date de creation (auto) |
| `updated_at` | `DateTimeField` | Date de derniere modification (auto) |
| `is_active` | `BooleanField` | Drapeau actif/inactif (defaut: `True`) |

**Methodes :**
- `deactivate()` -- Desactive l'enregistrement
- `activate()` -- Reactive l'enregistrement

**Managers :**
- `objects` -- `ActiveManager` (seulement les actifs)
- `all_objects` -- `AllObjectsManager` (tout inclus)

```python
from apps.core.models import BaseModel

class Evenement(BaseModel):
    nom = models.CharField(max_length=200)
    # Herite automatiquement: id (UUID), created_at, updated_at, is_active

    class Meta:
        verbose_name = 'Evenement'
```

#### SoftDeleteModel

Etend `BaseModel` avec la suppression logique (soft delete). Au lieu de supprimer physiquement un enregistrement de la base de donnees, on marque la date de suppression. Cela permet de recuperer des donnees supprimees accidentellement et de conserver un historique pour les audits.

| Champ supplementaire | Type | Description |
|---------------------|------|-------------|
| `deleted_at` | `DateTimeField` (nullable) | Date de suppression logique |

**Methodes :**
- `delete()` -- Suppression logique (marque `deleted_at`, desactive)
- `delete(hard_delete=True)` -- Suppression physique reelle de la base de donnees
- `restore()` -- Restaure un enregistrement supprime (remet `deleted_at=None`, reactive)
- `hard_delete()` -- Alias pour la suppression physique

**Propriete :**
- `is_deleted` -- Retourne `True` si l'enregistrement a ete supprime logiquement

```python
from apps.core.models import SoftDeleteModel

class Membre(SoftDeleteModel):
    prenom = models.CharField(max_length=100)

# Suppression logique (les donnees restent en base)
membre.delete()
print(membre.is_deleted)   # True
print(membre.deleted_at)   # 2026-02-06 14:30:00+00:00

# Restauration
membre.restore()
print(membre.is_deleted)   # False

# Suppression definitive (irrecuperable)
membre.hard_delete()
```

#### TimeStampedMixin

Mixin leger qui ajoute uniquement les horodatages `created_at` et `updated_at`, sans UUID ni drapeau `is_active`. Utile pour les modeles de jointure ou les modeles secondaires qui n'ont pas besoin d'un UUID comme cle primaire.

```python
from apps.core.models import TimeStampedMixin

class JournalActivite(TimeStampedMixin):
    action = models.CharField(max_length=200)
    # Utilise la cle primaire auto-increment standard de Django
```

#### OrderedMixin

Ajoute un champ `order` (`PositiveIntegerField`, defaut `0`) pour permettre le tri manuel des enregistrements. Le `Meta.ordering` est configure sur `['order']`.

```python
from apps.core.models import BaseModel, OrderedMixin

class ElementMenu(BaseModel, OrderedMixin):
    titre = models.CharField(max_length=100)
    # Herite de: id, created_at, updated_at, is_active, order
```

---

### 2. Constantes (`constants.py`)

Toutes les listes de choix et enumerations du systeme sont centralisees ici. Chaque constante est une classe Python contenant les valeurs possibles et une liste `CHOICES` compatible avec les champs Django.

> **Pour les non-techniciens :** Ce fichier est comme un dictionnaire de reference. Au lieu de taper "pasteur" ou "pastor" a differents endroits (avec des risques de fautes), on definit chaque option une seule fois ici et on la reutilise partout.

#### Roles

| Constante | Valeur | Libelle francais | Description |
|-----------|--------|-----------------|-------------|
| `Roles.MEMBER` | `'member'` | Membre | Role de base, tout utilisateur authentifie |
| `Roles.VOLUNTEER` | `'volunteer'` | Volontaire | Benevole participant aux activites |
| `Roles.GROUP_LEADER` | `'group_leader'` | Leader de groupe | Responsable d'un groupe/cellule |
| `Roles.PASTOR` | `'pastor'` | Pasteur | Equipe pastorale, acces elargi |
| `Roles.TREASURER` | `'treasurer'` | Tresorier | Acces aux donnees financieres |
| `Roles.ADMIN` | `'admin'` | Administrateur | Acces complet au systeme |

**Groupes de permissions predefinis :**
- `Roles.STAFF_ROLES` = `[PASTOR, ADMIN]`
- `Roles.VIEW_ALL_ROLES` = `[PASTOR, TREASURER, ADMIN]`
- `Roles.FINANCE_ROLES` = `[TREASURER, ADMIN]`

#### Toutes les constantes

| Classe | Valeurs | Utilisation |
|--------|---------|-------------|
| `FamilyStatus` | `single`, `married`, `widowed`, `divorced` | Etat civil des membres |
| `GroupType` | `cell`, `ministry`, `committee`, `class`, `choir`, `other` | Categories de groupes d'eglise |
| `PrivacyLevel` | `public`, `group`, `private` | Visibilite du profil dans le repertoire |
| `DonationType` | `tithe`, `offering`, `special`, `campaign`, `building`, `missions`, `other` | Categories de dons |
| `PaymentMethod` | `cash`, `check`, `card`, `bank_transfer`, `online`, `other` | Modes de paiement |
| `EventType` | `worship`, `group`, `meal`, `special`, `meeting`, `training`, `outreach`, `other` | Types d'evenements |
| `RSVPStatus` | `pending`, `confirmed`, `declined`, `maybe` | Reponses de presence |
| `VolunteerRole` | `worship`, `hospitality`, `technical`, `children`, `youth`, `admin`, `outreach`, `other` | Domaines de benevolat |
| `VolunteerFrequency` | `weekly`, `biweekly`, `monthly`, `occasional` | Frequence de disponibilite |
| `ScheduleStatus` | `scheduled`, `confirmed`, `declined`, `completed`, `no_show` | Etats d'affectation de benevoles |
| `HelpRequestCategory` | `prayer`, `financial`, `material`, `pastoral`, `transport`, `medical`, `other` | Types de demandes d'aide |
| `HelpRequestUrgency` | `low`, `medium`, `high`, `urgent` | Niveaux de priorite (TextChoices) |
| `HelpRequestStatus` | `new`, `in_progress`, `resolved`, `closed` | Etats du workflow (TextChoices) |
| `NewsletterStatus` | `draft`, `scheduled`, `sending`, `sent`, `failed` | Etats d'envoi de l'infolettre |
| `NotificationType` | `birthday`, `event`, `volunteer`, `help_request`, `donation`, `general` | Categories de notifications |
| `Province` | `AB`, `BC`, `MB`, `NB`, `NL`, `NS`, `NT`, `NU`, `ON`, `PE`, `QC`, `SK`, `YT` | Provinces et territoires canadiens |

> **Note :** `Urgency` et `RequestStatus` sont des alias de retrocompatibilite pour `HelpRequestUrgency` et `HelpRequestStatus` respectivement.

```python
from apps.core.constants import Roles, DonationType, Province

# Utilisation dans un modele
class Don(models.Model):
    type_don = models.CharField(max_length=20, choices=DonationType.CHOICES, default=DonationType.OFFERING)
    province = models.CharField(max_length=2, choices=Province.CHOICES, default=Province.QC)

# Verification de role
if membre.role in Roles.FINANCE_ROLES:
    print("Acces aux finances autorise")
```

---

### 3. Permissions (`permissions.py`)

Classes de permission pour Django REST Framework (DRF) implementant le controle d'acces base sur les roles (RBAC).

> **Pour les non-techniciens :** Les permissions sont comme des badges d'acces. Chaque page ou fonctionnalite de l'API verifie si l'utilisateur a le bon "badge" (role) avant de lui donner acces.

#### Classes de permission

| Classe | Niveau requis | Description |
|--------|--------------|-------------|
| `IsMember` | Tout utilisateur authentifie | Verifie simplement que l'utilisateur est connecte |
| `IsVolunteer` | Volontaire ou superieur | Volunteer, Group Leader, Pastor, Treasurer, Admin |
| `IsGroupLeader` | Leader de groupe ou superieur | Group Leader, Pastor, Admin |
| `IsPastor` | Pasteur ou admin | Pastor, Admin |
| `IsTreasurer` | Tresorier ou admin | Treasurer, Admin |
| `IsAdmin` | Administrateur seulement | Admin ou superuser Django |
| `IsPastorOrAdmin` | Pasteur ou admin | Utilise `Roles.STAFF_ROLES` |
| `IsFinanceStaff` | Equipe financiere | Treasurer, Pastor, Admin |
| `IsOwnerOrStaff` | Proprietaire de l'objet ou staff | Permission au niveau objet (object-level) |
| `IsOwnerOrReadOnly` | Proprietaire pour ecrire, tous pour lire | Lecture pour tous, ecriture pour le proprietaire |
| `CanViewMember` | Selon les parametres de confidentialite | Respecte les niveaux `public`/`group`/`private` |

#### Fonctions utilitaires

| Fonction | Description | Retour |
|----------|-------------|--------|
| `get_user_role(user)` | Retourne le role de l'utilisateur sous forme de chaine | `str` ou `None` |
| `is_staff_member(user)` | Verifie si l'utilisateur a un acces staff | `bool` |
| `can_manage_finances(user)` | Verifie l'acces aux donnees financieres | `bool` |

#### Hierarchie des roles

La hierarchie des permissions est inclusive vers le haut :

```text
Admin
  |-- Pastor
  |     |-- Group Leader
  |     |     |-- Volunteer
  |     |           |-- Member (tout authentifie)
  |-- Treasurer (acces finances, independant de la hierarchie pastorale)
```

```python
# Utilisation dans un ViewSet DRF
from rest_framework import viewsets
from apps.core.permissions import IsPastorOrAdmin, IsFinanceStaff

class DonViewSet(viewsets.ModelViewSet):
    permission_classes = [IsFinanceStaff]

# Utilisation de CanViewMember (permission au niveau objet)
class ProfilMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsMember]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj
```

---

### 4. Mixins (`mixins.py`)

Composants reutilisables pour les vues Django basees sur les classes (CBV). Les mixins sont organises en quatre categories.

> **Pour les non-techniciens :** Un mixin est un "module" reutilisable qu'on ajoute a une page web. Par exemple, au lieu de reecrire le code "verifier si l'utilisateur est pasteur" sur chaque page, on ajoute simplement `PastorRequiredMixin` et c'est fait.

#### Mixins de permission

Equivalent des classes de permission DRF, mais pour les vues frontend Django (templates HTML).

| Mixin | Role requis | Comportement si refuse |
|-------|------------|----------------------|
| `MemberRequiredMixin` | Utilisateur avec profil membre | Redirige vers la creation de profil |
| `VolunteerRequiredMixin` | Volontaire ou superieur | Message d'erreur + redirection |
| `GroupLeaderRequiredMixin` | Leader de groupe ou superieur | Message d'erreur + redirection vers `/` |
| `PastorRequiredMixin` | Pasteur ou admin | Message d'erreur + redirection vers `/` |
| `TreasurerRequiredMixin` | Tresorier ou admin | Message d'erreur + redirection vers `/` |
| `AdminRequiredMixin` | Admin ou superuser | Message d'erreur + redirection vers `/` |
| `FinanceStaffRequiredMixin` | Tresorier, pasteur ou admin | Message d'erreur + redirection vers `/` |
| `OwnerOrStaffRequiredMixin` | Proprietaire ou staff | Message d'erreur + redirection vers `/` |

```python
from django.views.generic import ListView
from apps.core.mixins import PastorRequiredMixin, ChurchContextMixin

class ListeMembresView(PastorRequiredMixin, ChurchContextMixin, ListView):
    model = Member
    template_name = 'members/member_list.html'
    # Seuls les pasteurs et admins pourront voir cette page
```

#### Mixins de contexte

Ajoutent des donnees au contexte du template automatiquement.

| Mixin | Variables ajoutees | Description |
|-------|-------------------|-------------|
| `ChurchContextMixin` | `current_user_role`, `current_member`, `today_birthdays` | Contexte global d'eglise. Les anniversaires sont affiches uniquement pour Pastor/Admin/GroupLeader (max 5). |
| `PageTitleMixin` | `page_title` | Titre de page via attribut ou `get_page_title()` |
| `BreadcrumbMixin` | `breadcrumbs` | Fil d'Ariane via `get_breadcrumbs()` retournant `[(label, url), ...]` |

```python
from apps.core.mixins import PageTitleMixin, BreadcrumbMixin

class DetailMembreView(PageTitleMixin, BreadcrumbMixin, DetailView):
    page_title = "Profil du membre"

    def get_breadcrumbs(self):
        return [
            ('Membres', '/members/'),
            (self.object.full_name, None),  # Dernier element sans lien
        ]
```

#### Mixins de formulaire

| Mixin | Description |
|-------|-------------|
| `FormMessageMixin` | Affiche un message de succes (`messages.success`) apres `form_valid()` et un message d'erreur (`messages.error`) apres `form_invalid()`. Personnalisable via `success_message` et `error_message`. |
| `SetOwnerMixin` | Assigne automatiquement le champ `member`, `user` ou `created_by` de l'instance du formulaire a l'utilisateur connecte, si le champ existe et n'est pas deja rempli. |

```python
from django.views.generic import CreateView
from apps.core.mixins import FormMessageMixin, SetOwnerMixin, MemberRequiredMixin

class CreerDemandeView(MemberRequiredMixin, FormMessageMixin, SetOwnerMixin, CreateView):
    model = DemandeAide
    fields = ['categorie', 'description', 'urgence']
    success_message = "Votre demande a ete soumise avec succes."
    # SetOwnerMixin va automatiquement mettre request.user.member_profile dans le champ 'member'
```

#### Mixin de queryset

| Mixin | Description |
|-------|-------------|
| `FilterByMemberMixin` | Filtre le queryset pour ne montrer que les objets du membre connecte. Les utilisateurs staff et les roles `STAFF_ROLES` (Pastor, Admin) voient tous les objets. Si le modele n'a pas d'attribut `member`, retourne un queryset vide pour les non-staff. |

```python
from django.views.generic import ListView
from apps.core.mixins import FilterByMemberMixin, MemberRequiredMixin

class MesDonsView(MemberRequiredMixin, FilterByMemberMixin, ListView):
    model = Don
    template_name = 'donations/mes_dons.html'
    # Un membre voit uniquement SES dons ; un pasteur/admin voit TOUS les dons
```

---

### 5. W3CRMFormMixin -- Stylisation automatique des formulaires

> **Section speciale :** Ce mixin est un ajout recent qui simplifie considerablement la creation de formulaires dans EgliseConnect.

#### Le probleme

Dans Django, les widgets de formulaire sont rendus en HTML brut sans classes CSS. Pour utiliser Bootstrap (ou le theme W3CRM), il faut normalement ajouter manuellement la classe CSS appropriee a **chaque** champ de **chaque** formulaire :

```python
# AVANT (approche manuelle et repetitive) :
class MonFormulaire(forms.ModelForm):
    class Meta:
        model = MonModele
        fields = ['nom', 'courriel', 'province', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'courriel': forms.EmailInput(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-select'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
```

#### La solution : W3CRMFormMixin

Le mixin parcourt automatiquement tous les champs du formulaire lors de l'initialisation (`__init__`) et ajoute la classe CSS Bootstrap appropriee selon le type de widget.

#### Correspondance widget / classe CSS

| Type de widget Django | Classe CSS ajoutee |
|----------------------|-------------------|
| `TextInput` | `form-control` |
| `NumberInput` | `form-control` |
| `EmailInput` | `form-control` |
| `PasswordInput` | `form-control` |
| `DateInput` | `form-control` |
| `DateTimeInput` | `form-control` |
| `TimeInput` | `form-control` |
| `Textarea` | `form-control` |
| `URLInput` | `form-control` |
| `FileInput` | `form-control` |
| `ClearableFileInput` | `form-control` |
| `Select` | `form-select` |
| `SelectMultiple` | `form-select` |
| `CheckboxInput` | `form-check-input` |

#### Utilisation

```python
from apps.core.mixins import W3CRMFormMixin

# APRES (propre et automatique) :
class MonFormulaire(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = MonModele
        fields = ['nom', 'courriel', 'province', 'actif']
    # C'est tout ! Les classes CSS sont ajoutees automatiquement.
```

#### Comportement detaille

1. Le mixin **ne remplace pas** les classes CSS existantes -- il les **complete**.
2. Si un widget a deja la classe appropriee, elle n'est pas ajoutee en double.
3. Le mixin est place **avant** `forms.ModelForm` ou `forms.Form` dans l'ordre d'heritage (MRO Python).

```python
# Exemple avec classes CSS personnalisees additionnelles :
class FormulaireAvance(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = MonModele
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'ma-classe-custom',  # Sera conservee
                'rows': 5,
            }),
        }
    # Resultat HTML : class="ma-classe-custom form-control"
```

#### Tous les formulaires du projet utilisent ce mixin

Chaque formulaire dans EgliseConnect herite de `W3CRMFormMixin` pour assurer un rendu visuel coherent. Si vous creez un nouveau formulaire, **ajoutez toujours** ce mixin :

```python
class NouveauFormulaire(W3CRMFormMixin, forms.ModelForm):
    # ...
```

---

### 6. Validateurs (`validators.py`)

Fonctions de validation reutilisables pour les telechargements de fichiers.

| Validateur | Types acceptes | Taille max | Description |
|-----------|---------------|-----------|-------------|
| `validate_image_file` | JPEG, PNG, GIF, WebP | 5 Mo | Validation des photos de profil et images |
| `validate_pdf_file` | PDF | 10 Mo | Validation des documents PDF |

```python
from apps.core.validators import validate_image_file

class Membre(models.Model):
    photo = models.ImageField(
        upload_to='members/photos/%Y/%m/',
        validators=[validate_image_file],
    )
```

Les messages d'erreur sont en francais et incluent les details (taille actuelle du fichier, type recu vs types acceptes).

---

### 7. Utilitaires (`utils.py`)

Fonctions d'aide regroupees par categorie.

#### Generation de numeros

Tous les generateurs utilisent `select_for_update()` dans une transaction atomique pour prevenir les conditions de course (race conditions) lors de requetes concurrentes.

| Fonction | Format | Exemple | Modele source |
|----------|--------|---------|--------------|
| `generate_member_number()` | `MBR-YYYY-XXXX` | `MBR-2026-0001` | `Member` |
| `generate_donation_number()` | `DON-YYYYMM-XXXX` | `DON-202602-0001` | `Donation` |
| `generate_request_number()` | `HR-YYYYMM-XXXX` | `HR-202602-0001` | `HelpRequest` |
| `generate_receipt_number(year)` | `REC-YYYY-XXXX` | `REC-2026-0001` | `TaxReceipt` |

> **Note technique :** Les prefixes sont configurables via `settings.py` (`MEMBER_NUMBER_PREFIX`, `DONATION_NUMBER_PREFIX`, `HELP_REQUEST_NUMBER_PREFIX`, `TAX_RECEIPT_NUMBER_PREFIX`).

```python
from apps.core.utils import generate_member_number, generate_donation_number

numero = generate_member_number()    # 'MBR-2026-0042'
don_numero = generate_donation_number()  # 'DON-202602-0015'
```

#### Utilitaires d'anniversaires

| Fonction | Parametres | Description |
|----------|-----------|-------------|
| `get_today_birthdays()` | -- | Membres dont c'est l'anniversaire aujourd'hui |
| `get_week_birthdays()` | -- | Anniversaires des 7 prochains jours (gere le passage decembre/janvier) |
| `get_month_birthdays(month)` | `month` (optionnel, defaut: mois courant) | Anniversaires d'un mois specifique |
| `get_upcoming_birthdays(days)` | `days` (defaut: 30) | Anniversaires des N prochains jours, retourne `[(member, birthday_date)]` tries par date |

```python
from apps.core.utils import get_today_birthdays, get_upcoming_birthdays

# Anniversaires du jour
anniversaires = get_today_birthdays()
for membre in anniversaires:
    print(f"Joyeux anniversaire {membre.full_name} !")

# Prochains 30 jours
a_venir = get_upcoming_birthdays(30)
for membre, date_anniv in a_venir:
    print(f"{membre.full_name} : {date_anniv.strftime('%d %B')}")
```

#### Utilitaires de dates

| Fonction | Parametres | Retour | Description |
|----------|-----------|--------|-------------|
| `get_current_week_range()` | -- | `(lundi, dimanche)` | Plage lundi-dimanche de la semaine courante |
| `get_current_month_range()` | -- | `(premier_jour, dernier_jour)` | Premier et dernier jour du mois courant |
| `get_date_range(period)` | `'today'`, `'week'`, `'month'`, `'year'` | `(debut, fin)` | Plage de dates selon la periode |

```python
from apps.core.utils import get_date_range

debut, fin = get_date_range('month')
dons_du_mois = Don.objects.filter(date__range=(debut, fin))
```

#### Formatage

| Fonction | Entree | Sortie | Description |
|----------|--------|--------|-------------|
| `format_phone(phone)` | `'5145550123'` | `'(514) 555-0123'` | Formatage nord-americain (10 ou 11 chiffres) |
| `format_postal_code(postal_code)` | `'H2X1Y4'` | `'H2X 1Y4'` | Formatage code postal canadien |
| `format_currency(amount)` | `1234.56` | `'$1,234.56'` | Formatage monnaie canadienne |

```python
from apps.core.utils import format_phone, format_postal_code, format_currency

print(format_phone('5145550123'))        # (514) 555-0123
print(format_postal_code('H2X1Y4'))      # H2X 1Y4
print(format_currency(1500.00))          # $1,500.00
print(format_currency(None))             # $0.00
```

---

## Exemples d'utilisation complets

### Creer un modele avec soft delete

```python
from django.db import models
from apps.core.models import SoftDeleteModel
from apps.core.constants import DonationType, PaymentMethod

class Don(SoftDeleteModel):
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    type_don = models.CharField(max_length=20, choices=DonationType.CHOICES)
    methode = models.CharField(max_length=20, choices=PaymentMethod.CHOICES)

    class Meta:
        verbose_name = 'Don'
        verbose_name_plural = 'Dons'

# Utilisation
don = Don.objects.create(montant=100, type_don='tithe', methode='cash')
don.delete()          # Soft delete (conserve en base)
don.restore()         # Restauration
don.hard_delete()     # Suppression definitive
```

### Creer une vue protegee avec contexte d'eglise

```python
from django.views.generic import CreateView
from apps.core.mixins import (
    PastorRequiredMixin,
    ChurchContextMixin,
    PageTitleMixin,
    BreadcrumbMixin,
    FormMessageMixin,
    SetOwnerMixin,
)

class CreerEvenementView(
    PastorRequiredMixin,
    ChurchContextMixin,
    PageTitleMixin,
    BreadcrumbMixin,
    FormMessageMixin,
    SetOwnerMixin,
    CreateView,
):
    model = Evenement
    fields = ['nom', 'date', 'type_evenement']
    template_name = 'events/form.html'
    page_title = "Creer un evenement"
    success_message = "L'evenement a ete cree avec succes."

    def get_breadcrumbs(self):
        return [
            ('Evenements', '/events/'),
            ('Creer', None),
        ]
```

### Creer un ViewSet API avec permissions

```python
from rest_framework import viewsets
from apps.core.permissions import IsFinanceStaff, IsOwnerOrStaff

class DonViewSet(viewsets.ModelViewSet):
    queryset = Don.objects.all()
    serializer_class = DonSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsFinanceStaff()]
        if self.action in ['update', 'partial_update']:
            return [IsOwnerOrStaff()]
        return [IsFinanceStaff()]
```

---

## Tests

Lancer les tests de l'application `core` :

```bash
# Tous les tests core
pytest apps/core/ -v

# Tests specifiques
pytest apps/core/ -v -k "test_base_model"
pytest apps/core/ -v -k "test_permissions"
pytest apps/core/ -v -k "test_utils"

# Avec couverture de code
pytest apps/core/ -v --cov=apps.core --cov-report=html
```

### Structure de tests recommandee

```text
apps/core/
    tests/
        __init__.py
        test_models.py        # BaseModel, SoftDeleteModel, managers
        test_constants.py     # Validation des constantes et choix
        test_permissions.py   # Classes de permission DRF
        test_mixins.py        # Mixins de vues, incluant W3CRMFormMixin
        test_validators.py    # Validateurs de fichiers
        test_utils.py         # Generation de numeros, anniversaires, formatage
```

---

## Arborescence des fichiers

```text
apps/core/
    __init__.py
    constants.py       # Constantes et choix centralises
    mixins.py          # Mixins de vues (permissions, contexte, formulaires)
    models.py          # Modeles abstraits (BaseModel, SoftDeleteModel, etc.)
    permissions.py     # Classes de permission DRF
    utils.py           # Fonctions utilitaires
    validators.py      # Validateurs de fichiers
```
