# Donations App

## Overview

The Donations app manages all financial giving within the EgliseConnect church management system. It provides a complete donation lifecycle -- from online and physical donation recording, through campaign-based fundraising, to CRA-compliant annual tax receipt generation. The app supports role-based access control ensuring that sensitive financial data is only accessible to authorized personnel (treasurers, pastors, administrators, and staff).

### Key Features

- **Online donations** -- Members submit donations through the web interface; payment method is automatically set to `online` and the donating member is inferred from the authenticated user.
- **Physical donation recording** -- Treasurers record cash, check, bank transfer, and other in-person donations on behalf of members, with automatic notification to the donor.
- **Fundraising campaigns** -- Pastors and admins create goal-based campaigns with start/end dates, images, and real-time progress tracking (current amount, percentage).
- **CRA-compliant tax receipts** -- Annual tax receipts are generated per member (one per year, enforced by `unique_together`). Member name and address are snapshot at generation time for historical accuracy. Receipts can be downloaded as PDF (via `xhtml2pdf`) and batch-emailed.
- **Monthly financial reports** -- Finance staff view donation totals broken down by type and payment method, filterable by month or custom date range.
- **Finance delegation** -- Pastors and admins can grant (and revoke) finance-level access to other members who do not inherently have finance roles, with notifications on both grant and revoke.
- **CSV export** -- Finance staff export filtered donation lists to CSV (UTF-8 BOM for Excel compatibility).
- **Donation filtering** -- Admin list supports filtering by date range, donation type, payment method, campaign, and member name/number.
- **Soft delete** -- Donations use `SoftDeleteModel`, preserving records for audit trails and accidental deletion recovery.
- **REST API** -- Full DRF-based API with filtering, searching, ordering, and role-based permissions.

---

## File Structure

```text
apps/donations/
    __init__.py
    admin.py                  # Django admin configuration (3 ModelAdmin classes)
    apps.py                   # AppConfig
    forms.py                  # 6 Django forms
    models.py                 # 4 models: Donation, DonationCampaign, TaxReceipt, FinanceDelegation
    serializers.py            # 11 DRF serializers
    urls.py                   # API router + frontend URL patterns
    views_api.py              # 3 DRF ViewSets
    views_frontend.py         # 19 function-based views
    migrations/
        __init__.py
        0001_initial.py
        ...
    templates/
        donations/
            campaign_delete.html
            campaign_detail.html
            campaign_form.html          # Used for both create and edit
            campaign_list.html
            donation_admin_list.html
            donation_delete.html
            donation_detail.html
            donation_edit.html
            donation_form.html          # Online donation form
            donation_history.html
            donation_record.html        # Physical donation recording
            monthly_report.html
            receipt_detail.html
            receipt_list.html
            receipt_pdf.html            # PDF template for xhtml2pdf
    tests/
        __init__.py
        factories.py
        test_finance_delegation.py
        test_forms.py
        test_models.py
        test_views_api.py
        test_views_frontend.py
```

One additional template lives at the project level:

```text
templates/
    donations/
        finance_delegations.html    # Finance delegation management page
```

---

## Models

All models use UUID primary keys inherited from `BaseModel` (which provides `id`, `created_at`, `updated_at`, `is_active`). The `Donation` model additionally inherits `deleted_at` from `SoftDeleteModel`.

### Donation

