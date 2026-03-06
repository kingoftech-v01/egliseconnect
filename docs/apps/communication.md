# App: Communication

## Description
Systeme de communication multi-canal: newsletters, notifications in-app et temps reel, SMS (Twilio), push (VAPID), email templates, automations, A/B testing, messagerie directe et chat de groupe.

## Modeles (16)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `Newsletter` | subject, content, content_plain, status, scheduled_for, recipients_count, opened_count | FK: created_by. M2M: target_groups |
| `NewsletterRecipient` | email, sent_at, opened_at, failed | FK: newsletter, member. Unique: [newsletter, member] |
| `Notification` | title, message, notification_type, link, is_read | FK: member |
| `NotificationPreference` | email_newsletter/events/birthdays, push_enabled, sms_enabled | OneToOne: Member |
| `SMSTemplate` | name, body_template | - |
| `SMSMessage` | phone_number, body, status, twilio_sid | FK: recipient_member, template, sent_by |
| `SMSOptOut` | phone_number, opted_out_at | FK: member. Unique: [phone_number] |
| `PushSubscription` | endpoint, p256dh_key, auth_key | FK: member. Unique: [member, endpoint] |
| `EmailTemplate` | name, subject_template, body_html_template, category | - |
| `Automation` | name, trigger_type, is_active | FK: created_by |
| `AutomationStep` | order, delay_days, subject, body, channel | FK: automation. Unique: [automation, order] |
| `AutomationEnrollment` | current_step, status, next_step_at | FK: automation, member. Unique: [automation, member] |
| `ABTest` | variant_a/b_subject/content, test_size_pct, variant_a/b_opens/clicks, winner, status | OneToOne: Newsletter |
| `DirectMessage` | body, read_at | FK: sender, recipient |
| `GroupChat` | name | M2M: members. FK: created_by |
| `GroupChatMessage` | body, sent_at | FK: chat, sender |

## Services
- `TwilioSMSService` (services_sms.py) - Envoi SMS via Twilio API
- `WebPushService` (services_push.py) - Push notifications VAPID
- `AutomationService` (services_automation.py) - Execution des automations

## API ViewSets (15)
NewsletterViewSet (actions: send, schedule), NotificationViewSet (actions: mark-read, unread_count), NotificationPreferenceViewSet, SMSMessageViewSet (actions: send, track-delivery), SMSTemplateViewSet, SMSOptOutViewSet, PushSubscriptionViewSet (actions: unsubscribe, test-send), EmailTemplateViewSet, AutomationViewSet (action: trigger), AutomationStepViewSet, AutomationEnrollmentViewSet, ABTestViewSet (action: pick-winner), DirectMessageViewSet (action: mark-read), GroupChatViewSet, GroupChatMessageViewSet

## Frontend Views (27 templates)
newsletter_list/create/detail/edit/delete/send, notification_list, mark_all_read, preferences, sms_list/compose, sms_template_list/create/edit, email_template_list/create/edit/preview, push_test, automation_list/create/detail/step_add, analytics_dashboard, abtest_results, message_inbox/compose/detail, group_chat_list/create/detail, social_media_dashboard (stub)

## Forms (9)
NewsletterForm (bleach HTML sanitization), SMSComposeForm, SMSBulkForm, SMSTemplateForm, EmailTemplateForm (bleach), AutomationForm, AutomationStepForm, DirectMessageForm, GroupChatForm, GroupChatMessageForm

## Celery Tasks
- `send_newsletter_task` - Envoi asynchrone newsletters
- `process_automation_steps` - Traitement des enrollments en attente
- `send_birthday_messages` - SMS + push + in-app anniversaires
- `send_anniversary_messages` - Notifications anniversaire adhesion
- `send_reengagement_messages` - Re-engagement membres inactifs 8+ semaines

## Points d'attention
- WebSocket pour notifications temps reel via Django Channels (`ws://host/ws/notifications/`)
- HTML sanitize avec bleach avant stockage (newsletters et email templates)
- A/B testing: 2 variantes, auto-winner base sur opens
- Social media dashboard est un stub (template existe, pas d'integration reelle)
- Chat n'est pas temps reel (REST only, necessiterait WebSocket extension)

## Fichiers cles
- `apps/communication/models.py` - 16 modeles
- `apps/communication/views_api.py` - 15 ViewSets (le plus riche)
- `apps/communication/services_sms.py` - Integration Twilio
- `apps/communication/services_push.py` - Push VAPID
- `apps/communication/services_automation.py` - Moteur automations
