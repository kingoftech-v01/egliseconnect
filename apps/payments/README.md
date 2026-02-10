# Payments App

## Overview

The payments app integrates Stripe for online donations and recurring giving. It provides a donation page with Stripe Elements, payment history, recurring donation management, and webhook handling. Successful payments are automatically linked to the donations app by creating Donation records.

### Key Features

- **Stripe Elements**: Client-side payment form using Stripe.js
- **One-time Donations**: PaymentIntent-based donations with type and campaign selection
- **Recurring Donations**: Stripe Subscription-based recurring giving (weekly/monthly)
- **Webhook Handling**: Receives `payment_intent.succeeded` and `payment_intent.payment_failed` events
- **Donation Integration**: Automatically creates `Donation` records on successful payments
- **Payment History**: Members see their own history; admin/pastor/treasurer see all
- **Refund Support**: Admin API action for refunding successful payments
- **Development Mode**: Graceful fallback with mock IDs when Stripe is not configured

## File Structure

```
apps/payments/
├── __init__.py
├── admin.py                 # Django admin configuration
├── apps.py                  # App config
├── models.py                # StripeCustomer, OnlinePayment, RecurringDonation
├── serializers.py           # DRF serializers + CreatePaymentIntentSerializer, CreateRecurringSerializer
├── services.py              # PaymentService (Stripe operations)
├── urls.py                  # Frontend + API URL patterns
├── views_api.py             # DRF ViewSets + StripeWebhookView
├── views_frontend.py        # Template-based views (4 views)
├── migrations/
│   └── 0001_initial.py
└── tests/
    ├── __init__.py
    ├── factories.py          # Test factories
    ├── test_models.py        # Model tests
    ├── test_services.py      # PaymentService tests
    ├── test_views_api.py     # API endpoint tests
    └── test_views_frontend.py # Frontend view tests
```

## Models

### PaymentStatus (Constants)

| Value | Label |
|-------|-------|
| `pending` | En attente |
| `processing` | En cours |
| `succeeded` | Reussi |
| `failed` | Echoue |
| `refunded` | Rembourse |
| `cancelled` | Annule |

### RecurringFrequency (Constants)

| Value | Label |
|-------|-------|
| `weekly` | Hebdomadaire |
| `monthly` | Mensuel |

### StripeCustomer

Links a member to their Stripe customer account.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | OneToOneField → Member | The church member |
| `stripe_customer_id` | CharField(100) | Stripe customer identifier (unique) |

### OnlinePayment

Individual online payment via Stripe.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | ForeignKey → Member | The paying member |
| `donation` | OneToOneField → Donation | Linked donation record (created on success) |
| `stripe_payment_intent_id` | CharField(100) | Stripe PaymentIntent ID (unique) |
| `amount` | DecimalField(12,2) | Payment amount |
| `currency` | CharField(3) | Currency code (default: `CAD`) |
| `status` | CharField(30) | Payment status (see PaymentStatus) |
| `donation_type` | CharField(20) | Type: `offering`, `tithe`, `building_fund`, etc. |
| `campaign` | ForeignKey → DonationCampaign | Optional campaign link |
| `receipt_email` | EmailField | Email for receipt |
| `stripe_receipt_url` | URLField | Stripe-hosted receipt URL |

**Properties:**
- `amount_display` → `str`: Formatted amount with currency (e.g., "50.00 CAD")
- `is_successful` → `bool`: True if status is `succeeded`

### RecurringDonation

Recurring donation via Stripe Subscription.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | ForeignKey → Member | The donating member |
| `stripe_subscription_id` | CharField(100) | Stripe Subscription ID (unique) |
| `amount` | DecimalField(12,2) | Recurring amount |
| `currency` | CharField(3) | Currency code (default: `CAD`) |
| `frequency` | CharField(20) | `weekly` or `monthly` |
| `donation_type` | CharField(20) | Type (default: `tithe`) |
| `next_payment_date` | DateField | Next scheduled payment |
| `is_active_subscription` | BooleanField | Whether the subscription is active |
| `cancelled_at` | DateTimeField | When the subscription was cancelled |

**Properties:**
- `amount_display` → `str`: Formatted amount with currency

## Services

### PaymentService

Central business logic for all Stripe operations:

| Method | Description |
|--------|-------------|
| `get_or_create_stripe_customer(member)` | Get or create a StripeCustomer for a member |
| `create_payment_intent(member, amount, donation_type, campaign)` | Create Stripe PaymentIntent + local OnlinePayment record |
| `handle_payment_succeeded(payment_intent_id, receipt_url)` | Webhook handler: mark succeeded, create Donation, notify member |
| `handle_payment_failed(payment_intent_id, failure_reason)` | Webhook handler: mark failed, notify member |
| `refund_payment(payment)` | Refund a successful payment via Stripe |
| `create_recurring_donation(member, amount, frequency, donation_type)` | Create Stripe Subscription + local RecurringDonation |
| `cancel_recurring_donation(recurring)` | Cancel Stripe Subscription, mark inactive |

