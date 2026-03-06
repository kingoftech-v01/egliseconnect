"""Tests for onboarding services - comprehensive coverage."""
import pytest
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.utils import timezone

from apps.core.constants import (
    MembershipStatus,
    InterviewStatus,
    LessonStatus,
    Roles,
)
from apps.communication.models import Notification
from apps.attendance.models import MemberQRCode
from apps.members.tests.factories import (
    MemberFactory,
    PastorFactory,
    AdminMemberFactory,
    UserFactory,
)
from apps.onboarding.models import (
    TrainingCourse,
    Lesson,
    MemberTraining,
    ScheduledLesson,
    Interview,
)
from apps.onboarding.services import OnboardingService

from .factories import (
    TrainingCourseFactory,
    LessonFactory,
    MemberTrainingFactory,
    ScheduledLessonFactory,
    InterviewFactory,
)


# ---------------------------------------------------------------------------
# initialize_onboarding
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestInitializeOnboarding:
    """Tests for OnboardingService.initialize_onboarding."""

    def test_sets_membership_status_to_registered(self):
        """Sets membership_status to REGISTERED."""
        member = MemberFactory()
        OnboardingService.initialize_onboarding(member)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REGISTERED

    def test_sets_registration_date(self):
        """Sets registration_date to now."""
        member = MemberFactory()
        before = timezone.now()
        OnboardingService.initialize_onboarding(member)
        member.refresh_from_db()
        assert member.registration_date is not None
        assert member.registration_date >= before

    def test_sets_form_deadline(self):
        """Sets form_deadline to now + ONBOARDING_FORM_DEADLINE_DAYS."""
        member = MemberFactory()
        deadline_days = getattr(settings, 'ONBOARDING_FORM_DEADLINE_DAYS', 30)
        before = timezone.now()
        OnboardingService.initialize_onboarding(member)
        member.refresh_from_db()
        expected_min = before + timedelta(days=deadline_days)
        assert member.form_deadline is not None
        assert member.form_deadline >= expected_min - timedelta(seconds=5)

    def test_creates_qr_code(self):
        """Creates a MemberQRCode for the member."""
        member = MemberFactory()
        OnboardingService.initialize_onboarding(member)
        assert MemberQRCode.objects.filter(member=member).exists()

    def test_qr_code_not_duplicated_on_repeat_call(self):
        """Calling twice does not create a second QR code (get_or_create)."""
        member = MemberFactory()
        OnboardingService.initialize_onboarding(member)
        OnboardingService.initialize_onboarding(member)
        assert MemberQRCode.objects.filter(member=member).count() == 1

    def test_creates_welcome_notification(self):
        """Creates a welcome notification for the member."""
        member = MemberFactory()
        OnboardingService.initialize_onboarding(member)
        notif = Notification.objects.filter(member=member).first()
        assert notif is not None
        assert 'Bienvenue' in notif.title
        assert notif.notification_type == 'general'

    def test_notification_message_includes_deadline_days(self):
        """Notification message mentions the deadline in days."""
        member = MemberFactory()
        OnboardingService.initialize_onboarding(member)
        notif = Notification.objects.filter(member=member).first()
        deadline_days = getattr(settings, 'ONBOARDING_FORM_DEADLINE_DAYS', 30)
        assert str(deadline_days) in notif.message

    def test_returns_member(self):
        """Returns the updated member object."""
        member = MemberFactory()
        result = OnboardingService.initialize_onboarding(member)
        assert result == member
        assert result.membership_status == MembershipStatus.REGISTERED


