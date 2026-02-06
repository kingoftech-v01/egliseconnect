# EgliseConnect - Suggestions de fonctionnalites

Ce document presente les fonctionnalites recommandees pour enrichir EgliseConnect,
organisees par priorite et categorie.

---

## PRIORITE HAUTE - Fonctionnalites essentielles

### 1. Authentification et securite avancee

**Actuellement:** Authentification basique par session Django.

**Suggestions:**
- **Authentification a deux facteurs (2FA)** - TOTP via Google Authenticator ou SMS
- **Connexion OAuth2/Social** - Permettre la connexion via Google, Facebook, Apple
- **Reinitialisation de mot de passe** - Flux complet par courriel avec tokens securises
- **Journalisation des connexions** - Historique des connexions avec IP, appareil, geolocalisation
- **Verrouillage de compte** - Apres X tentatives echouees, verrouiller temporairement

**Justification:** La securite des donnees personnelles des membres est critique, surtout avec les informations financieres et pastorales confidentielles.

---

### 2. Application mobile (PWA ou React Native)

**Actuellement:** Interface web responsive uniquement.

**Suggestions:**
- **Progressive Web App (PWA)** - Service workers pour fonctionnement hors-ligne, notifications push natives, installation sur ecran d'accueil
- **Application native** - React Native ou Flutter pour iOS/Android
- **Fonctionnalites mobiles prioritaires:**
  - Consulter le calendrier des evenements
  - RSVP rapide aux evenements
  - Recevoir des notifications push
  - Consulter le repertoire des membres
  - Soumettre des demandes d'aide
  - Voir ses recus fiscaux

**Justification:** La majorite des membres d'eglise utilisent principalement leur telephone. Une PWA serait le meilleur rapport effort/impact.

---

### 3. Systeme de messagerie interne

**Actuellement:** Newsletters et notifications, mais pas de messagerie directe.

**Suggestions:**
- **Messagerie membre-a-membre** - Messages prives entre membres
- **Conversations de groupe** - Chat par groupe/ministere
- **Messagerie pastorale** - Canal securise et confidentiel pour les demandes pastorales
- **Fil de discussion** - Reponses en fil pour les groupes de cellules
- **Partage de fichiers** - Documents, photos dans les conversations

**Justification:** Reduire la dependance a WhatsApp/Facebook Messenger pour les communications internes de l'eglise.

---

### 4. Gestion des presences (Check-in)

**Actuellement:** RSVP aux evenements, mais pas de suivi reel des presences.

**Suggestions:**
- **Check-in numerique** - QR code a scanner a l'entree
- **Suivi des presences aux cultes** - Historique de frequentation par membre
- **Alertes d'absence** - Notification automatique apres X semaines d'absence
- **Check-in enfants** - Systeme securise avec badges pour le departement enfants
- **Rapports de frequentation** - Tendances, moyennes, pics de presence
- **Check-in benevoles** - Confirmer la presence effective des benevoles programmes

**Justification:** Le suivi pastoral depend enormement de la connaissance des presences. L'alerte d'absence permet un suivi proactif des membres.

---

## PRIORITE MOYENNE - Ameliorations significatives

### 5. Dons en ligne et integration de paiement

**Actuellement:** Enregistrement manuel des dons (cash, cheque, carte, virement).

**Suggestions:**
- **Integration Stripe/PayPal** - Dons en ligne directement depuis l'application
- **Dons recurrents** - Configuration de dons automatiques mensuels/hebdomadaires
- **Page de don publique** - Page accessible sans connexion pour les visiteurs
- **Don par campagne** - Page dediee par campagne de financement
- **Don par texto** - Envoi d'un SMS pour declencher un don
- **Recu instantane** - Confirmation par courriel immediatement apres le don

**Justification:** Faciliter les dons augmente significativement les revenus de l'eglise. Les dons recurrents assurent une stabilite financiere.

---

### 6. Gestion de contenu et site web public

**Actuellement:** Interface d'administration uniquement, pas de site public.

**Suggestions:**
- **Site web public de l'eglise** - Page d'accueil, a propos, horaires, localisation
- **Blog/Devotions** - Articles, devotions quotidiennes, reflexions pastorales
- **Sermons en ligne** - Upload audio/video des predications avec recherche par serie, theme, predicateur
- **Galerie photos** - Albums par evenement
- **Formulaire de contact** - Pour les visiteurs potentiels
- **Page "Nouveau ici?"** - Parcours d'integration pour les nouveaux venus

**Justification:** La presence en ligne est le premier point de contact pour les nouveaux membres potentiels.

---

### 7. Gestion des petits groupes / cellules de maison

**Actuellement:** Groupes basiques avec leader et horaire.

**Suggestions:**
- **Curriculum/Etudes bibliques** - Assigner des etudes aux groupes avec progression
- **Notes de reunion** - Compte-rendus partages avec les membres du groupe
- **Demandes de priere du groupe** - Liste de prieres partagee dans le groupe
- **Rapports de leader** - Formulaire hebdomadaire pour les leaders de cellule
- **Localisation des groupes** - Carte interactive des cellules par quartier
- **Inscription ouverte** - Les membres peuvent demander a joindre un groupe