Individual donation record with an auto-generated donation number. Inherits from `SoftDeleteModel` (which extends `BaseModel`, adding `deleted_at` and soft-delete behavior).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUIDField` | PK, auto-generated | Inherited from `BaseModel` |
| `donation_number` | `CharField(20)` | Unique, non-editable | Auto-generated on first save via `core.utils.generate_donation_number()` (e.g. `DON-202601-0001`) |
| `member` | `ForeignKey` -> `Member` | `on_delete=PROTECT` | The donating member (related_name: `donations`) |
| `amount` | `DecimalField(12, 2)` | Required | Donation amount in dollars |
| `donation_type` | `CharField(20)` | Choices: `DonationType.CHOICES`, default: `offering` | Category of the donation |
| `payment_method` | `CharField(20)` | Choices: `PaymentMethod.CHOICES`, default: `cash` | How the donation was made |
| `campaign` | `ForeignKey` -> `DonationCampaign` | `on_delete=SET_NULL`, nullable, blank | Associated fundraising campaign (related_name: `donations`) |
| `date` | `DateField` | Default: `timezone.now` | Donation date |
| `notes` | `TextField` | Blank | Additional notes |
| `recorded_by` | `ForeignKey` -> `Member` | `on_delete=SET_NULL`, nullable, blank | Staff member who recorded a physical donation (related_name: `recorded_donations`) |
| `check_number` | `CharField(50)` | Blank | Check number (for check payments) |
| `transaction_id` | `CharField(100)` | Blank | Online transaction reference |
| `receipt_sent` | `BooleanField` | Default: `False` | Whether a receipt has been sent |
| `receipt_sent_date` | `DateTimeField` | Nullable, blank | When the receipt was sent |
| `is_active` | `BooleanField` | Default: `True` | Inherited from `BaseModel` |
| `created_at` | `DateTimeField` | Auto-set on create | Inherited from `BaseModel` |
| `updated_at` | `DateTimeField` | Auto-set on save | Inherited from `BaseModel` |
| `deleted_at` | `DateTimeField` | Nullable, blank | Inherited from `SoftDeleteModel`; set on soft delete |

**Computed properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `is_online` | `bool` | `True` if `payment_method` is `online` or `card` |

**Database indexes:** `donation_number`, `(member, date)`, `date`, `donation_type`, `payment_method`

**Ordering:** `-date`, `-created_at`

**`save()` behavior:** Auto-generates `donation_number` on first save if blank.

**DonationType choices:**

| Value | French Label | English |
|-------|-------------|---------|
| `tithe` | Dime | Tithe |
| `offering` | Offrande generale | General Offering |
| `special` | Offrande speciale | Special Offering |
| `campaign` | Campagne | Campaign |
| `building` | Batiment | Building |
| `missions` | Missions | Missions |
| `other` | Autre | Other |

**PaymentMethod choices:**

| Value | French Label | English |
|-------|-------------|---------|
| `cash` | Especes | Cash |
| `check` | Cheque | Check |
| `card` | Carte de credit/debit | Credit/Debit Card |
| `bank_transfer` | Virement bancaire | Bank Transfer |
| `online` | En ligne | Online |
| `other` | Autre | Other |

---

### DonationCampaign

Fundraising campaign with a financial goal and date range. Inherits from `BaseModel`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUIDField` | PK, auto-generated | Inherited from `BaseModel` |
| `name` | `CharField(200)` | Required | Campaign name |
| `description` | `TextField` | Blank | Detailed description |
| `goal_amount` | `DecimalField(12, 2)` | Default: `0.00` | Target fundraising amount |
| `start_date` | `DateField` | Required | Campaign start date |
| `end_date` | `DateField` | Nullable, blank | Campaign end date (open-ended if null) |
| `image` | `ImageField` | Blank, nullable, upload_to: `campaigns/%Y/` | Campaign image, validated by `validate_image_file` |
| `is_active` | `BooleanField` | Default: `True` | Inherited from `BaseModel` |
| `created_at` | `DateTimeField` | Auto-set on create | Inherited from `BaseModel` |
| `updated_at` | `DateTimeField` | Auto-set on save | Inherited from `BaseModel` |

**Computed properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `current_amount` | `Decimal` | Sum of all active donations linked to this campaign (returns `0.00` if none) |
| `progress_percentage` | `int` | Percentage towards goal, capped at 100 (returns 0 if `goal_amount` is 0) |
| `is_ongoing` | `bool` | `True` if campaign is active, has started, and has not ended |

**Ordering:** `-start_date`

---

### TaxReceipt

Annual CRA tax receipt. One receipt per member per year. Inherits from `BaseModel`.