# ---------------------------------------------------------------------------
# submit_form
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestSubmitForm:
    """Tests for OnboardingService.submit_form."""

    def test_sets_status_to_form_submitted(self):
        """Sets membership_status to FORM_SUBMITTED."""
        member = MemberFactory()
        OnboardingService.submit_form(member)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.FORM_SUBMITTED

    def test_sets_form_submitted_at(self):
        """Records when the form was submitted."""
        member = MemberFactory()
        before = timezone.now()
        OnboardingService.submit_form(member)
        member.refresh_from_db()
        assert member.form_submitted_at is not None
        assert member.form_submitted_at >= before

    def test_notifies_admin_members(self):
        """Creates notifications for all admin and pastor members."""
        admin = AdminMemberFactory()
        pastor = PastorFactory()
        regular = MemberFactory()
        member = MemberFactory(first_name='Paul', last_name='Martin')

        OnboardingService.submit_form(member)

        admin_notif = Notification.objects.filter(member=admin)
        pastor_notif = Notification.objects.filter(member=pastor)
        regular_notif = Notification.objects.filter(member=regular)

        assert admin_notif.exists()
        assert pastor_notif.exists()
        assert not regular_notif.exists()

    def test_admin_notification_content(self):
        """Admin notification mentions the member name and review."""
        admin = AdminMemberFactory()
        member = MemberFactory(first_name='Paul', last_name='Martin')
        OnboardingService.submit_form(member)

        notif = Notification.objects.filter(member=admin).first()
        assert 'Paul Martin' in notif.message
        assert 'formulaire' in notif.title.lower()

    def test_admin_notification_link(self):
        """Admin notification includes a link to review the member."""
        admin = AdminMemberFactory()
        member = MemberFactory()
        OnboardingService.submit_form(member)

        notif = Notification.objects.filter(member=admin).first()
        assert str(member.pk) in notif.link

    def test_no_admins_no_crash(self):
        """No crash when there are no admin/pastor members."""
        member = MemberFactory()
        OnboardingService.submit_form(member)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.FORM_SUBMITTED


