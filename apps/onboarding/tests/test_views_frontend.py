"""Tests for onboarding frontend views."""
import pytest
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from apps.core.constants import (
    InterviewStatus,
    LessonStatus,
    MembershipStatus,
    Roles,
)
from apps.communication.models import Notification
from apps.members.models import Member
from apps.members.tests.factories import (
    AdminMemberFactory,
    MemberFactory,
    PastorFactory,
    UserFactory,
)
from apps.onboarding.models import (
    Interview,
    Lesson,
    MemberTraining,
    ScheduledLesson,
    TrainingCourse,
)
from apps.onboarding.models import InvitationCode
from apps.onboarding.tests.factories import (
    InterviewFactory,
    InvitationCodeFactory,
    LessonFactory,
    MemberTrainingFactory,
    ScheduledLessonFactory,
    TrainingCourseFactory,
)


# ---------------------------------------------------------------------------
# Template stub fixture (autouse) -- matches the pattern in members tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs so render() doesn't blow up."""
    onboarding_dir = tmp_path / 'onboarding'
    onboarding_dir.mkdir()
    template_names = [
        'status_registered.html',
        'status_submitted.html',
        'status_in_training.html',
        'status_interview.html',
        'status_rejected.html',
        'form_complete.html',
        'training_detail.html',
        'interview_detail.html',
        'admin_pipeline.html',
        'admin_review.html',
        'admin_schedule_interview.html',
        'admin_interview_result.html',
        'admin_schedule_lessons.html',
        'admin_courses.html',
        'admin_course_form.html',
        'admin_course_detail.html',
        'admin_lesson_form.html',
        'admin_stats.html',
        'admin_invitations.html',
        'admin_invitation_form.html',
        'admin_invitation_edit.html',
        'admin_invitation_delete.html',
        'accept_invitation.html',
    ]
    for name in template_names:
        (onboarding_dir / name).write_text('{{ page_title|default:"test" }}')
    settings.TEMPLATES = [
        {
            **settings.TEMPLATES[0],
            'DIRS': [str(tmp_path)] + [
                str(d) for d in settings.TEMPLATES[0].get('DIRS', [])
            ],
        }
    ]


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def member_user():
    """Regular member with linked user account (no onboarding signal)."""
    user = UserFactory()
    # Create without user first to avoid the signal, then attach
    member = MemberFactory(
        user=None,
        role=Roles.MEMBER,
        membership_status=MembershipStatus.REGISTERED,
        registration_date=timezone.now() - timedelta(days=5),
        form_deadline=timezone.now() + timedelta(days=25),
    )
    # Attach user without triggering signal (already has registration_date)
    member.user = user
    member.save(update_fields=['user'])
    return user, member


@pytest.fixture
def admin_user():
    """Admin with linked user account."""
    user = UserFactory()
    member = AdminMemberFactory(
        user=None,
        registration_date=timezone.now() - timedelta(days=60),
        form_deadline=timezone.now() - timedelta(days=30),
        membership_status=MembershipStatus.ACTIVE,
    )
    member.user = user
    member.save(update_fields=['user'])
    return user, member


@pytest.fixture
def pastor_user():
    """Pastor with linked user account."""
    user = UserFactory()
    member = PastorFactory(
        user=None,
        registration_date=timezone.now() - timedelta(days=60),
        form_deadline=timezone.now() - timedelta(days=30),
        membership_status=MembershipStatus.ACTIVE,
    )
    member.user = user
    member.save(update_fields=['user'])
    return user, member


