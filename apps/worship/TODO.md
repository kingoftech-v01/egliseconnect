# TODO - Worship App

## CRUD Completions

- [ ] Add service delete view (create and edit exist, but no delete)
- [ ] Add section edit and delete views (currently only add section)
- [ ] Add assignment remove/unassign view

## Frontend Refinements

- [ ] Service list: add date range filter
- [ ] Service detail: add print view for worship order (printable service program)
- [ ] Section management: add section reordering (drag & drop to change order)
- [ ] My assignments: show confirm/decline buttons inline (currently requires navigating to respond URL)
- [ ] Service detail: show confirmation rate as a visual progress bar

## Sidebar / Navigation

- [ ] Add "Creer un culte" link in sidebar under Cultes for staff roles
- [ ] Add "Mes assignations" link in sidebar visible to all members
- [ ] Verify "Cultes" section is visible in sidebar for all members with full access

## Small Complementary Features

- [ ] Add notification when a new assignment is created (currently handled by WorshipServiceManager)
- [ ] Service detail: add "Publish/Finalize" button to change status from draft to planned/confirmed
- [ ] Add eligible member list management UI (currently EligibleMemberList model exists but no frontend)
- [ ] Add service duplication (copy sections from a previous service as template)
- [ ] Service list: add calendar view alongside list view
- [ ] Add API endpoints (currently `api_urlpatterns = []`)

## Admin Configuration

- [ ] Upgrade admin registration from basic `admin.site.register()` to custom ModelAdmin classes with list_display, list_filter, search_fields, and inlines