Captures a snapshot of the member's name and address at generation time to ensure historical accuracy even if the member's information changes later.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUIDField` | PK, auto-generated | Inherited from `BaseModel` |
| `receipt_number` | `CharField(20)` | Unique | Format `REC-YYYY-XXXX`, generated via `core.utils.generate_receipt_number(year)` |
| `member` | `ForeignKey` -> `Member` | `on_delete=PROTECT` | The member this receipt is for (related_name: `tax_receipts`) |
| `year` | `PositiveIntegerField` | Required | Fiscal year |
| `total_amount` | `DecimalField(12, 2)` | Required | Total donations for the year |
| `generated_at` | `DateTimeField` | `auto_now_add=True` | When the receipt was generated |
| `generated_by` | `ForeignKey` -> `Member` | `on_delete=SET_NULL`, nullable, blank | Staff member who generated the receipt (related_name: `generated_receipts`) |
| `pdf_file` | `FileField` | Blank, nullable, upload_to: `receipts/%Y/` | Stored PDF file |
| `email_sent` | `BooleanField` | Default: `False` | Whether the receipt has been emailed |
| `email_sent_date` | `DateTimeField` | Nullable, blank | When the receipt email was sent |
| `member_name` | `CharField(200)` | Required | Snapshot of member's name at generation time |
| `member_address` | `TextField` | Blank | Snapshot of member's address at generation time |
| `is_active` | `BooleanField` | Default: `True` | Inherited from `BaseModel` |
| `created_at` | `DateTimeField` | Auto-set on create | Inherited from `BaseModel` |
| `updated_at` | `DateTimeField` | Auto-set on save | Inherited from `BaseModel` |

**Constraints:** `unique_together = ['member', 'year']` -- one receipt per member per year

**Database indexes:** `receipt_number`, `(member, year)`, `year`

**Ordering:** `-year`, `-generated_at`

**`save()` behavior:** On first save, auto-populates `member_name` from `member.full_name` and `member_address` from `member.full_address` if they are blank.

---

### FinanceDelegation

Delegation of finance access from a pastor/admin to another member. Inherits from `BaseModel`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUIDField` | PK, auto-generated | Inherited from `BaseModel` |
| `delegated_to` | `ForeignKey` -> `Member` | `on_delete=CASCADE` | Member receiving finance access (related_name: `finance_delegations_received`) |
| `delegated_by` | `ForeignKey` -> `Member` | `on_delete=CASCADE` | Pastor/admin granting access (related_name: `finance_delegations_granted`) |
| `granted_at` | `DateTimeField` | `auto_now_add=True` | When the delegation was granted |
| `revoked_at` | `DateTimeField` | Nullable, blank | When the delegation was revoked (null means still active) |
| `reason` | `TextField` | Blank | Reason for the delegation |
| `is_active` | `BooleanField` | Default: `True` | Inherited from `BaseModel` |
| `created_at` | `DateTimeField` | Auto-set on create | Inherited from `BaseModel` |
| `updated_at` | `DateTimeField` | Auto-set on save | Inherited from `BaseModel` |

**Computed properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `is_active_delegation` | `bool` | `True` if `is_active` is `True` and `revoked_at` is `None` |

**Ordering:** `-granted_at`

---

## Forms

All forms use the `W3CRMFormMixin` for consistent styling with the DexignZone/W3CRM frontend template.

### DonationForm

Online donation form for members. The `member` and `payment_method` fields are set automatically in the view.

| Field | Widget | Notes |
|-------|--------|-------|
| `amount` | `NumberInput` (min=1, step=0.01, placeholder="Montant en $") | Validated to be positive |
| `donation_type` | `Select` | Standard donation type choices |
| `campaign` | `Select` | Filtered to active campaigns only; optional |
| `notes` | `Textarea` (rows=2) | Optional |

### PhysicalDonationForm

Form for treasurers to record in-person donations (cash, check, bank transfer, other).

| Field | Widget | Notes |
|-------|--------|-------|
| `member` | `Select` | The donating member |
| `amount` | `NumberInput` (min=1, step=0.01) | Donation amount |
| `donation_type` | `Select` | Standard donation type choices |
| `payment_method` | `Select` | Restricted to: Cash, Check, Bank Transfer, Other |
| `date` | `DateInput` (type=date) | Donation date |
| `campaign` | `Select` | Active campaigns only; optional |
| `check_number` | `TextInput` | Required when `payment_method` is `check` |
| `notes` | `Textarea` (rows=2) | Optional |

**Custom validation:** If `payment_method` is `check`, `check_number` is required.

### DonationEditForm

Form for finance staff to edit an existing donation.

| Field | Widget | Notes |
|-------|--------|-------|
| `amount` | `NumberInput` (min=1, step=0.01) | Validated to be positive |
| `donation_type` | `Select` | Standard donation type choices |
| `payment_method` | `Select` | All payment method choices |
| `date` | `DateInput` (type=date) | Donation date |
| `campaign` | `Select` | Active campaigns only; optional |
| `check_number` | `TextInput` | Check number |
| `notes` | `Textarea` (rows=2) | Optional |

### DonationCampaignForm

Create/edit fundraising campaigns.