# ---------------------------------------------------------------------------
# Dashboard view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDashboardView:
    """Tests for onboarding dashboard view."""

    url = '/onboarding/dashboard/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects_to_create(self, client):
        """User without member_profile redirects to member create."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert 'register' in response.url or 'member' in response.url

    def test_registered_status_renders_registered_template(self, client, member_user):
        """REGISTERED status renders status_registered template."""
        user, member = member_user
        member.membership_status = MembershipStatus.REGISTERED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_form_pending_status_renders_registered_template(self, client, member_user):
        """FORM_PENDING status renders status_registered template."""
        user, member = member_user
        member.membership_status = MembershipStatus.FORM_PENDING
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_form_submitted_status(self, client, member_user):
        """FORM_SUBMITTED renders status_submitted template."""
        user, member = member_user
        member.membership_status = MembershipStatus.FORM_SUBMITTED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_in_review_status(self, client, member_user):
        """IN_REVIEW renders status_submitted template."""
        user, member = member_user
        member.membership_status = MembershipStatus.IN_REVIEW
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_in_training_status_with_training(self, client, member_user):
        """IN_TRAINING with training shows training template."""
        user, member = member_user
        member.membership_status = MembershipStatus.IN_TRAINING
        member.save(update_fields=['membership_status'])
        course = TrainingCourseFactory()
        MemberTrainingFactory(member=member, course=course)
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_in_training_status_without_training(self, client, member_user):
        """IN_TRAINING without training object still renders."""
        user, member = member_user
        member.membership_status = MembershipStatus.IN_TRAINING
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_approved_status_renders_training_template(self, client, member_user):
        """APPROVED status also shows training template."""
        user, member = member_user
        member.membership_status = MembershipStatus.APPROVED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_interview_scheduled_status(self, client, member_user):
        """INTERVIEW_SCHEDULED renders status_interview template."""
        user, member = member_user
        member.membership_status = MembershipStatus.INTERVIEW_SCHEDULED
        member.save(update_fields=['membership_status'])
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        InterviewFactory(member=member, training=training)
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_rejected_status(self, client, member_user):
        """REJECTED renders status_rejected template."""
        user, member = member_user
        member.membership_status = MembershipStatus.REJECTED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_expired_status(self, client, member_user):
        """EXPIRED renders status_rejected template."""
        user, member = member_user
        member.membership_status = MembershipStatus.EXPIRED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_active_status_redirects_to_reports_dashboard(self, client, member_user):
        """ACTIVE members are redirected to the reports dashboard."""
        user, member = member_user
        member.membership_status = MembershipStatus.ACTIVE
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 302
        assert 'reports' in response.url or 'dashboard' in response.url

    def test_fallback_renders_registered_template(self, client, member_user):
        """Unknown/unhandled status falls through to registered template."""
        user, member = member_user
        # SUSPENDED is not explicitly handled, hits the fallback
        member.membership_status = MembershipStatus.SUSPENDED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Onboarding form view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOnboardingFormView:
    """Tests for onboarding_form view."""

    url = '/onboarding/form/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client):
        """User without member_profile redirects to member create."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_get_shows_form(self, client, member_user):
        """GET renders the onboarding form."""
        user, member = member_user
        member.membership_status = MembershipStatus.REGISTERED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    def test_already_submitted_redirects(self, client, member_user):
        """Member with status beyond form phase is redirected."""
        user, member = member_user
        member.membership_status = MembershipStatus.IN_TRAINING
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 302

    def test_form_expired_redirects(self, client, member_user):
        """Member whose form deadline has passed is redirected."""
        user, member = member_user
        member.membership_status = MembershipStatus.REGISTERED
        member.form_deadline = timezone.now() - timedelta(days=1)
        member.save(update_fields=['membership_status', 'form_deadline'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 302

    def test_in_review_can_access_form(self, client, member_user):
        """Member in IN_REVIEW status can still access the form (request_changes case)."""
        user, member = member_user
        member.membership_status = MembershipStatus.IN_REVIEW
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    @patch('apps.onboarding.views_frontend.OnboardingService.submit_form')
    def test_valid_post_submits_form(self, mock_submit, client, member_user):
        """Valid POST calls OnboardingService.submit_form and redirects."""
        user, member = member_user
        member.membership_status = MembershipStatus.REGISTERED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        data = {
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean@example.com',
            'phone': '514-555-0001',
            'birth_date': '1990-01-15',
            'address': '123 Rue Test',
            'city': 'Montreal',
            'province': 'QC',
            'postal_code': 'H1A 1A1',
            'family_status': 'single',
        }
        response = client.post(self.url, data)
        assert response.status_code == 302
        mock_submit.assert_called_once()

    def test_invalid_post_re_renders(self, client, member_user):
        """Invalid POST re-renders the form with errors."""
        user, member = member_user
        member.membership_status = MembershipStatus.REGISTERED
        member.save(update_fields=['membership_status'])
        client.force_login(user)

        data = {
            'first_name': '',
            'last_name': '',
        }
        response = client.post(self.url, data)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# My training view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMyTrainingView:
    """Tests for my_training view."""

    url = '/onboarding/training/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client):
        """User without member_profile redirects."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_no_training_redirects(self, client, member_user):
        """Member with no training is redirected to dashboard."""
        user, member = member_user
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 302

    def test_with_training_renders(self, client, member_user):
        """Member with training sees training detail."""
        user, member = member_user
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        lesson = LessonFactory(course=course)
        ScheduledLessonFactory(training=training, lesson=lesson)
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# My interview view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMyInterviewView:
    """Tests for my_interview view."""

    url = '/onboarding/interview/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client):
        """User without member_profile redirects."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_no_interview_redirects(self, client, member_user):
        """Member with no interview is redirected."""
        user, member = member_user
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 302

    def test_get_with_interview(self, client, member_user):
        """Member with interview sees interview detail."""
        user, member = member_user
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        InterviewFactory(member=member, training=training)
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 200

    @patch('apps.onboarding.views_frontend.OnboardingService.member_accept_interview')
    def test_post_accept(self, mock_accept, client, member_user):
        """POST with action=accept calls member_accept_interview."""
        user, member = member_user
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        InterviewFactory(member=member, training=training)
        client.force_login(user)

        response = client.post(self.url, {'action': 'accept'})
        assert response.status_code == 302
        mock_accept.assert_called_once()

    @patch('apps.onboarding.views_frontend.OnboardingService.member_counter_propose')
    def test_post_counter_propose(self, mock_counter, client, member_user):
        """POST with action=counter and valid date calls member_counter_propose."""
        user, member = member_user
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        InterviewFactory(member=member, training=training)
        client.force_login(user)

        future_date = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M')
        response = client.post(
            self.url,
            {'action': 'counter', 'counter_proposed_date': future_date},
        )
        assert response.status_code == 302
        mock_counter.assert_called_once()

    def test_post_counter_propose_invalid_form(self, client, member_user):
        """POST with action=counter but invalid date re-renders."""
        user, member = member_user
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        InterviewFactory(member=member, training=training)
        client.force_login(user)

        response = client.post(
            self.url,
            {'action': 'counter', 'counter_proposed_date': ''},
        )
        # Invalid form -> re-renders the page (200)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Admin pipeline view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminPipelineView:
    """Tests for admin_pipeline view."""

    url = '/onboarding/admin/pipeline/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_regular_member_denied(self, client, member_user):
        """Regular members are redirected (access denied)."""
        user, member = member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_admin_can_access(self, client, admin_user):
        """Admins can access the pipeline."""
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_pastor_can_access(self, client, pastor_user):
        """Pastors can access the pipeline."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_user_without_profile_redirects(self, client):
        """User without member_profile is redirected."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_pipeline_with_populated_columns(self, client, admin_user):
        """Pipeline shows members in all Kanban columns with annotations."""
        user, _ = admin_user
        client.force_login(user)

        # Create members in each status
        reg_member = MemberFactory(
            user=None,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        sub_member = MemberFactory(
            user=None,
            membership_status=MembershipStatus.FORM_SUBMITTED,
            registration_date=timezone.now() - timedelta(days=10),
        )
        train_member = MemberFactory(
            user=None,
            membership_status=MembershipStatus.IN_TRAINING,
            registration_date=timezone.now() - timedelta(days=20),
        )
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=train_member, course=course)

        iv_member = MemberFactory(
            user=None,
            membership_status=MembershipStatus.INTERVIEW_SCHEDULED,
            registration_date=timezone.now() - timedelta(days=30),
        )
        InterviewFactory(member=iv_member, training=MemberTrainingFactory(member=iv_member, course=course))

        response = client.get(self.url)
        assert response.status_code == 200
        assert len(response.context['registered_list']) >= 1
        assert len(response.context['submitted_list']) >= 1
        assert len(response.context['training_list']) >= 1
        assert len(response.context['interview_list']) >= 1


# ---------------------------------------------------------------------------
# Admin review view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminReviewView:
    """Tests for admin_review view."""

    def _url(self, pk):
        return f'/onboarding/admin/review/{pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        member = MemberFactory(user=None, registration_date=timezone.now())
        response = client.get(self._url(member.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied access."""
        user, member = member_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)
        response = client.get(self._url(target.pk))
        assert response.status_code == 302

    def test_admin_get_review(self, client, admin_user):
        """Admin can GET the review page."""
        user, admin_member = admin_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)
        response = client.get(self._url(target.pk))
        assert response.status_code == 200

    @patch('apps.onboarding.views_frontend.OnboardingService.admin_approve')
    def test_post_approve_with_course(self, mock_approve, client, admin_user):
        """POST approve with a course calls admin_approve."""
        user, admin_member = admin_user
        target = MemberFactory(
            user=None,
            registration_date=timezone.now(),
            membership_status=MembershipStatus.FORM_SUBMITTED,
        )
        course = TrainingCourseFactory()
        client.force_login(user)

        response = client.post(self._url(target.pk), {
            'action': 'approve',
            'course': str(course.pk),
        })
        assert response.status_code == 302
        mock_approve.assert_called_once()

    def test_post_approve_without_course_shows_error(self, client, admin_user):
        """POST approve without course shows error, stays on page."""
        user, admin_member = admin_user
        target = MemberFactory(
            user=None,
            registration_date=timezone.now(),
            membership_status=MembershipStatus.FORM_SUBMITTED,
        )
        client.force_login(user)

        response = client.post(self._url(target.pk), {
            'action': 'approve',
            'course': '',
        })
        # Re-renders the form (200) because course is missing
        assert response.status_code == 200

    @patch('apps.onboarding.views_frontend.OnboardingService.admin_reject')
    def test_post_reject(self, mock_reject, client, admin_user):
        """POST reject calls admin_reject."""
        user, admin_member = admin_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)

        response = client.post(self._url(target.pk), {
            'action': 'reject',
            'reason': 'Not qualified',
        })
        assert response.status_code == 302
        mock_reject.assert_called_once()

    @patch('apps.onboarding.views_frontend.OnboardingService.admin_request_changes')
    def test_post_request_changes(self, mock_changes, client, admin_user):
        """POST request_changes calls admin_request_changes."""
        user, admin_member = admin_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)

        response = client.post(self._url(target.pk), {
            'action': 'request_changes',
            'reason': 'Missing document',
        })
        assert response.status_code == 302
        mock_changes.assert_called_once()

    def test_user_without_profile_redirects(self, client):
        """User without member_profile is redirected."""
        user = UserFactory()
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)
        response = client.get(self._url(target.pk))
        assert response.status_code == 302

    def test_nonexistent_member_404(self, client, admin_user):
        """404 for non-existent member."""
        import uuid
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404

    def test_review_with_training_progress(self, client, admin_user):
        """Review page includes training_progress when member has active training."""
        user, _ = admin_user
        client.force_login(user)

        member = MemberFactory(
            user=None,
            membership_status=MembershipStatus.IN_TRAINING,
            registration_date=timezone.now() - timedelta(days=20),
        )
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        lesson = LessonFactory(course=course, order=1)
        ScheduledLessonFactory(training=training, lesson=lesson)

        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert response.context['training_progress'] is not None
        assert response.context['training_progress']['total'] == 1


# ---------------------------------------------------------------------------
# Admin schedule interview view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminScheduleInterviewView:
    """Tests for admin_schedule_interview view."""

    def _url(self, pk):
        return f'/onboarding/admin/schedule-interview/{pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        member = MemberFactory(user=None, registration_date=timezone.now())
        response = client.get(self._url(member.pk))
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied."""
        user, member = member_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)
        response = client.get(self._url(target.pk))
        assert response.status_code == 302

    def test_admin_no_completed_training_redirects(self, client, admin_user):
        """Admin redirected if member has no completed training."""
        user, _ = admin_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)

        response = client.get(self._url(target.pk))
        assert response.status_code == 302

    def test_admin_with_completed_training_renders(self, client, admin_user):
        """Admin can view form if member has completed training."""
        user, admin_member = admin_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        course = TrainingCourseFactory()
        MemberTrainingFactory(member=target, course=course, is_completed=True)
        client.force_login(user)

        response = client.get(self._url(target.pk))
        assert response.status_code == 200

    @patch('apps.onboarding.views_frontend.OnboardingService.schedule_interview')
    def test_post_schedules_interview(self, mock_schedule, client, admin_user):
        """Valid POST schedules interview."""
        user, admin_member = admin_user
        target = MemberFactory(user=None, registration_date=timezone.now())
        course = TrainingCourseFactory()
        MemberTrainingFactory(member=target, course=course, is_completed=True)
        interviewer = PastorFactory(user=None, registration_date=timezone.now())
        client.force_login(user)

        future_date = (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M')
        response = client.post(self._url(target.pk), {
            'proposed_date': future_date,
            'location': 'Bureau pastoral',
            'interviewer': str(interviewer.pk),
        })
        assert response.status_code == 302
        mock_schedule.assert_called_once()

    def test_user_without_profile_redirects(self, client):
        """User without member_profile redirected."""
        user = UserFactory()
        target = MemberFactory(user=None, registration_date=timezone.now())
        client.force_login(user)
        response = client.get(self._url(target.pk))
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin interview result view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminInterviewResultView:
    """Tests for admin_interview_result view."""

    def _url(self, pk):
        return f'/onboarding/admin/interview-result/{pk}/'

    def _create_interview(self):
        """Helper to create an interview."""
        member = MemberFactory(user=None, registration_date=timezone.now())
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course, is_completed=True)
        return InterviewFactory(member=member, training=training)

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        iv = self._create_interview()
        response = client.get(self._url(iv.pk))
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied."""
        user, member = member_user
        iv = self._create_interview()
        client.force_login(user)
        response = client.get(self._url(iv.pk))
        assert response.status_code == 302

    def test_admin_get_renders(self, client, admin_user):
        """Admin can GET the interview result form."""
        user, _ = admin_user
        iv = self._create_interview()
        client.force_login(user)
        response = client.get(self._url(iv.pk))
        assert response.status_code == 200

    @patch('apps.onboarding.views_frontend.OnboardingService.complete_interview')
    def test_post_passed(self, mock_complete, client, admin_user):
        """POST with passed=True calls complete_interview."""
        user, _ = admin_user
        iv = self._create_interview()
        client.force_login(user)

        response = client.post(self._url(iv.pk), {
            'passed': 'on',
            'result_notes': 'Great interview',
        })
        assert response.status_code == 302
        mock_complete.assert_called_once()

    @patch('apps.onboarding.views_frontend.OnboardingService.complete_interview')
    def test_post_failed(self, mock_complete, client, admin_user):
        """POST with passed unchecked calls complete_interview with passed=False."""
        user, _ = admin_user
        iv = self._create_interview()
        client.force_login(user)

        response = client.post(self._url(iv.pk), {
            'result_notes': 'Needs more time',
        })
        assert response.status_code == 302
        mock_complete.assert_called_once()
        # passed is the second arg; it should be False (checkbox not sent)
        call_args = mock_complete.call_args
        assert call_args[0][1] is False

    def test_user_without_profile_redirects(self, client):
        """User without member_profile redirected."""
        user = UserFactory()
        iv = self._create_interview()
        client.force_login(user)
        response = client.get(self._url(iv.pk))
        assert response.status_code == 302

    def test_nonexistent_interview_404(self, client, admin_user):
        """404 for non-existent interview."""
        import uuid
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Admin schedule lessons view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminScheduleLessonsView:
    """Tests for admin_schedule_lessons view."""

    def _setup_training_with_lessons(self):
        """Create a training with scheduled lessons."""
        member = MemberFactory(user=None, registration_date=timezone.now())
        course = TrainingCourseFactory()
        lesson1 = LessonFactory(course=course, order=1)
        lesson2 = LessonFactory(course=course, order=2)
        training = MemberTrainingFactory(member=member, course=course)
        sl1 = ScheduledLessonFactory(training=training, lesson=lesson1)
        sl2 = ScheduledLessonFactory(training=training, lesson=lesson2)
        return training, sl1, sl2

    def _url(self, training_pk):
        return f'/onboarding/admin/schedule-lessons/{training_pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        training, _, _ = self._setup_training_with_lessons()
        response = client.get(self._url(training.pk))
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied."""
        user, _ = member_user
        training, _, _ = self._setup_training_with_lessons()
        client.force_login(user)
        response = client.get(self._url(training.pk))
        assert response.status_code == 302

    def test_admin_get_renders(self, client, admin_user):
        """Admin can GET the schedule lessons form."""
        user, _ = admin_user
        training, _, _ = self._setup_training_with_lessons()
        client.force_login(user)
        response = client.get(self._url(training.pk))
        assert response.status_code == 200

    def test_post_updates_dates(self, client, admin_user):
        """POST with valid dates updates scheduled lesson dates."""
        user, _ = admin_user
        training, sl1, sl2 = self._setup_training_with_lessons()
        client.force_login(user)

        new_date = '2026-03-15T10:00'
        response = client.post(self._url(training.pk), {
            f'date_{sl1.pk}': new_date,
            f'location_{sl1.pk}': 'Salle A',
            f'date_{sl2.pk}': '',
        })
        assert response.status_code == 302
        sl1.refresh_from_db()
        assert sl1.location == 'Salle A'

    def test_post_no_dates_still_redirects(self, client, admin_user):
        """POST with no valid dates still redirects."""
        user, _ = admin_user
        training, sl1, sl2 = self._setup_training_with_lessons()
        client.force_login(user)

        response = client.post(self._url(training.pk), {
            f'date_{sl1.pk}': '',
            f'date_{sl2.pk}': '',
        })
        assert response.status_code == 302

    def test_user_without_profile_redirects(self, client):
        """User without member_profile redirected."""
        user = UserFactory()
        training, _, _ = self._setup_training_with_lessons()
        client.force_login(user)
        response = client.get(self._url(training.pk))
        assert response.status_code == 302

    def test_nonexistent_training_404(self, client, admin_user):
        """404 for non-existent training."""
        import uuid
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Admin courses list view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminCoursesView:
    """Tests for admin_courses view."""

    url = '/onboarding/admin/courses/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied."""
        user, _ = member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_admin_can_list_courses(self, client, admin_user):
        """Admin can list courses."""
        user, _ = admin_user
        TrainingCourseFactory.create_batch(3)
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_pastor_can_list_courses(self, client, pastor_user):
        """Pastor can list courses."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_user_without_profile_redirects(self, client):
        """User without member_profile redirected."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin course create view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminCourseCreateView:
    """Tests for admin_course_create view."""

    url = '/onboarding/admin/courses/create/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied."""
        user, _ = member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_admin_get_form(self, client, admin_user):
        """Admin can GET the create course form."""
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_post_creates_course(self, client, admin_user):
        """Valid POST creates a new course."""
        user, _ = admin_user
        client.force_login(user)

        response = client.post(self.url, {
            'name': 'New Course',
            'description': 'Description here',
            'total_lessons': 5,
        })
        assert response.status_code == 302
        assert TrainingCourse.objects.filter(name='New Course').exists()

    def test_post_invalid_re_renders(self, client, admin_user):
        """Invalid POST re-renders the form."""
        user, _ = admin_user
        client.force_login(user)

        response = client.post(self.url, {
            'name': '',
            'total_lessons': 5,
        })
        assert response.status_code == 200

    def test_course_created_by_is_set(self, client, admin_user):
        """created_by is set to the admin who created it."""
        user, admin_member = admin_user
        client.force_login(user)

        client.post(self.url, {
            'name': 'Admin Course',
            'description': 'Test',
            'total_lessons': 3,
        })
        course = TrainingCourse.objects.get(name='Admin Course')
        assert course.created_by == admin_member

    def test_user_without_profile_redirects(self, client):
        """User without member_profile redirected."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin course detail view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminCourseDetailView:
    """Tests for admin_course_detail view."""

    def _url(self, pk):
        return f'/onboarding/admin/courses/{pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        course = TrainingCourseFactory()
        response = client.get(self._url(course.pk))
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        """Regular members are denied."""
        user, _ = member_user
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 302

    def test_admin_get_renders(self, client, admin_user):
        """Admin can GET the course detail."""
        user, _ = admin_user
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 200

    def test_admin_get_empty_course(self, client, admin_user):
        """Admin can view course with no lessons (initial order=1)."""
        user, _ = admin_user
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 200

    def test_post_adds_lesson(self, client, admin_user):
        """POST adds a lesson to the course."""
        user, _ = admin_user
        course = TrainingCourseFactory()
        client.force_login(user)

        response = client.post(self._url(course.pk), {
            'order': 1,
            'title': 'New Lesson',
            'description': 'Lesson content',
            'duration_minutes': 60,
            'materials_notes': '',
        })
        assert response.status_code == 302
        assert Lesson.objects.filter(course=course, title='New Lesson').exists()

    def test_post_invalid_re_renders(self, client, admin_user):
        """Invalid POST re-renders the detail page."""
        user, _ = admin_user
        course = TrainingCourseFactory()
        client.force_login(user)

        response = client.post(self._url(course.pk), {
            'order': '',
            'title': '',
        })
        assert response.status_code == 200

    def test_lesson_course_is_set(self, client, admin_user):
        """Newly added lesson has the correct course FK."""
        user, _ = admin_user
        course = TrainingCourseFactory()
        client.force_login(user)

        client.post(self._url(course.pk), {
            'order': 1,
            'title': 'Test Lesson',
            'duration_minutes': 90,
        })
        lesson = Lesson.objects.get(course=course, title='Test Lesson')
        assert lesson.course == course

    def test_nonexistent_course_404(self, client, admin_user):
        """404 for non-existent course."""
        import uuid
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404

    def test_user_without_profile_redirects(self, client):
        """User without member_profile redirected."""
        user = UserFactory()
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin stats view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminStatsView:
    """Tests for admin_stats view."""

    url = '/onboarding/admin/stats/'

    def test_admin_can_access(self, client, admin_user):
        """Admin can access the stats dashboard."""
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'pipeline' in response.context
        assert 'success_rate' in response.context

    def test_pastor_can_access(self, client, pastor_user):
        """Pastor can access the stats dashboard."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_redirected(self, client, member_user):
        """Regular member is redirected with error message."""
        user, member = member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_no_member_profile_redirected(self, client):
        """User without member_profile is redirected."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin course edit view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminCourseEditView:
    """Tests for admin_course_edit view."""

    def _url(self, pk):
        return f'/onboarding/admin/courses/{pk}/edit/'

    def test_login_required(self, client):
        course = TrainingCourseFactory()
        response = client.get(self._url(course.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 302

    def test_admin_get_renders(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 200

    def test_admin_post_updates(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory(name='Old Name')
        client.force_login(user)
        response = client.post(self._url(course.pk), {
            'name': 'New Name',
            'description': 'Updated',
            'total_lessons': 10,
        })
        assert response.status_code == 302
        course.refresh_from_db()
        assert course.name == 'New Name'

    def test_post_invalid_re_renders(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.post(self._url(course.pk), {'name': '', 'total_lessons': ''})
        assert response.status_code == 200

    def test_user_without_profile_redirects(self, client):
        user = UserFactory()
        course = TrainingCourseFactory()
        client.force_login(user)
        response = client.get(self._url(course.pk))
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin lesson edit view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLessonEditView:
    """Tests for admin_lesson_edit view."""

    def _url(self, course_pk, lesson_pk):
        return f'/onboarding/admin/courses/{course_pk}/lessons/{lesson_pk}/edit/'

    def test_login_required(self, client):
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        response = client.get(self._url(course.pk, lesson.pk))
        assert response.status_code == 302

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.get(self._url(course.pk, lesson.pk))
        assert response.status_code == 302

    def test_admin_get_renders(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.get(self._url(course.pk, lesson.pk))
        assert response.status_code == 200

    def test_admin_post_updates(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1, title='Old Title')
        client.force_login(user)
        response = client.post(self._url(course.pk, lesson.pk), {
            'order': 1,
            'title': 'New Title',
            'duration_minutes': 60,
        })
        assert response.status_code == 302
        lesson.refresh_from_db()
        assert lesson.title == 'New Title'

    def test_post_invalid_re_renders(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.post(self._url(course.pk, lesson.pk), {'order': '', 'title': ''})
        assert response.status_code == 200

    def test_user_without_profile_redirects(self, client):
        user = UserFactory()
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.get(self._url(course.pk, lesson.pk))
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Admin lesson delete view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLessonDeleteView:
    """Tests for admin_lesson_delete view."""

    def _url(self, course_pk, lesson_pk):
        return f'/onboarding/admin/courses/{course_pk}/lessons/{lesson_pk}/delete/'

    def test_login_required(self, client):
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        response = client.post(self._url(course.pk, lesson.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_regular_member_denied(self, client, member_user):
        user, _ = member_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.post(self._url(course.pk, lesson.pk))
        assert response.status_code == 302

    def test_admin_post_soft_deletes(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.post(self._url(course.pk, lesson.pk))
        assert response.status_code == 302
        lesson.refresh_from_db()
        assert lesson.is_active is False

    def test_get_redirects_without_deleting(self, client, admin_user):
        user, _ = admin_user
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.get(self._url(course.pk, lesson.pk))
        assert response.status_code == 302
        lesson.refresh_from_db()
        assert lesson.is_active is True

    def test_user_without_profile_redirects(self, client):
        user = UserFactory()
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        client.force_login(user)
        response = client.post(self._url(course.pk, lesson.pk))
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Invitation Edit
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInvitationEdit:
    """Tests for admin_invitation_edit view."""

    def _url(self, pk):
        return f'/onboarding/admin/invitations/{pk}/edit/'

    def test_login_required(self, client):
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_profile_redirects(self, client):
        user = UserFactory()
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 302

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 302

    def test_admin_get(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 200

    def test_pastor_get(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 200

    def test_post_updates(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        inv = InvitationCodeFactory(max_uses=1, note='')
        data = {
            'role': Roles.VOLUNTEER,
            'expires_at': (timezone.now() + timedelta(days=60)).strftime('%Y-%m-%dT%H:%M'),
            'max_uses': 5,
            'note': 'Updated note',
            'is_active': True,
        }
        response = client.post(self._url(inv.pk), data)
        assert response.status_code == 302
        inv.refresh_from_db()
        assert inv.max_uses == 5
        assert inv.note == 'Updated note'
        assert inv.role == Roles.VOLUNTEER

    def test_post_invalid(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        data = {
            'role': Roles.MEMBER,
            'expires_at': '',
            'max_uses': 1,
        }
        response = client.post(self._url(inv.pk), data)
        assert response.status_code == 200  # re-renders form

    def test_404_for_missing(self, client, admin_user):
        import uuid
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Invitation Delete
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInvitationDelete:
    """Tests for admin_invitation_delete view."""

    def _url(self, pk):
        return f'/onboarding/admin/invitations/{pk}/delete/'

    def test_login_required(self, client):
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_profile_redirects(self, client):
        user = UserFactory()
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 302

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 302

    def test_admin_get_confirm(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        response = client.get(self._url(inv.pk))
        assert response.status_code == 200

    def test_post_deactivates(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        assert inv.is_active is True
        response = client.post(self._url(inv.pk))
        assert response.status_code == 302
        inv.refresh_from_db()
        assert inv.is_active is False

    def test_get_does_not_deactivate(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        inv = InvitationCodeFactory()
        client.get(self._url(inv.pk))
        inv.refresh_from_db()
        assert inv.is_active is True

    def test_404_for_missing(self, client, admin_user):
        import uuid
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Sprint 8: Pipeline search/filter tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminPipelineSearch:
    """Tests for Sprint 8 pipeline search by member name."""

    url = '/onboarding/admin/pipeline/'

    def test_search_by_first_name(self, client, admin_user):
        """Searching by first name filters registered column."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            first_name='Zacharie',
            last_name='Dupont',
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        MemberFactory(
            user=None,
            first_name='Paul',
            last_name='Martin',
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        response = client.get(self.url, {'q': 'Zacharie'})
        assert response.status_code == 200
        registered = response.context['registered_list']
        names = [m.first_name for m in registered]
        assert 'Zacharie' in names
        assert 'Paul' not in names

    def test_search_by_last_name(self, client, admin_user):
        """Searching by last name filters results."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            first_name='Jean',
            last_name='Tremblay',
            membership_status=MembershipStatus.FORM_SUBMITTED,
            registration_date=timezone.now() - timedelta(days=10),
        )
        MemberFactory(
            user=None,
            first_name='Marc',
            last_name='Lavoie',
            membership_status=MembershipStatus.FORM_SUBMITTED,
            registration_date=timezone.now() - timedelta(days=10),
        )
        response = client.get(self.url, {'q': 'Tremblay'})
        assert response.status_code == 200
        submitted = response.context['submitted_list']
        names = [m.last_name for m in submitted]
        assert 'Tremblay' in names
        assert 'Lavoie' not in names

    def test_search_case_insensitive(self, client, admin_user):
        """Search is case-insensitive."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            first_name='Marie',
            last_name='Gagnon',
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        response = client.get(self.url, {'q': 'marie'})
        assert response.status_code == 200
        registered = response.context['registered_list']
        names = [m.first_name for m in registered]
        assert 'Marie' in names

    def test_empty_search_returns_all(self, client, admin_user):
        """Empty search query returns all members."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        response = client.get(self.url, {'q': ''})
        assert response.status_code == 200
        assert len(response.context['registered_list']) >= 1

    def test_no_search_param_returns_all(self, client, admin_user):
        """No 'q' param returns all members."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        response = client.get(self.url)
        assert response.status_code == 200
        assert len(response.context['registered_list']) >= 1

    def test_search_query_in_context(self, client, admin_user):
        """search_query is available in context for template rendering."""
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self.url, {'q': 'TestSearch'})
        assert response.status_code == 200
        assert response.context['search_query'] == 'TestSearch'

    def test_search_no_results(self, client, admin_user):
        """Search query that matches nothing returns empty lists."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            first_name='Jean',
            last_name='Tremblay',
            membership_status=MembershipStatus.REGISTERED,
            registration_date=timezone.now() - timedelta(days=5),
            form_deadline=timezone.now() + timedelta(days=25),
        )
        response = client.get(self.url, {'q': 'ZZZZNONEXISTENT'})
        assert response.status_code == 200
        assert len(response.context['registered_list']) == 0

    def test_search_filters_all_columns(self, client, admin_user):
        """Search filters across all pipeline columns."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(
            user=None,
            first_name='UniqueFirst',
            last_name='UniqueLast',
            membership_status=MembershipStatus.IN_TRAINING,
            registration_date=timezone.now() - timedelta(days=20),
        )
        # Search should NOT find this member in registered column
        response = client.get(self.url, {'q': 'UniqueFirst'})
        assert response.status_code == 200
        registered = response.context['registered_list']
        training = response.context['training_list']
        reg_names = [m.first_name for m in registered]
        train_names = [m.first_name for m in training]
        assert 'UniqueFirst' not in reg_names
        assert 'UniqueFirst' in train_names
