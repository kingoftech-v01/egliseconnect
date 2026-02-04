# Core App

Base infrastructure for ÉgliseConnect church management system.

## Overview

The core app provides foundational components used across all other apps:

- **Base Models**: UUID primary keys, timestamps, soft delete
- **Constants**: Centralized choices and enums
- **Permissions**: Role-based permission classes
- **Utilities**: Helper functions for common operations
- **Mixins**: Reusable view mixins

## Components

### Models (`models.py`)

- `BaseModel`: Abstract base with UUID PK, `created_at`, `updated_at`, `is_active`
- `SoftDeleteModel`: Extends BaseModel with soft delete (`deleted_at`)
- `TimeStampedMixin`: Just timestamps without UUID
- `OrderedMixin`: Adds ordering capability

### Constants (`constants.py`)

All application-wide choices:

- `Roles`: Member roles (member, volunteer, group_leader, pastor, treasurer, admin)
- `FamilyStatus`: Single, married, widowed, divorced
- `GroupType`: Cell, ministry, committee, etc.
- `PrivacyLevel`: Public, group, private
- `DonationType`: Tithe, offering, special, campaign
- `PaymentMethod`: Cash, check, card, bank_transfer, online
- `EventType`: Worship, group, meal, special, meeting
- `RSVPStatus`: Pending, confirmed, declined, maybe
- `VolunteerRole`: Worship, hospitality, technical, etc.
- `ScheduleStatus`: Scheduled, confirmed, declined, completed, no_show
- `HelpRequestCategory`: Prayer, financial, material, pastoral
- `Urgency`: Low, medium, high, urgent
- `RequestStatus`: New, in_progress, resolved, closed
- `NewsletterStatus`: Draft, scheduled, sending, sent, failed
- `NotificationType`: Birthday, event, volunteer, etc.
- `Province`: Canadian provinces

### Permissions (`permissions.py`)

DRF permission classes:

- `IsMember`: Any authenticated member
- `IsVolunteer`: Volunteer role and above
- `IsGroupLeader`: Group leader and above
- `IsPastor`: Pastor and admin only
- `IsTreasurer`: Treasurer and admin only
- `IsAdmin`: Admin only
- `IsPastorOrAdmin`: Pastor or admin
- `IsFinanceStaff`: Treasurer, pastor, or admin
- `IsOwnerOrStaff`: Object owner or staff
- `IsOwnerOrReadOnly`: Owner can edit, others read-only
- `CanViewMember`: Based on privacy settings

### Mixins (`mixins.py`)

View mixins for Django CBVs:

**Permission Mixins:**
- `MemberRequiredMixin`
- `VolunteerRequiredMixin`
- `GroupLeaderRequiredMixin`
- `PastorRequiredMixin`
- `TreasurerRequiredMixin`
- `AdminRequiredMixin`
- `FinanceStaffRequiredMixin`
- `OwnerOrStaffRequiredMixin`

**Context Mixins:**
- `ChurchContextMixin`: Adds user role, member, today's birthdays
- `PageTitleMixin`: Adds page title
- `BreadcrumbMixin`: Adds breadcrumbs

**Form Mixins:**
- `FormMessageMixin`: Success/error messages
- `SetOwnerMixin`: Auto-sets owner on create

**Queryset Mixins:**
- `FilterByMemberMixin`: Filter by current member

### Utilities (`utils.py`)

Helper functions:

**Number Generation:**
- `generate_member_number()`: MBR-YYYY-XXXX
- `generate_donation_number()`: DON-YYYYMM-XXXX
- `generate_request_number()`: HR-YYYYMM-XXXX
- `generate_receipt_number()`: REC-YYYY-XXXX

**Birthday Utilities:**
- `get_today_birthdays()`
- `get_week_birthdays()`
- `get_month_birthdays(month)`
- `get_upcoming_birthdays(days)`

**Date Utilities:**
- `get_current_week_range()`
- `get_current_month_range()`
- `get_date_range(period)`

**Formatting:**
- `format_phone(phone)`
- `format_postal_code(postal_code)`
- `format_currency(amount)`

## Usage Examples

### Using BaseModel

```python
from apps.core.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'My Model'
```

### Using Permissions

```python
from rest_framework import viewsets
from apps.core.permissions import IsPastor

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPastor]
```

### Using View Mixins

```python
from django.views.generic import ListView
from apps.core.mixins import PastorRequiredMixin, ChurchContextMixin

class MemberListView(PastorRequiredMixin, ChurchContextMixin, ListView):
    model = Member
    template_name = 'members/list.html'
```

### Using Constants

```python
from apps.core.constants import Roles, DonationType

class Member(models.Model):
    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        default=Roles.MEMBER
    )

class Donation(models.Model):
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.OFFERING
    )
```

## Testing

Run tests with:

```bash
pytest apps/core/ -v
```