**Justification:** Les petits groupes sont le coeur de la vie communautaire. Des outils dedies renforcent l'engagement.

---

### 8. Gestion des enfants et jeunesse

**Actuellement:** Aucune fonctionnalite specifique pour les enfants.

**Suggestions:**
- **Profils enfants** - Lies aux parents/tuteurs avec informations medicales et allergies
- **Autorisations parentales** - Formulaires numeriques signes electroniquement
- **Check-in securise** - Badge avec code unique, seul le parent peut recuperer l'enfant
- **Curriculum ecole du dimanche** - Planification des lecons par classe d'age
- **Communication aux parents** - Notifications specifiques pour le departement enfants
- **Suivi de progression** - Memorisation de versets, badges, recompenses

**Justification:** La securite des enfants est une priorite absolue. Un systeme dedie rassure les parents et professionnalise le ministere.

---

### 9. Planification des cultes (Worship Planning)

**Actuellement:** Evenements generiques sans details de planification.

**Suggestions:**
- **Ordre du culte** - Planifier chaque element du service (louange, predication, offrande, annonces)
- **Gestion des chants** - Bibliotheque de chants avec paroles, tonalites, BPM
- **Planning technique** - Son, projection, accueil, multimedia
- **Integration ProPresenter/EasyWorship** - Export des listes de chants
- **Historique des chants** - Eviter les repetitions, voir les chants les plus utilises
- **Partage avec l'equipe** - L'equipe de louange voit le programme a l'avance

**Justification:** La planification des cultes implique beaucoup de coordination. Un outil dedie remplace les echanges informels par un processus structure.

---

### 10. Formulaires personnalisables

**Actuellement:** Formulaires fixes codes en dur.

**Suggestions:**
- **Constructeur de formulaires** - Interface drag-and-drop pour creer des formulaires
- **Types de champs** - Texte, choix multiple, date, fichier, signature
- **Cas d'utilisation:**
  - Inscription aux evenements (avec questions specifiques)
  - Formulaire de nouveau membre
  - Sondages de satisfaction
  - Demandes de bapteme/mariage
  - Formulaires de benevolat
- **Collecte de reponses** - Tableau de bord avec export CSV/Excel
- **Formulaires publics** - Accessibles sans compte (pour les visiteurs)

**Justification:** Chaque eglise a des besoins uniques. Des formulaires flexibles evitent les modifications de code constantes.

---

## PRIORITE NORMALE - Fonctionnalites complementaires

### 11. Calendrier partage et integration

**Suggestions:**
- **Synchronisation iCal/Google Calendar** - Export/import des evenements
- **Abonnement au calendrier** - Flux iCal pour abonnement automatique
- **Rappels par courriel/SMS** - Avant les evenements
- **Gestion des conflits** - Detection des chevauchements de salles/ressources
- **Reservation de salles** - Systeme de reservation des espaces de l'eglise

---

### 12. Gestion des ressources et inventaire

**Suggestions:**
- **Inventaire du materiel** - Equipement audio, chaises, projecteurs, etc.
- **Reservation d'equipement** - Systeme de pret pour les groupes
- **Gestion des cles** - Qui possede quelle cle/acces
- **Suivi de maintenance** - Planification de l'entretien du batiment
- **Budget par departement** - Allocation et suivi des depenses par ministere

---

### 13. Parcours d'integration des nouveaux membres

**Suggestions:**
- **Parcours etape par etape** - De visiteur a membre actif
- **Classe de decouverte** - Inscription et suivi automatise
- **Mentorat** - Jumeler un nouveau avec un membre experimente
- **Suivi automatise** - Courriels/messages automatiques aux differentes etapes
- **Etapes:**
  1. Premier visiteur → courriel de bienvenue
  2. Deuxieme visite → invitation a un petit groupe
  3. Troisieme visite → invitation au cours de decouverte
  4. Cours complete → proposition de membership
  5. Membre → proposition de benevolat

**Justification:** L'integration structuree reduit considerablement le taux d'abandon des nouveaux visiteurs.

---

### 14. Demandes de priere

**Suggestions:**
- **Soumission de demandes** - Publiques ou confidentielles
- **Mur de priere** - Page communautaire avec les demandes actives
- **"Je prie pour toi"** - Bouton pour indiquer son soutien
- **Mises a jour** - Le demandeur peut publier des mises a jour sur sa demande
- **Exaucements** - Marquer et celebrer les prieres exaucees
- **Equipe de priere** - Groupe dedie recevant les demandes confidentielles

---

### 15. Rapports et analyses avancees

**Actuellement:** Statistiques de base par le module reports.

**Suggestions:**
- **Tableau de bord pastoral** - Vue d'ensemble pour le pasteur avec alertes
- **Tendances de croissance** - Graphiques d'evolution sur 1, 3, 5 ans
- **Taux de retention** - Mesurer l'engagement et la retention des membres
- **Rapports financiers avances** - Comparaison annuelle, previsions budgetaires
- **Export PDF** - Rapports formates pour les assemblees generales
- **Rapports automatiques** - Envoi mensuel par courriel aux responsables
- **Segmentation des membres** - Filtres avances (age, anciennete, engagement, dons)

