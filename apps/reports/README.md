# Reports App

Dashboard and statistics for ÉgliseConnect.

## Features
- Main dashboard with summary statistics
- Member statistics and breakdowns
- Donation reports with monthly/yearly analysis
- Event attendance tracking
- Volunteer activity reports
- Birthday calendar

## API Endpoints

### Dashboard
- /api/v1/reports/dashboard/ - Complete dashboard summary
- /api/v1/reports/dashboard/members/ - Member statistics
- /api/v1/reports/dashboard/donations/ - Donation statistics
- /api/v1/reports/dashboard/events/ - Event statistics
- /api/v1/reports/dashboard/volunteers/ - Volunteer statistics
- /api/v1/reports/dashboard/help-requests/ - Help request statistics
- /api/v1/reports/dashboard/birthdays/ - Upcoming birthdays

### Reports
- /api/v1/reports/reports/attendance/ - Attendance report
- /api/v1/reports/reports/donations/{year}/ - Annual donation report
- /api/v1/reports/reports/volunteers/ - Volunteer activity report

### Treasurer Access
- /api/v1/reports/treasurer/donations/ - Treasurer donation report
- /api/v1/reports/treasurer/donations/{year}/ - Yearly report

## Frontend URLs
- /reports/ - Main dashboard
- /reports/members/ - Member statistics
- /reports/donations/ - Donation reports
- /reports/attendance/ - Attendance reports
- /reports/volunteers/ - Volunteer reports
- /reports/birthdays/ - Birthday calendar

## Permissions
- Dashboard: Pastor, Admin
- Donation Reports: Pastor, Admin, Treasurer
- Other Reports: Pastor, Admin
- Birthday Calendar: All authenticated members