# ---------------------------------------------------------------------------
# admin_approve
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestAdminApprove:
    """Tests for OnboardingService.admin_approve."""

    def _setup(self):
        """Common setup: member, admin, course with lessons."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1, title='Lesson 1')
        LessonFactory(course=course, order=2, title='Lesson 2')
        return member, admin, course

    def test_sets_status_to_in_training(self):
        """Sets membership_status to IN_TRAINING."""
        member, admin, course = self._setup()
        OnboardingService.admin_approve(member, admin, course)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.IN_TRAINING

    def test_sets_admin_reviewed_at(self):
        """Records when the admin reviewed."""
        member, admin, course = self._setup()
        before = timezone.now()
        OnboardingService.admin_approve(member, admin, course)
        member.refresh_from_db()
        assert member.admin_reviewed_at is not None
        assert member.admin_reviewed_at >= before

    def test_sets_admin_reviewed_by(self):
        """Records which admin performed the review."""
        member, admin, course = self._setup()
        OnboardingService.admin_approve(member, admin, course)
        member.refresh_from_db()
        assert member.admin_reviewed_by == admin

    def test_creates_member_training(self):
        """Creates a MemberTraining enrollment."""
        member, admin, course = self._setup()
        training = OnboardingService.admin_approve(member, admin, course)
        assert training is not None
        assert training.member == member
        assert training.course == course
        assert training.assigned_by == admin

    def test_creates_scheduled_lessons_for_active_lessons(self):
        """Creates ScheduledLesson for each active lesson in the course."""
        member, admin, course = self._setup()
        training = OnboardingService.admin_approve(member, admin, course)
        scheduled = ScheduledLesson.objects.filter(training=training)
        assert scheduled.count() == 2

    def test_scheduled_lessons_status_upcoming(self):
        """All created ScheduledLessons have UPCOMING status."""
        member, admin, course = self._setup()
        training = OnboardingService.admin_approve(member, admin, course)
        for sl in ScheduledLesson.objects.filter(training=training):
            assert sl.status == LessonStatus.UPCOMING

    def test_excludes_inactive_lessons(self):
        """Inactive lessons in the course are not scheduled."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        inactive = LessonFactory(course=course, order=2)
        inactive.deactivate()

        training = OnboardingService.admin_approve(member, admin, course)
        scheduled = ScheduledLesson.objects.filter(training=training)
        assert scheduled.count() == 1

    def test_notifies_member(self):
        """Creates a notification for the member about training."""
        member, admin, course = self._setup()
        OnboardingService.admin_approve(member, admin, course)
        notif = Notification.objects.filter(member=member).first()
        assert notif is not None
        assert 'parcours' in notif.title.lower() or 'formation' in notif.title.lower()
        assert course.name in notif.message

    def test_returns_training(self):
        """Returns the created MemberTraining."""
        member, admin, course = self._setup()
        training = OnboardingService.admin_approve(member, admin, course)
        assert isinstance(training, MemberTraining)

    def test_course_with_no_lessons(self):
        """Approve works with a course that has zero lessons."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        course = TrainingCourseFactory()
        training = OnboardingService.admin_approve(member, admin, course)
        assert training is not None
        assert ScheduledLesson.objects.filter(training=training).count() == 0


# ---------------------------------------------------------------------------
# admin_reject
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestAdminReject:
    """Tests for OnboardingService.admin_reject."""

    def test_sets_status_to_rejected(self):
        """Sets membership_status to REJECTED."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_reject(member, admin, 'Incomplete info')
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REJECTED

    def test_sets_admin_reviewed_at(self):
        """Records when the admin reviewed."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        before = timezone.now()
        OnboardingService.admin_reject(member, admin, 'Reason')
        member.refresh_from_db()
        assert member.admin_reviewed_at >= before

    def test_sets_admin_reviewed_by(self):
        """Records which admin performed the rejection."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_reject(member, admin, 'Reason')
        member.refresh_from_db()
        assert member.admin_reviewed_by == admin

    def test_saves_rejection_reason(self):
        """Stores the reason for rejection on the member."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        reason = 'Incomplete documentation provided.'
        OnboardingService.admin_reject(member, admin, reason)
        member.refresh_from_db()
        assert member.rejection_reason == reason

    def test_notifies_member(self):
        """Creates a rejection notification for the member."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        reason = 'Missing ID'
        OnboardingService.admin_reject(member, admin, reason)
        notif = Notification.objects.filter(member=member).first()
        assert notif is not None
        assert reason in notif.message

    def test_notification_mentions_refusal(self):
        """Notification title or message mentions refusal."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_reject(member, admin, 'Missing docs')
        notif = Notification.objects.filter(member=member).first()
        assert 'demande' in notif.title.lower() or 'refus' in notif.message.lower()


# ---------------------------------------------------------------------------
# admin_request_changes
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestAdminRequestChanges:
    """Tests for OnboardingService.admin_request_changes."""

    def test_sets_status_to_in_review(self):
        """Sets membership_status to IN_REVIEW."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_request_changes(member, admin, 'Please fix address')
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.IN_REVIEW

    def test_sets_admin_reviewed_by(self):
        """Records which admin requested changes."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_request_changes(member, admin, 'Fix things')
        member.refresh_from_db()
        assert member.admin_reviewed_by == admin

    def test_notifies_member_with_message(self):
        """Creates a notification with the admin's message."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        msg = 'Veuillez corriger votre adresse.'
        OnboardingService.admin_request_changes(member, admin, msg)
        notif = Notification.objects.filter(member=member).first()
        assert notif is not None
        assert notif.message == msg

    def test_notification_has_form_link(self):
        """Notification links to the onboarding form."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_request_changes(member, admin, 'Fix')
        notif = Notification.objects.filter(member=member).first()
        assert '/onboarding/form/' in notif.link

    def test_notification_title(self):
        """Notification title mentions required changes."""
        member = MemberFactory()
        admin = AdminMemberFactory()
        OnboardingService.admin_request_changes(member, admin, 'Fix')
        notif = Notification.objects.filter(member=member).first()
        assert 'requis' in notif.title.lower() or 'compl' in notif.title.lower()


# ---------------------------------------------------------------------------
# mark_lesson_attended
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestMarkLessonAttended:
    """Tests for OnboardingService.mark_lesson_attended."""

    def _setup_training_with_lessons(self, num_lessons=2):
        """Create a training with scheduled lessons."""
        member = MemberFactory()
        admin = PastorFactory()
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(
            member=member, course=course, assigned_by=admin
        )
        scheduled = []
        for i in range(1, num_lessons + 1):
            lesson = LessonFactory(course=course, order=i)
            sl = ScheduledLessonFactory(
                training=training,
                lesson=lesson,
                status=LessonStatus.UPCOMING,
            )
            scheduled.append(sl)
        return member, admin, training, scheduled

    def test_marks_lesson_completed(self):
        """Sets scheduled lesson status to COMPLETED."""
        member, admin, training, scheduled = self._setup_training_with_lessons(2)
        OnboardingService.mark_lesson_attended(scheduled[0], admin)
        scheduled[0].refresh_from_db()
        assert scheduled[0].status == LessonStatus.COMPLETED

    def test_sets_attended_at(self):
        """Records when the attendance was marked."""
        member, admin, training, scheduled = self._setup_training_with_lessons(1)
        before = timezone.now()
        OnboardingService.mark_lesson_attended(scheduled[0], admin)
        scheduled[0].refresh_from_db()
        assert scheduled[0].attended_at is not None
        assert scheduled[0].attended_at >= before

    def test_sets_marked_by(self):
        """Records who marked the attendance."""
        member, admin, training, scheduled = self._setup_training_with_lessons(1)
        OnboardingService.mark_lesson_attended(scheduled[0], admin)
        scheduled[0].refresh_from_db()
        assert scheduled[0].marked_by == admin

    def test_does_not_complete_training_when_partial(self):
        """Training not marked complete when some lessons remain."""
        member, admin, training, scheduled = self._setup_training_with_lessons(2)
        OnboardingService.mark_lesson_attended(scheduled[0], admin)
        training.refresh_from_db()
        assert training.is_completed is False
        assert training.completed_at is None

    def test_completes_training_at_100_percent(self):
        """Marks training as completed when all lessons are done."""
        member, admin, training, scheduled = self._setup_training_with_lessons(2)
        OnboardingService.mark_lesson_attended(scheduled[0], admin)
        OnboardingService.mark_lesson_attended(scheduled[1], admin)
        training.refresh_from_db()
        assert training.is_completed is True
        assert training.completed_at is not None

    def test_notifies_admins_on_training_completion(self):
        """Admins receive notification when training is 100% complete."""
        admin_member = AdminMemberFactory()
        member, marker, training, scheduled = self._setup_training_with_lessons(1)
        OnboardingService.mark_lesson_attended(scheduled[0], marker)

        # Notification title uses French accented characters: "Formation compl\u00e9t\u00e9e"
        all_admin_notifs = Notification.objects.filter(member=admin_member)
        completion_notifs = [
            n for n in all_admin_notifs if 'Formation' in n.title
        ]
        assert len(completion_notifs) >= 1

    def test_notifies_member_on_training_completion(self):
        """Member receives congratulations notification on completion."""
        member, admin, training, scheduled = self._setup_training_with_lessons(1)
        OnboardingService.mark_lesson_attended(scheduled[0], admin)

        member_notifs = Notification.objects.filter(member=member)
        completion_notifs = [
            n for n in member_notifs if 'Formation' in n.title
        ]
        assert len(completion_notifs) >= 1

    def test_completion_notification_mentions_interview(self):
        """Member completion notification mentions the upcoming interview."""
        member, admin, training, scheduled = self._setup_training_with_lessons(1)
        OnboardingService.mark_lesson_attended(scheduled[0], admin)

        member_notifs = Notification.objects.filter(member=member)
        completion_notifs = [
            n for n in member_notifs if 'Formation' in n.title
        ]
        assert any('interview' in n.message.lower() for n in completion_notifs)

    def test_no_completion_notifications_when_partial(self):
        """No completion notifications when training is not 100%."""
        member, admin, training, scheduled = self._setup_training_with_lessons(3)
        Notification.objects.all().delete()  # Clear pre-existing
        OnboardingService.mark_lesson_attended(scheduled[0], admin)

        member_notifs = Notification.objects.filter(member=member)
        completion_notifs = [
            n for n in member_notifs if 'Formation' in n.title
        ]
        assert len(completion_notifs) == 0

    def test_admin_notification_includes_review_link(self):
        """Admin notification links to the member's review page on completion."""
        admin_member = AdminMemberFactory()
        member, marker, training, scheduled = self._setup_training_with_lessons(1)
        OnboardingService.mark_lesson_attended(scheduled[0], marker)

        admin_notifs = Notification.objects.filter(member=admin_member)
        completion_notifs = [
            n for n in admin_notifs if 'Formation' in n.title
        ]
        if completion_notifs:
            assert str(member.pk) in completion_notifs[0].link