### `get_stripe()`

Helper function that imports and configures the Stripe module. Returns `None` if Stripe is not installed or `STRIPE_SECRET_KEY` is not set, enabling development without Stripe.

## Serializers

| Serializer | Model/Type | Description |
|------------|------------|-------------|
| `StripeCustomerSerializer` | StripeCustomer | Member name + Stripe ID |
| `OnlinePaymentSerializer` | OnlinePayment | Full payment details with computed fields |
| `RecurringDonationSerializer` | RecurringDonation | Full subscription details |
| `CreatePaymentIntentSerializer` | Plain Serializer | `amount`, `donation_type`, `campaign_id` (optional) |
| `CreateRecurringSerializer` | Plain Serializer | `amount`, `frequency`, `donation_type` |

## API Endpoints

Base path: `/api/v1/payments/`

### OnlinePaymentViewSet (ReadOnly + Actions)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/payments/` | List payments (own or all for staff) | Authenticated |
| GET | `/payments/{id}/` | Payment details | Authenticated |
| POST | `/payments/create_intent/` | Create Stripe PaymentIntent | Authenticated |
| POST | `/payments/{id}/refund/` | Refund a payment | Pastor/Admin |

### RecurringDonationViewSet (ReadOnly + Actions)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/recurring/` | List recurring donations | Authenticated |
| GET | `/recurring/{id}/` | Recurring donation details | Authenticated |
| POST | `/recurring/create_subscription/` | Create recurring donation | Authenticated |
| POST | `/recurring/{id}/cancel/` | Cancel recurring donation | Authenticated (own only) |

### StripeWebhookView
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/webhook/` | Stripe webhook endpoint | CSRF-exempt, signature validated |

Handled events: `payment_intent.succeeded`, `payment_intent.payment_failed`

## Frontend URLs

Base path: `/payments/`

| URL | View | Name | Roles |
|-----|------|------|-------|
| `/payments/donate/` | `donate` | `payments:donate` | All members |
| `/payments/success/` | `donation_success` | `payments:donation_success` | All members |
| `/payments/history/` | `payment_history` | `payments:payment_history` | All (own); Admin/Pastor/Treasurer (all) |
| `/payments/recurring/` | `recurring_manage` | `payments:recurring_manage` | All members (own) |

## Templates

All templates are in `templates/payments/` and extend `base.html`.

| Template | View | Description |
|----------|------|-------------|
| `donate.html` | `donate` | Donation form with Stripe Elements, campaign and type selection |
| `donation_success.html` | `donation_success` | Payment confirmation page |
| `payment_history.html` | `payment_history` | Payment history list |
| `recurring_manage.html` | `recurring_manage` | Active and cancelled recurring donations |

## Admin Configuration

All 3 models are registered in Django admin:

- **StripeCustomerAdmin**: list by member/Stripe ID/date, search by member name/Stripe ID
- **OnlinePaymentAdmin**: list by member/amount/currency/status/type/date, filter by status/type/currency, date hierarchy
- **RecurringDonationAdmin**: list by member/amount/frequency/type/active/date, filter by active/frequency/type

## Permissions Matrix

| Action | Member | Volunteer | Group Leader | Deacon | Treasurer | Pastor | Admin |
|--------|--------|-----------|-------------|--------|-----------|--------|-------|
| Make a donation | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View own payment history | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View all payment history | — | — | — | — | Yes | Yes | Yes |
| Manage own recurring | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Refund payments | — | — | — | — | — | Yes | Yes |

## Dependencies

- **members**: Member model (payer)
- **donations**: Donation model (linked on success), DonationCampaign model (campaign selection)
- **communication**: Notification model (payment success/failure notifications)
- **core**: BaseModel, constants (DonationType, PaymentMethod), permissions (IsPastorOrAdmin)
- **External**: `stripe` Python library (optional, graceful fallback), Stripe.js (frontend)

## Configuration

Required settings in `config/settings/`:

| Setting | Description |
|---------|-------------|
| `STRIPE_PUBLIC_KEY` | Stripe publishable key (for frontend) |
| `STRIPE_SECRET_KEY` | Stripe secret key (for backend API calls) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (for event verification) |

## Tests

Test files in `apps/payments/tests/`:
- `factories.py` — Test data factories
- `test_models.py` — Model creation, properties, constraints
- `test_services.py` — PaymentService (mock Stripe interactions)
- `test_views_api.py` — API endpoint tests (payment intent, webhook, refund)
- `test_views_frontend.py` — Frontend view tests (access control, rendering)
