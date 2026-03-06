# Communication App

## Overview

The Communication app manages all messaging channels for EgliseConnect: email newsletters, in-app notifications, and per-member notification preferences. It supports a full newsletter lifecycle (draft, schedule, send) with HTML sanitization, recipient tracking with open/delivery metrics, and a configurable notification preference system across email, push, and SMS channels.

### Key Features

- Newsletter management with full CRUD, send, and schedule workflows
- HTML content sanitization via bleach (XSS prevention)
- Per-recipient delivery tracking (sent, opened, failed)
- In-app notifications with type filtering and bulk mark-as-read
- Per-member notification preferences (email, push, SMS toggles)
- Role-based access: staff (pastor/admin) manage newsletters; members view sent ones
- REST API with search, filtering, and custom actions
- Recipient count estimation on create/edit forms

## File Structure

```
apps/communication/
    __init__.py
    admin.py              # Admin registration for all 4 models
    apps.py               # App configuration
    forms.py              # NewsletterForm with bleach sanitization
    models.py             # Newsletter, NewsletterRecipient, Notification, NotificationPreference
    serializers.py        # DRF serializers (4 classes)
    urls.py               # API router + frontend URL patterns
    views_api.py          # 3 DRF ViewSets with custom actions
    views_frontend.py     # 9 frontend views
    tests/
        __init__.py
        factories.py      # Test data factories
        test_forms.py     # Form validation tests
        test_models.py    # Model tests
        test_views_api.py # API endpoint tests
        test_views_frontend.py  # Frontend view tests
```

## Models

All models extend `BaseModel` (UUID primary key, `created_at`, `updated_at`, `is_active`).

### Newsletter

Email newsletter with lifecycle management.

| Field | Type | Description |
|-------|------|-------------|
| `subject` | CharField(200) | Newsletter subject line |
| `content` | TextField | HTML body content |
| `content_plain` | TextField | Plain text fallback (optional) |
| `created_by` | FK(Member) | Author (SET_NULL on delete) |
| `status` | CharField(20) | draft, scheduled, sending, sent, failed |
| `scheduled_for` | DateTimeField | Scheduled delivery datetime (nullable) |
| `sent_at` | DateTimeField | Actual send datetime (nullable) |
| `send_to_all` | BooleanField | True = all active members; False = target groups only |
| `target_groups` | M2M(Group) | Target groups when `send_to_all` is False |
| `recipients_count` | PositiveIntegerField | Number of recipients (populated on send) |
| `opened_count` | PositiveIntegerField | Number of opens tracked |

### NewsletterRecipient

Per-recipient delivery and engagement tracking.

| Field | Type | Description |
|-------|------|-------------|
| `newsletter` | FK(Newsletter) | Parent newsletter (CASCADE) |
| `member` | FK(Member) | Recipient member (CASCADE) |
| `email` | EmailField | Email address used for delivery |
| `sent_at` | DateTimeField | When the email was sent (nullable) |
| `opened_at` | DateTimeField | When the email was opened (nullable) |
| `failed` | BooleanField | Whether delivery failed |
| `failure_reason` | TextField | Error details if failed |

Unique constraint: `(newsletter, member)`.

### Notification

In-app notification for a specific member.

| Field | Type | Description |
|-------|------|-------------|
| `member` | FK(Member) | Target member (CASCADE) |
| `title` | CharField(200) | Notification title |
| `message` | TextField | Notification body |
| `notification_type` | CharField(50) | Type from NotificationType choices |
| `link` | URLField | Optional action URL |
| `is_read` | BooleanField | Read status (default False) |
| `read_at` | DateTimeField | When marked as read (nullable) |

### NotificationPreference

Per-member settings for notification channels. One-to-one with Member.

| Field | Type | Description |
|-------|------|-------------|
| `member` | OneToOne(Member) | Owner member (CASCADE) |
| `email_newsletter` | BooleanField | Receive newsletters by email (default True) |
| `email_events` | BooleanField | Receive event notifications (default True) |
| `email_birthdays` | BooleanField | Receive birthday notifications (default True) |
| `push_enabled` | BooleanField | Enable push notifications (default True) |
| `sms_enabled` | BooleanField | Enable SMS notifications (default False) |

## Forms

### NewsletterForm

Extends `W3CRMFormMixin` + `ModelForm`.

| Field | Widget | Notes |
|-------|--------|-------|
| `subject` | Default | Required |
| `content` | Textarea(rows=10) | HTML sanitized via bleach on clean |
| `content_plain` | Textarea(rows=5) | Optional plain text version |
| `send_to_all` | Default checkbox | Toggle audience scope |
| `target_groups` | Default select | Active when `send_to_all` is False |

**HTML Sanitization:** The `clean_content()` method uses bleach with a whitelist of safe tags (`a`, `b`, `blockquote`, `br`, `div`, `em`, `h1`-`h6`, `hr`, `i`, `img`, `li`, `ol`, `p`, `pre`, `span`, `strong`, `table`, `tbody`, `td`, `th`, `thead`, `tr`, `u`, `ul`) and safe attributes (href, style, class, src, alt, etc.). The same whitelist is reused by the API serializer.

## Serializers

### NewsletterSerializer