# ---------------------------------------------------------------------------
# schedule_interview
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestScheduleInterview:
    """Tests for OnboardingService.schedule_interview."""

    def _setup(self):
        """Common setup for interview scheduling."""
        member = MemberFactory()
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=member, course=course)
        interviewer = PastorFactory()
        proposed_date = timezone.now() + timedelta(days=14)
        return member, training, interviewer, proposed_date

    def test_sets_status_to_interview_scheduled(self):
        """Sets membership_status to INTERVIEW_SCHEDULED."""
        member, training, interviewer, proposed = self._setup()
        OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.INTERVIEW_SCHEDULED

    def test_creates_interview(self):
        """Creates an Interview record."""
        member, training, interviewer, proposed = self._setup()
        interview = OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        assert interview is not None
        assert interview.pk is not None
        assert interview.member == member
        assert interview.training == training
        assert interview.interviewer == interviewer
        assert interview.proposed_date == proposed

    def test_interview_status_proposed(self):
        """Interview is created with PROPOSED status."""
        member, training, interviewer, proposed = self._setup()
        interview = OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        assert interview.status == InterviewStatus.PROPOSED

    def test_with_location(self):
        """Location is stored on the interview."""
        member, training, interviewer, proposed = self._setup()
        interview = OnboardingService.schedule_interview(
            member, training, interviewer, proposed, location='Salle 202'
        )
        assert interview.location == 'Salle 202'

    def test_without_location(self):
        """Location defaults to empty string."""
        member, training, interviewer, proposed = self._setup()
        interview = OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        assert interview.location == ''

    def test_notifies_member(self):
        """Creates notification for the member about the interview."""
        member, training, interviewer, proposed = self._setup()
        OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        notif = Notification.objects.filter(member=member).first()
        assert notif is not None
        assert 'interview' in notif.title.lower()

    def test_notification_includes_date(self):
        """Notification message includes the proposed date."""
        member, training, interviewer, proposed = self._setup()
        OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        notif = Notification.objects.filter(member=member).first()
        assert proposed.strftime('%d/%m/%Y') in notif.message

    def test_notification_has_link(self):
        """Notification links to the interview page."""
        member, training, interviewer, proposed = self._setup()
        OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        notif = Notification.objects.filter(member=member).first()
        assert '/onboarding/interview/' in notif.link

    def test_returns_interview_object(self):
        """Returns the created Interview."""
        member, training, interviewer, proposed = self._setup()
        interview = OnboardingService.schedule_interview(
            member, training, interviewer, proposed
        )
        assert isinstance(interview, Interview)


