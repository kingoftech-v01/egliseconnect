# App: Attendance (Presence)

## Description
Systeme de presence multi-methode: QR codes HMAC-signes, scanner camera, kiosque self-service, NFC, geolocalisation, check-in enfants securise, visiteurs, alertes d'absence et analytics.

## Modeles (10)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `MemberQRCode` | code (HMAC-signed UUID), generated_at, expires_at (7j), qr_image | OneToOne: Member |
| `AttendanceSession` | name, session_type, date, start/end_time, is_open | FK: event, scheduled_lesson, opened_by |
| `AttendanceRecord` | checked_in_at, method (qr/nfc/manual/kiosk/geo), checked_out_at | FK: session, member, checked_in_by. Unique: [session, member] |
| `AbsenceAlert` | consecutive_absences, last_attendance_date, alert_sent | FK: member, acknowledged_by |
| `ChildCheckIn` | check_in_time, check_out_time, security_code (6 digits) | FK: child, parent_member, session, checked_out_by |
| `KioskConfig` | name, location, admin_pin, auto_timeout_seconds | FK: session |
| `NFCTag` | tag_id (unique) | OneToOne: Member |
| `AttendanceStreak` | current_streak, longest_streak, last_attendance_date | OneToOne: Member |
| `GeoFence` | name, latitude, longitude, radius_meters | - |
| `VisitorInfo` | name, email, phone, source, follow_up_completed | FK: session, follow_up_assigned_to |

## Fonctions utilitaires
- `generate_secure_qr_code()` - HMAC-signed UUID
- `generate_qr_image()` - PNG via qrcode library
- `generate_security_code()` - 6 chiffres random pour check-out enfants
- `GeoFence.is_within_fence()` - Formule Haversine

## API ViewSets (12)
- `MemberQRCodeViewSet` (ReadOnly) - Mon QR. Action: regenerate
- `AttendanceSessionViewSet` - IsPastorOrAdmin. Filtre: session_type, date, is_open
- `CheckInViewSet` - Valide QR HMAC, verifie session ouverte, cree record
- `CheckOutViewSet` - Check-out membre
- `AbsenceAlertViewSet` - Alertes d'absence
- `ChildCheckInViewSet` - Check-in/out enfants
- `NFCTagViewSet` - Gestion tags NFC
- `GeoFenceViewSet` - CRUD geo-fences
- `VisitorInfoViewSet` - CRUD visiteurs
- `FamilyCheckInViewSet` - Check-in famille entiere
- `AttendanceAnalyticsViewSet` - Tendances et stats

## Scanner QR (template le plus complexe)
- Camera web via `html5-qrcode.min.js`
- Scan continu (ne s'arrete pas entre les scans) pour presence en masse
- Debounce 5 secondes par QR code
- POST AJAX vers `/attendance/scanner/checkin-ajax/`
- Son succes: sine-wave 880Hz 0.3s (Web Audio API)
- Son erreur: square-wave 200Hz 0.5s
- Animation flash verte sur nouvelles lignes
- Recherche membre comme fallback

## Frontend Views (30+)
my_qr, scanner, process_checkin (AJAX), session_list/create/detail/edit/toggle/delete/add_manual_record, my_history, child_checkin/receipt/checkout/history, kiosk_home/search/checkin/family-checkin/family-search/admin/list/create/edit/delete, analytics_dashboard, trends_api, family_checkin/summary, nfc_register/reader_config, checkout_member, geo_checkin, prediction_dashboard, visitor_list/create/followup, absence_alert_list/acknowledge

## Forms (8)
AttendanceSessionForm, SessionFilterForm, ChildCheckInForm, ChildCheckOutForm (security code), KioskConfigForm (PIN), KioskPinForm, NFCTagForm, GeoFenceForm, VisitorInfoForm, MemberSearchForm

## Services
- `AttendanceAnalyticsService.get_attendance_trends(period, weeks_back)`
- `AttendanceAnalyticsService.get_average_attendance_by_type()`
- `AttendanceAnalyticsService.get_member_attendance_rate(member, days)`

## Points d'attention
- QR codes expirent apres 7 jours, regeneration a la demande
- HMAC signature empeche la falsification des QR codes
- Check-out enfants necessite le code securite 6 chiffres genere au check-in
- Kiosk PIN (PasswordInput) pour securiser l'acces admin kiosk
- Geo-fencing utilise Haversine (rayon par defaut 100m)
- Streak tracking (serie de presences + record personnel)

## Fichiers cles
- `apps/attendance/models.py` - 10 modeles + helpers crypto
- `apps/attendance/views_api.py` - 12 ViewSets
- `apps/attendance/services.py` - AttendanceAnalyticsService
- `templates/attendance/scanner.html` - Template le plus JS-heavy du projet
- `templates/attendance/my_qr.html` - Affichage QR
