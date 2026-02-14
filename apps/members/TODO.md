# TODO - Members App

## P1 — Critical

### CRUD Completions

- [ ] Group CRUD: add create, edit, delete views in frontend (only list + detail exist)
- [ ] Family CRUD: add create, edit, delete frontend views (only detail exists)
- [ ] GroupMembership: add frontend for adding/removing members from groups
- [ ] Department: add delete view (create/edit exist, but no delete)

### Member Data Import/Export

- [ ] Add CSV/Excel import for bulk member creation (with field mapping wizard and validation preview)
- [ ] Add CSV/PDF/Excel export for member lists with configurable columns
- [ ] Add import error report (show which rows failed and why)
- [ ] Add import history log (who imported what, when, how many records)

### Child & Dependent Profiles

- [ ] Add child/dependent model linked to parent member(s) via Family
- [ ] Add child profile form (name, DOB, allergies, medical notes, authorized pickups)
- [ ] Add child list view on family detail page
- [ ] Add child check-in integration with attendance app (security tag, parent matching)

### Family Management

- [ ] Add family dashboard showing all family members, giving summary, attendance
- [ ] Add family merge tool (combine duplicate families)
- [ ] Add household address management (shared address across family members)

### Frontend Refinements

- [ ] Member list: add export to CSV/PDF button
- [ ] Directory: add pagination (currently shows all members at once)
- [ ] Member form: add photo upload preview before submission
- [ ] Profile modification request: add list view for staff to see all pending requests
- [ ] Disciplinary list: add date range filter alongside existing status/type filters
- [ ] My profile page: add "Edit my profile" button linking to member form

## P2 — Important

### Care & Follow-Up Tracking

- [ ] Add pastoral care model (visit type, date, notes, follow-up date, assigned pastor/deacon)
- [ ] Add care visit log on member detail page (visible to staff)
- [ ] Add follow-up reminder system (auto-notify pastor when follow-up date arrives)
- [ ] Add care dashboard for pastors (open follow-ups, recent visits, overdue items)

### Background Check Integration

- [ ] Add background check status model (check type, status, date, expiry, provider reference)
- [ ] Add background check tracking per volunteer/leader
- [ ] Add expiry alerts (notify admin when background checks need renewal)
- [ ] Add background check status indicator on member profile

### Small Group Lifecycle

- [ ] Add group lifecycle stages: launching, active, multiplying, closed
- [ ] Add group health metrics (attendance trend, member growth, leader feedback)
- [ ] Add group multiplication workflow (split group, assign new leader, transfer members)
- [ ] Add group finder for members (search by location, topic, day of week)

### Member Merge & Dedup

- [ ] Add duplicate detection tool (fuzzy match on name, email, phone, address)
- [ ] Add merge wizard (select primary record, preview merged result, confirm)
- [ ] Add merge audit trail (record which records were merged and by whom)

### Sidebar / Navigation

- [ ] Add "Departements" link under Membres section for admin/pastor users
- [ ] Add "Mon profil" link visible to all members (currently only accessible via header)
- [ ] Verify "Disciplinaire" link is visible only to staff roles (admin, pastor, deacon)

## P3 — Nice-to-Have

### Custom Member Fields

- [ ] Add church-configurable custom fields (text, date, dropdown, checkbox)
- [ ] Add custom field management in admin settings
- [ ] Add custom field display on member detail and forms
- [ ] Add custom field support in CSV import/export

### Member Self-Service Enhancements

- [ ] Add photo crop/resize tool on profile page
- [ ] Add address autocomplete via Google Places or Mapbox
- [ ] Add profile completeness indicator (percentage bar showing what fields are filled)

### Member Engagement Score

- [ ] Add composite engagement score based on attendance + giving + volunteering + group participation
- [ ] Add engagement score display on member profile (visible to staff)
- [ ] Add engagement trend chart (improving, declining, stable)
- [ ] Add at-risk member report (low engagement, declining attendance)

### Church Directory

- [ ] Add public-facing opt-in directory (members choose what info to share)
- [ ] Add directory search by name, group, ministry
- [ ] Add directory photo grid view
- [ ] Add PDF directory export for printing

### Existing Small Fixes

- [ ] Member detail: show department memberships section
- [ ] Member detail: show disciplinary history section (for staff)
- [ ] Department detail: add "Remove member" button
- [ ] Department list: show member count per department
- [ ] Birthday list: add "Send wishes" button/link
- [ ] Add member search autocomplete on disciplinary create form
