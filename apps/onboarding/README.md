# Onboarding App

## Overview

The onboarding app manages the full member integration pipeline — from initial registration through form submission, admin review, training courses, lesson attendance, final interview, and activation as a full member. It also handles invitation codes for fast-tracking pre-existing members.

### Key Features

- **Membership Lifecycle**: Status-driven pipeline (Registered → Form Submitted → In Review → In Training → Interview → Active)
- **Profile Form**: Mandatory form that must be completed within a configurable deadline (default 30 days)
- **Admin Review**: Approve, reject, or request changes on submitted applications
- **Training Courses**: Configurable multi-lesson courses with PDF materials and notes
- **Lesson Scheduling**: Per-member lesson scheduling with date, location, and attendance tracking
- **Interview System**: Propose, counter-propose, confirm, and record final interview results
- **Invitation Codes**: HMAC-signed codes with role assignment, expiration, max uses, and skip-onboarding option
- **Automated Reminders**: Celery tasks for form deadlines (7d/3d/1d), lessons (5d/3d/1d/same day), and interviews (5d/3d/1d/same day)
- **Statistics Dashboard**: Pipeline counts, success rates, average completion days, monthly registrations
- **Signal Integration**: Automatic onboarding initialization when a new member is created

## File Structure

```
apps/onboarding/
├── __init__.py
├── admin.py                 # Django admin configuration
├── apps.py                  # App config (ready() loads signals)
├── forms.py                 # 11 forms (profile, review, course, lesson, interview, invitation)
├── models.py                # TrainingCourse, Lesson, MemberTraining, ScheduledLesson, Interview, InvitationCode
├── serializers.py           # DRF serializers
├── services.py              # OnboardingService (all lifecycle transitions)
├── signals.py               # Auto-initialize onboarding on member creation
├── stats.py                 # OnboardingStats (pipeline metrics)
├── tasks.py                 # Celery tasks (expiration, reminders)
├── urls.py                  # Frontend + API URL patterns
├── views_api.py             # DRF ViewSets (courses, lessons, trainings, interviews, status, stats)
├── views_frontend.py        # Template-based views (21 views)
├── migrations/
│   ├── 0001_initial.py
│   ├── 0002_invitation_code.py
│   └── 0003_interview_reminder_5days_sent_and_more.py
└── tests/
    ├── __init__.py
    ├── factories.py          # Test factories
    ├── test_models.py        # Model tests
    ├── test_forms.py         # Form validation tests
    ├── test_invitations.py   # Invitation code tests
    ├── test_tasks.py         # Celery task tests
    └── test_views_frontend.py # Frontend view tests
```

## Models

### TrainingCourse

Template for a training program assigned to new members.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `name` | CharField(200) | Course name (e.g., "Parcours Decouverte 2025") |
| `description` | TextField | Course description (optional) |
| `total_lessons` | PositiveIntegerField | Expected number of lessons (default: 5) |
| `is_default` | BooleanField | Auto-assigned to new members if True |
| `created_by` | ForeignKey → Member | Admin who created the course |

**Properties:**
- `lesson_count` / `lessons_count` → `int`: Active lessons in this course
- `participants_count` → `int`: Active enrollments

### Lesson

Individual lesson within a training course.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `course` | ForeignKey → TrainingCourse | Parent course |
| `order` | PositiveIntegerField | Lesson number in the course |
| `title` | CharField(200) | Lesson title |
| `description` | TextField | Lesson description (optional) |
| `duration_minutes` | PositiveIntegerField | Duration in minutes (default: 90) |
| `materials_pdf` | FileField | PDF attachment (validated by `validate_pdf_file`) |
| `materials_notes` | TextField | Text-based course notes |

**Constraints:**
- `unique_together = ['course', 'order']`

### MemberTraining

Enrollment of a specific member in a training course.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | ForeignKey → Member | The enrolled member |
| `course` | ForeignKey → TrainingCourse | The training course |
| `assigned_by` | ForeignKey → Member | Admin who assigned the training |
| `assigned_at` | DateTimeField | Auto-set on creation |
| `completed_at` | DateTimeField | When the training was fully completed |
| `is_completed` | BooleanField | Whether all lessons are done |

