# ÉgliseConnect - Church Management System

A comprehensive Django-based church management system for managing members, donations, events, volunteers, and communications.

## Features

- **Member Management**: Member profiles with auto-generated member numbers, families, groups, and directory
- **Donation Tracking**: Online and physical donations, campaigns, tax receipts (Canadian CRA compliant)
- **Event Management**: Calendar, RSVP, recurring events
- **Volunteer Scheduling**: Position management, scheduling, rotations, swap requests
- **Communication**: Newsletters, notifications, email/SMS integration
- **Help Requests**: Ticketing system for prayer, financial, material, and pastoral support
- **Reports & Dashboard**: Statistics, attendance tracking, financial reports

## Architecture

This project follows the **dual-layer architecture** with:
- **Frontend Views** (`views_frontend.py`): Django template-based views with HTMX/Alpine.js
- **API Views** (`views_api.py`): REST API endpoints using Django Rest Framework

## Project Structure

```
egliseconnect/
├── manage.py
├── requirements.txt
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/           # Base models, permissions, utilities
│   ├── members/        # Member management
│   ├── donations/      # Donations & accounting
│   ├── events/         # Events & calendar
│   ├── volunteers/     # Volunteer scheduling
│   ├── communication/  # Newsletter, notifications
│   ├── help_requests/  # Help request ticketing
│   └── reports/        # Dashboard & statistics
└── templates/
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Running Tests

```bash
pytest apps/ -v
```

## API Documentation

API documentation is available at `/api/docs/` when running the development server.

## URL Namespaces

- Frontend: `frontend:app_name:view_name`
- API: `api:v1:app_name:resource-name`

## Roles & Permissions

| Role | Description |
|------|-------------|
| `member` | Basic church member |
| `volunteer` | Active volunteer |
| `group_leader` | Leader of a group/ministry |
| `pastor` | Pastoral staff |
| `treasurer` | Financial administrator |
| `admin` | Full system access |

## License

Proprietary - All rights reserved.