| Field | Widget | Notes |
|-------|--------|-------|
| `name` | `TextInput` | Campaign name |
| `description` | `Textarea` (rows=3) | Description |
| `goal_amount` | `NumberInput` (min=0, step=0.01) | Financial goal |
| `start_date` | `DateInput` (type=date) | Start date |
| `end_date` | `DateInput` (type=date) | End date; must be after start date |
| `image` | `FileInput` | Campaign image |
| `is_active` | `CheckboxInput` | Enable/disable the campaign |

**Custom validation:** `end_date` must be after `start_date`.

### DonationFilterForm

Filter form used in the admin donation list and CSV export views.

| Field | Widget | Notes |
|-------|--------|-------|
| `date_from` | `DateInput` (type=date) | Filter from this date |
| `date_to` | `DateInput` (type=date) | Filter until this date |
| `donation_type` | `Select` | Filter by type (includes "All" default option) |
| `payment_method` | `Select` | Filter by payment method (includes "All" default option) |
| `campaign` | `ModelChoiceField` | Filter by campaign (includes "All" empty label) |
| `member` | `TextInput` (placeholder="Nom ou numero") | Search by member name or member number |

### DonationReportForm

Form for generating donation reports with flexible period selection.

| Field | Widget | Notes |
|-------|--------|-------|
| `period` | `Select` | Choices: Month, Quarter, Year, Custom |
| `year` | `NumberInput` | Year (2000-2100); optional |
| `month` | `NumberInput` | Month (1-12); optional |
| `date_from` | `DateInput` (type=date) | Start date for custom period |
| `date_to` | `DateInput` (type=date) | End date for custom period |
| `group_by` | `Select` | Group by: Type, Payment Method, Campaign, or Member |

---

## Serializers

| Serializer | Used For | Key Fields |
|------------|----------|------------|
| `DonationListSerializer` | `list` action | `id`, `donation_number`, `member`, `member_name`, `amount`, `donation_type`, `donation_type_display`, `payment_method`, `payment_method_display`, `campaign`, `campaign_name`, `date`, `receipt_sent` |
| `DonationSerializer` | `retrieve`, `update`, `partial_update` | All donation fields plus display names for type, method, campaign, and `recorded_by_name`. Read-only: `donation_number`, `created_at`, `updated_at` |
| `DonationCreateSerializer` | `create` action (online donations) | `amount`, `donation_type`, `campaign`, `notes`. Validates amount > 0. Member set from request |
| `PhysicalDonationCreateSerializer` | `record_physical` action | `member`, `amount`, `donation_type`, `payment_method`, `date`, `campaign`, `check_number`, `notes`. Validates amount > 0 and requires `check_number` for check payments |
| `MemberDonationHistorySerializer` | `my_history` action | `id`, `donation_number`, `amount`, `donation_type`, `donation_type_display`, `campaign`, `campaign_name`, `date` |
| `DonationCampaignSerializer` | Campaign detail | All campaign fields plus computed: `current_amount`, `progress_percentage`, `is_ongoing`, `donation_count` |
| `DonationCampaignListSerializer` | Campaign list | `id`, `name`, `goal_amount`, `current_amount`, `progress_percentage`, `start_date`, `end_date`, `is_ongoing` |
| `TaxReceiptSerializer` | Receipt detail | All receipt fields plus `member_full_name`. Read-only: `receipt_number`, `generated_at`, `member_name`, `member_address` |
| `TaxReceiptListSerializer` | Receipt list | `id`, `receipt_number`, `member`, `member_full_name`, `year`, `total_amount`, `email_sent` |
| `DonationSummarySerializer` | `summary` action | `period`, `total_amount`, `donation_count`, `average_donation`, `by_type` (dict), `by_method` (dict) |
| `MemberDonationSummarySerializer` | Per-member summary | `member_id`, `member_name`, `total_amount`, `donation_count`, `last_donation_date` |

---

## API Endpoints

All API endpoints are prefixed with `/donations/api/` and require authentication. The three ViewSets are registered via a DRF `DefaultRouter`.

