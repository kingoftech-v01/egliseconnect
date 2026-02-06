# Module Communication (Infolettres et Notifications)

> **Application Django** : `apps.communication`
> **Chemin** : `apps/communication/`

---

## Vue d'ensemble

### Pour les non-techniques

Ce module gere l'ensemble des communications de l'eglise. Il offre trois fonctionnalites principales :

- **Infolettres (Newsletters)** : Les pasteurs et administrateurs peuvent creer des infolettres avec du contenu riche (HTML), les planifier pour un envoi futur ou les envoyer immediatement a tous les membres ou a des groupes cibles specifiques. Le systeme suit le nombre de destinataires et les ouvertures.
- **Notifications** : Les membres recoivent des notifications dans l'application pour les evenements, les anniversaires, les rappels de benevolat, les mises a jour de demandes d'aide, les recus de don, et plus encore. Chaque notification peut inclure un lien direct vers l'element concerne.
- **Preferences de notification** : Chaque membre peut configurer ses preferences -- activer ou desactiver les courriels pour les infolettres, les evenements ou les anniversaires, ainsi que les notifications push et SMS.

### Pour les techniques

L'application repose sur Django + Django REST Framework. Elle utilise quatre models principaux. Le contenu HTML des infolettres est **assaini avec `bleach`** (whitelist de balises et attributs securitaires) aussi bien dans le `ModelForm` que dans le `Serializer`, prevenant ainsi les attaques XSS. Les infolettres supportent un workflow de statut (`draft` -> `scheduled` -> `sending` -> `sent`). Les notifications sont scoped au membre connecte. Le suivi des destinataires est gere par le model `NewsletterRecipient`.

---

## Architecture des fichiers

```
apps/communication/
    __init__.py
    apps.py
    models.py              # 4 models
    forms.py               # 1 formulaire (NewsletterForm) + constantes bleach
    serializers.py          # 4 serializers
    views_api.py            # 3 ViewSets REST
    views_frontend.py       # 5 vues avec templates
    urls.py                 # Routage API + frontend
    admin.py                # Configuration Django Admin
    migrations/
        0001_initial.py
    tests/
        __init__.py
        factories.py        # 3 factories (factory_boy)
        test_forms.py       # Tests des formulaires
        test_views_api.py   # Tests API
        test_views_frontend.py
```

---

## Models

### Newsletter

Represente une infolettre envoyable aux membres.

| Champ | Type | Description |
|-------|------|-------------|
| `subject` | `CharField(200)` | Sujet de l'infolettre |
| `content` | `TextField` | Contenu HTML (assaini avec bleach) |
| `content_plain` | `TextField` | Version texte brut (optionnel) |
| `created_by` | `ForeignKey(Member)` | Auteur (nullable, SET_NULL) |
| `status` | `CharField(20)` | Statut de livraison (`NewsletterStatus.CHOICES`) |
| `scheduled_for` | `DateTimeField` | Date d'envoi planifie (optionnel) |
| `sent_at` | `DateTimeField` | Date d'envoi effectif (optionnel) |
| `send_to_all` | `BooleanField` | Envoyer a tous les membres (defaut: `True`) |
| `target_groups` | `ManyToManyField(Group)` | Groupes cibles (si `send_to_all=False`) |
| `recipients_count` | `PositiveIntegerField` | Nombre de destinataires |
| `opened_count` | `PositiveIntegerField` | Nombre d'ouvertures |

**Valeurs possibles pour `status`** :

| Constante | Valeur | Libelle FR |
|-----------|--------|------------|
| `NewsletterStatus.DRAFT` | `'draft'` | Brouillon |
| `NewsletterStatus.SCHEDULED` | `'scheduled'` | Planifiee |
| `NewsletterStatus.SENDING` | `'sending'` | En cours d'envoi |
| `NewsletterStatus.SENT` | `'sent'` | Envoyee |
| `NewsletterStatus.FAILED` | `'failed'` | Echec |

**Meta** : ordonne par `-created_at`, verbose `"Infolettre"`.

---

### NewsletterRecipient

Suit le statut de livraison et d'ouverture pour chaque destinataire.

