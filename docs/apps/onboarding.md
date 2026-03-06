# App: Onboarding (Integration des nouveaux membres)

## Description
Parcours d'integration complet: pipeline admin, formulaire avec deadline, formation (cours/lecons), interviews, codes d'invitation, mentorat, documents a signer, welcome sequences, multi-track, gamification (achievements, quiz, leaderboard).

## Modeles (22)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `TrainingCourse` | name, description, total_lessons, is_default | FK: created_by |
| `Lesson` | order, title, description, duration_minutes, materials_pdf, video_url | FK: course. Unique: [course, order] |
| `MemberTraining` | assigned_at, completed_at, is_completed | FK: member, course, assigned_by, track. Unique: [member, course] |
| `ScheduledLesson` | scheduled_date, location, status, reminder_*_sent flags | FK: training, lesson |
| `Interview` | status, proposed/counter_proposed/confirmed_date, location, result_notes | FK: member, training, interviewer |
| `InvitationCode` | code (8-char auto), role, max_uses, use_count, skip_onboarding, expires_at | FK: created_by, used_by |
| `MentorAssignment` | start_date, status, check_in_count | FK: new_member, mentor |
| `MentorCheckIn` | date, notes | FK: assignment, logged_by |
| `OnboardingFormField` | label, field_type, is_required, options (JSON), order, conditional_value | FK: conditional_field(self) |
| `OnboardingFormResponse` | value, file | FK: member, field. Unique: [member, field] |
| `WelcomeSequence` | name, description | - |
| `WelcomeStep` | day_offset, channel, subject, body, order | FK: sequence |
| `WelcomeProgress` | current_step, started_at, completed_at | FK: member, sequence. Unique: [member, sequence] |
| `OnboardingDocument` | title, content, requires_signature, document_type | - |
| `DocumentSignature` | signature_text, signed_at, ip_address | FK: document, member. Unique: [document, member] |
| `VisitorFollowUp` | visitor_name/email/phone, first_visit_date, status, converted_at | FK: assigned_to, member |
| `OnboardingTrackModel` | name, track_type, description | M2M: courses, documents |
| `Achievement` | name, description, icon, badge_image, points, trigger_type | - |
| `MemberAchievement` | earned_at | FK: member, achievement. Unique: [member, achievement] |
| `Quiz` | title, passing_score (default 70%) | OneToOne: Lesson |
| `QuizQuestion` | text, order | FK: quiz |
| `QuizAnswer` | text, is_correct | FK: question |
| `QuizAttempt` | score, passed, answers (JSON) | FK: member, quiz |

## Lifecycle du membre
```
REGISTERED → FORM_SUBMITTED → IN_TRAINING → INTERVIEW_PENDING → ACTIVE
```

Chaque transition est geree par `OnboardingService`:
1. **REGISTERED**: `initialize_onboarding()` → set form_deadline (30j), cree MemberQRCode, envoie Notification, demarre WelcomeSequence
2. **FORM_SUBMITTED**: `submit_form()` → notifie admins
3. **IN_TRAINING**: `admin_approve()` → assigne cours de formation
4. **INTERVIEW**: Planification, counter-propose, confirmation, resultat
5. **ACTIVE**: Acces complet au dashboard

## API ViewSets (20+)
Courses, lessons, trainings, interviews, status, stats, mentor-assignments, form-fields, form-responses, welcome-sequences, welcome-progress, documents, signatures, visitors, tracks, achievements, member-achievements, quizzes, quiz-attempts

## Frontend Views (40+ templates)
Admin: pipeline (kanban), review/approval, courses CRUD, lesson scheduling, interview scheduling/result, invitation codes CRUD, mentor admin, form field admin, welcome sequences, visitor follow-ups, stats, bulk actions
Member: dashboard (par status), form submission, training detail, interview detail/counter-propose, mentee view, journey map, document signing, achievements/leaderboard, accept invitation, congratulations

## Forms (18)
OnboardingProfileForm, TrainingCourseForm, LessonForm, ScheduleLessonForm, ScheduleInterviewForm, InterviewCounterProposeForm, InterviewResultForm, AdminReviewForm, InvitationCreateForm, InvitationEditForm, InvitationAcceptForm, MentorAssignmentForm, MentorCheckInForm, OnboardingFormFieldForm, WelcomeSequenceForm, WelcomeStepForm, OnboardingDocumentForm, DocumentSignatureForm, VisitorFollowUpForm, OnboardingTrackForm, AchievementForm, BulkPipelineActionForm

## Services
- `OnboardingService.initialize_onboarding(member)` - Initialise tout le parcours
- `OnboardingService.submit_form(member)` - Transition FORM_SUBMITTED
- `OnboardingService.admin_approve(member, course)` - Transition IN_TRAINING

## Signals
- `initialize_onboarding_on_create` - post_save Member → auto-initialise pour nouveaux membres avec compte user

## Points d'attention
- Pipeline kanban: 4 colonnes CSS-only, pas de drag-and-drop
- Invitation codes: 8 chars uppercase alphanumeric, max_uses, expiry, skip_onboarding flag
- Champs conditionnels: field B visible seulement si field A = valeur X
- Multi-track: parcours differents (nouveau croyant, transfert, jeunesse, famille)
- Quiz: passing_score configurable, multiple tentatives possibles
- Gamification: achievements attribues manuellement pour l'instant (auto-trigger partiel)

## Fichiers cles
- `apps/onboarding/models.py` - 22 modeles (app la plus complexe)
- `apps/onboarding/services.py` - OnboardingService
- `apps/onboarding/signals.py` - Auto-initialization
- `apps/onboarding/views_api.py` - 20+ ViewSets
- `apps/onboarding/views_frontend.py` - 40+ vues
- `apps/onboarding/forms.py` - 18 formulaires
