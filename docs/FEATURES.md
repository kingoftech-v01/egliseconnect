# Inventaire des fonctionnalites - EgliseConnect

## Legende
- **Existant**: Fonctionnalite implementee et fonctionnelle
- **Partiel**: Implemente mais incomplet ou avec limitations
- **Propose**: Nouvelle fonctionnalite a ajouter

---

## 1. Core (Infrastructure)

### Existant
- Modeles abstraits UUID (BaseModel, SoftDeleteModel) avec soft-delete et managers
- Systeme de permissions role-based (9 classes DRF)
- Support multi-roles via MemberRole + propriete `all_roles`
- Audit de connexion (LoginAudit: IP, user agent, methode, succes/echec)
- Middleware 2FA (enforcement avec deadline configurable)
- Middleware acces membership (restriction par statut)
- Context processors (branding, langue, notifications)
- Feature flags (django-waffle)
- API versioning (v1/v2 avec headers deprecation)
- Health check endpoint (/health/)
- Church branding configurable (logo, couleurs, coordonnees)
- Webhooks sortants avec signature HMAC et retry exponentiel
- Audit trail complet (AuditLog: create/update/delete/login/export)
- Multi-campus support
- PWA (service worker, manifest, offline page)
- Recherche globale avec autocomplete AJAX
- Documentation API auto-generee (Swagger, ReDoc)

### Propose
- **Rate limiting intelligent** par role (admins ont plus de quota)
- **API key management** pour integrations tierces
- **Audit dashboard** visuel avec filtres et export
- **Health check avance** (status DB, Redis, Celery, disk space)
- **Configuration dynamique** (settings en DB, editable sans redeploy)

---

## 2. Members (Gestion des membres)

