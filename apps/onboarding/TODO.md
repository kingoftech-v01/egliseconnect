# TODO - Onboarding App

## P1 — Critical

### Mentor/Buddy Assignment

- [ ] Add MentorAssignment model (new_member, mentor, start_date, status, notes)
- [ ] Add mentor matching UI (admin assigns mentor from available member list)
- [ ] Add mentor dashboard (see assigned mentees, check-in status, notes)
- [ ] Add mentee view (see assigned mentor, contact info, meeting schedule)
- [ ] Add mentor-mentee check-in log (record meetings, progress notes)

### Custom Onboarding Form Builder

- [ ] Add configurable profile fields per church (custom questions during registration)
- [ ] Add form field types: text, dropdown, checkbox, date, file upload
- [ ] Add conditional logic (show field B only if field A = "yes")
- [ ] Add form data export (CSV of all onboarding form submissions)

### Automated Welcome Sequence

- [ ] Add email/SMS welcome sequence triggered on new member registration
- [ ] Add sequence template: Day 1 (welcome), Day 3 (intro to ministries), Day 7 (invitation to group)
- [ ] Add sequence tracking (which step each member is on, opened/clicked)
- [ ] Add sequence customization per church

### Frontend Refinements

- [ ] Invitation delete: add confirmation dialog (currently just a POST to deactivate)
- [ ] Course form: add lesson reordering (drag & drop to change lesson order)
- [ ] Pipeline: add bulk actions (approve multiple members, send batch reminders)
- [ ] Training detail: add progress percentage display as a visual progress bar
- [ ] Admin review: add quick-action buttons inline (approve/reject without scrolling)

## P2 — Important

### Onboarding Progress Dashboard

- [ ] Add visual journey map for the member (step-by-step progress indicator)
- [ ] Add estimated completion date/time for each step
- [ ] Add "What's next?" guidance at each stage
- [ ] Add congratulations page/notification on onboarding completion

### Integration with Attendance

- [ ] Auto-detect first-time visitors from attendance check-in (new QR scan, no member profile)
- [ ] Add first-time visitor follow-up trigger (auto-create onboarding record)
- [ ] Add visitor-to-member conversion tracking (how many visitors become members)
- [ ] Add visitor follow-up assignment (assign staff to follow up with first-time visitors)

### Digital Document Signing

- [ ] Add document model (title, content, requires_signature, template)
- [ ] Add e-signature capture (typed name + date as legal signature)
- [ ] Add signed document storage and retrieval
- [ ] Add document types: membership covenant, volunteer agreement, child safety policy
- [ ] Add signature status tracking per member (signed, pending, expired)

### Sidebar / Navigation

- [ ] Verify "Invitations" link is in sidebar admin section
- [ ] Add "Statistiques" link under Adhesions in sidebar for admin/pastor

## P3 — Nice-to-Have

### Multi-Track Onboarding Paths

- [ ] Add onboarding tracks (different paths for: new believer, transfer member, youth, family)
- [ ] Add track assignment based on member type or admin selection
- [ ] Add track-specific courses, documents, and milestones
- [ ] Add track comparison analytics (which track has best completion rate)

### Gamification

- [ ] Add achievement/badge system (badges for: completed profile, first group, first volunteer shift)
- [ ] Add progress points per completed step
- [ ] Add achievement display on member profile
- [ ] Add leaderboard for new members (encouragement, not competition)

### Video-Based Training

- [ ] Add video lesson support (embed YouTube/Vimeo in course lessons)
- [ ] Add video completion tracking (did the member watch the full video?)
- [ ] Add quiz/assessment after video lessons
- [ ] Add certificate of completion for video courses

### Existing Small Fixes

- [ ] Interview result: add notification to member about outcome
- [ ] Stats page: add chart visualizations (pipeline, monthly registrations)
- [ ] Add reminder for expired/expiring forms in pipeline view
- [ ] Course detail: add participant count display
- [ ] Training: add "Download materials" button for each lesson's PDF
- [ ] Admin pipeline: add search/filter by member name
- [ ] Invitation list: add "Copy code" button for easy sharing
