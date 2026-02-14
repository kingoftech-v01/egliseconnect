# TODO - Communication App

## P1 — Critical

### SMS Messaging Integration

- [ ] Add Twilio SMS integration for sending bulk SMS to members
- [ ] Add individual SMS sending from member profile
- [ ] Add SMS template library (common messages: event reminders, welcome, follow-up)
- [ ] Add SMS delivery status tracking (sent, delivered, failed)
- [ ] Add SMS opt-in/opt-out management per member

### Push Notifications (PWA)

- [ ] Add web push notification support via service worker
- [ ] Add push subscription management per member
- [ ] Add push notification triggers for key events (new assignment, event reminder, help request)
- [ ] Add push notification testing tool for admin

### Email Template Library

- [ ] Add pre-built email templates for common messages (welcome, event reminder, birthday, giving receipt)
- [ ] Add template editor with drag-and-drop blocks (header, text, image, button, footer)
- [ ] Add template preview and test send
- [ ] Add template variable system (merge fields: {{member_name}}, {{event_title}}, etc.)

### Frontend Refinements

- [ ] Newsletter detail: add "Send" and "Schedule" buttons (currently only via API)
- [ ] Notification list: add "Mark all as read" button
- [ ] Notification list: add filter by notification type
- [ ] Preferences page: add success message after saving notification preferences

## P2 — Important

### Communication Automation & Drip Campaigns

- [ ] Add automation model (trigger, conditions, actions, delay, status)
- [ ] Add triggered sequences: welcome series (day 1, 3, 7), first-visit follow-up, birthday
- [ ] Add automation builder UI (define trigger, wait, send, wait, send)
- [ ] Add automation analytics (how many entered, completed, unsubscribed)

### A/B Testing for Newsletters

- [ ] Add A/B subject line testing (send variant A to 20%, variant B to 20%, winner to 60%)
- [ ] Add A/B content testing (different body content)
- [ ] Add winner selection criteria (open rate, click rate)
- [ ] Add A/B test results dashboard

### Communication Analytics Dashboard

- [ ] Add open rate and click rate tracking per newsletter
- [ ] Add engagement trends chart (opens over time, clicks over time)
- [ ] Add subscriber growth chart
- [ ] Add best send time analysis (which day/hour gets highest engagement)
- [ ] Add bounce rate and complaint tracking

### Sidebar / Navigation

- [ ] Verify all communication features are accessible from sidebar (newsletters, notifications, preferences)

## P3 — Nice-to-Have

### Social Media Integration

- [ ] Add Facebook page posting from newsletter content
- [ ] Add Instagram post scheduling
- [ ] Add social media content calendar
- [ ] Add social media engagement metrics

### In-App Messaging

- [ ] Add direct member-to-member messaging (with privacy controls)
- [ ] Add group chat per ministry/team
- [ ] Add message read receipts
- [ ] Add file/image sharing in messages

### Automated Lifecycle Messages

- [ ] Add automated birthday messages (email/SMS/push on member's birthday)
- [ ] Add automated anniversary messages (membership anniversary)
- [ ] Add automated re-engagement messages (inactive member after X weeks)
- [ ] Add configurable message templates for each lifecycle event

### WhatsApp Integration

- [ ] Add WhatsApp Business API integration
- [ ] Add WhatsApp message templates (pre-approved by Meta)
- [ ] Add WhatsApp group management
- [ ] Add WhatsApp delivery tracking

### Existing Small Fixes

- [ ] Add notification badge count in header (number of unread notifications)
- [ ] Newsletter: add preview before sending
- [ ] Newsletter: add recipient count display on create/edit form
- [ ] Add email digest option in notification preferences (daily/weekly summary)
