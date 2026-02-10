# TODO - Core App

## Frontend Refinements

- [ ] Header search bar (`templates/elements/header.html`) is a non-functional placeholder — implement global search or remove the input
- [ ] Add active page highlighting in sidebar navigation (currently no visual indicator of current page)
- [ ] Add breadcrumb consistency across all pages (some pages have breadcrumbs, some don't)

## Sidebar / Navigation

- [ ] Verify all new app features (departments, disciplinary, payments history, worship) have corresponding sidebar links
- [ ] Add sidebar section collapsing memory (remember which sections user has expanded/collapsed)

## Permissions

- [ ] Add `IsDeacon` permission usage in views that should allow deacon access
- [ ] Review `IsFinanceStaff` usage to ensure delegated finance access works consistently across all donation/payment views

## PWA

- [ ] Add offline caching strategy for key pages (dashboard, my profile, my QR code)
- [ ] Add PWA install prompt banner for mobile users

## Code Cleanup

- [ ] Consolidate reminder logic — `apps/core/reminders.py` `send_reminder_batch()` is used by onboarding, volunteers, and worship; verify all apps use it consistently
- [ ] Add missing test coverage for `views_pwa.py` offline page rendering