---

### 16. Multi-eglise / Multi-campus

**Suggestions:**
- **Support multi-sites** - Une installation pour plusieurs campus
- **Tableau de bord par campus** - Statistiques par emplacement
- **Evenements par campus** - Calendrier filtre par site
- **Transfert de membres** - D'un campus a l'autre
- **Rapports consolides** - Vue globale de tous les campus

---

### 17. Internationalisation complete

**Actuellement:** Francais canadien uniquement.

**Suggestions:**
- **Support multilingue** - Anglais, espagnol, creole haitien (communautes frequentes au Canada)
- **Interface bilingue** - Changement de langue par l'utilisateur
- **Contenu multilingue** - Newsletters et notifications dans la langue preferee du membre
- **Formats regionaux** - Dates, devises, formats d'adresse selon la locale

---

### 18. Integration avec des services externes

**Suggestions:**
- **Mailchimp/SendGrid** - Pour l'envoi massif de courriels (remplacer SMTP direct)
- **Twilio** - Pour les notifications SMS
- **Zoom/Google Meet** - Creation automatique de liens pour les evenements en ligne
- **YouTube/Vimeo** - Integration des diffusions en direct
- **QuickBooks/Wave** - Synchronisation comptable
- **Planning Center** - Import/export de donnees
- **Zapier/Make** - Automatisations sans code

---

### 19. Accessibilite et inclusivite

**Suggestions:**
- **Conformite WCAG 2.1 AA** - Accessibilite complete de l'interface
- **Mode contraste eleve** - Pour les malvoyants
- **Navigation au clavier** - Toutes les fonctionnalites accessibles sans souris
- **Lecteur d'ecran** - Compatibilite avec NVDA, JAWS, VoiceOver
- **Taille de police ajustable** - Pour les personnes agees
- **Traduction en langue des signes** - Pour les contenus video

---

### 20. Sauvegarde et export de donnees

**Suggestions:**
- **Sauvegarde automatique** - Planification de backups reguliers
- **Export complet** - Toutes les donnees en CSV/JSON/XML
- **Export RGPD/LPRPDE** - Conformite aux lois sur la protection des donnees
- **Droit a l'oubli** - Suppression complete des donnees d'un membre sur demande
- **Import de donnees** - Migration depuis d'autres systemes (ChurchTools, Planning Center, Excel)
- **Historique des modifications** - Audit trail complet de toutes les modifications

---

## Resume des priorites

| # | Fonctionnalite | Priorite | Effort | Impact |
|---|---------------|----------|--------|--------|
| 1 | Authentification avancee (2FA, OAuth) | Haute | Moyen | Haut |
| 2 | Application mobile (PWA) | Haute | Eleve | Tres haut |
| 3 | Messagerie interne | Haute | Eleve | Haut |
| 4 | Gestion des presences (Check-in) | Haute | Moyen | Tres haut |
| 5 | Dons en ligne (Stripe/PayPal) | Moyenne | Moyen | Tres haut |
| 6 | Site web public + blog | Moyenne | Eleve | Haut |
| 7 | Petits groupes avances | Moyenne | Moyen | Haut |
| 8 | Gestion enfants/jeunesse | Moyenne | Eleve | Haut |
| 9 | Planification des cultes | Moyenne | Moyen | Moyen |
| 10 | Formulaires personnalisables | Moyenne | Eleve | Haut |
| 11 | Calendrier partage (iCal) | Normale | Faible | Moyen |
| 12 | Gestion des ressources | Normale | Moyen | Moyen |
| 13 | Parcours d'integration | Normale | Moyen | Haut |
| 14 | Demandes de priere | Normale | Faible | Haut |
| 15 | Rapports avances | Normale | Moyen | Moyen |
| 16 | Multi-eglise / Multi-campus | Normale | Eleve | Variable |
| 17 | Internationalisation | Normale | Moyen | Variable |
| 18 | Integrations externes | Normale | Variable | Moyen |
| 19 | Accessibilite (WCAG) | Normale | Moyen | Haut |
| 20 | Sauvegarde et export | Normale | Faible | Haut |

---

## Recommandation de feuille de route

### Phase 1 - Fondations (prochaine version)
1. Authentification avancee (2FA, reset mot de passe)
2. Gestion des presences (Check-in QR)
3. Demandes de priere
4. Synchronisation calendrier (iCal)

### Phase 2 - Engagement (version suivante)
5. Application PWA
6. Dons en ligne (Stripe)
7. Parcours d'integration nouveaux membres
8. Petits groupes avances

### Phase 3 - Croissance
9. Site web public + blog + sermons
10. Gestion enfants/jeunesse
11. Formulaires personnalisables
12. Messagerie interne

### Phase 4 - Excellence
13. Planification des cultes
14. Rapports avances + export PDF
15. Integrations externes
16. Multi-eglise / Internationalisation
17. Accessibilite WCAG 2.1 AA