**Properties:**
- `progress_percentage` → `int`: Percentage of completed lessons (0-100)
- `completed_count` → `int`: Number of completed lessons
- `total_count` → `int`: Total scheduled lessons
- `absent_count` → `int`: Number of missed lessons

**Constraints:**
- `unique_together = ['member', 'course']`

### ScheduledLesson

A specific lesson scheduled for a member at a date/time.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `training` | ForeignKey → MemberTraining | The member's training enrollment |
| `lesson` | ForeignKey → Lesson | The lesson template |
| `scheduled_date` | DateTimeField | Scheduled date and time |
| `location` | CharField(200) | Location (optional) |
| `status` | CharField(20) | `upcoming`, `completed`, `absent`, `cancelled` |
| `attended_at` | DateTimeField | When attendance was marked |
| `marked_by` | ForeignKey → Member | Staff who marked attendance |
| `is_makeup` | BooleanField | Whether this is a make-up session |
| `notes` | TextField | Additional notes |
| `reminder_5days_sent` | BooleanField | Reminder tracking flags |
| `reminder_3days_sent` | BooleanField | |
| `reminder_1day_sent` | BooleanField | |
| `reminder_sameday_sent` | BooleanField | |

### Interview

Final interview to become an official member.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `member` | ForeignKey → Member | The interviewee |
| `training` | ForeignKey → MemberTraining | Associated training |
| `status` | CharField(20) | `proposed`, `confirmed`, `counter`, `accepted`, `completed_pass`, `completed_fail`, `no_show` |
| `proposed_date` | DateTimeField | Admin-proposed interview date |
| `counter_proposed_date` | DateTimeField | Member's counter-proposed date |
| `confirmed_date` | DateTimeField | Final confirmed date |
| `location` | CharField(200) | Interview location |
| `interviewer` | ForeignKey → Member | Conducting pastor/admin |
| `completed_at` | DateTimeField | When the interview took place |
| `result_notes` | TextField | Notes from the interview |
| `reminder_5days_sent` | BooleanField | Reminder tracking flags |
| `reminder_3days_sent` | BooleanField | |
| `reminder_1day_sent` | BooleanField | |
| `reminder_sameday_sent` | BooleanField | |

**Properties:**
- `final_date` → `datetime`: Returns `confirmed_date` or falls back to `proposed_date`

### InvitationCode

Code for integrating new members or assigning roles.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (from BaseModel) |
| `code` | CharField(32) | Unique 8-char alphanumeric code (auto-generated) |
| `role` | CharField(20) | Role assigned on use (default: `member`) |
| `created_by` | ForeignKey → Member | Admin who created the code |
| `used_by` | ForeignKey → Member | Member who used the code |
| `used_at` | DateTimeField | When the code was used |
| `expires_at` | DateTimeField | Expiration date |
| `max_uses` | PositiveIntegerField | Maximum uses (default: 1) |
| `use_count` | PositiveIntegerField | Current use count |
| `skip_onboarding` | BooleanField | Skip entire pipeline if True (pre-existing members) |
| `note` | TextField | Admin note |

**Properties:**
- `is_expired` → `bool`: Whether the code has passed its expiration
- `is_usable` → `bool`: Active, not expired, and uses remaining

## Forms

| Form | Type | Description |
|------|------|-------------|
| `OnboardingProfileForm` | ModelForm (Member) | Mandatory profile form (name, contact, address, photo, family status) |
| `TrainingCourseForm` | ModelForm | Create/edit training courses |
| `LessonForm` | ModelForm | Create/edit lessons (with PDF upload) |
| `ScheduleLessonForm` | ModelForm | Schedule lessons with datetime-local widget |
| `ScheduleInterviewForm` | ModelForm | Schedule interview with interviewer selection |
| `InterviewCounterProposeForm` | Form | Member counter-proposes alternative date |
| `InterviewResultForm` | Form | Record pass/fail and notes |
| `AdminReviewForm` | Form | Approve/reject/request changes with course selection |
| `InvitationCreateForm` | Form | Create invitation with role, expiration, max uses, skip option |
| `InvitationEditForm` | ModelForm | Edit existing invitation |
| `InvitationAcceptForm` | Form | Member enters invitation code (with validation) |

