"""Tests for OnboardingStats analytics service."""
import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.core.constants import (
    MembershipStatus,
    InterviewStatus,
    AttendanceSessionType,
)
from apps.members.tests.factories import MemberFactory
from apps.onboarding.tests.factories import (
    MemberTrainingFactory,
    InterviewFactory,
    TrainingCourseFactory,
)
from apps.attendance.tests.factories import (
    AttendanceSessionFactory,
    AttendanceRecordFactory,
    AbsenceAlertFactory,
)
from apps.onboarding.stats import OnboardingStats


@pytest.mark.django_db
class TestPipelineCounts:
    """Tests for OnboardingStats.pipeline_counts."""

    def test_empty_database(self):
        counts = OnboardingStats.pipeline_counts()
        assert counts['registered'] == 0
        assert counts['active'] == 0
        assert counts['total_in_process'] == 0

    def test_counts_registered_members(self):
        MemberFactory(membership_status=MembershipStatus.REGISTERED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.REGISTERED, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['registered'] == 2

    def test_counts_form_pending(self):
        MemberFactory(membership_status=MembershipStatus.FORM_PENDING, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['form_pending'] == 1

    def test_counts_form_submitted(self):
        MemberFactory(membership_status=MembershipStatus.FORM_SUBMITTED, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['form_submitted'] == 1

    def test_counts_in_review(self):
        MemberFactory(membership_status=MembershipStatus.IN_REVIEW, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['in_review'] == 1

    def test_counts_in_training(self):
        MemberFactory(membership_status=MembershipStatus.IN_TRAINING, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['in_training'] == 1

    def test_counts_interview_scheduled(self):
        MemberFactory(
            membership_status=MembershipStatus.INTERVIEW_SCHEDULED,
            registration_date=None,
        )
        counts = OnboardingStats.pipeline_counts()
        assert counts['interview_scheduled'] == 1

    def test_counts_active(self):
        MemberFactory(membership_status=MembershipStatus.ACTIVE)
        MemberFactory(membership_status=MembershipStatus.ACTIVE)
        MemberFactory(membership_status=MembershipStatus.ACTIVE)
        counts = OnboardingStats.pipeline_counts()
        assert counts['active'] == 3

    def test_counts_rejected(self):
        MemberFactory(membership_status=MembershipStatus.REJECTED, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['rejected'] == 1

    def test_counts_expired(self):
        MemberFactory(membership_status=MembershipStatus.EXPIRED, registration_date=None)
        counts = OnboardingStats.pipeline_counts()
        assert counts['expired'] == 1

    def test_total_in_process(self):
        MemberFactory(membership_status=MembershipStatus.REGISTERED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.FORM_PENDING, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.IN_TRAINING, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.ACTIVE)  # Not in process
        counts = OnboardingStats.pipeline_counts()
        assert counts['total_in_process'] == 3

    def test_all_statuses_counted(self):
        MemberFactory(membership_status=MembershipStatus.REGISTERED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.FORM_PENDING, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.FORM_SUBMITTED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.IN_REVIEW, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.IN_TRAINING, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.INTERVIEW_SCHEDULED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.ACTIVE)
        MemberFactory(membership_status=MembershipStatus.REJECTED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.EXPIRED, registration_date=None)

        counts = OnboardingStats.pipeline_counts()
        assert counts['registered'] == 1
        assert counts['form_pending'] == 1
        assert counts['form_submitted'] == 1
        assert counts['in_review'] == 1
        assert counts['in_training'] == 1
        assert counts['interview_scheduled'] == 1
        assert counts['active'] == 1
        assert counts['rejected'] == 1
        assert counts['expired'] == 1
        assert counts['total_in_process'] == 6


@pytest.mark.django_db
class TestSuccessRate:
    """Tests for OnboardingStats.success_rate."""

    def test_no_data_returns_zero(self):
        assert OnboardingStats.success_rate() == 0

    def test_all_active(self):
        now = timezone.now()
        for _ in range(3):
            MemberFactory(
                membership_status=MembershipStatus.ACTIVE,
                became_active_at=now,
            )
        rate = OnboardingStats.success_rate()
        assert rate == 100.0

    def test_mixed_results(self):
        now = timezone.now()
        # 3 active, 1 rejected, 1 expired => 3/5 = 60%
        for _ in range(3):
            MemberFactory(
                membership_status=MembershipStatus.ACTIVE,
                became_active_at=now,
            )
        MemberFactory(membership_status=MembershipStatus.REJECTED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.EXPIRED, registration_date=None)

        rate = OnboardingStats.success_rate()
        assert rate == 60.0

    def test_all_rejected(self):
        MemberFactory(membership_status=MembershipStatus.REJECTED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.REJECTED, registration_date=None)
        rate = OnboardingStats.success_rate()
        assert rate == 0

    def test_only_in_process_not_counted(self):
        MemberFactory(membership_status=MembershipStatus.REGISTERED, registration_date=None)
        MemberFactory(membership_status=MembershipStatus.IN_TRAINING, registration_date=None)
        rate = OnboardingStats.success_rate()
        assert rate == 0

    def test_active_without_became_active_at_not_counted(self):
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at=None,
        )
        MemberFactory(
            membership_status=MembershipStatus.REJECTED,
            registration_date=None,
        )
        rate = OnboardingStats.success_rate()
        assert rate == 0  # 0 active (no became_active_at) / 1 rejected


@pytest.mark.django_db
class TestAvgCompletionDays:
    """Tests for OnboardingStats.avg_completion_days."""

    def test_no_data_returns_zero(self):
        assert OnboardingStats.avg_completion_days() == 0

    def test_calculates_average(self):
        now = timezone.now()
        # Member 1: 10 days
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            registration_date=now - timedelta(days=10),
            became_active_at=now,
        )
        # Member 2: 20 days
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            registration_date=now - timedelta(days=20),
            became_active_at=now,
        )
        avg = OnboardingStats.avg_completion_days()
        assert avg == 15.0

    def test_single_member(self):
        now = timezone.now()
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            registration_date=now - timedelta(days=30),
            became_active_at=now,
        )
        avg = OnboardingStats.avg_completion_days()
        assert avg == 30.0

    def test_excludes_members_without_registration_date(self):
        now = timezone.now()
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            registration_date=None,
            became_active_at=now,
        )
        avg = OnboardingStats.avg_completion_days()
        assert avg == 0

    def test_excludes_members_without_became_active_at(self):
        now = timezone.now()
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            registration_date=now - timedelta(days=10),
            became_active_at=None,
        )
        avg = OnboardingStats.avg_completion_days()
        assert avg == 0

    def test_excludes_non_active_members(self):
        now = timezone.now()
        MemberFactory(
            membership_status=MembershipStatus.REJECTED,
            registration_date=now - timedelta(days=10),
            became_active_at=now,
        )
        avg = OnboardingStats.avg_completion_days()
        assert avg == 0