### Existant
- CRUD complet membres avec photo, roles, contacts, dates
- Auto-generation numero membre (MBR-YYYY-XXXX)
- Profil personnel (mon profil, editer)
- Annuaire avec respect privacy settings (public/group/private)
- Annuaire public
- Export PDF annuaire
- Groupes: CRUD, ajouter/retirer membres, finder par type/jour
- Groupes lifecycle (launching/active/multiplying/closed)
- Familles: CRUD, dashboard, merge, sync adresse
- Enfants: CRUD avec allergies, notes medicales, pickups autorises
- Departements: CRUD, membres, types de taches
- Actions disciplinaires: CRUD avec workflow approbation (hierarchy-enforced)
- Soins pastoraux: CRUD, dashboard, suivi
- Verifications antecedents: CRUD, expiration tracking
- Import CSV/Excel (wizard 3 etapes: upload → mapping → preview)
- Detection et fusion de doublons (merge wizard)
- Historique des imports et merges
- Champs personnalises (7 types: text, textarea, number, date, dropdown, checkbox, file)
- Score d'engagement (4 dimensions: presence, dons, benevolat, groupes)
- Demandes de modification de profil (workflow staff)
- Anniversaires (aujourd'hui, cette semaine, ce mois)
- Export DataTables (CSV, Excel, PDF)

### Partiel
- Recherche membres: fonctionne mais pas de recherche full-text
- Privacy settings: le toggle existe mais pas tous les champs sont respectes partout

### Propose
- **Photo auto-crop/resize** a l'upload
- **Tags/etiquettes membres** pour segmentation flexible
- **Historique des changements** de role avec raisons
- **Notes privees** par staff sur chaque membre
- **Carte membre** generee (PDF ou QR enrichi)
- **Bulk actions** (changer role, envoyer email, ajouter a groupe en masse)
- **Anniversaire de bapteme** tracking et notifications
- **Statut de sante spirituelle** (indicateur configurable par l'eglise)

---

## 3. Donations (Dons et finances)

### Existant
- CRUD dons avec types (dime, offrande, special, campagne, missions, etc.)
- Auto-generation numero don (DON-YYYY-XXXX)
- Methodes paiement (especes, cheque, carte, virement, en ligne)
- Campagnes de collecte avec objectif, progress bar, dates
- Recus fiscaux annuels (generation PDF, envoi email)
- Delegation financiere (donner acces finances a un non-tresorier)
- Pledges/engagements (CRUD, suivi progression, frequences)
- PledgeFulfillment tracking
- Releves de dons (mid-year, annuel, generation PDF)
- Objectifs de don personnels (par annee, progress tracking)
- Import CSV/OFX (wizard)
- Mode kiosque (boutons montants rapides)
- Donations crypto (BTC, ETH, LTC, USDC via Coinbase Commerce)
- Matching campaigns (ratio, cap, tracking)
- Analytics dashboard (tendances mensuelles, comparaison YoY, retention donateurs)
- Rapport mensuel
- Role-scoped access (finance staff voient tout, membres voient les leurs)

### Partiel
- Email receipt: la logique existe mais l'envoi reel depend de la config email
- Crypto: le modele existe mais l'integration Coinbase n'est pas completement testee

### Propose
- **Recurring donations via Stripe** (automatisation complete)
- **Text-to-give** (SMS → Stripe charge)
- **Donor journey analytics** (first-time → regular → lapsed)
- **Giving envelopes** numeriques (pre-assignes par famille)
- **Budget vs actual** reporting par categorie
- **Multi-currency** support complet (USD, EUR en plus de CAD)
- **Donation acknowledgment letters** automatiques
- **Batch entry mode** pour saisie rapide de plusieurs dons

---

## 4. Events (Evenements)

### Existant
- CRUD evenements avec types, dates, lieu, capacite
- RSVP (pending/confirmed/declined/maybe) avec compteur invites
- Calendrier interactif (FullCalendar)
- Evenements en ligne/hybrides (lien virtuel, plateforme)
- Recurrence (daily, weekly, biweekly, monthly, yearly + RRULE)
- Export iCal (par evenement + feed complet)
- Gestion des salles (CRUD, capacite, equipements)
- Reservations de salles avec detection conflits
- Calendrier des salles
- Templates d'evenements (reutiliser configs courantes)
- Waitlist (file d'attente quand evenement complet)
- Besoins volontaires par evenement (positions, compteur rempli/requis)
- Inscription volontaire aux besoins
- Galerie photos par evenement (upload, approbation)
- Sondages post-evenement (builder JSON, reponses, resultats)
- Formulaires d'inscription personnalises (champs JSON)
- Kiosk check-in par evenement
- Annulation d'evenement

### Partiel
- Recurrence: le parent_event FK existe mais la generation auto d'occurrences n'est pas implementee
- Notifications: rappels d'evenements references dans le code mais pas tous branches

### Propose
- **Billetterie** (evenements payants, QR tickets)
- **Check-in par evenement** avec stats en temps reel
- **Streaming integre** (embed YouTube/Facebook Live dans la page)
- **Co-organisateurs** (plusieurs organisateurs par evenement)
- **Evenements recurents** generation automatique des occurrences
- **Maps integration** (afficher lieu sur carte)
- **Calendar sync** (Google Calendar, Outlook bidirectionnel)
- **Event analytics** (taux de participation, demographics des participants)

---

## 5. Volunteers (Benevolat)

### Existant
- Positions (CRUD avec type, description, min/max volontaires)
- Schedule (planification par membre, position, event, date)
- Mon planning personnel (vue simple + vue mobile)
- Disponibilites (par position, frequence)
- Creneaux de disponibilite hebdomadaires (jour, heure debut/fin)
- Heatmap de disponibilite
- Calendrier de disponibilite
- Absences planifiees (CRUD avec approbation)
- Echanges de quarts (swap requests avec workflow pending/approved/rejected)
- Log des heures de service
- Sommaire personnel des heures
- Rapport admin des heures
- Verifications antecedents specifiques benevolat
- Annonces d'equipe (par position)
- Checklists par position (onboarding volontaire)
- Progression des checklists
- Competences (CRUD, categories, niveaux proficiency)
- Profil de competences par volontaire
- Milestones (heures, annees) avec badges
- Achievements
- Volontaire du mois
- Cross-training (formation sur d'autres positions)
- Suggestions de cross-training
- Rappels multiples (5j, 3j, 1j, jour meme) - flags dans le modele

### Partiel
- Rappels: les flags `reminder_*_sent` existent mais la tache Celery n'est pas confirmee active
- Auto-scheduling: le endpoint existe mais l'algorithme est basique

### Propose
- **Auto-scheduling intelligent** (basé sur disponibilites, competences, rotation equitable)
- **Burnout detection** (trop d'heures consecutives → alerte)
- **Shift bidding** (volontaires choisissent parmi les creneaux disponibles)
- **Team dashboard** (vue d'ensemble par equipe/position)
- **Volunteer onboarding flow** dedie (separe du member onboarding)
- **Training videos** integrees dans les checklists
- **Appreciation system** (merci, kudos entre volontaires)
- **Conflict detection** (double-booking d'un volontaire)

---

## 6. Communication

### Existant
- Newsletters: CRUD, envoi async (Celery), ciblage par groupe, compteur ouvertures
- A/B testing newsletters (2 variantes, auto-winner par opens)
- Notifications in-app (CRUD, mark read, compteur)
- Notifications temps reel via WebSocket (Django Channels)
- Preferences de communication (email, push, SMS toggles)
- SMS via Twilio (compose, templates, envoi, suivi livraison)
- SMS opt-out tracking
- Push notifications (VAPID, subscribe/unsubscribe, test)
- Templates email (CRUD, categories, preview)
- Automations (triggers: new member, birthday, anniversary, donation, etc.)
- Automation steps (delai, canal: email/SMS/push/in-app)
- Automation enrollments tracking
- Messagerie directe (inbox, compose, mark read)
- Chat de groupe (CRUD, messages)
- Sanitization HTML (bleach)

### Partiel
- Social media dashboard: template existe mais stub (pas d'integration reelle)
- Chat: pas de temps reel (polling serait necessaire ou WebSocket extension)
- Newsletter analytics: opened_count existe mais click tracking non implemente

### Propose
- **Rich text editor** pour newsletters (WYSIWYG moderne type TipTap)
- **Email builder** drag-and-drop (comme Mailchimp)
- **Click tracking** dans newsletters (liens traces)
- **Unsubscribe one-click** (header List-Unsubscribe)
- **Scheduled SMS** (envoi differe)
- **WhatsApp integration** (Business API)
- **Chat temps reel** via WebSocket (pas juste REST)
- **Communication analytics** avances (deliverability, engagement par canal)

---

## 7. Help Requests (Entraide)

### Existant
- Demandes d'aide: CRUD avec categories bilingues, urgence, confidentialite
- Auto-generation numero (HR-YYYYMM-XXXX)
- Assignation a un staff member
- Resolution avec notes
- Commentaires (publics + internes staff-only)
- Role-scoped: pasteurs/admins voient tout, leaders voient leur groupe, membres voient les leurs
- Soins pastoraux: CRUD, dashboard, calendrier
- Equipes de soin (CRUD, membres)
- Mur de priere (public, anonyme optionnel, moderation)
- Demande de priere anonyme (sans login)
- Temoignages (quand priere exaucee)
- Fonds de benevolence (CRUD, balance, requests, approbation, decaissement)
- Trains de repas (CRUD, inscriptions par date, restrictions alimentaires)
- Protocoles de crise (CRUD, etapes JSON)
- Ressources de crise (CRUD, contacts, URLs)
- Notification de crise

### Partiel
- Calendrier soins pastoraux: affichage basique, pas de calendrier interactif
- Benevolence fund: le balance tracking est manuel (pas de deduction auto apres decaissement)

### Propose
- **Case management** complet (timeline, documents, historique)
- **Auto-assignation** basee sur les competences de l'equipe de soin
- **Follow-up reminders** automatiques (relance si pas de resolution)
- **SLA tracking** (temps de reponse, temps de resolution)
- **Dashboard analytique** (tendances, categories les plus demandees)
- **Integration calendrier** pour soins pastoraux (sync Google Calendar)
- **Formulaire d'aide public** (accessible sans login, comme priere anonyme)
- **Reporting anonymise** pour le conseil d'eglise

---

## 8. Reports (Rapports)

### Existant
- Dashboard principal (stats membres, dons, evenements, volontaires)
- Graphiques (ApexCharts, Chart.js)
- Rapport statistiques membres
- Rapport dons (filtres date, type, methode)
- Rapport presence
- Rapport volontaires
- Rapport anniversaires
- Rapport demandes d'aide
- Rapport communications
- Comparaison annee sur annee
- Tendances de dons
- Pipeline onboarding stats
- Dashboard predictif
- Church health scorecard
- BI API endpoint
- Rapports planifies (CRUD, frequence, destinataires, filtres JSON)
- Rapports sauvegardes (CRUD, filtres/colonnes JSON, partage)
- Exports CSV (membres, dons, presence, volontaires)
- Service rapport pour tresorier

### Partiel
- Dashboard predictif: modele basique, pas de vrai ML
- BI endpoint: retourne des donnees brutes, pas de transformation avancee

### Propose
- **Report builder** visuel (drag-and-drop colonnes, filtres, grouping)
- **Scheduled email reports** avec PDF attache
- **Dashboards personnalisables** (widgets, layout configurable)
- **Benchmarking** (comparer avec moyennes denomination)
- **Cohort analysis** (retention membres par cohorte d'entree)
- **Giving forecast** (projection basee sur historique)
- **Export PowerPoint** pour presentations au conseil
- **Real-time dashboard** (auto-refresh, live stats)

---

## 9. Onboarding (Integration)

### Existant
- Pipeline admin kanban (4 colonnes: inscrit → formulaire → formation → interview)
- Review et approbation par admin
- Formulaire d'integration (deadline 30 jours, champs configurables)
- Champs conditionnels (afficher champ B si champ A = valeur X)
- Cours de formation (CRUD, lecons ordonnees, materiels PDF, videos)
- Planning des lecons (date, lieu, status, makeup, rappels)
- Interviews (proposition, contre-proposition, confirmation, resultat)
- Codes d'invitation (role, expiration, max uses, skip onboarding)
- Mentorat (assignation, check-ins, dashboard)
- Documents a signer (covenant, policy, consent, waiver)
- Signature electronique (texte + IP)
- Welcome sequences (etapes par jour, multi-canal)
- Progress tracking par etape
- Multi-track onboarding (nouveau croyant, transfert, jeunesse, famille)
- Gamification (achievements, badges, points, trigger types)
- Leaderboard
- Quiz par lecon (questions, reponses, score, pass/fail)
- Status pages par etape (registered, submitted, training, interview, rejected)
- Journey map visuel
- Congratulations page
- Visiteur follow-up tracking
- Stats admin
- Bulk pipeline actions (approuver, envoyer rappel en masse)

### Partiel
- Welcome sequences: le modele existe mais l'envoi automatique via Celery n'est pas confirme actif
- Gamification: les achievements sont crees manuellement, pas d'attribution automatique sur tous les triggers

### Propose
- **Onboarding analytics** (taux de completion par etape, temps moyen, drop-off)
- **Video onboarding** (tutoriels integres dans le parcours)
- **Self-service scheduling** pour interviews (calendrier disponible)
- **Peer groups** (cohortes d'integration qui avancent ensemble)
- **Certificate generation** (PDF certificat de completion)
- **Progress notifications** automatiques au mentor et a l'admin
- **Re-onboarding flow** pour membres inactifs qui reviennent
- **Parent onboarding** dedie (avec gestion enfants)

---

## 10. Attendance (Presence)

### Existant
- QR codes membres (HMAC-signed, expiration 7 jours, regeneration)
- Generation image QR (PNG)
- Scanner QR (camera web, continuous scanning, debounce 5s)
- Son de succes/erreur (Web Audio API)
- Recherche membre dans le scanner (fallback si pas de QR)
- Check-in AJAX (JSON response avec nom, heure)
- Sessions (CRUD, types: culte/evenement/lecon)
- Ajout manuel de presence
- Historique personnel
- Check-in enfants (code securite 6 chiffres, check-out verifie)
- Historique enfants
- Kiosk mode (config, PIN admin, timeout)
- Kiosk multi-ecrans (home, search, checkin, family-checkin, admin)
- Family check-in (check-in tous les membres d'une famille en une fois)
- NFC tag registration et reader config
- Geo-fencing (Haversine formula, rayon configurable)
- Geo check-in
- Alertes d'absence (consecutive absences tracking, acknowledgment)
- Visiteurs (CRUD, source, follow-up assignation)
- Streak tracking (serie de presences, record)
- Analytics dashboard (tendances, moyennes par type)
- Trends API
- Prediction dashboard
- Member attendance rate API
- Check-out (depart anticipe)

### Partiel
- NFC: les modeles et vues existent mais necessitent hardware specifique
- Geo-fencing: fonctionne mais pas de validation GPS cote client
- Predictions: dashboard existe mais modele predictif basique

### Propose
- **Bluetooth beacon** check-in (iBeacon/Eddystone)
- **Face recognition** opt-in (pour kiosk avance)
- **Attendance heatmap** (visualisation par place dans l'eglise)
- **Late arrival tracking** (heure d'arrivee vs debut service)
- **Group attendance** (voir presence par groupe/departement)
- **Attendance goals** (objectif personnel de presence)
- **Parent notification** quand enfant est checked-in/out
- **Visitor welcome workflow** automatise (email + assignation follow-up)

---

## 11. Payments (Paiements)

### Existant
- Integration Stripe (PaymentIntent, customer management)
- Mode dev fallback (quand Stripe pas configure)
- Paiements en ligne (formulaire, confirmation)
- Historique des paiements
- Dons recurrents (Stripe Subscriptions: create, cancel, edit)
- Releves de dons (generer, download PDF, bulk generate)
- Objectifs de don annuels
- Sessions kiosque (date, lieu, total, reconciliation)
- Plans de paiement (montant total, versements, frequence, progression)
- Employer matching (ratio, cap, montant recu)
- Campagnes de dons (goal, progress, year-end flag)
- Crypto donations (BTC, ETH, LTC, USDC via Coinbase Commerce)
- SMS donations (parse commande SMS → Stripe charge)
- Webhooks Stripe et Twilio
- Webhook error monitoring

### Partiel
- SMS donations: le modele existe mais l'integration complete Twilio → Stripe n'est pas confirmee testee
- Employer matching: tracking manuel, pas de verification automatique

### Propose
- **Apple Pay / Google Pay** integration native
- **ACH/EFT direct** (virement bancaire automatise)
- **Donation receipts** email automatique apres chaque transaction
- **Failed payment retry** automatique avec notification
- **Giving analytics** par donateur (lifetime value, frequence, tendance)
- **Multi-fund giving** (repartir un don entre plusieurs fonds en une transaction)
- **Pledge reminders** automatiques (email quand pledge en retard)
- **Tax receipt batch** avec merge mail

---

## 12. Worship (Culte)

### Existant
- Services (CRUD, sections ordonnees, assignments par section)
- Validation deadline auto (14 jours avant service)
- Confirmation rate tracking
- Sections par type (prelude, annonces, louange, offrande, predication, communion, priere, benediction)
- Assignments avec workflow (assigned/confirmed/declined)
- Rappels multiples (flags 5j/3j/1j/jour meme)
- Listes d'eligibilite par type de section
- Sermons (CRUD, series, audio/video URLs, scripture, speaker)
- RSS feed sermons
- Archive sermons
- Chants (CRUD, tonalite, BPM, paroles, accords, CCLI number, tags)
- Recherche de chants (texte + tonalite)
- Chord chart display + impression
- Setlist builder (chants ordonnes, override tonalite)
- CCLI report
- Calendrier des services
- Planning timeline
- Most played songs analytics
- Song rotation tracking
- Auto-schedule preview
- Live streams (CRUD, plateforme, viewer count, recording URL)
- Rehearsals (CRUD, attendees RSVP)
- Song requests (submit, vote, moderation, scheduling)
- Duplicate service
- Print service order
- Preferences volontaires culte (positions preferees, blackout dates, max services/mois)
- Export ProPresenter
- Export EasyWorship

### Partiel
- Auto-scheduling: preview existe mais algorithme basique
- Live streaming: pas d'integration API reelle (juste URL tracking)

### Propose
- **Drag-and-drop setlist** (reorder visuel)
- **Chord transposition** en temps reel
- **Live lyrics display** (mode presentation pour projecteur)
- **Spotify/YouTube integration** pour preview chants
- **Sermon notes** collaboratives (congregation peut prendre des notes)
- **Service evaluation** post-culte (feedback equipe)
- **Planning template** (reutiliser un format de service type)
- **Automatic CCLI reporting** (submission directe)