# ---------------------------------------------------------------------------
# member_accept_interview
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestMemberAcceptInterview:
    """Tests for OnboardingService.member_accept_interview."""

    def test_sets_status_to_confirmed(self):
        """Sets interview status to CONFIRMED."""
        interview = InterviewFactory(status=InterviewStatus.PROPOSED)
        OnboardingService.member_accept_interview(interview)
        interview.refresh_from_db()
        assert interview.status == InterviewStatus.CONFIRMED

    def test_sets_confirmed_date_to_proposed_date(self):
        """confirmed_date is set to the proposed_date."""
        proposed = timezone.now() + timedelta(days=7)
        interview = InterviewFactory(
            proposed_date=proposed,
            status=InterviewStatus.PROPOSED,
        )
        OnboardingService.member_accept_interview(interview)
        interview.refresh_from_db()
        assert interview.confirmed_date == proposed

    def test_notifies_interviewer(self):
        """Creates notification for the interviewer."""
        interviewer = PastorFactory()
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        interview = InterviewFactory(
            member=member,
            interviewer=interviewer,
            status=InterviewStatus.PROPOSED,
        )
        OnboardingService.member_accept_interview(interview)
        notif = Notification.objects.filter(member=interviewer).first()
        assert notif is not None
        assert 'confirm' in notif.title.lower()
        assert 'Jean Dupont' in notif.message


# ---------------------------------------------------------------------------
# member_counter_propose
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestMemberCounterPropose:
    """Tests for OnboardingService.member_counter_propose."""

    def test_sets_status_to_counter(self):
        """Sets interview status to COUNTER."""
        interview = InterviewFactory(status=InterviewStatus.PROPOSED)
        new_date = timezone.now() + timedelta(days=21)
        OnboardingService.member_counter_propose(interview, new_date)
        interview.refresh_from_db()
        assert interview.status == InterviewStatus.COUNTER

    def test_sets_counter_proposed_date(self):
        """Stores the counter-proposed date."""
        interview = InterviewFactory(status=InterviewStatus.PROPOSED)
        new_date = timezone.now() + timedelta(days=21)
        OnboardingService.member_counter_propose(interview, new_date)
        interview.refresh_from_db()
        assert interview.counter_proposed_date == new_date

    def test_notifies_interviewer(self):
        """Creates notification for the interviewer about counter-proposal."""
        interviewer = PastorFactory()
        member = MemberFactory(first_name='Marie', last_name='Tremblay')
        interview = InterviewFactory(
            member=member,
            interviewer=interviewer,
            status=InterviewStatus.PROPOSED,
        )
        new_date = timezone.now() + timedelta(days=21)
        OnboardingService.member_counter_propose(interview, new_date)
        notif = Notification.objects.filter(member=interviewer).first()
        assert notif is not None
        assert 'contre' in notif.title.lower() or 'proposition' in notif.title.lower()
        assert 'Marie Tremblay' in notif.message

    def test_notification_includes_new_date(self):
        """Notification message includes the counter-proposed date."""
        interview = InterviewFactory(status=InterviewStatus.PROPOSED)
        new_date = timezone.now() + timedelta(days=21)
        OnboardingService.member_counter_propose(interview, new_date)
        notif = Notification.objects.filter(
            member=interview.interviewer
        ).first()
        assert new_date.strftime('%d/%m/%Y') in notif.message