@pytest.mark.django_db
class TestTrainingStats:
    """Tests for OnboardingStats.training_stats."""

    def test_no_data(self):
        stats = OnboardingStats.training_stats()
        assert stats['total'] == 0
        assert stats['completed'] == 0
        assert stats['in_progress'] == 0
        assert stats['completion_rate'] == 0

    def test_with_trainings(self):
        # 2 completed, 1 in progress
        MemberTrainingFactory(is_completed=True)
        MemberTrainingFactory(is_completed=True)
        MemberTrainingFactory(is_completed=False)

        stats = OnboardingStats.training_stats()
        assert stats['total'] == 3
        assert stats['completed'] == 2
        assert stats['in_progress'] == 1
        assert stats['completion_rate'] == round((2 / 3) * 100, 1)

    def test_all_completed(self):
        MemberTrainingFactory(is_completed=True)
        MemberTrainingFactory(is_completed=True)

        stats = OnboardingStats.training_stats()
        assert stats['total'] == 2
        assert stats['completed'] == 2
        assert stats['in_progress'] == 0
        assert stats['completion_rate'] == 100.0

    def test_inactive_not_in_progress(self):
        # Inactive and not completed should not count as in_progress.
        # BaseModel.objects (ActiveManager) filters is_active=False,
        # so total also drops to 0 since the default manager excludes it.
        training = MemberTrainingFactory(is_completed=False)
        training.is_active = False
        training.save()

        stats = OnboardingStats.training_stats()
        assert stats['total'] == 0
        assert stats['in_progress'] == 0