### Donations (`/donations/api/donations/`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/donations/api/donations/` | List donations | `IsMember` (finance staff see all; regular members see their own) |
| `POST` | `/donations/api/donations/` | Create an online donation | `IsMember` (member and `payment_method=online` set automatically) |
| `GET` | `/donations/api/donations/{uuid}/` | Retrieve donation detail | `IsMember` (scoped by queryset) |
| `PUT` | `/donations/api/donations/{uuid}/` | Full update | `IsFinanceStaff` |
| `PATCH` | `/donations/api/donations/{uuid}/` | Partial update | `IsFinanceStaff` |
| `DELETE` | `/donations/api/donations/{uuid}/` | Delete donation (soft delete) | `IsFinanceStaff` |
| `GET` | `/donations/api/donations/my-history/` | Current user's donation history (optional `?year=` filter) | `IsMember` |
| `POST` | `/donations/api/donations/record-physical/` | Record a physical donation (cash, check, etc.) | `IsTreasurer` |
| `GET` | `/donations/api/donations/summary/` | Donation statistics for a period (`?period=month\|year`, `?year=`, `?month=`) | `IsFinanceStaff` |

**Filters:** `donation_type`, `payment_method`, `campaign`, `date`
**Search:** `donation_number`, `member__first_name`, `member__last_name`
**Ordering:** `date`, `amount`, `created_at` (default: `-date`, `-created_at`)

### Campaigns (`/donations/api/campaigns/`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/donations/api/campaigns/` | List all campaigns | `IsMember` |
| `POST` | `/donations/api/campaigns/` | Create a campaign | `IsPastorOrAdmin` |
| `GET` | `/donations/api/campaigns/{uuid}/` | Retrieve campaign detail | `IsMember` |
| `PUT` | `/donations/api/campaigns/{uuid}/` | Full update | `IsPastorOrAdmin` |
| `PATCH` | `/donations/api/campaigns/{uuid}/` | Partial update | `IsPastorOrAdmin` |
| `DELETE` | `/donations/api/campaigns/{uuid}/` | Delete campaign | `IsPastorOrAdmin` |
| `GET` | `/donations/api/campaigns/active/` | List currently active campaigns (started and not ended) | `IsMember` |

**Filters:** `is_active`
**Search:** `name`, `description`
**Ordering:** `name`, `start_date`, `goal_amount` (default: `-start_date`)

### Tax Receipts (`/donations/api/receipts/`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| `GET` | `/donations/api/receipts/` | List tax receipts | `IsMember` (finance staff see all; regular members see their own) |
| `POST` | `/donations/api/receipts/` | Create a tax receipt manually | `IsTreasurer` |
| `GET` | `/donations/api/receipts/{uuid}/` | Retrieve receipt detail | `IsMember` (scoped by queryset) |
| `PUT` | `/donations/api/receipts/{uuid}/` | Full update | `IsTreasurer` |
| `PATCH` | `/donations/api/receipts/{uuid}/` | Partial update | `IsTreasurer` |
| `DELETE` | `/donations/api/receipts/{uuid}/` | Delete receipt | `IsTreasurer` |
| `GET` | `/donations/api/receipts/my-receipts/` | Current user's tax receipts | `IsMember` |
| `POST` | `/donations/api/receipts/generate/{year}/` | Generate receipts for a year | `IsTreasurer` |

The `generate` endpoint accepts an optional `?member={uuid}` query parameter. If provided, it generates a receipt for that single member. Otherwise, it generates receipts for all members who made donations that year. Existing receipts are returned as-is (not regenerated). Only members with active donations totaling more than $0 for the specified year receive a receipt.

**Filters:** `year`, `email_sent`
**Search:** `receipt_number`, `member__first_name`, `member__last_name`
**Ordering:** `year`, `generated_at`, `total_amount` (default: `-year`, `-generated_at`)

---

## Frontend URLs

All frontend URLs are prefixed with `/donations/` and require `@login_required`. URL names are namespaced under `frontend:donations:`.

### Donation Views

| Path | View | Name | Allowed Roles |
|------|------|------|---------------|
| `/donations/donate/` | `donation_create` | `donation_create` | Any authenticated member |
| `/donations/history/` | `donation_history` | `donation_history` | Any authenticated member (sees own history, filterable by year, paginated 20/page) |
| `/donations/<uuid:pk>/` | `donation_detail` | `donation_detail` | Donation owner, or Treasurer / Pastor / Admin / Staff |
| `/donations/<uuid:pk>/edit/` | `donation_edit` | `donation_edit` | Treasurer, Pastor, Admin, Staff |
| `/donations/<uuid:pk>/delete/` | `donation_delete` | `donation_delete` | Admin, Staff only |
| `/donations/admin/` | `donation_admin_list` | `donation_admin_list` | Treasurer, Pastor, Admin, Staff (paginated 50/page) |
| `/donations/admin/export/` | `donation_export_csv` | `donation_export_csv` | Treasurer, Pastor, Admin, Staff |
| `/donations/record/` | `donation_record` | `donation_record` | Treasurer, Admin, Staff |