# ---------------------------------------------------------------------------
# admin_confirm_counter
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestAdminConfirmCounter:
    """Tests for OnboardingService.admin_confirm_counter."""

    def test_sets_status_to_confirmed(self):
        """Sets interview status to CONFIRMED."""
        counter_date = timezone.now() + timedelta(days=21)
        interview = InterviewFactory(
            status=InterviewStatus.COUNTER,
            counter_proposed_date=counter_date,
        )
        OnboardingService.admin_confirm_counter(interview)
        interview.refresh_from_db()
        assert interview.status == InterviewStatus.CONFIRMED

    def test_sets_confirmed_date_to_counter_proposed_date(self):
        """confirmed_date is set to the counter_proposed_date."""
        counter_date = timezone.now() + timedelta(days=21)
        interview = InterviewFactory(
            status=InterviewStatus.COUNTER,
            counter_proposed_date=counter_date,
        )
        OnboardingService.admin_confirm_counter(interview)
        interview.refresh_from_db()
        assert interview.confirmed_date == counter_date

    def test_notifies_member(self):
        """Creates notification for the member about confirmed date."""
        member = MemberFactory(first_name='Luc', last_name='Bernard')
        counter_date = timezone.now() + timedelta(days=21)
        interview = InterviewFactory(
            member=member,
            status=InterviewStatus.COUNTER,
            counter_proposed_date=counter_date,
        )
        OnboardingService.admin_confirm_counter(interview)
        notif = Notification.objects.filter(member=member).last()
        assert notif is not None
        assert 'confirm' in notif.title.lower()

    def test_notification_mentions_definitive(self):
        """Notification message mentions the date is definitive."""
        member = MemberFactory()
        counter_date = timezone.now() + timedelta(days=21)
        interview = InterviewFactory(
            member=member,
            status=InterviewStatus.COUNTER,
            counter_proposed_date=counter_date,
        )
        OnboardingService.admin_confirm_counter(interview)
        notif = Notification.objects.filter(member=member).last()
        assert 'FINITIVE' in notif.message.upper() or 'definitive' in notif.message.lower()

    def test_notification_includes_confirmed_date(self):
        """Notification message includes the confirmed date."""
        member = MemberFactory()
        counter_date = timezone.now() + timedelta(days=21)
        interview = InterviewFactory(
            member=member,
            status=InterviewStatus.COUNTER,
            counter_proposed_date=counter_date,
        )
        OnboardingService.admin_confirm_counter(interview)
        notif = Notification.objects.filter(member=member).last()
        assert counter_date.strftime('%d/%m/%Y') in notif.message


