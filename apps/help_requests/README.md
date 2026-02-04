# Help Requests App

Help request ticketing system for ÉgliseConnect.

## Features
- Help request submission
- Category management (Prayer, Financial, Material, Pastoral)
- Urgency levels (Low, Medium, High, Urgent)
- Request assignment to staff
- Comment system with internal notes
- Confidential requests (pastor-only visibility)

## API Endpoints
- /api/v1/help-requests/requests/ - Help request CRUD
- /api/v1/help-requests/requests/my-requests/ - User's own requests
- /api/v1/help-requests/requests/{uuid}/assign/ - Assign request
- /api/v1/help-requests/requests/{uuid}/resolve/ - Resolve request
- /api/v1/help-requests/requests/{uuid}/comment/ - Add comment
- /api/v1/help-requests/categories/ - List categories

## Frontend URLs
- /help-requests/create/ - Submit new request
- /help-requests/ - All requests (staff only)
- /help-requests/my-requests/ - User's requests
- /help-requests/{uuid}/ - Request detail
- /help-requests/{uuid}/update/ - Update status
- /help-requests/{uuid}/comment/ - Add comment

## Models
- HelpRequestCategory - Categories (Prayer, Financial, etc.)
- HelpRequest - Main request with auto-generated number (HR-YYYYMM-XXXX)
- HelpRequestComment - Comments with internal note option

## Permissions
- Members: Create own requests, view own requests
- Group Leaders: View group members' non-confidential requests
- Pastors/Admins: Full access, manage internal notes