### Campaign Views

| Path | View | Name | Allowed Roles |
|------|------|------|---------------|
| `/donations/campaigns/` | `campaign_list` | `campaign_list` | Any authenticated member |
| `/donations/campaigns/create/` | `campaign_create` | `campaign_create` | Treasurer, Pastor, Admin, Staff |
| `/donations/campaigns/<uuid:pk>/` | `campaign_detail` | `campaign_detail` | Any authenticated member |
| `/donations/campaigns/<uuid:pk>/edit/` | `campaign_update` | `campaign_update` | Treasurer, Pastor, Admin, Staff |
| `/donations/campaigns/<uuid:pk>/delete/` | `campaign_delete` | `campaign_delete` | Treasurer, Pastor, Admin, Staff |

### Receipt Views

| Path | View | Name | Allowed Roles |
|------|------|------|---------------|
| `/donations/receipts/` | `receipt_list` | `receipt_list` | Any member (sees own); Treasurer / Admin / Staff see all |
| `/donations/receipts/batch-email/` | `receipt_batch_email` | `receipt_batch_email` | Treasurer, Pastor, Admin, Staff (POST only) |
| `/donations/receipts/<uuid:pk>/` | `receipt_detail` | `receipt_detail` | Receipt owner, or Treasurer / Admin / Staff |
| `/donations/receipts/<uuid:pk>/pdf/` | `receipt_download_pdf` | `receipt_download_pdf` | Receipt owner, or Treasurer / Admin / Staff |

### Report Views

| Path | View | Name | Allowed Roles |
|------|------|------|---------------|
| `/donations/reports/monthly/` | `donation_monthly_report` | `monthly_report` | Treasurer, Pastor, Admin, Staff |

### Finance Delegation Views

| Path | View | Name | Allowed Roles |
|------|------|------|---------------|
| `/donations/delegations/` | `finance_delegations` | `finance_delegations` | Pastor, Admin only |
| `/donations/delegations/grant/` | `delegate_finance_access` | `delegate_finance_access` | Pastor, Admin only (POST) |
| `/donations/delegations/<uuid:pk>/revoke/` | `revoke_finance_access` | `revoke_finance_access` | Pastor, Admin only (POST) |

---

## Templates

### App-Level Templates (`apps/donations/templates/donations/`)

| Template | Description |
|----------|-------------|
| `campaign_delete.html` | Campaign deletion confirmation page |
| `campaign_detail.html` | Campaign detail with goal, progress bar, and 10 most recent donations |
| `campaign_form.html` | Create/edit campaign form (shared by `campaign_create` and `campaign_update` views) |
| `campaign_list.html` | List of active campaigns with progress indicators |
| `donation_admin_list.html` | Admin donation list with filter form, totals, and pagination (50 per page) |
| `donation_delete.html` | Donation deletion confirmation page (admin only) |
| `donation_detail.html` | Full donation detail (number, amount, type, method, campaign, notes, receipt status) |
| `donation_edit.html` | Edit donation form for finance staff |
| `donation_form.html` | Online donation form for members |
| `donation_history.html` | Paginated member donation history with year filter (20 per page) |
| `donation_record.html` | Physical donation recording form for treasurers |
| `monthly_report.html` | Monthly report with totals, counts, and breakdowns by type and payment method |
| `receipt_detail.html` | Tax receipt detail with PDF download link |
| `receipt_list.html` | Paginated list of tax receipts (20 per page) |
| `receipt_pdf.html` | HTML template rendered to PDF by xhtml2pdf; includes church name, address, and registration number from Django settings (`CHURCH_NAME`, `CHURCH_ADDRESS`, `CHURCH_REGISTRATION`) |

### Project-Level Templates (`templates/donations/`)

| Template | Description |
|----------|-------------|
| `finance_delegations.html` | Finance delegation management page with active/revoked delegation lists and grant form |

---

## Admin Configuration

Three `ModelAdmin` classes are registered. The `FinanceDelegation` model is **not** registered in the admin -- it is managed exclusively through the frontend delegation views.

### DonationAdmin (extends `SoftDeleteModelAdmin`)