All forms use `W3CRMFormMixin` for automatic CSS class application.

## Services

### OnboardingService

Central business logic for all lifecycle transitions:

| Method | Description |
|--------|-------------|
| `initialize_onboarding(member)` | Set REGISTERED status, create QR code, set form deadline, send welcome notification |
| `submit_form(member)` | Mark FORM_SUBMITTED, notify admins |
| `admin_approve(member, admin, course)` | Mark IN_TRAINING, create MemberTraining + ScheduledLessons, notify member |
| `admin_reject(member, admin, reason)` | Mark REJECTED, record reason, notify member |
| `admin_request_changes(member, admin, message)` | Mark IN_REVIEW, notify member to correct form |
| `mark_lesson_attended(lesson, marked_by)` | Mark lesson COMPLETED, check if training is 100% done, notify admins/member |
| `schedule_interview(member, training, interviewer, date, location)` | Mark INTERVIEW_SCHEDULED, create Interview, notify member |
| `member_accept_interview(interview)` | Mark CONFIRMED, notify interviewer |
| `member_counter_propose(interview, new_date)` | Mark COUNTER, notify interviewer |
| `admin_confirm_counter(interview)` | Accept counter-proposal, mark CONFIRMED |
| `complete_interview(interview, passed, notes)` | Mark ACTIVE (pass) or REJECTED (fail), notify member |
| `mark_interview_no_show(interview)` | Mark NO_SHOW, reject member definitively |
| `create_invitation(created_by, role, expires, max_uses, skip, note)` | Create InvitationCode |
| `accept_invitation(invitation, member)` | Use code, assign role, optionally skip onboarding |
| `expire_overdue_members()` | Expire accounts that missed form deadline |

## API Endpoints

Base path: `/api/v1/onboarding/`

### TrainingCourseViewSet (ModelViewSet)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/courses/` | List courses | Pastor/Admin |
| POST | `/courses/` | Create course | Pastor/Admin |
| GET/PUT/DELETE | `/courses/{id}/` | CRUD operations | Pastor/Admin |

### LessonViewSet (ModelViewSet)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/lessons/` | List lessons (filterable by `course`) | Pastor/Admin |
| POST | `/lessons/` | Create lesson | Pastor/Admin |
| GET/PUT/DELETE | `/lessons/{id}/` | CRUD operations | Pastor/Admin |

### MemberTrainingViewSet (ReadOnly)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/trainings/` | List trainings (own for members, all for admins) | Authenticated |
| GET | `/trainings/{id}/` | Retrieve training details | Authenticated |

### InterviewViewSet (ReadOnly + Actions)
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/interviews/` | List interviews (own or all) | Authenticated |
| GET | `/interviews/{id}/` | Retrieve interview | Authenticated |
| POST | `/interviews/{id}/accept/` | Accept proposed date | Authenticated |
| POST | `/interviews/{id}/counter_propose/` | Counter-propose a date | Authenticated |

### OnboardingStatusView
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/status/` | Get current onboarding status + progress | Authenticated |

