# TODO - Attendance App

## P1 — Critical

### Child Check-In/Check-Out System

- [ ] Add ChildCheckIn model (child, parent_member, session, check_in_time, check_out_time, security_code)
- [ ] Add security tag generation (unique code printed on parent receipt + child label)
- [ ] Add parent matching verification on check-out (must present matching security code)
- [ ] Add allergy/medical alert display on check-in (prominent warning for allergies, medications)
- [ ] Add authorized pickup list per child (only listed adults can check out)
- [ ] Add child check-in/check-out history

### Kiosk Self-Check-In Mode

- [ ] Add kiosk-mode UI (touch-screen friendly, large buttons, no login required)
- [ ] Add name search check-in (type name, select from results, confirm)
- [ ] Add QR code scan check-in on kiosk
- [ ] Add family check-in on kiosk (check in entire household at once)
- [ ] Add auto-timeout and screen lock on kiosk (return to start after 30s idle)
- [ ] Add kiosk admin PIN for configuration

### Attendance Analytics

- [ ] Add attendance trends chart (weekly/monthly attendance over time)
- [ ] Add average attendance calculation per session type
- [ ] Add attendance rate per member (attended / total sessions)
- [ ] Add growth/decline indicators with percentage change
- [ ] Add seasonal trend analysis (identify patterns: summer dip, holiday spikes)

### Frontend Refinements

- [ ] Session list: add filter by session_type and date range
- [ ] Session detail: add export attendance list to CSV
- [ ] My history: add statistics summary (total sessions attended, attendance rate)
- [ ] Scanner: add sound/visual feedback on successful scan
- [ ] Scanner: add manual member search (search by name, not just QR text input)

## P2 — Important

### Family Check-In

- [ ] Add household check-in flow (select family, show all members, check in selected)
- [ ] Add family search on kiosk (search by last name, show all family members)
- [ ] Add family attendance summary (which family members attended which sessions)

### NFC/Tap Check-In

- [ ] Add NFC tag reading support (tap card/phone to check in)
- [ ] Add NFC tag assignment per member (link physical tag to member profile)
- [ ] Add NFC reader configuration page for admin
- [ ] Add fallback to QR code if NFC not available

### Attendance-Based Engagement Scoring

- [ ] Add attendance consistency score (how regularly does a member attend)
- [ ] Add attendance streak tracking (consecutive weeks attended)
- [ ] Add absence alert triggers (auto-notify pastor after X consecutive absences)
- [ ] Add engagement score contribution from attendance data to member engagement score

### Check-Out Time Tracking

- [ ] Add check-out timestamp for session duration calculation
- [ ] Add average session duration report
- [ ] Add early departure tracking (left before session end)

### Sidebar / Navigation

- [ ] Verify "Mon historique" link is in sidebar for all members
- [ ] Verify "Sessions" and "Scanner QR" links are in admin section of sidebar

## P3 — Nice-to-Have

### Geo-Fenced Check-In

- [ ] Add location-based auto check-in (detect when member is near church via GPS)
- [ ] Add geo-fence radius configuration per campus/location
- [ ] Add opt-in consent for location tracking
- [ ] Add location-based attendance verification

### Facial Recognition Check-In (Opt-In)

- [ ] Add face enrollment per member (capture reference photo during profile setup)
- [ ] Add camera-based check-in station (identify member by face)
- [ ] Add privacy controls (explicit opt-in, data retention policies)
- [ ] Add fallback to manual check-in if recognition fails

### Attendance Prediction

- [ ] Add expected attendance prediction for upcoming sessions (based on historical data)
- [ ] Add actual vs. predicted comparison chart
- [ ] Add resource planning recommendations based on predicted attendance

### Visitor Follow-Up Automation

- [ ] Auto-detect first-time visitors (checked in but no member profile)
- [ ] Auto-create follow-up task for hospitality team
- [ ] Add visitor info capture form (name, email, phone, how did you hear about us)
- [ ] Add automated welcome email/SMS to first-time visitors

### Existing Small Fixes

- [ ] Add AbsenceAlert acknowledgment UI (view/acknowledge alerts)
- [ ] My QR: add QR code download button (save QR image as file)
- [ ] Session detail: add "Close session" button inline
- [ ] Session create: add option to link session to an existing event
- [ ] Add attendance rate chart on member detail page
- [ ] Scanner page: show member photo on successful scan