- **List display:** `donation_number`, `member`, `amount`, `donation_type`, `payment_method`, `date`, `receipt_sent`
- **List filters:** `donation_type`, `payment_method`, `date`, `receipt_sent`, `campaign`
- **Search fields:** `donation_number`, `member__first_name`, `member__last_name`, `member__member_number`
- **Read-only fields:** `id`, `donation_number`, `created_at`, `updated_at`, `deleted_at`
- **Autocomplete fields:** `member`, `campaign`, `recorded_by`
- **Date hierarchy:** `date`
- **Fieldsets:**
  - Don -- `donation_number`, `member`, `amount`, `donation_type`, `payment_method`, `date`
  - Campagne (collapsible) -- `campaign`
  - Details du paiement (collapsible) -- `check_number`, `transaction_id`
  - Enregistrement -- `recorded_by`, `notes`
  - Recu -- `receipt_sent`, `receipt_sent_date`
  - Statut -- `is_active`, `deleted_at`
  - Metadonnees (collapsible) -- `id`, `created_at`, `updated_at`

### DonationCampaignAdmin (extends `BaseModelAdmin`)

- **List display:** `name`, `goal_amount`, `current_amount`, `progress_percentage`, `start_date`, `end_date`, `is_active`
- **List filters:** `is_active`, `start_date`
- **Search fields:** `name`, `description`
- **Read-only fields:** `id`, `current_amount`, `progress_percentage`, `created_at`, `updated_at`
- **Computed columns:** `current_amount` (formatted as `$X`), `progress_percentage` (formatted as `X%`)
- **Fieldsets:**
  - General -- `name`, `description`, `image`
  - Objectif -- `goal_amount`, `current_amount`, `progress_percentage`
  - Dates -- `start_date`, `end_date`
  - Statut -- `is_active`
  - Metadonnees (collapsible) -- `id`, `created_at`, `updated_at`

### TaxReceiptAdmin (extends `BaseModelAdmin`)

- **List display:** `receipt_number`, `member`, `year`, `total_amount`, `email_sent`, `generated_at`
- **List filters:** `year`, `email_sent`, `generated_at`
- **Search fields:** `receipt_number`, `member__first_name`, `member__last_name`, `member_name`
- **Read-only fields:** `id`, `receipt_number`, `member_name`, `member_address`, `generated_at`, `created_at`, `updated_at`
- **Autocomplete fields:** `member`, `generated_by`
- **Fieldsets:**
  - General -- `receipt_number`, `member`, `year`, `total_amount`
  - Member info snapshot (collapsible) -- `member_name`, `member_address`
  - Generation -- `generated_at`, `generated_by`, `pdf_file`
  - Envoi -- `email_sent`, `email_sent_date`
  - Metadonnees (collapsible) -- `id`, `created_at`, `updated_at`

---

## Permissions Matrix

### Frontend Views

| Action | Member | Treasurer | Pastor | Admin | Staff |
|--------|--------|-----------|--------|-------|-------|
| Make online donation | Yes | Yes | Yes | Yes | Yes |
| View own donation history | Yes | Yes | Yes | Yes | Yes |
| View own donation detail | Yes | Yes | Yes | Yes | Yes |
| View any donation detail | -- | Yes | Yes | Yes | Yes |
| Edit any donation | -- | Yes | Yes | Yes | Yes |
| Delete any donation | -- | -- | -- | Yes | Yes |
| View admin donation list | -- | Yes | Yes | Yes | Yes |
| Export donations to CSV | -- | Yes | Yes | Yes | Yes |
| Record physical donation | -- | Yes | -- | Yes | Yes |
| View campaigns | Yes | Yes | Yes | Yes | Yes |
| Create/edit/delete campaigns | -- | Yes | Yes | Yes | Yes |
| View own tax receipts | Yes | Yes | Yes | Yes | Yes |
| View all tax receipts | -- | Yes | -- | Yes | Yes |
| Download own receipt PDF | Yes | Yes | Yes | Yes | Yes |
| Download any receipt PDF | -- | Yes | -- | Yes | Yes |
| Batch-email receipts | -- | Yes | Yes | Yes | Yes |
| View monthly report | -- | Yes | Yes | Yes | Yes |
| Manage finance delegations | -- | -- | Yes | Yes | -- |
| Grant/revoke finance access | -- | -- | Yes | Yes | -- |

### API Permission Classes