# ---------------------------------------------------------------------------
# complete_interview
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCompleteInterview:
    """Tests for OnboardingService.complete_interview."""

    def test_passed_sets_status_completed_pass(self):
        """Passing sets interview status to COMPLETED_PASS."""
        interview = InterviewFactory()
        OnboardingService.complete_interview(interview, passed=True)
        interview.refresh_from_db()
        assert interview.status == InterviewStatus.COMPLETED_PASS

    def test_passed_sets_member_active(self):
        """Passing sets member status to ACTIVE."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(interview, passed=True)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.ACTIVE

    def test_passed_sets_became_active_at(self):
        """Passing records when member became active."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        before = timezone.now()
        OnboardingService.complete_interview(interview, passed=True)
        member.refresh_from_db()
        assert member.became_active_at is not None
        assert member.became_active_at >= before

    def test_passed_sets_joined_date(self):
        """Passing sets the member's joined_date to today."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(interview, passed=True)
        member.refresh_from_db()
        assert member.joined_date == timezone.now().date()

    def test_passed_sets_completed_at(self):
        """Passing records the interview completion time."""
        interview = InterviewFactory()
        before = timezone.now()
        OnboardingService.complete_interview(interview, passed=True)
        interview.refresh_from_db()
        assert interview.completed_at is not None
        assert interview.completed_at >= before

    def test_passed_stores_notes(self):
        """Passing stores the result notes."""
        interview = InterviewFactory()
        OnboardingService.complete_interview(
            interview, passed=True, notes='Excellent candidate'
        )
        interview.refresh_from_db()
        assert interview.result_notes == 'Excellent candidate'

    def test_passed_notifies_member(self):
        """Passing creates a welcome notification for the member."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(interview, passed=True)
        notif = Notification.objects.filter(member=member).last()
        assert notif is not None
        assert 'bienvenue' in notif.title.lower() or 'famille' in notif.title.lower()

    def test_passed_notification_has_link(self):
        """Passing notification links to reports/dashboard."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(interview, passed=True)
        notif = Notification.objects.filter(member=member).last()
        assert '/reports/' in notif.link

    def test_failed_sets_status_completed_fail(self):
        """Failing sets interview status to COMPLETED_FAIL."""
        interview = InterviewFactory()
        OnboardingService.complete_interview(interview, passed=False)
        interview.refresh_from_db()
        assert interview.status == InterviewStatus.COMPLETED_FAIL

    def test_failed_sets_member_rejected(self):
        """Failing sets member status to REJECTED."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(interview, passed=False)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REJECTED

    def test_failed_sets_rejection_reason(self):
        """Failing stores the notes as rejection reason."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(
            interview, passed=False, notes='Not ready yet'
        )
        member.refresh_from_db()
        assert member.rejection_reason == 'Not ready yet'

    def test_failed_sets_completed_at(self):
        """Failing records the interview completion time."""
        interview = InterviewFactory()
        before = timezone.now()
        OnboardingService.complete_interview(interview, passed=False)
        interview.refresh_from_db()
        assert interview.completed_at is not None
        assert interview.completed_at >= before

    def test_failed_notifies_member(self):
        """Failing creates a notification about the result."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        notes = 'Needs more preparation'
        OnboardingService.complete_interview(
            interview, passed=False, notes=notes
        )
        notif = Notification.objects.filter(member=member).last()
        assert notif is not None
        assert notes in notif.message

    def test_passed_without_notes(self):
        """Passing without notes stores empty string."""
        interview = InterviewFactory()
        OnboardingService.complete_interview(interview, passed=True)
        interview.refresh_from_db()
        assert interview.result_notes == ''

    def test_failed_without_notes(self):
        """Failing without notes stores empty string."""
        member = MemberFactory()
        interview = InterviewFactory(member=member)
        OnboardingService.complete_interview(interview, passed=False)
        interview.refresh_from_db()
        assert interview.result_notes == ''
        member.refresh_from_db()
        assert member.rejection_reason == ''


# ---------------------------------------------------------------------------
# mark_interview_no_show
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestMarkInterviewNoShow:
    """Tests for OnboardingService.mark_interview_no_show."""

    def test_sets_interview_status_no_show(self):
        """Sets interview status to NO_SHOW."""
        interview = InterviewFactory(status=InterviewStatus.CONFIRMED)
        OnboardingService.mark_interview_no_show(interview)
        interview.refresh_from_db()
        assert interview.status == InterviewStatus.NO_SHOW

    def test_sets_completed_at(self):
        """Records when the no-show was marked."""
        interview = InterviewFactory(status=InterviewStatus.CONFIRMED)
        before = timezone.now()
        OnboardingService.mark_interview_no_show(interview)
        interview.refresh_from_db()
        assert interview.completed_at is not None
        assert interview.completed_at >= before

    def test_sets_member_rejected(self):
        """Sets member status to REJECTED."""
        member = MemberFactory()
        interview = InterviewFactory(member=member, status=InterviewStatus.CONFIRMED)
        OnboardingService.mark_interview_no_show(interview)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REJECTED

    def test_sets_rejection_reason(self):
        """Sets a rejection reason about the no-show."""
        member = MemberFactory()
        interview = InterviewFactory(member=member, status=InterviewStatus.CONFIRMED)
        OnboardingService.mark_interview_no_show(interview)
        member.refresh_from_db()
        assert member.rejection_reason != ''
        assert 'absent' in member.rejection_reason.lower() or 'interview' in member.rejection_reason.lower()