| Champ | Type | Description |
|-------|------|-------------|
| `newsletter` | `ForeignKey(Newsletter)` | Infolettre associee |
| `member` | `ForeignKey(Member)` | Membre destinataire |
| `email` | `EmailField` | Courriel utilise |
| `sent_at` | `DateTimeField` | Date/heure d'envoi (nullable) |
| `opened_at` | `DateTimeField` | Date/heure d'ouverture (nullable) |
| `failed` | `BooleanField` | Si l'envoi a echoue |
| `failure_reason` | `TextField` | Raison de l'echec |

**Contrainte unique** : `(newsletter, member)` -- un seul envoi par membre par infolettre.

---

### Notification

Notification in-app pour un membre.

| Champ | Type | Description |
|-------|------|-------------|
| `member` | `ForeignKey(Member)` | Membre concerne |
| `title` | `CharField(200)` | Titre de la notification |
| `message` | `TextField` | Message detaille |
| `notification_type` | `CharField(50)` | Type de notification (`NotificationType.CHOICES`) |
| `link` | `URLField` | Lien vers l'element concerne (optionnel) |
| `is_read` | `BooleanField` | Si la notification a ete lue (defaut: `False`) |
| `read_at` | `DateTimeField` | Date/heure de lecture (nullable) |

**Valeurs possibles pour `notification_type`** :

| Constante | Valeur | Libelle FR |
|-----------|--------|------------|
| `NotificationType.BIRTHDAY` | `'birthday'` | Anniversaire |
| `NotificationType.EVENT` | `'event'` | Rappel d'evenement |
| `NotificationType.VOLUNTEER` | `'volunteer'` | Rappel de benevolat |
| `NotificationType.HELP_REQUEST` | `'help_request'` | Mise a jour de requete |
| `NotificationType.DONATION` | `'donation'` | Recu de don |
| `NotificationType.GENERAL` | `'general'` | General |

**Meta** : ordonne par `-created_at`.

---

### NotificationPreference

Preferences de notification par membre (relation OneToOne).

| Champ | Type | Description |
|-------|------|-------------|
| `member` | `OneToOneField(Member)` | Membre concerne |
| `email_newsletter` | `BooleanField` | Recevoir les infolettres par courriel (defaut: `True`) |
| `email_events` | `BooleanField` | Rappels d'evenements par courriel (defaut: `True`) |
| `email_birthdays` | `BooleanField` | Rappels d'anniversaires par courriel (defaut: `True`) |
| `push_enabled` | `BooleanField` | Notifications push (defaut: `True`) |
| `sms_enabled` | `BooleanField` | Notifications SMS (defaut: `False`) |

---

## Formulaire

### NewsletterForm

Utilise `W3CRMFormMixin` pour le style des formulaires et `bleach` pour l'assainissement du contenu HTML.

```python
class NewsletterForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['subject', 'content', 'content_plain', 'send_to_all', 'target_groups']
```

**Methode `clean_content()`** : assainit le HTML avec `bleach.clean()` en utilisant une whitelist de balises et attributs securitaires.

**Balises HTML autorisees** :
`a`, `abbr`, `acronym`, `b`, `blockquote`, `br`, `code`, `div`, `em`, `h1`-`h6`, `hr`, `i`, `img`, `li`, `ol`, `p`, `pre`, `span`, `strong`, `table`, `tbody`, `td`, `th`, `thead`, `tr`, `u`, `ul`

**Attributs autorises par balise** :

| Balise | Attributs |
|--------|-----------|
| `a` | `href`, `title`, `target`, `rel` |
| `img` | `src`, `alt`, `width`, `height`, `style` |
| `td`, `th` | `colspan`, `rowspan`, `style` |
| `div`, `span`, `p`, `h1`-`h3` | `style`, `class` |

---

## Securite : assainissement HTML

Le contenu HTML est assaini a **deux niveaux** pour prevenir les attaques XSS :

1. **Formulaire** (`forms.py`) : methode `clean_content()` applique `bleach.clean()`
2. **Serializer** (`serializers.py`) : methode `validate_content()` applique le meme assainissement

Les deux utilisent les memes constantes `ALLOWED_TAGS` et `ALLOWED_ATTRIBUTES` definies dans `forms.py`, assurant une coherence entre les entrees frontend et API.

```python
# Exemple de balises supprimees par bleach :
# <script>, <iframe>, <object>, <embed>, <form>, <input>,
# evenements JavaScript (onclick, onerror, etc.)
```

---

## Serializers