### OnboardingStatsView
| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/stats/` | Pipeline counts, success rate, averages | Pastor/Admin |

## Frontend URLs

Base path: `/onboarding/`

### Member-facing views

| URL | View | Name | Access |
|-----|------|------|--------|
| `/onboarding/dashboard/` | `dashboard` | `onboarding:dashboard` | All members |
| `/onboarding/form/` | `onboarding_form` | `onboarding:form` | Registered/Form Pending/In Review |
| `/onboarding/training/` | `my_training` | `onboarding:training` | In Training |
| `/onboarding/interview/` | `my_interview` | `onboarding:interview` | Interview Scheduled |
| `/onboarding/invitation/` | `accept_invitation` | `onboarding:accept_invitation` | All members |

### Admin views

| URL | View | Name | Access |
|-----|------|------|--------|
| `/onboarding/admin/pipeline/` | `admin_pipeline` | `onboarding:admin_pipeline` | Admin, Pastor |
| `/onboarding/admin/review/<uuid>/` | `admin_review` | `onboarding:admin_review` | Admin, Pastor |
| `/onboarding/admin/schedule-interview/<uuid>/` | `admin_schedule_interview` | `onboarding:admin_schedule_interview` | Admin, Pastor |
| `/onboarding/admin/interview-result/<uuid>/` | `admin_interview_result` | `onboarding:admin_interview_result` | Admin, Pastor |
| `/onboarding/admin/schedule-lessons/<uuid>/` | `admin_schedule_lessons` | `onboarding:admin_schedule_lessons` | Admin, Pastor |
| `/onboarding/admin/courses/` | `admin_courses` | `onboarding:admin_courses` | Admin, Pastor |
| `/onboarding/admin/courses/create/` | `admin_course_create` | `onboarding:admin_course_create` | Admin, Pastor |
| `/onboarding/admin/courses/<uuid>/` | `admin_course_detail` | `onboarding:admin_course_detail` | Admin, Pastor |
| `/onboarding/admin/courses/<uuid>/edit/` | `admin_course_edit` | `onboarding:admin_course_edit` | Admin, Pastor |
| `/onboarding/admin/courses/<uuid>/lessons/<uuid>/edit/` | `admin_lesson_edit` | `onboarding:admin_lesson_edit` | Admin, Pastor |
| `/onboarding/admin/courses/<uuid>/lessons/<uuid>/delete/` | `admin_lesson_delete` | `onboarding:admin_lesson_delete` | Admin, Pastor |
| `/onboarding/admin/stats/` | `admin_stats` | `onboarding:admin_stats` | Admin, Pastor |
| `/onboarding/admin/invitations/` | `admin_invitations` | `onboarding:admin_invitations` | Admin, Pastor |
| `/onboarding/admin/invitations/create/` | `admin_invitation_create` | `onboarding:admin_invitation_create` | Admin, Pastor |
| `/onboarding/admin/invitations/<uuid>/edit/` | `admin_invitation_edit` | `onboarding:admin_invitation_edit` | Admin, Pastor |
| `/onboarding/admin/invitations/<uuid>/delete/` | `admin_invitation_delete` | `onboarding:admin_invitation_delete` | Admin, Pastor |

## Templates

All templates are in `templates/onboarding/` and extend `base.html`.

### Member-facing templates

| Template | View | Description |
|----------|------|-------------|
| `status_registered.html` | `dashboard` | Shows form deadline countdown |
| `status_submitted.html` | `dashboard` | Waiting for admin review |
| `status_in_training.html` | `dashboard` | Training progress with lesson list |
| `status_interview.html` | `dashboard` | Interview date and status |
| `status_rejected.html` | `dashboard` | Rejection notice with reason |
| `form_complete.html` | `onboarding_form` | Mandatory profile form |
| `training_detail.html` | `my_training` | Full training view with lessons |
| `interview_detail.html` | `my_interview` | Accept or counter-propose interview |
| `accept_invitation.html` | `accept_invitation` | Enter invitation code form |

### Admin templates

| Template | View | Description |
|----------|------|-------------|
| `admin_pipeline.html` | `admin_pipeline` | Kanban-style pipeline overview |
| `admin_review.html` | `admin_review` | Member application review (approve/reject/request changes) |
| `admin_schedule_interview.html` | `admin_schedule_interview` | Schedule interview form |
| `admin_interview_result.html` | `admin_interview_result` | Record pass/fail result |
| `admin_schedule_lessons.html` | `admin_schedule_lessons` | Schedule dates for all lessons |
| `admin_courses.html` | `admin_courses` | Course list |
| `admin_course_detail.html` | `admin_course_detail` | Course detail with lesson management |
| `admin_course_form.html` | `admin_course_create/edit` | Course create/edit form |
| `admin_lesson_form.html` | `admin_lesson_edit` | Lesson edit form |
| `admin_stats.html` | `admin_stats` | Statistics dashboard |
| `admin_invitations.html` | `admin_invitations` | Invitation code list |
| `admin_invitation_form.html` | `admin_invitation_create` | Create invitation form |
| `admin_invitation_edit.html` | `admin_invitation_edit` | Edit invitation form |
| `admin_invitation_delete.html` | `admin_invitation_delete` | Deactivation confirmation |

## Celery Tasks

### `check_expired_forms`
Daily task that expires accounts that missed the form submission deadline.

### `send_form_deadline_reminders`
Daily task that sends reminders at 7, 3, and 1 day(s) before the form deadline.

### `send_lesson_reminders`
Daily task that sends lesson reminders at 5, 3, 1 day(s) before, and on the same day. Uses per-lesson tracking flags to avoid duplicate notifications.

### `send_interview_reminders`
Daily task that sends interview reminders at 5, 3, 1 day(s) before, and on the same day. Only for confirmed/accepted interviews.

## Signals

### `initialize_onboarding_on_create`
`post_save` on `Member`: When a new member is created with a user account (and no existing `registration_date`), automatically calls `OnboardingService.initialize_onboarding()`. Superusers are excluded.

## Admin Configuration

All 5 main models are registered in Django admin:

- **TrainingCourseAdmin**: list by name/lessons/default/active, inline Lessons
- **LessonAdmin**: list by title/course/order/duration, filter by course
- **MemberTrainingAdmin**: list by member/course/completed/date, inline ScheduledLessons
- **ScheduledLessonAdmin**: list by lesson/training/date/status/makeup
- **InterviewAdmin**: list by member/status/dates/interviewer

## Permissions Matrix

| Action | Member | Volunteer | Group Leader | Deacon | Pastor | Admin |
|--------|--------|-----------|-------------|--------|--------|-------|
| View own dashboard | Yes | Yes | Yes | Yes | Yes | Yes |
| Submit profile form | Yes* | — | — | — | — | — |
| View own training | Yes* | — | — | — | — | — |
| View/respond to interview | Yes* | — | — | — | — | — |
| Accept invitation code | Yes | Yes | Yes | Yes | Yes | Yes |
| Admin pipeline | — | — | — | — | Yes | Yes |
| Review applications | — | — | — | — | Yes | Yes |
| Manage courses/lessons | — | — | — | — | Yes | Yes |
| Schedule interviews | — | — | — | — | Yes | Yes |
| Record interview results | — | — | — | — | Yes | Yes |
| Manage invitations | — | — | — | — | Yes | Yes |
| View statistics | — | — | — | — | Yes | Yes |

\* Only available when membership status is at the appropriate pipeline stage

## Dependencies

- **members**: Member model (profile data, status fields, role assignment)
- **attendance**: MemberQRCode (created during onboarding initialization)
- **communication**: Notification model (all lifecycle notifications and reminders)
- **core**: BaseModel, constants (MembershipStatus, Roles, LessonStatus, InterviewStatus, FamilyStatus, Province), validators (validate_pdf_file), mixins (W3CRMFormMixin), permissions (IsPastorOrAdmin)
- **External**: Celery (periodic tasks)

## Tests

Test files in `apps/onboarding/tests/`:
- `factories.py` — Test data factories for all models
- `test_models.py` — Model creation, properties, constraints
- `test_forms.py` — Form validation (profile, review, invitation)
- `test_invitations.py` — Invitation code lifecycle (create, accept, expire, skip onboarding)
- `test_tasks.py` — Celery task tests (expiration, reminders with timezone handling)
- `test_views_frontend.py` — Frontend view tests (pipeline, review, scheduling, permissions)
