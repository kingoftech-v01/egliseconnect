# App: Payments (Paiements)

## Description
Integration Stripe pour paiements en ligne, dons recurrents (subscriptions), sessions kiosque, plans de paiement, employer matching, campagnes de dons, crypto et SMS donations.

## Modeles (10)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `StripeCustomer` | stripe_customer_id (unique) | OneToOne: Member |
| `OnlinePayment` | stripe_payment_intent_id, amount, currency, status, payment_method_type, receipt_email, stripe_receipt_url | OneToOne: Donation. FK: member, campaign |
| `RecurringDonation` | stripe_subscription_id, amount, frequency, next_payment_date, is_active_subscription | FK: member |
| `GivingStatement` | period_start/end, statement_type, total_amount, pdf_file | FK: member. Unique: [member, start, end, type] |
| `GivingGoal` | year, target_amount | FK: member. Unique: [member, year] |
| `SMSDonation` | phone_number, amount, command_text, is_recurring, frequency | FK: member |
| `KioskSession` | session_date, location, total_transactions, total_amount, reconciled | - |
| `PaymentPlan` | total_amount, installment_amount, frequency, remaining_amount, status | FK: member |
| `EmployerMatch` | employer_name, match_ratio, annual_cap, match_amount_received | FK: member |
| `GivingCampaign` | name, goal_amount, current_amount, start/end_date, is_year_end | - |

## Services (apps/payments/services.py)
- `PaymentService.get_or_create_stripe_customer(member)` - Cree/recupere Stripe Customer
- `PaymentService.create_payment_intent(member, amount, ...)` - Cree Stripe PaymentIntent + OnlinePayment local
- Mode dev fallback quand Stripe pas configure (simule le succes)

## API ViewSets (9+)
StripeCustomer, OnlinePayment, RecurringDonation, GivingStatement, GivingGoal, KioskSession, PaymentPlan, EmployerMatch, GivingCampaign + `stripe_webhook`, `twilio_sms_webhook`, `crypto_charge` endpoints

## Frontend Views
donate, payment_history, recurring create/cancel/edit, giving statements list/generate/bulk/download, giving goals set/list, kiosk session/reconcile, payment plans CRUD, employer matching, giving campaigns CRUD, crypto donation, webhook_errors, payment_confirmation

## Forms (7)
DonateForm, GivingGoalForm, BulkStatementForm, EditRecurringForm, PaymentPlanForm, EmployerMatchForm, GivingCampaignForm

## Points d'attention
- Stripe PaymentIntent flow (not Charges API)
- Subscriptions Stripe pour dons recurrents
- Dev mode fallback: simule Stripe quand les cles ne sont pas configurees
- SMS donations: parse commande texte (`GIVE 50`, `GIVE 100 MONTHLY`)
- Kiosk session reconciliation: rapprocher les transactions de la session
- Payment plans: progression trackee, statut (active/completed/defaulted/cancelled)
- Webhooks: Stripe et Twilio avec error monitoring

## Fichiers cles
- `apps/payments/models.py` - 10 modeles
- `apps/payments/services.py` - PaymentService (Stripe integration)
- `apps/payments/views_api.py` - ViewSets + webhooks
- `apps/payments/views_frontend.py` - Vues template
