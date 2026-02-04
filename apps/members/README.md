# Members App

Member management for ÉgliseConnect church management system.

## Overview

The members app handles:

- **Member Profiles**: Personal information, church roles, auto-generated member numbers
- **Families**: Group related members, shared address
- **Groups**: Cell groups, ministries, committees
- **Directory**: Member directory with privacy settings
- **Birthdays**: Birthday tracking and notifications

## Models

### Member

Church member profile with auto-generated member number (MBR-YYYY-XXXX).

**Fields:**
- `member_number`: Auto-generated unique identifier
- `user`: Optional link to Django User for authentication
- `first_name`, `last_name`: Name
- `email`, `phone`, `phone_secondary`: Contact info
- `birth_date`: For birthday tracking
- `address`, `city`, `province`, `postal_code`: Address
- `photo`: Profile photo
- `role`: Church role (member, volunteer, group_leader, pastor, treasurer, admin)
- `family_status`: Single, married, widowed, divorced
- `family`: Link to Family
- `joined_date`, `baptism_date`: Church membership dates
- `notes`: Pastoral notes (staff only)

### Family

Family unit grouping related members.

**Fields:**
- `name`: Family name (e.g., "Famille Dupont")
- `address`, `city`, `province`, `postal_code`: Shared address
- `notes`: Notes

### Group

Church groups (cells, ministries, committees).

**Fields:**
- `name`: Group name
- `group_type`: Cell, ministry, committee, class, choir, other
- `description`: Group description
- `leader`: Group leader (Member)
- `meeting_day`, `meeting_time`, `meeting_location`: Meeting schedule
- `email`: Group contact email

### DirectoryPrivacy

Privacy settings for member directory visibility.

**Fields:**
- `visibility`: Public, group, private
- `show_email`, `show_phone`, `show_address`, `show_birth_date`, `show_photo`: Field visibility

## API Endpoints

### Members

| Method | URL | Description | Permission |
|--------|-----|-------------|------------|
| GET | `/api/v1/members/members/` | List members | Staff sees all, members see self |
| POST | `/api/v1/members/members/` | Create member | Public (registration) |
| GET | `/api/v1/members/members/{uuid}/` | Get member | Owner or staff |
| PUT/PATCH | `/api/v1/members/members/{uuid}/` | Update member | Owner or staff |
| DELETE | `/api/v1/members/members/{uuid}/` | Delete member | Pastor/Admin |
| GET | `/api/v1/members/members/me/` | Current user's profile | Authenticated |
| GET | `/api/v1/members/members/birthdays/` | Birthdays list | Authenticated |
| GET | `/api/v1/members/members/directory/` | Member directory | Authenticated |

### Groups

| Method | URL | Description | Permission |
|--------|-----|-------------|------------|
| GET | `/api/v1/members/groups/` | List groups | Authenticated |
| POST | `/api/v1/members/groups/` | Create group | Pastor/Admin |
| GET | `/api/v1/members/groups/{uuid}/` | Get group | Authenticated |
| PUT/PATCH | `/api/v1/members/groups/{uuid}/` | Update group | Pastor/Admin |
| DELETE | `/api/v1/members/groups/{uuid}/` | Delete group | Pastor/Admin |
| GET | `/api/v1/members/groups/{uuid}/members/` | Group members | Authenticated |
| POST | `/api/v1/members/groups/{uuid}/add-member/` | Add member | Pastor/Admin |
| POST | `/api/v1/members/groups/{uuid}/remove-member/` | Remove member | Pastor/Admin |

### Families

| Method | URL | Description | Permission |
|--------|-----|-------------|------------|
| GET | `/api/v1/members/families/` | List families | Authenticated |
| POST | `/api/v1/members/families/` | Create family | Pastor/Admin |
| GET | `/api/v1/members/families/{uuid}/` | Get family | Authenticated |
| PUT/PATCH | `/api/v1/members/families/{uuid}/` | Update family | Pastor/Admin |

## Frontend URLs

| URL | View | Description |
|-----|------|-------------|
| `/members/` | `member_list` | List all members (staff only) |
| `/members/register/` | `member_create` | Registration form |
| `/members/{uuid}/` | `member_detail` | Member profile |
| `/members/{uuid}/edit/` | `member_update` | Edit profile |
| `/members/birthdays/` | `birthday_list` | Birthday list |
| `/members/directory/` | `directory` | Member directory |
| `/members/privacy-settings/` | `privacy_settings` | Privacy settings |
| `/members/groups/` | `group_list` | List groups |
| `/members/groups/{uuid}/` | `group_detail` | Group details |
| `/members/families/{uuid}/` | `family_detail` | Family details |

## Usage Examples

### Creating a Member

```python
from apps.members.models import Member

member = Member.objects.create(
    first_name='Jean',
    last_name='Dupont',
    email='jean@example.com',
    phone='514-555-0123',
)
# member_number is auto-generated
print(member.member_number)  # MBR-2026-0001
```

### Getting Birthdays

```python
from apps.core.utils import get_week_birthdays, get_today_birthdays

# Get today's birthdays
today = get_today_birthdays()

# Get this week's birthdays
week = get_week_birthdays()
```

### Checking Permissions

```python
from apps.core.permissions import IsPastor

class MyView(APIView):
    permission_classes = [IsPastor]
```

## Testing

Run tests with:

```bash
pytest apps/members/ -v
```

## Forms

- `MemberRegistrationForm`: Public registration
- `MemberProfileForm`: Profile updates (member)
- `MemberAdminForm`: Full edit form (staff)
- `FamilyForm`: Family management
- `GroupForm`: Group management
- `DirectoryPrivacyForm`: Privacy settings
- `MemberSearchForm`: Search/filter form