| Serializer | Model | Champs supplementaires (read-only) |
|------------|-------|------------------------------------|
| `NewsletterSerializer` | `Newsletter` | `status_display`, `created_by_name` |
| `NewsletterListSerializer` | `Newsletter` | `status_display` (champs limites pour la liste) |
| `NotificationSerializer` | `Notification` | `type_display` |
| `NotificationPreferenceSerializer` | `NotificationPreference` | -- (5 champs booleens seulement) |

`NewsletterListSerializer` retourne un sous-ensemble de champs pour optimiser les listes : `id`, `subject`, `status`, `status_display`, `sent_at`, `recipients_count`, `opened_count`.

---

## Endpoints API REST

Tous les endpoints sont prefixes par `/api/v1/communication/` et utilisent le `DefaultRouter` de DRF.

### NewsletterViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/communication/newsletters/` | Lister les infolettres | `IsMember` |
| `POST` | `/api/v1/communication/newsletters/` | Creer une infolettre | `IsPastorOrAdmin` |
| `GET` | `/api/v1/communication/newsletters/{id}/` | Detail | `IsMember` |
| `PUT/PATCH` | `/api/v1/communication/newsletters/{id}/` | Modifier | `IsPastorOrAdmin` |
| `DELETE` | `/api/v1/communication/newsletters/{id}/` | Supprimer | `IsPastorOrAdmin` |
| `POST` | `/api/v1/communication/newsletters/{id}/send/` | Envoyer immediatement | `IsPastorOrAdmin` |
| `POST` | `/api/v1/communication/newsletters/{id}/schedule/` | Planifier un envoi futur | `IsPastorOrAdmin` |

**Filtres** : `status` (via `DjangoFilterBackend`)
**Recherche** : `subject` (via `SearchFilter`)

L'action `send` passe le statut a `'sending'` et declenche l'envoi (via Celery). L'action `schedule` attend un champ `scheduled_for` dans le body.

### NotificationViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/communication/notifications/` | Mes notifications | `IsMember` |
| `POST` | `/api/v1/communication/notifications/mark-read/` | Marquer comme lue(s) | `IsMember` |
| `GET` | `/api/v1/communication/notifications/unread_count/` | Nombre de non-lues | `IsMember` |

L'action `mark-read` accepte un champ `ids` (liste d'IDs) dans le body. Si `ids` est vide, toutes les notifications non-lues du membre sont marquees comme lues.

### NotificationPreferenceViewSet

| Methode | URL | Action | Permission |
|---------|-----|--------|------------|
| `GET` | `/api/v1/communication/preferences/me/` | Mes preferences | `IsMember` |
| `PUT/PATCH` | `/api/v1/communication/preferences/me/` | Modifier mes preferences | `IsMember` |

L'endpoint `me` utilise `get_or_create` pour initialiser les preferences si elles n'existent pas encore.

---

## URLs frontend

| URL | Vue | Template | Description |
|-----|-----|----------|-------------|
| `/communication/newsletters/` | `newsletter_list` | `communication/newsletter_list.html` | Liste des infolettres (paginee, 20/page) |
| `/communication/newsletters/create/` | `newsletter_create` | `communication/newsletter_form.html` | Creer une infolettre (Pasteur/Admin) |
| `/communication/newsletters/<uuid:pk>/` | `newsletter_detail` | `communication/newsletter_detail.html` | Detail d'une infolettre |
| `/communication/notifications/` | `notification_list` | `communication/notification_list.html` | Mes notifications (paginee, 20/page) |
| `/communication/preferences/` | `preferences` | `communication/preferences.html` | Gerer mes preferences de notification |

**Logique de visibilite des infolettres** : les pasteurs/admins voient toutes les infolettres (y compris les brouillons); les membres reguliers ne voient que les infolettres envoyees (`status='sent'`).

---

## Templates

| Template | Description |
|----------|-------------|
| `communication/newsletter_list.html` | Liste paginee des infolettres avec statut et compteurs |
| `communication/newsletter_detail.html` | Affichage complet d'une infolettre avec son contenu HTML |
| `communication/newsletter_form.html` | Formulaire de creation/edition avec textarea HTML + texte brut |
| `communication/notification_list.html` | Liste paginee des notifications avec indicateur lu/non-lu |
| `communication/preferences.html` | Formulaire avec checkboxes pour chaque canal de notification |

---

## Administration Django

Quatre classes d'administration enregistrees dans `admin.py` :