@pytest.mark.django_db
class TestInterviewStats:
    """Tests for OnboardingStats.interview_stats."""

    def test_no_data(self):
        stats = OnboardingStats.interview_stats()
        assert stats['total'] == 0
        assert stats['passed'] == 0
        assert stats['failed'] == 0
        assert stats['no_show'] == 0
        assert stats['pending'] == 0
        assert stats['pass_rate'] == 0

    def test_with_interviews(self):
        InterviewFactory(status=InterviewStatus.COMPLETED_PASS)
        InterviewFactory(status=InterviewStatus.COMPLETED_PASS)
        InterviewFactory(status=InterviewStatus.COMPLETED_FAIL)
        InterviewFactory(status=InterviewStatus.NO_SHOW)
        InterviewFactory(status=InterviewStatus.PROPOSED)

        stats = OnboardingStats.interview_stats()
        assert stats['total'] == 5
        assert stats['passed'] == 2
        assert stats['failed'] == 1
        assert stats['no_show'] == 1
        assert stats['pending'] == 1
        # pass_rate: 2 / (2 + 1 + 1) = 50.0
        assert stats['pass_rate'] == 50.0

    def test_all_passed(self):
        InterviewFactory(status=InterviewStatus.COMPLETED_PASS)
        InterviewFactory(status=InterviewStatus.COMPLETED_PASS)

        stats = OnboardingStats.interview_stats()
        assert stats['pass_rate'] == 100.0

    def test_all_pending_statuses_counted(self):
        InterviewFactory(status=InterviewStatus.PROPOSED)
        InterviewFactory(status=InterviewStatus.ACCEPTED)
        InterviewFactory(status=InterviewStatus.COUNTER)
        InterviewFactory(status=InterviewStatus.CONFIRMED)

        stats = OnboardingStats.interview_stats()
        assert stats['pending'] == 4

    def test_cancelled_not_in_pending(self):
        InterviewFactory(status=InterviewStatus.CANCELLED)

        stats = OnboardingStats.interview_stats()
        assert stats['pending'] == 0
        assert stats['total'] == 1

    def test_pass_rate_with_no_completions(self):
        InterviewFactory(status=InterviewStatus.PROPOSED)
        InterviewFactory(status=InterviewStatus.ACCEPTED)

        stats = OnboardingStats.interview_stats()
        assert stats['pass_rate'] == 0


@pytest.mark.django_db
class TestAttendanceStats:
    """Tests for OnboardingStats.attendance_stats."""

    def test_no_data(self):
        stats = OnboardingStats.attendance_stats()
        assert stats['total_sessions'] == 0
        assert stats['total_checkins'] == 0
        assert stats['avg_attendance'] == 0
        assert stats['active_alerts'] == 0

    def test_sessions_in_last_30_days(self):
        # Session within 30 days
        recent = AttendanceSessionFactory(date=timezone.now().date() - timedelta(days=5))
        # Session older than 30 days
        old = AttendanceSessionFactory(date=timezone.now().date() - timedelta(days=45))

        stats = OnboardingStats.attendance_stats()
        assert stats['total_sessions'] == 1

    def test_checkins_counted(self):
        session = AttendanceSessionFactory(date=timezone.now().date() - timedelta(days=2))
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)

        stats = OnboardingStats.attendance_stats()
        assert stats['total_checkins'] == 3

    def test_avg_attendance_calculated(self):
        # 2 sessions, 6 total checkins => avg 3.0
        s1 = AttendanceSessionFactory(date=timezone.now().date() - timedelta(days=2))
        s2 = AttendanceSessionFactory(date=timezone.now().date() - timedelta(days=1))

        AttendanceRecordFactory(session=s1)
        AttendanceRecordFactory(session=s1)
        AttendanceRecordFactory(session=s2)
        AttendanceRecordFactory(session=s2)
        AttendanceRecordFactory(session=s2)
        AttendanceRecordFactory(session=s2)

        stats = OnboardingStats.attendance_stats()
        assert stats['avg_attendance'] == 3.0

    def test_active_alerts_counted(self):
        AbsenceAlertFactory(alert_sent=False)
        AbsenceAlertFactory(alert_sent=False)
        AbsenceAlertFactory(alert_sent=True)  # Already sent, not active

        stats = OnboardingStats.attendance_stats()
        assert stats['active_alerts'] == 2

    def test_inactive_alerts_not_counted(self):
        alert = AbsenceAlertFactory(alert_sent=False)
        alert.is_active = False
        alert.save()

        stats = OnboardingStats.attendance_stats()
        assert stats['active_alerts'] == 0

    def test_old_checkins_not_counted(self):
        old_session = AttendanceSessionFactory(
            date=timezone.now().date() - timedelta(days=45)
        )
        AttendanceRecordFactory(session=old_session)

        stats = OnboardingStats.attendance_stats()
        assert stats['total_checkins'] == 0


