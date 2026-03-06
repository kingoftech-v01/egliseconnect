# App: Donations (Dons et finances)

## Description
Gestion financiere complete: dons, campagnes de collecte, recus fiscaux, delegations financieres, pledges, releves, objectifs de don, import, analytics, kiosque et crypto-monnaie.

## Modeles (12)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `DonationCampaign` | name, description, goal_amount, start/end_date, image | - |
| `Donation` (SoftDelete) | donation_number (DON-YYYY-XXXX), amount, donation_type, payment_method, date, receipt_sent, currency | FK: member, campaign, recorded_by |
| `TaxReceipt` | receipt_number, year, total_amount, pdf_file, member_name/address (snapshot) | FK: member, generated_by. Unique: [member, year] |
| `FinanceDelegation` | granted_at, revoked_at, reason | FK: delegated_to, delegated_by |
| `Pledge` | amount, frequency, start/end_date, status | FK: member, campaign |
| `PledgeFulfillment` | amount, date | FK: pledge, donation |
| `GivingStatement` | year, period (mid_year/annual), total_amount, pdf_file | FK: member. Unique: [member, year, period] |
| `GivingGoal` | year, target_amount | FK: member. Unique: [member, year] |
| `DonationImport` | file, status, total_rows, imported_count, skipped_count | FK: imported_by |
| `DonationImportRow` | row_number, data_json, status, error_message | FK: donation_import, donation |
| `MatchingCampaign` | matcher_name, match_ratio, match_cap, matched_total | FK: campaign |
| `CryptoDonation` | crypto_type, wallet_address, amount_crypto, amount_cad, status | FK: member, OneToOne: donation |

## Proprietes calculees
- `DonationCampaign.current_amount` → somme des dons de la campagne
- `DonationCampaign.progress_percentage` → current/goal * 100
- `Pledge.fulfilled_amount` → somme des PledgeFulfillment
- `Pledge.remaining_amount` → amount - fulfilled_amount
- `GivingGoal.current_amount` → somme des dons de l'annee

## API ViewSets (10)
- `DonationViewSet` - Filtre: type, method, campaign, date. Search: number, member name. Role-scoped.
- `DonationCampaignViewSet` - CRUD campagnes
- `TaxReceiptViewSet` - Generation et consultation recus
- `PledgeViewSet` - CRUD pledges
- `GivingStatementViewSet` - Releves de dons
- `GivingGoalViewSet` - Objectifs personnels
- `DonationImportViewSet` - Import CSV/OFX
- `MatchingCampaignViewSet` - Campagnes matching
- `CryptoDonationViewSet` - Dons crypto
- `DonationAnalyticsViewSet` - Tendances, analytics

## Frontend Views (35+)
Donation CRUD, campaign management, tax receipt generation/emailing, finance delegation, pledge CRUD, giving statements, giving goals, import wizard (CSV/OFX), analytics dashboard, kiosk giving mode, crypto donations, monthly report

## Forms (12)
DonationForm, PhysicalDonationForm, DonationCampaignForm, DonationEditForm, DonationFilterForm, DonationReportForm, PledgeForm, MemberPledgeForm, GivingGoalForm, ImportUploadForm, KioskDonationForm, CryptoDonationForm, StatementGenerateForm

## Points d'attention
- Les templates sont dans `apps/donations/templates/donations/` (seule app avec templates au niveau app)
- `FinanceDelegation` etend l'acces finance a des non-tresoriers (verifie par `IsFinanceStaff`)
- Les recus fiscaux font un snapshot du nom/adresse au moment de la generation
- Le numero de don est auto-genere dans `save()` avec format DON-YYYY-XXXX

## Fichiers cles
- `apps/donations/models.py` - 12 modeles financiers
- `apps/donations/views_api.py` - 10 ViewSets
- `apps/donations/views_frontend.py` - 35+ vues
- `apps/donations/forms.py` - 12 formulaires
- `apps/donations/templates/donations/` - Templates (dans l'app, pas global)