| Permission Class | Who Has Access | Description |
|------------------|---------------|-------------|
| `IsMember` | Any authenticated user | Base-level access for all logged-in users |
| `IsTreasurer` | Treasurer, Admin, Staff | Required for recording physical donations and generating tax receipts |
| `IsPastorOrAdmin` | Pastor, Admin, Staff | Required for campaign create/update/delete via API |
| `IsFinanceStaff` | Treasurer, Pastor, Admin, Staff, or members with active finance delegation | Required for editing/deleting donations and viewing statistics |
| `IsOwnerOrStaff` | Object owner (via `obj.member` or `obj.user`) or Django staff | Object-level permission for resource ownership checks |

**Note on finance delegation:** Members who receive a finance delegation gain finance-level access via the `IsFinanceStaff` DRF permission class, which checks for active delegations in addition to role-based checks. The frontend views check roles directly and do not currently factor in delegations.

---

## Dependencies

### Internal App Dependencies

| Dependency | Usage |
|------------|-------|
| `apps.core.models.BaseModel` | Base class for `DonationCampaign`, `TaxReceipt`, `FinanceDelegation` |
| `apps.core.models.SoftDeleteModel` | Base class for `Donation` (soft-delete support) |
| `apps.core.constants.DonationType` | Donation type choices (`tithe`, `offering`, `special`, `campaign`, `building`, `missions`, `other`) |
| `apps.core.constants.PaymentMethod` | Payment method choices (`cash`, `check`, `card`, `bank_transfer`, `online`, `other`) |
| `apps.core.constants.Roles` | Role-based access checks (`MEMBER`, `VOLUNTEER`, `GROUP_LEADER`, `DEACON`, `TREASURER`, `PASTOR`, `ADMIN`) |
| `apps.core.validators.validate_image_file` | Image upload validation for campaign images |
| `apps.core.utils.generate_donation_number` | Auto-generates donation numbers (format: `DON-YYYYMM-XXXX`) |
| `apps.core.utils.generate_receipt_number` | Auto-generates tax receipt numbers (format: `REC-YYYY-XXXX`) |
| `apps.core.permissions` | DRF permission classes: `IsMember`, `IsTreasurer`, `IsPastorOrAdmin`, `IsFinanceStaff`, `IsOwnerOrStaff` |
| `apps.core.mixins.W3CRMFormMixin` | Form styling mixin for the DexignZone/W3CRM template |
| `apps.core.admin.SoftDeleteModelAdmin` | Admin base class for soft-deletable models |
| `apps.core.admin.BaseModelAdmin` | Admin base class for standard models |
| `apps.members.models.Member` | Foreign key target for all member references (`member`, `recorded_by`, `generated_by`, `delegated_to`, `delegated_by`) |
| `apps.communication.models.Notification` | Used to create donation confirmation and delegation notifications |

### External Python Dependencies

| Package | Usage |
|---------|-------|
| `djangorestframework` | API ViewSets, serializers, permissions, pagination |
| `django-filter` | `DjangoFilterBackend` for API queryset filtering |
| `xhtml2pdf` | PDF generation for tax receipt downloads (optional; graceful fallback with error message if not installed) |

---

## Tests

Tests are located in `apps/donations/tests/` and organized by concern.

| File | Description |
|------|-------------|
| `factories.py` | Test data factories for `Donation`, `DonationCampaign`, `TaxReceipt`, `FinanceDelegation`, and related objects |
| `test_models.py` | Donation number auto-generation, computed properties (`is_online`, `current_amount`, `progress_percentage`, `is_ongoing`, `is_active_delegation`), `TaxReceipt` snapshot behavior, `unique_together` constraint, soft-delete |
| `test_forms.py` | Amount validation, campaign queryset filtering, check number requirement for check payments, date validation (end after start), filter form behavior, report form choices |
| `test_views_api.py` | Full CRUD for all three ViewSets, role-based permission checks, custom actions (`my-history`, `record-physical`, `summary`, `generate`, `active`, `my-receipts`), filtering, searching, ordering |
| `test_views_frontend.py` | Page access for all roles, form submission, redirections, pagination, CSV export, PDF download, batch email, campaign CRUD, notification creation |
| `test_finance_delegation.py` | Delegation model behavior, `is_active_delegation` property, grant and revoke workflows, notification creation on grant/revoke, access control enforcement |

### Running Tests

```bash
# All donation tests
python manage.py test apps.donations

# Individual test modules
python manage.py test apps.donations.tests.test_models
python manage.py test apps.donations.tests.test_forms
python manage.py test apps.donations.tests.test_views_api
python manage.py test apps.donations.tests.test_views_frontend
python manage.py test apps.donations.tests.test_finance_delegation
```