@pytest.mark.django_db
class TestRecentActivity:
    """Tests for OnboardingStats.recent_activity."""

    def test_no_data(self):
        activity = OnboardingStats.recent_activity()
        assert list(activity['recent_registrations']) == []
        assert list(activity['recent_completions']) == []

    def test_returns_recent_registrations(self):
        now = timezone.now()
        m1 = MemberFactory(
            membership_status=MembershipStatus.REGISTERED,
            registration_date=now - timedelta(days=1),
        )
        m2 = MemberFactory(
            membership_status=MembershipStatus.FORM_PENDING,
            registration_date=now - timedelta(days=5),
        )

        activity = OnboardingStats.recent_activity()
        pks = [m.pk for m in activity['recent_registrations']]
        assert m1.pk in pks
        assert m2.pk in pks

    def test_returns_recent_completions(self):
        now = timezone.now()
        m1 = MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at=now - timedelta(days=1),
        )
        m2 = MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at=now - timedelta(days=3),
        )

        activity = OnboardingStats.recent_activity()
        pks = [m.pk for m in activity['recent_completions']]
        assert m1.pk in pks
        assert m2.pk in pks

    def test_registrations_ordered_newest_first(self):
        now = timezone.now()
        m_old = MemberFactory(
            registration_date=now - timedelta(days=10),
        )
        m_new = MemberFactory(
            registration_date=now - timedelta(days=1),
        )

        activity = OnboardingStats.recent_activity()
        pks = [m.pk for m in activity['recent_registrations']]
        assert pks[0] == m_new.pk

    def test_completions_ordered_newest_first(self):
        now = timezone.now()
        m_old = MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at=now - timedelta(days=10),
        )
        m_new = MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at=now - timedelta(days=1),
        )

        activity = OnboardingStats.recent_activity()
        pks = [m.pk for m in activity['recent_completions']]
        assert pks[0] == m_new.pk

    def test_respects_limit(self):
        now = timezone.now()
        for i in range(15):
            MemberFactory(registration_date=now - timedelta(days=i))

        activity = OnboardingStats.recent_activity(limit=5)
        assert len(activity['recent_registrations']) == 5

    def test_default_limit_is_10(self):
        now = timezone.now()
        for i in range(15):
            MemberFactory(registration_date=now - timedelta(days=i))

        activity = OnboardingStats.recent_activity()
        assert len(activity['recent_registrations']) == 10

    def test_members_without_registration_date_excluded(self):
        MemberFactory(registration_date=None)

        activity = OnboardingStats.recent_activity()
        assert len(activity['recent_registrations']) == 0

    def test_members_without_became_active_at_excluded(self):
        MemberFactory(
            membership_status=MembershipStatus.ACTIVE,
            became_active_at=None,
        )

        activity = OnboardingStats.recent_activity()
        assert len(activity['recent_completions']) == 0


@pytest.mark.django_db
class TestMonthlyRegistrations:
    """Tests for OnboardingStats.monthly_registrations."""

    def test_returns_correct_number_of_months(self):
        result = OnboardingStats.monthly_registrations(months=6)
        assert len(result) == 6

    def test_returns_3_months(self):
        result = OnboardingStats.monthly_registrations(months=3)
        assert len(result) == 3

    def test_each_entry_has_month_and_count(self):
        result = OnboardingStats.monthly_registrations(months=1)
        assert len(result) == 1
        assert 'month' in result[0]
        assert 'count' in result[0]

    def test_counts_registrations_in_current_month(self):
        now = timezone.now()
        MemberFactory(registration_date=now - timedelta(days=1))
        MemberFactory(registration_date=now - timedelta(days=2))

        result = OnboardingStats.monthly_registrations(months=1)
        # The last entry is the current month
        assert result[-1]['count'] >= 2

    def test_no_registrations_returns_zero_counts(self):
        result = OnboardingStats.monthly_registrations(months=3)
        for entry in result:
            assert entry['count'] == 0

    def test_month_format_contains_year(self):
        result = OnboardingStats.monthly_registrations(months=1)
        # Month format should be like 'February 2026'
        assert any(char.isdigit() for char in result[0]['month'])

    def test_default_6_months(self):
        result = OnboardingStats.monthly_registrations()
        assert len(result) == 6