# ---------------------------------------------------------------------------
# expire_overdue_members
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestExpireOverdueMembers:
    """Tests for OnboardingService.expire_overdue_members."""

    def test_expires_registered_past_deadline(self):
        """Expires members with REGISTERED status past deadline."""
        member = MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.EXPIRED
        assert count >= 1

    def test_expires_form_pending_past_deadline(self):
        """Expires members with FORM_PENDING status past deadline."""
        member = MemberFactory(
            membership_status=MembershipStatus.FORM_PENDING,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.EXPIRED
        assert count >= 1

    def test_deactivates_expired_members(self):
        """Expired members have is_active set to False."""
        member = MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        OnboardingService.expire_overdue_members()
        # Use all_objects since is_active=False hides from default manager
        from apps.members.models import Member
        member = Member.all_objects.get(pk=member.pk)
        assert member.is_active is False

    def test_does_not_expire_before_deadline(self):
        """Members with future deadline are not expired."""
        member = MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() + timedelta(days=10),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REGISTERED
        assert count == 0

    def test_does_not_expire_form_submitted(self):
        """Members who submitted their form are not expired."""
        member = MemberFactory(
            membership_status=MembershipStatus.FORM_SUBMITTED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.FORM_SUBMITTED

    def test_does_not_expire_in_training(self):
        """Members in training are not expired."""
        member = MemberFactory(
            membership_status=MembershipStatus.IN_TRAINING,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.IN_TRAINING

    def test_does_not_expire_active_members(self):
        """Active members are not expired."""
        member = MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.ACTIVE

    def test_returns_count_of_expired(self):
        """Returns the number of members expired."""
        MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() - timedelta(days=5),
        )
        MemberFactory(
            membership_status=MembershipStatus.FORM_PENDING,
            form_deadline=timezone.now() - timedelta(days=2),
        )
        count = OnboardingService.expire_overdue_members()
        assert count == 3

    def test_returns_zero_when_none_expired(self):
        """Returns 0 when no members qualify for expiration."""
        MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() + timedelta(days=10),
        )
        count = OnboardingService.expire_overdue_members()
        assert count == 0

    def test_multiple_statuses_mixed(self):
        """Only REGISTERED and FORM_PENDING past deadline are expired."""
        expired_registered = MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        expired_pending = MemberFactory(
            membership_status=MembershipStatus.FORM_PENDING,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        safe_submitted = MemberFactory(
            membership_status=MembershipStatus.FORM_SUBMITTED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        safe_future = MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() + timedelta(days=10),
        )
        count = OnboardingService.expire_overdue_members()
        assert count == 2

        from apps.members.models import Member
        expired_registered = Member.all_objects.get(pk=expired_registered.pk)
        expired_pending = Member.all_objects.get(pk=expired_pending.pk)
        assert expired_registered.membership_status == MembershipStatus.EXPIRED
        assert expired_pending.membership_status == MembershipStatus.EXPIRED
        safe_submitted.refresh_from_db()
        safe_future.refresh_from_db()
        assert safe_submitted.membership_status == MembershipStatus.FORM_SUBMITTED
        assert safe_future.membership_status == MembershipStatus.REGISTERED

    def test_does_not_expire_rejected(self):
        """Already-rejected members are not affected."""
        member = MemberFactory(
            membership_status=MembershipStatus.REJECTED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REJECTED

    def test_does_not_expire_already_expired(self):
        """Already-expired members are not double-counted."""
        # Note: expired members have is_active=False, so they won't show in
        # the default manager anyway, but this verifies correctness.
        member = MemberFactory(
            membership_status=MembershipStatus.EXPIRED,
            form_deadline=timezone.now() - timedelta(days=1),
        )
        count = OnboardingService.expire_overdue_members()
        assert count == 0


# ---------------------------------------------------------------------------
# Signal integration test
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestOnboardingSignal:
    """Tests for the post_save signal that auto-initializes onboarding."""

    def test_signal_initializes_onboarding_for_new_member_with_user(self):
        """Signal triggers initialize_onboarding when member has user and no registration_date."""
        from apps.members.tests.factories import MemberWithUserFactory
        member = MemberWithUserFactory(registration_date=None)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REGISTERED
        assert member.registration_date is not None
        assert MemberQRCode.objects.filter(member=member).exists()

    def test_signal_does_not_trigger_without_user(self):
        """Signal does not trigger when member has no user."""
        member = MemberFactory(registration_date=None)
        member.refresh_from_db()
        # MemberFactory sets default status; signal should not have changed it
        assert not MemberQRCode.objects.filter(member=member).exists()

    def test_signal_does_not_trigger_with_existing_registration_date(self):
        """Signal does not trigger when registration_date is already set."""
        from apps.members.tests.factories import MemberWithUserFactory
        existing_date = timezone.now() - timedelta(days=10)
        member = MemberWithUserFactory(registration_date=existing_date)
        member.refresh_from_db()
        # registration_date should remain the original value
        # The signal condition checks `not instance.registration_date`,
        # so an existing date prevents initialization
        assert member.registration_date == existing_date
