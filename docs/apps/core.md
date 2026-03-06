# App: Core

## Description
Infrastructure partagee pour l'ensemble du projet. Fournit les modeles abstraits, le systeme de permissions, les constantes, le middleware, l'audit et les utilitaires communs.

## Modeles

### Abstracts (apps/core/models.py)
| Modele | Description |
|--------|-------------|
| `BaseModel` | UUID PK, `created_at`, `updated_at`, `is_active`. Managers: `objects` (ActiveManager), `all_objects` (AllObjectsManager) |
| `SoftDeleteModel` | Extends BaseModel. `deleted_at`, `.delete()` = soft delete, `.restore()`, `.hard_delete()` |
| `TimeStampedMixin` | Juste `created_at`, `updated_at` (sans UUID) |
| `OrderedMixin` | `order` PositiveIntegerField |

### Concrets (apps/core/models_extended.py)
| Modele | Description |
|--------|-------------|
| `ChurchBranding` | Logo, couleurs, coordonnees eglise (singleton) |
| `WebhookEndpoint` | URLs webhook sortantes avec signature HMAC |
| `WebhookDelivery` | Log de livraison avec retry tracking |
| `AuditLog` | Trail d'audit (create/update/delete/login/export) |
| `Campus` | Support multi-campus |

### Audit (apps/core/audit.py)
| Modele | Description |
|--------|-------------|
| `LoginAudit` | IP, user agent, succes/echec, methode (password/totp/social/code) |

## Permissions (apps/core/permissions.py)

| Classe | Acces requis |
|--------|-------------|
| `IsMember` | Tout utilisateur authentifie |
| `IsVolunteer` | volunteer+ |
| `IsGroupLeader` | group_leader+ |
| `IsDeacon` | deacon+ |
| `IsPastor` | pastor, admin |
| `IsTreasurer` | treasurer, pastor, admin |
| `IsAdmin` | pastor, admin, superuser |
| `IsPastorOrAdmin` | STAFF_ROLES (deacon, pastor, admin) |
| `IsFinanceStaff` | FINANCE_ROLES + FinanceDelegation |
| `IsOwnerOrStaff` | Object owner ou staff (object-level) |
| `IsOwnerOrReadOnly` | Lecture tous, ecriture owner/staff |
| `CanViewMember` | Respecte DirectoryPrivacy (public/group/private) |

Pattern: Utilise `member.all_roles` (set) avec intersection (`&`) pour verifier les permissions multi-roles.

## Middleware (apps/core/middleware.py)

| Middleware | Role |
|-----------|------|
| `TwoFactorEnforcementMiddleware` | Redirige vers `/accounts/2fa/` si deadline 2FA depassee |
| `MembershipAccessMiddleware` | Restreint acces dashboard aux membres ACTIVE. Staff bypass. |
| `APIDeprecationHeadersMiddleware` | Ajoute headers `API-Version` et `Deprecation` aux reponses API |

## Mixins (apps/core/mixins.py)

### Auth Mixins (pour views template)
`MemberRequiredMixin`, `VolunteerRequiredMixin`, `GroupLeaderRequiredMixin`, `PastorRequiredMixin`, `TreasurerRequiredMixin`, `AdminRequiredMixin`, `FinanceStaffRequiredMixin`, `OwnerOrStaffRequiredMixin`

### Context Mixins
- `ChurchContextMixin`: Injecte `current_user_role`, `current_member`, `today_birthdays` (staff)
- `PageTitleMixin`: Ajoute `page_title` au contexte
- `BreadcrumbMixin`: Ajoute breadcrumbs

### Form Mixins
- `FormMessageMixin`: Messages flash succes/erreur automatiques
- `SetOwnerMixin`: Auto-set le champ owner au user courant
- `FilterByMemberMixin`: Filtre queryset par membre courant
- `W3CRMFormMixin`: Auto-apply classes Bootstrap CSS aux widgets de formulaire

## Constants (apps/core/constants.py)

50+ classes de constantes couvrant tous les domaines: `Roles`, `MembershipStatus`, `DonationType`, `PaymentMethod`, `EventType`, `RSVPStatus`, `VolunteerRole`, `ScheduleStatus`, etc.

## Signals
- `log_successful_login`: Cree LoginAudit + sync `two_factor_enabled`
- `log_failed_login`: Cree LoginAudit echec

## Celery Tasks
- `deliver_webhook`: Envoi webhook avec retry exponentiel
- `retry_failed_webhooks`: Relance periodique des webhooks echoues
- `cleanup_old_audit_logs`: Supprime logs > 365 jours
- `cleanup_old_webhook_deliveries`: Supprime deliveries > 90 jours

## Fichiers cles
- `apps/core/models.py` - Modeles abstraits
- `apps/core/permissions.py` - Toutes les permissions DRF
- `apps/core/constants.py` - Toutes les constantes
- `apps/core/middleware.py` - Middleware custom
- `apps/core/mixins.py` - Mixins views
- `apps/core/audit.py` - LoginAudit
- `apps/core/signals.py` - Signals auth
- `apps/core/allauth_forms.py` - CustomSignupForm avec invitation code
