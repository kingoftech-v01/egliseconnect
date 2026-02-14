# TODO - Core App

## P1 — Critical

### Global Search
- [ ] Implement global search across members, events, donations, groups (header search bar is currently non-functional placeholder)
- [ ] Add search results page with categorized sections (members, events, donations, help requests)
- [ ] Add AJAX autocomplete/typeahead for instant results as user types

### Real-Time Notifications
- [ ] Add WebSocket support via Django Channels for real-time in-app notifications
- [ ] Add notification badge count in header (unread notification count, auto-updating)
- [ ] Add toast/popup notifications for high-priority alerts (new assignment, help request, etc.)

### API Rate Limiting & Throttling
- [ ] Add DRF throttle classes (per-user, per-IP, per-endpoint) to prevent abuse
- [ ] Add rate limit headers in API responses (X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] Add admin-configurable rate limits per API consumer/token

### Navigation & UX
- [ ] Add active page highlighting in sidebar navigation (currently no visual indicator of current page)
- [ ] Add breadcrumb consistency across all pages (some pages have breadcrumbs, some don't)
- [ ] Verify all app features (departments, disciplinary, payments, worship) have corresponding sidebar links
- [ ] Add sidebar section collapsing memory (remember which sections user has expanded/collapsed via localStorage)

### PWA Enhancements
- [ ] Add offline caching strategy for key pages (dashboard, my profile, my QR code) via service worker
- [ ] Add PWA install prompt banner for mobile users
- [ ] Add background sync for offline form submissions (queue and retry when online)

### Permissions Gaps
- [ ] Add `IsDeacon` permission usage in views that should allow deacon access
- [ ] Review `IsFinanceStaff` usage to ensure delegated finance access works consistently across all donation/payment views

## P2 — Important

### Multi-Language Support
- [ ] Add full English UI toggle (all templates, messages, form labels) using Django's i18n framework
- [ ] Add language preference per member (stored in profile or preferences)
- [ ] Extract all hardcoded French strings into translation files (.po/.mo)
- [ ] Add language switcher in header/footer

### Custom Theme & Branding
- [ ] Add church-configurable branding settings (logo, primary color, church name) stored in database
- [ ] Add dynamic CSS variable injection based on branding settings
- [ ] Add branding preview in admin settings page

### API OAuth2 & External Access
- [ ] Add OAuth2 token support for third-party app integrations (django-oauth-toolkit)
- [ ] Add API key management page for admin (generate, revoke, set scopes)
- [ ] Add developer documentation portal for API consumers

### Webhook System
- [ ] Add outgoing webhook system for external integrations (configurable per-event triggers)
- [ ] Support webhook events: member.created, donation.received, event.created, attendance.checked_in
- [ ] Add webhook delivery log with retry mechanism for failed deliveries
- [ ] Add webhook secret/signature verification (HMAC-SHA256)

### Audit & Activity Logging
- [ ] Add comprehensive audit log viewer for admins (who changed what, when)
- [ ] Add activity feed on dashboard (recent actions across all apps: new members, donations, events)
- [ ] Add data export for audit logs (CSV/JSON)

## P3 — Nice-to-Have

### Feature Flags
- [ ] Add feature flag system for gradual rollouts (enable/disable features per church or per role)
- [ ] Add admin UI for managing feature flags
- [ ] Add feature flag checks in templates and views

### API Versioning
- [ ] Implement API versioning strategy (URL-based: /api/v1/, /api/v2/)
- [ ] Add deprecation headers for old API versions
- [ ] Add API changelog documentation

### Multi-Tenant / Multi-Campus
- [ ] Add multi-campus support (single database, campus-scoped data)
- [ ] Add campus selector in header for multi-campus users
- [ ] Add campus-level permissions (campus pastor vs. global admin)

### Code Quality
- [ ] Consolidate reminder logic — verify all apps use `send_reminder_batch()` consistently
- [ ] Add missing test coverage for `views_pwa.py` offline page rendering
- [ ] Add type hints across all core utility functions
- [ ] Add OpenAPI/Swagger documentation auto-generation for all API endpoints
