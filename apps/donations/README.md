# Application Donations (Dons)

> Module de gestion des contributions financieres pour EgliseConnect.

---

## Table des matieres

1. [Apercu general](#apercu-general)
2. [Apercu technique](#apercu-technique)
3. [Modeles (Models)](#modeles-models)
4. [Formulaires (Forms)](#formulaires-forms)
5. [Endpoints API](#endpoints-api)
6. [URLs Frontend](#urls-frontend)
7. [Templates](#templates)
8. [Conformite ARC (CRA Compliance)](#conformite-arc-cra-compliance)
9. [Exemples d'utilisation](#exemples-dutilisation)
10. [Tests](#tests)

---

## Apercu general

### Pour les utilisateurs non techniques

Ce module permet a l'eglise de gerer l'ensemble des dons financiers recus. Voici ce qu'il offre :

- **Dons en ligne** : Les membres peuvent faire des dons directement via le site web, de facon securisee.
- **Dons en personne** : Le tresorier peut enregistrer les dons recus en especes, par cheque ou par virement bancaire lors des cultes ou reunions.
- **Campagnes de collecte de fonds** : L'eglise peut creer des campagnes speciales (ex. : renovation du batiment, missions, projets communautaires) avec un objectif financier et un suivi en temps reel de la progression.
- **Recus fiscaux annuels** : A la fin de chaque annee, le systeme genere des recus fiscaux conformes aux exigences de l'Agence du revenu du Canada (ARC), que les membres peuvent utiliser pour leur declaration d'impots.
- **Rapports financiers** : Le tresorier et le pasteur peuvent consulter des rapports mensuels et annuels sur les dons, regroupes par type, par mode de paiement, par campagne ou par membre.

### Qui utilise ce module ?

| Role | Acces |
|------|-------|
| **Membre** | Faire un don en ligne, consulter son historique de dons, telecharger ses recus fiscaux |
| **Tresorier** | Enregistrer les dons physiques, generer les recus fiscaux, consulter tous les dons et rapports |
| **Pasteur / Admin** | Creer et gerer les campagnes de collecte, consulter les statistiques financieres |
| **Personnel financier** | Modifier/supprimer des dons, consulter l'ensemble des dons et statistiques |

---

## Apercu technique

L'application `donations` est construite avec Django et Django REST Framework (DRF). Elle suit l'architecture standard d'EgliseConnect :

- **Models** : 3 modeles Django (`Donation`, `DonationCampaign`, `TaxReceipt`)
- **Forms** : 5 formulaires utilisant le mixin `W3CRMFormMixin`
- **API** : 3 ViewSets DRF avec filtrage, recherche et pagination
- **Frontend** : 10 vues basees sur des templates Django
- **Permissions** : Controle d'acces base sur les roles (`IsMember`, `IsTreasurer`, `IsFinanceStaff`, `IsPastorOrAdmin`)

### Architecture des fichiers

```text
apps/donations/
    __init__.py
    admin.py              # Configuration Django Admin
    apps.py               # AppConfig
    forms.py              # 5 formulaires Django
    models.py             # Donation, DonationCampaign, TaxReceipt
    serializers.py        # Serializers DRF (8 serializers)
    urls.py               # Routage API + Frontend
    views_api.py          # ViewSets DRF
    views_frontend.py     # Vues Django classiques
    migrations/
        0001_initial.py
    templates/
        donations/
            donation_form.html
            donation_detail.html
            donation_history.html
            donation_admin_list.html
            donation_record.html
            campaign_list.html
            campaign_detail.html
            receipt_list.html
            receipt_detail.html
            monthly_report.html
    tests/
        __init__.py
        factories.py      # Factory Boy factories
        test_models.py
        test_forms.py
        test_views_api.py
        test_views_frontend.py
```

---

## Modeles (Models)

### Donation

Enregistrement individuel d'un don avec un numero auto-genere au format `DON-YYYYMM-XXXX`.

Le modele herite de `SoftDeleteModel`, ce qui permet la suppression logique (le champ `is_active` passe a `False` au lieu d'une suppression en base de donnees).

| Champ | Type | Description |
|-------|------|-------------|
| `donation_number` | `CharField(20)` | Numero unique auto-genere (ex. : `DON-202601-0001`). Non modifiable. |
| `member` | `ForeignKey(Member)` | Le membre donateur. Protege contre la suppression (`PROTECT`). |
| `amount` | `DecimalField(12,2)` | Montant du don en dollars. |
| `donation_type` | `CharField(20)` | Type de don. Choix : `tithe`, `offering`, `special`, `campaign`, `building`, `missions`, `other`. |
| `payment_method` | `CharField(20)` | Mode de paiement. Choix : `cash`, `check`, `card`, `bank_transfer`, `online`, `other`. |
| `campaign` | `ForeignKey(DonationCampaign)` | Campagne associee (optionnel). `SET_NULL` a la suppression. |
| `date` | `DateField` | Date du don. Par defaut : aujourd'hui. |
| `notes` | `TextField` | Notes additionnelles (optionnel). |
| `recorded_by` | `ForeignKey(Member)` | Personne ayant enregistre le don (pour les dons physiques). |
| `check_number` | `CharField(50)` | Numero de cheque (pour les paiements par cheque). |
| `transaction_id` | `CharField(100)` | Reference de la transaction en ligne. |
| `receipt_sent` | `BooleanField` | Indique si un recu a ete envoye. Par defaut : `False`. |
| `receipt_sent_date` | `DateTimeField` | Date d'envoi du recu (optionnel). |

**Proprietes calculees :**

| Propriete | Type retourne | Description |
|-----------|---------------|-------------|
| `is_online` | `bool` | `True` si le mode de paiement est `online` ou `card`. |

**Index de base de donnees :**

```python
indexes = [
    models.Index(fields=['donation_number']),
    models.Index(fields=['member', 'date']),
    models.Index(fields=['date']),
    models.Index(fields=['donation_type']),
    models.Index(fields=['payment_method']),
]
```

**Comportement du `save()` :** Si le `donation_number` est vide, il est genere automatiquement via `apps.core.utils.generate_donation_number()`.

---

### DonationCampaign

Campagne de collecte de fonds avec un objectif et des dates de debut/fin.

Le modele herite de `BaseModel` (qui fournit `id` UUID, `created_at`, `updated_at`, `is_active`).

| Champ | Type | Description |
|-------|------|-------------|
| `name` | `CharField(200)` | Nom de la campagne. |
| `description` | `TextField` | Description detaillee (optionnel). |
| `goal_amount` | `DecimalField(12,2)` | Montant cible de la campagne. Par defaut : `0.00`. |
| `start_date` | `DateField` | Date de debut de la campagne. |
| `end_date` | `DateField` | Date de fin (optionnel). |
| `image` | `ImageField` | Image de la campagne. Upload vers `campaigns/%Y/`. |

**Proprietes calculees :**

| Propriete | Type retourne | Description |
|-----------|---------------|-------------|
| `current_amount` | `Decimal` | Total des dons actifs associes a cette campagne. |
| `progress_percentage` | `int` | Pourcentage de progression vers l'objectif (max 100). |
| `is_ongoing` | `bool` | `True` si la campagne est active et que la date courante est dans la plage de dates. |

---

### TaxReceipt

Recu fiscal annuel genere pour l'ARC. Un seul recu par membre par annee (contrainte `unique_together`).

Le modele capture un "snapshot" (instantane) du nom et de l'adresse du membre au moment de la generation, assurant ainsi l'exactitude historique meme si le membre change ses informations par la suite.

| Champ | Type | Description |
|-------|------|-------------|
| `receipt_number` | `CharField(20)` | Numero unique au format `REC-YYYY-XXXX`. |
| `member` | `ForeignKey(Member)` | Le membre concerne. Protege contre la suppression (`PROTECT`). |
| `year` | `PositiveIntegerField` | Annee fiscale. |
| `total_amount` | `DecimalField(12,2)` | Montant total des dons pour l'annee. |
| `generated_at` | `DateTimeField` | Date de generation (auto). |
| `generated_by` | `ForeignKey(Member)` | Personne ayant genere le recu. |
| `pdf_file` | `FileField` | Fichier PDF du recu. Upload vers `receipts/%Y/`. |
| `email_sent` | `BooleanField` | Indique si le recu a ete envoye par courriel. |
| `email_sent_date` | `DateTimeField` | Date d'envoi par courriel (optionnel). |
| `member_name` | `CharField(200)` | Nom du membre au moment de la generation (snapshot). |
| `member_address` | `TextField` | Adresse du membre au moment de la generation (snapshot). |

**Contraintes :**

```python
unique_together = ['member', 'year']  # Un seul recu par membre par annee
```

**Comportement du `save()` :** Si `member_name` ou `member_address` sont vides, ils sont automatiquement remplis a partir du profil du membre.

---

## Formulaires (Forms)

Tous les formulaires utilisent le mixin `W3CRMFormMixin` pour un style uniforme avec le theme W3.CSS / W3CRM d'EgliseConnect.

### 1. DonationForm

Formulaire pour les dons en ligne des membres.

| Champ | Widget | Notes |
|-------|--------|-------|
| `amount` | `NumberInput` (min=1, step=0.01) | Validation : le montant doit etre positif. |
| `donation_type` | `Select` | Types de don standards. |
| `campaign` | `Select` | Filtre automatiquement pour n'afficher que les campagnes actives. Optionnel. |
| `notes` | `Textarea` (rows=2) | Notes additionnelles. |

### 2. PhysicalDonationForm

Formulaire pour le tresorier afin d'enregistrer les dons physiques recus en personne.

| Champ | Widget | Notes |
|-------|--------|-------|
| `member` | `Select` | Membre donateur. |
| `amount` | `NumberInput` (min=1, step=0.01) | Montant du don. |
| `donation_type` | `Select` | Types de don standards. |
| `payment_method` | `Select` | Limite a : Especes, Cheque, Virement bancaire, Autre. |
| `date` | `DateInput` (type=date) | Date du don. |
| `campaign` | `Select` | Campagnes actives uniquement. Optionnel. |
| `check_number` | `TextInput` | Requis si le mode de paiement est "cheque". |
| `notes` | `Textarea` (rows=2) | Notes additionnelles. |

**Validation personnalisee :** Si `payment_method` est `check`, le champ `check_number` est obligatoire.

### 3. DonationCampaignForm

Formulaire de creation et modification des campagnes de collecte de fonds.

| Champ | Widget | Notes |
|-------|--------|-------|
| `name` | `TextInput` | Nom de la campagne. |
| `description` | `Textarea` (rows=3) | Description. |
| `goal_amount` | `NumberInput` (min=0, step=0.01) | Objectif financier. |
| `start_date` | `DateInput` (type=date) | Date de debut. |
| `end_date` | `DateInput` (type=date) | Date de fin. Doit etre apres la date de debut. |
| `image` | `FileInput` | Image de la campagne. |
| `is_active` | `CheckboxInput` | Activer/desactiver la campagne. |

**Validation personnalisee :** La date de fin doit etre posterieure a la date de debut.

### 4. DonationFilterForm

Formulaire de filtrage pour la liste des dons (utilise dans la vue d'administration).

| Champ | Widget | Notes |
|-------|--------|-------|
| `date_from` | `DateInput` (type=date) | Filtrer a partir de cette date. |
| `date_to` | `DateInput` (type=date) | Filtrer jusqu'a cette date. |
| `donation_type` | `Select` | Filtrer par type de don (option "Tous" par defaut). |
| `payment_method` | `Select` | Filtrer par mode de paiement (option "Tous" par defaut). |
| `campaign` | `Select` | Filtrer par campagne (option "Toutes" par defaut). |
| `member` | `TextInput` | Recherche par nom ou numero de membre. |

### 5. DonationReportForm

Formulaire pour la generation de rapports financiers.

| Champ | Widget | Notes |
|-------|--------|-------|
| `period` | `Select` | Choix : Mois, Trimestre, Annee, Personnalise. |
| `year` | `NumberInput` | Annee (2000-2100). Optionnel. |
| `month` | `NumberInput` | Mois (1-12). Optionnel. |
| `date_from` | `DateInput` (type=date) | Date de debut (pour periode personnalisee). |
| `date_to` | `DateInput` (type=date) | Date de fin (pour periode personnalisee). |
| `group_by` | `Select` | Regroupement : Par type, Par mode de paiement, Par campagne, Par membre. |

---

## Endpoints API

Tous les endpoints sont prefixes par `/api/v1/donations/`. L'authentification est requise pour tous les endpoints.

### Dons (Donations)

| Methode | URL | Description | Permission |
|---------|-----|-------------|------------|
| `GET` | `/api/v1/donations/donations/` | Lister les dons | Le personnel financier voit tout; les membres voient les leurs |
| `POST` | `/api/v1/donations/donations/` | Creer un don en ligne | Membre authentifie |
| `GET` | `/api/v1/donations/donations/{uuid}/` | Detail d'un don | Proprietaire ou personnel financier |
| `PUT/PATCH` | `/api/v1/donations/donations/{uuid}/` | Modifier un don | Personnel financier uniquement |
| `DELETE` | `/api/v1/donations/donations/{uuid}/` | Supprimer un don | Personnel financier uniquement |
| `GET` | `/api/v1/donations/donations/my-history/` | Historique de mes dons | Membre authentifie |
| `POST` | `/api/v1/donations/donations/record-physical/` | Enregistrer un don physique | Tresorier uniquement |
| `GET` | `/api/v1/donations/donations/summary/` | Statistiques des dons | Personnel financier |

**Filtres disponibles :** `donation_type`, `payment_method`, `campaign`, `date`
**Recherche :** `donation_number`, `member.first_name`, `member.last_name`
**Tri :** `date`, `amount`, `created_at` (par defaut : `-date`, `-created_at`)

### Campagnes (Campaigns)

| Methode | URL | Description | Permission |
|---------|-----|-------------|------------|
| `GET` | `/api/v1/donations/campaigns/` | Lister les campagnes | Membre authentifie |
| `POST` | `/api/v1/donations/campaigns/` | Creer une campagne | Pasteur ou Admin |
| `GET` | `/api/v1/donations/campaigns/{uuid}/` | Detail d'une campagne | Membre authentifie |
| `GET` | `/api/v1/donations/campaigns/active/` | Campagnes en cours | Membre authentifie |

**Filtres disponibles :** `is_active`
**Recherche :** `name`, `description`
**Tri :** `name`, `start_date`, `goal_amount`

### Recus fiscaux (Tax Receipts)

| Methode | URL | Description | Permission |
|---------|-----|-------------|------------|
| `GET` | `/api/v1/donations/receipts/` | Lister les recus | Le personnel financier voit tout; les membres voient les leurs |
| `GET` | `/api/v1/donations/receipts/{uuid}/` | Detail d'un recu | Proprietaire ou personnel financier |
| `GET` | `/api/v1/donations/receipts/my-receipts/` | Mes recus fiscaux | Membre authentifie |
| `POST` | `/api/v1/donations/receipts/generate/{year}/` | Generer les recus pour une annee | Tresorier uniquement |

**Filtres disponibles :** `year`, `email_sent`
**Recherche :** `receipt_number`, `member.first_name`, `member.last_name`
**Tri :** `year`, `generated_at`, `total_amount`

### Serializers

L'application utilise 8 serializers pour differents cas d'usage :

| Serializer | Utilisation |
|------------|-------------|
| `DonationListSerializer` | Liste legere des dons (action `list`) |
| `DonationSerializer` | Detail complet d'un don |
| `DonationCreateSerializer` | Creation de don en ligne (champs minimaux) |
| `PhysicalDonationCreateSerializer` | Enregistrement de don physique par le tresorier |
| `MemberDonationHistorySerializer` | Historique personnel d'un membre |
| `DonationCampaignSerializer` | Detail complet d'une campagne (avec proprietes calculees) |
| `DonationCampaignListSerializer` | Liste legere des campagnes |
| `TaxReceiptSerializer` / `TaxReceiptListSerializer` | Detail et liste des recus fiscaux |
| `DonationSummarySerializer` | Statistiques agreges (total, nombre, moyenne, ventilation) |

---

## URLs Frontend

Toutes les URLs sont prefixees par `/donations/` et necessitent une connexion.

| URL | Nom de la vue | Template | Description |
|-----|---------------|----------|-------------|
| `/donations/donate/` | `donation_create` | `donation_form.html` | Formulaire pour faire un don en ligne |
| `/donations/history/` | `donation_history` | `donation_history.html` | Historique personnel des dons du membre |
| `/donations/{uuid}/` | `donation_detail` | `donation_detail.html` | Detail d'un don specifique |
| `/donations/admin/` | `donation_admin_list` | `donation_admin_list.html` | Liste de tous les dons (personnel financier) |
| `/donations/record/` | `donation_record` | `donation_record.html` | Formulaire d'enregistrement de don physique (tresorier) |
| `/donations/campaigns/` | `campaign_list` | `campaign_list.html` | Liste des campagnes de collecte |
| `/donations/campaigns/{uuid}/` | `campaign_detail` | `campaign_detail.html` | Detail d'une campagne avec progression |
| `/donations/receipts/` | `receipt_list` | `receipt_list.html` | Liste des recus fiscaux |
| `/donations/receipts/{uuid}/` | `receipt_detail` | `receipt_detail.html` | Detail d'un recu fiscal avec telechargement PDF |
| `/donations/reports/monthly/` | `monthly_report` | `monthly_report.html` | Rapport mensuel des dons |

---

## Templates

Tous les templates sont situes dans `apps/donations/templates/donations/`.

| Template | Description |
|----------|-------------|
| `donation_form.html` | Formulaire de don en ligne avec selection du type, montant et campagne optionnelle |
| `donation_detail.html` | Affichage complet d'un don (numero, montant, type, mode de paiement, campagne, notes) |
| `donation_history.html` | Tableau pagine de l'historique des dons du membre connecte |
| `donation_admin_list.html` | Liste administrable de tous les dons avec filtres (date, type, methode, campagne, membre) |
| `donation_record.html` | Formulaire pour le tresorier afin d'enregistrer un don en personne |
| `campaign_list.html` | Liste des campagnes avec barre de progression et montants |
| `campaign_detail.html` | Detail d'une campagne incluant objectif, progression et liste des dons associes |
| `receipt_list.html` | Liste des recus fiscaux par annee |
| `receipt_detail.html` | Detail du recu fiscal avec option de telechargement en PDF |
| `monthly_report.html` | Rapport mensuel avec ventilation par type de don et mode de paiement |

---

## Conformite ARC (CRA Compliance)

Les recus fiscaux generes par EgliseConnect sont concus pour respecter les exigences de l'Agence du revenu du Canada (ARC) pour les organismes de bienfaisance enregistres. Chaque recu inclut :

| Information requise | Champ correspondant | Notes |
|---------------------|---------------------|-------|
| Nom de l'organisme et numero d'enregistrement | Configuration globale | Defini dans les parametres de l'eglise |
| Nom complet du donateur | `TaxReceipt.member_name` | Snapshot au moment de la generation |
| Adresse du donateur | `TaxReceipt.member_address` | Snapshot au moment de la generation |
| Montant total des dons | `TaxReceipt.total_amount` | Somme de tous les dons actifs de l'annee |
| Annee fiscale | `TaxReceipt.year` | Annee des dons couverts |
| Numero de recu | `TaxReceipt.receipt_number` | Format `REC-YYYY-XXXX`, unique |
| Date de generation | `TaxReceipt.generated_at` | Horodatage automatique |
| Fichier PDF | `TaxReceipt.pdf_file` | Document officiel telechargeable |

### Points importants

- **Snapshot des donnees** : Le nom et l'adresse du membre sont captures au moment de la generation du recu. Meme si le membre modifie ses informations par la suite, le recu conserve les donnees originales.
- **Unicite** : Un seul recu par membre par annee (`unique_together`). Si un recu existe deja, la generation le retourne sans en creer un nouveau.
- **Suppression logique** : Les dons utilisant `SoftDeleteModel` ne sont jamais reellement supprimes, preservant ainsi l'integrite des recus.
- **Envoi par courriel** : Le systeme suit l'envoi des recus par courriel (`email_sent`, `email_sent_date`).

---

## Exemples d'utilisation

### Creer un don en ligne (Python)

```python
from decimal import Decimal
from apps.donations.models import Donation
from apps.core.constants import DonationType, PaymentMethod

donation = Donation.objects.create(
    member=member,
    amount=Decimal('100.00'),
    donation_type=DonationType.TITHE,
    payment_method=PaymentMethod.ONLINE,
)
# Le numero est genere automatiquement
print(donation.donation_number)  # DON-202601-0001
```

### Enregistrer un don physique (Python)

```python
from decimal import Decimal
from apps.donations.models import Donation
from apps.core.constants import DonationType, PaymentMethod

donation = Donation.objects.create(
    member=donateur,
    amount=Decimal('50.00'),
    donation_type=DonationType.OFFERING,
    payment_method=PaymentMethod.CHECK,
    check_number='12345',
    recorded_by=tresorier,
    date=date(2026, 1, 15),
)
```

### Creer un don via l'API REST

```bash
# Don en ligne (le membre est determine par l'authentification)
curl -X POST /api/v1/donations/donations/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100.00",
    "donation_type": "tithe",
    "notes": "Dime du mois de janvier"
  }'
```

### Enregistrer un don physique via l'API REST

```bash
# Tresorier enregistre un don en especes
curl -X POST /api/v1/donations/donations/record-physical/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "member": "uuid-du-membre",
    "amount": "50.00",
    "donation_type": "offering",
    "payment_method": "cash",
    "date": "2026-01-15"
  }'
```

### Consulter les statistiques

```bash
# Statistiques du mois courant
curl /api/v1/donations/donations/summary/ \
  -H "Authorization: Bearer <token>"

# Statistiques pour un mois specifique
curl "/api/v1/donations/donations/summary/?period=month&year=2026&month=1" \
  -H "Authorization: Bearer <token>"

# Reponse :
# {
#   "period": "1/2026",
#   "total_amount": "5250.00",
#   "donation_count": 47,
#   "average_donation": "111.70",
#   "by_type": {"tithe": "3000.00", "offering": "1500.00", "special": "750.00"},
#   "by_method": {"online": "2000.00", "cash": "1750.00", "check": "1500.00"}
# }
```

### Generer les recus fiscaux

```python
from django.db.models import Sum
from apps.donations.models import Donation, TaxReceipt
from apps.core.utils import generate_receipt_number

# Calculer le total des dons d'un membre pour l'annee
total = Donation.objects.filter(
    member=member,
    date__year=2026,
    is_active=True,
).aggregate(Sum('amount'))['amount__sum']

# Creer le recu (le nom et l'adresse sont captures automatiquement)
receipt = TaxReceipt.objects.create(
    receipt_number=generate_receipt_number(2026),
    member=member,
    year=2026,
    total_amount=total,
    generated_by=tresorier,
)
print(receipt.receipt_number)  # REC-2026-0001
print(receipt.member_name)     # Capture automatiquement du profil membre
```

### Generer les recus via l'API REST

```bash
# Generer les recus pour tous les membres ayant fait des dons en 2026
curl -X POST /api/v1/donations/receipts/generate/2026/ \
  -H "Authorization: Bearer <token>"

# Reponse :
# {"generated_count": 42, "year": 2026}

# Generer pour un membre specifique
curl -X POST "/api/v1/donations/receipts/generate/2026/?member=uuid-du-membre" \
  -H "Authorization: Bearer <token>"
```

### Consulter la progression d'une campagne

```python
campaign = DonationCampaign.objects.get(name="Renovation du temple")
print(f"Objectif : {campaign.goal_amount} $")
print(f"Recueilli : {campaign.current_amount} $")
print(f"Progression : {campaign.progress_percentage}%")
print(f"En cours : {campaign.is_ongoing}")
```

---

## Tests

L'application dispose de 4 modules de tests couvrant les modeles, formulaires, vues API et vues frontend.

### Executer les tests

```bash
# Tous les tests de l'application donations
pytest apps/donations/ -v

# Tests par categorie
pytest apps/donations/tests/test_models.py -v
pytest apps/donations/tests/test_forms.py -v
pytest apps/donations/tests/test_views_api.py -v
pytest apps/donations/tests/test_views_frontend.py -v
```

### Structure des tests

| Fichier | Couverture |
|---------|------------|
| `tests/factories.py` | Factories Factory Boy pour `Donation`, `DonationCampaign`, `TaxReceipt` |
| `tests/test_models.py` | Generation auto du numero de don, proprietes calculees, contraintes `unique_together`, snapshot TaxReceipt |
| `tests/test_forms.py` | Validation des montants, filtrage des campagnes actives, validation du numero de cheque, validation des dates |
| `tests/test_views_api.py` | Permissions par role, CRUD complet, endpoints custom (`my-history`, `record-physical`, `summary`, `generate`) |
| `tests/test_views_frontend.py` | Acces aux pages, soumission des formulaires, redirections, pagination |

### Exemple de test

```python
import pytest
from decimal import Decimal
from apps.donations.tests.factories import DonationFactory, DonationCampaignFactory

@pytest.mark.django_db
def test_donation_auto_number():
    """Le numero de don est genere automatiquement."""
    donation = DonationFactory()
    assert donation.donation_number.startswith('DON-')

@pytest.mark.django_db
def test_campaign_progress():
    """La progression de la campagne est calculee correctement."""
    campaign = DonationCampaignFactory(goal_amount=Decimal('1000.00'))
    DonationFactory(campaign=campaign, amount=Decimal('250.00'))
    assert campaign.progress_percentage == 25
```

---

## Recent Additions

### FinanceDelegation Model

Allows a member to delegate finance access to another member (e.g., treasurer delegating to assistant).

| Field | Type | Description |
|-------|------|-------------|
| `delegated_to` | ForeignKey → Member | Member granted access |
| `delegated_by` | ForeignKey → Member | Member granting access |
| `granted_at` | DateTimeField | Auto-set on creation |
| `revoked_at` | DateTimeField | When delegation was revoked (nullable) |
| `reason` | TextField | Reason for delegation (optional) |

Property: `is_active_delegation` → True if active and not revoked.

### New Frontend Views
- `finance_delegations` — `/donations/delegations/` — List active and revoked delegations
- `delegate_finance_access` — `/donations/delegations/grant/` — Grant finance access (POST)
- `revoke_finance_access` — `/donations/delegations/<pk>/revoke/` — Revoke delegation (POST)

### New Templates
- `campaign_form.html` — Create/update campaign form
- `campaign_delete.html` — Delete campaign confirmation
- `finance_delegations.html` — Finance delegation management page
