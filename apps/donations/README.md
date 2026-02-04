# Donations App

Donation management for ÉgliseConnect church management system.

## Overview

The donations app handles:

- **Online Donations**: Members can donate through the website
- **Physical Donations**: Treasurer can record cash, check, and other donations
- **Donation Campaigns**: Special fundraising projects with goals
- **Tax Receipts**: Annual tax receipts for CRA compliance

## Models

### Donation

Individual donation record with auto-generated number (DON-YYYYMM-XXXX).

**Fields:**
- `donation_number`: Auto-generated unique identifier
- `member`: Donor (Member)
- `amount`: Donation amount
- `donation_type`: Tithe, offering, special, campaign, building, missions, other
- `payment_method`: Cash, check, card, bank transfer, online, other
- `campaign`: Optional link to DonationCampaign
- `date`: Donation date
- `notes`: Notes
- `recorded_by`: Staff who recorded (for physical donations)
- `check_number`: For check payments
- `transaction_id`: For online payments
- `receipt_sent`: Whether receipt was sent

### DonationCampaign

Special fundraising campaign with goals.

**Fields:**
- `name`: Campaign name
- `description`: Description
- `goal_amount`: Target amount
- `start_date`, `end_date`: Campaign dates
- `image`: Campaign image

### TaxReceipt

Annual tax receipt for CRA.

**Fields:**
- `receipt_number`: Unique receipt number
- `member`: Recipient
- `year`: Tax year
- `total_amount`: Total donations for year
- `member_name`, `member_address`: Snapshot at generation time
- `pdf_file`: Generated PDF
- `email_sent`: Whether emailed

## API Endpoints

### Donations

| Method | URL | Description | Permission |
|--------|-----|-------------|------------|
| GET | `/api/v1/donations/donations/` | List donations | Finance sees all, members see own |
| POST | `/api/v1/donations/donations/` | Create donation | Authenticated |
| GET | `/api/v1/donations/donations/{uuid}/` | Get donation | Owner or finance |
| PUT/PATCH | `/api/v1/donations/donations/{uuid}/` | Update donation | Finance |
| DELETE | `/api/v1/donations/donations/{uuid}/` | Delete donation | Finance |
| GET | `/api/v1/donations/donations/my-history/` | My donations | Authenticated |
| POST | `/api/v1/donations/donations/record-physical/` | Record physical | Treasurer |
| GET | `/api/v1/donations/donations/summary/` | Statistics | Finance |

### Campaigns

| Method | URL | Description | Permission |
|--------|-----|-------------|------------|
| GET | `/api/v1/donations/campaigns/` | List campaigns | Authenticated |
| POST | `/api/v1/donations/campaigns/` | Create campaign | Pastor/Admin |
| GET | `/api/v1/donations/campaigns/{uuid}/` | Get campaign | Authenticated |
| GET | `/api/v1/donations/campaigns/active/` | Active campaigns | Authenticated |

### Tax Receipts

| Method | URL | Description | Permission |
|--------|-----|-------------|------------|
| GET | `/api/v1/donations/receipts/` | List receipts | Finance sees all, members see own |
| GET | `/api/v1/donations/receipts/{uuid}/` | Get receipt | Owner or finance |
| GET | `/api/v1/donations/receipts/my-receipts/` | My receipts | Authenticated |
| POST | `/api/v1/donations/receipts/generate/{year}/` | Generate receipts | Treasurer |

## Frontend URLs

| URL | View | Description |
|-----|------|-------------|
| `/donations/donate/` | `donation_create` | Make a donation |
| `/donations/history/` | `donation_history` | My donation history |
| `/donations/{uuid}/` | `donation_detail` | Donation details |
| `/donations/admin/` | `donation_admin_list` | All donations (finance) |
| `/donations/record/` | `donation_record` | Record physical (treasurer) |
| `/donations/campaigns/` | `campaign_list` | List campaigns |
| `/donations/campaigns/{uuid}/` | `campaign_detail` | Campaign details |
| `/donations/receipts/` | `receipt_list` | Tax receipts |
| `/donations/receipts/{uuid}/` | `receipt_detail` | Receipt details |
| `/donations/reports/monthly/` | `monthly_report` | Monthly report |

## Usage Examples

### Making a Donation

```python
from apps.donations.models import Donation
from apps.core.constants import DonationType, PaymentMethod

donation = Donation.objects.create(
    member=member,
    amount=Decimal('100.00'),
    donation_type=DonationType.TITHE,
    payment_method=PaymentMethod.ONLINE,
)
# donation_number is auto-generated
print(donation.donation_number)  # DON-202601-0001
```

### Generating Tax Receipts

```python
from apps.donations.models import TaxReceipt
from apps.core.utils import generate_receipt_number

# Calculate total for year
total = Donation.objects.filter(
    member=member,
    date__year=2026,
).aggregate(Sum('amount'))['amount__sum']

receipt = TaxReceipt.objects.create(
    receipt_number=generate_receipt_number(2026),
    member=member,
    year=2026,
    total_amount=total,
)
```

## Testing

Run tests with:

```bash
pytest apps/donations/ -v
```

## CRA Compliance

Tax receipts include:
- Church registration number
- Member name and address
- Total donations for the year
- Receipt number for tracking
- Generation date