| Admin Class | Colonnes affichees | Filtres |
|-------------|-------------------|---------|
| `NewsletterAdmin` | subject, status, sent_at, recipients_count, opened_count | status, sent_at |
| `NewsletterRecipientAdmin` | newsletter, member, sent_at, opened_at, failed | failed, newsletter |
| `NotificationAdmin` | member, title, notification_type, is_read, created_at | notification_type, is_read |
| `NotificationPreferenceAdmin` | member, email_newsletter, email_events, push_enabled | -- |

---

## Permissions

| Role | Lire infolettres | Creer/envoyer infolettres | Notifications | Preferences |
|------|-----------------|---------------------------|---------------|-------------|
| **Membre** | Oui (envoyees seulement) | Non | Les siennes | Les siennes |
| **Responsable de groupe** | Oui (envoyees seulement) | Non | Les siennes | Les siennes |
| **Pasteur / Admin** | Oui (toutes, incl. brouillons) | Oui | Les siennes | Les siennes |

---

## Exemples d'utilisation

### API : Creer une infolettre

```bash
curl -X POST /api/v1/communication/newsletters/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Bulletin de la semaine - 9 fevrier 2026",
    "content": "<h2>Bienvenue</h2><p>Chers membres...</p>",
    "content_plain": "Bienvenue\n\nChers membres...",
    "send_to_all": true
  }'
```

**Reponse** (`201 Created`) :
```json
{
  "id": "...",
  "subject": "Bulletin de la semaine - 9 fevrier 2026",
  "content": "<h2>Bienvenue</h2><p>Chers membres...</p>",
  "status": "draft",
  "status_display": "Brouillon",
  "created_by_name": "Pasteur Martin",
  "send_to_all": true,
  "recipients_count": 0,
  "opened_count": 0,
  "created_at": "2026-02-06T14:00:00Z"
}
```

### API : Envoyer une infolettre

```bash
curl -X POST /api/v1/communication/newsletters/<id>/send/ \
  -H "Authorization: Bearer <token>"
```

### API : Planifier un envoi futur

```bash
curl -X POST /api/v1/communication/newsletters/<id>/schedule/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"scheduled_for": "2026-02-09T08:00:00Z"}'
```

### API : Marquer des notifications comme lues

```bash
# Marquer des notifications specifiques
curl -X POST /api/v1/communication/notifications/mark-read/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["uuid-1", "uuid-2"]}'

# Marquer toutes les notifications comme lues
curl -X POST /api/v1/communication/notifications/mark-read/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### API : Obtenir le nombre de notifications non-lues

```bash
curl -X GET /api/v1/communication/notifications/unread_count/ \
  -H "Authorization: Bearer <token>"
```

**Reponse** : `{"count": 5}`

### API : Mettre a jour les preferences de notification

```bash
curl -X PATCH /api/v1/communication/preferences/me/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email_newsletter": true,
    "email_events": true,
    "email_birthdays": false,
    "push_enabled": true,
    "sms_enabled": false
  }'
```

---

## Tests

Les tests utilisent `pytest` avec `pytest-django` et `factory_boy`.

### Factories disponibles

| Factory | Model | Valeurs par defaut |
|---------|-------|--------------------|
| `NewsletterFactory` | `Newsletter` | status=DRAFT, send_to_all=True |
| `NotificationFactory` | `Notification` | type=GENERAL, is_read=False |
| `NotificationPreferenceFactory` | `NotificationPreference` | tous les courriels actifs, push actif, SMS inactif |

### Executer les tests

```bash
# Tous les tests du module communication
pytest apps/communication/ -v

# Tests des formulaires (validation bleach)
pytest apps/communication/tests/test_forms.py -v

# Tests API seulement
pytest apps/communication/tests/test_views_api.py -v

# Tests frontend seulement
pytest apps/communication/tests/test_views_frontend.py -v
```

---

## Dependances

| Dependance | Utilisation |
|------------|-------------|
| `apps.core.models.BaseModel` | Heritage des models (UUID, timestamps, is_active) |
| `apps.core.constants` | `NewsletterStatus`, `NotificationType` |
| `apps.core.permissions` | `IsMember`, `IsPastorOrAdmin` |
| `apps.core.mixins.W3CRMFormMixin` | Mixin pour le style des formulaires |
| `apps.members.Member` | FK vers les membres |
| `apps.members.Group` | M2M pour les groupes cibles des infolettres |
| `bleach` | Assainissement HTML (prevention XSS) |
| `django-filter` | Filtrage des endpoints API |