Full model serializer with computed fields:
- `status_display` — human-readable status label
- `created_by_name` — author's full name
- `validate_content()` — bleach sanitization (same whitelist as form)

### NewsletterListSerializer

Lightweight serializer for list endpoints: `id`, `subject`, `status`, `status_display`, `sent_at`, `recipients_count`, `opened_count`.

### NotificationSerializer

Full model serializer with:
- `type_display` — human-readable notification type

### NotificationPreferenceSerializer

Fields: `email_newsletter`, `email_events`, `email_birthdays`, `push_enabled`, `sms_enabled`.

## API Endpoints

Base path: `/communication/api/`

### Newsletter API

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/newsletters/` | List newsletters (filterable by status, searchable by subject) | IsMember |
| POST | `/newsletters/` | Create newsletter | IsPastorOrAdmin |
| GET | `/newsletters/{id}/` | Retrieve newsletter detail | IsMember |
| PUT | `/newsletters/{id}/` | Update newsletter | IsPastorOrAdmin |
| PATCH | `/newsletters/{id}/` | Partial update newsletter | IsPastorOrAdmin |
| DELETE | `/newsletters/{id}/` | Delete newsletter | IsPastorOrAdmin |
| POST | `/newsletters/{id}/send/` | Trigger immediate delivery | IsPastorOrAdmin |
| POST | `/newsletters/{id}/schedule/` | Schedule for future delivery | IsPastorOrAdmin |

### Notification API

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/notifications/` | List current user's notifications | IsMember |
| GET | `/notifications/{id}/` | Retrieve notification detail | IsMember |
| POST | `/notifications/mark-read/` | Mark specific or all notifications as read | IsMember |
| GET | `/notifications/unread_count/` | Get unread notification count | IsMember |

### Notification Preference API

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/preferences/` | List preferences | IsMember |
| GET/PUT/PATCH | `/preferences/me/` | Get or update current user's preferences | IsMember |

## Frontend URLs

Base path: `/communication/`

| Path | View | Description |
|------|------|-------------|
| `newsletters/` | `newsletter_list` | List newsletters (staff sees all, members see sent only) |
| `newsletters/create/` | `newsletter_create` | Create new newsletter (staff only) |
| `newsletters/<uuid:pk>/` | `newsletter_detail` | View newsletter details |
| `newsletters/<uuid:pk>/edit/` | `newsletter_edit` | Edit draft newsletter (staff only) |
| `newsletters/<uuid:pk>/delete/` | `newsletter_delete` | Delete newsletter with POST confirmation (staff only) |
| `newsletters/<uuid:pk>/send/` | `newsletter_send` | Send or schedule newsletter (staff only, POST) |
| `notifications/` | `notification_list` | List user's notifications with type filter |
| `notifications/mark-all-read/` | `mark_all_read` | Mark all notifications as read (POST) |
| `preferences/` | `preferences` | View/update notification preferences |

## Templates

All in `templates/communication/`:

| Template | Description |
|----------|-------------|
| `newsletter_list.html` | Paginated newsletter list with status indicators |
| `newsletter_detail.html` | Newsletter content display with staff action buttons |
| `newsletter_form.html` | Create/edit form with recipient count display |
| `newsletter_delete.html` | Delete confirmation page |
| `notification_list.html` | Paginated notifications with type filter dropdown |
| `preferences.html` | Toggle switches for notification channel preferences |

## Admin Configuration

All 4 models are registered with `BaseModelAdmin`:

| Model | List Display | List Filter | Search |
|-------|-------------|-------------|--------|
| Newsletter | subject, status, sent_at, recipients_count, opened_count | status, sent_at | subject |
| NewsletterRecipient | newsletter, member, sent_at, opened_at, failed | failed, newsletter | — |
| Notification | member, title, notification_type, is_read, created_at | notification_type, is_read | title, message |
| NotificationPreference | member, email_newsletter, email_events, push_enabled | — | — |

## Permissions Matrix

| Action | Member | Volunteer | Group Leader | Deacon | Treasurer | Pastor | Admin |
|--------|--------|-----------|--------------|--------|-----------|--------|-------|
| View sent newsletters | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View all newsletters | — | — | — | — | — | Yes | Yes |
| Create newsletter | — | — | — | — | — | Yes | Yes |
| Edit newsletter | — | — | — | — | — | Yes | Yes |
| Delete newsletter | — | — | — | — | — | Yes | Yes |
| Send/schedule newsletter | — | — | — | — | — | Yes | Yes |
| View own notifications | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Mark notifications read | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Manage own preferences | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

## Dependencies

- **core** — BaseModel, constants (NewsletterStatus, NotificationType), permissions (IsMember, IsPastorOrAdmin), mixins (W3CRMFormMixin)
- **members** — Member model (FK for created_by, notifications, preferences), Group model (M2M for target_groups)
- **bleach** — HTML sanitization for newsletter content
- **django-filter** — DRF filter backend for status filtering

## Tests

152 test functions across 4 test files:

| File | Count | Coverage |
|------|-------|----------|
| `test_views_frontend.py` | 79 | All 9 frontend views, access control, form validation |
| `test_views_api.py` | 52 | All 3 ViewSets, custom actions, permissions |
| `test_forms.py` | 17 | Newsletter form validation, bleach sanitization |
| `test_models.py` | 4 | Model creation, string representation |
