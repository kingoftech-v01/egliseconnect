"""Tests for onboarding models."""
import pytest
from django.utils import timezone

from apps.core.constants import LessonStatus, InterviewStatus
from apps.members.tests.factories import MemberFactory
from apps.onboarding.models import (
    TrainingCourse,
    Lesson,
    MemberTraining,
    ScheduledLesson,
    Interview,
)

from .factories import (
    TrainingCourseFactory,
    LessonFactory,
    MemberTrainingFactory,
    ScheduledLessonFactory,
    InterviewFactory,
)


@pytest.mark.django_db
class TestTrainingCourseModel:
    """Tests for TrainingCourse model."""

    def test_create_course(self):
        """TrainingCourse creation works."""
        course = TrainingCourseFactory()
        assert course.id is not None
        assert course.name is not None

    def test_str(self):
        """String representation returns the course name."""
        course = TrainingCourseFactory(name='Parcours Decouverte 2025')
        assert str(course) == 'Parcours Decouverte 2025'

    def test_lesson_count_no_lessons(self):
        """lesson_count returns 0 when no lessons exist."""
        course = TrainingCourseFactory()
        assert course.lesson_count == 0

    def test_lesson_count_with_active_lessons(self):
        """lesson_count counts only active lessons."""
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        LessonFactory(course=course, order=2)
        LessonFactory(course=course, order=3)
        assert course.lesson_count == 3

    def test_lesson_count_excludes_inactive_lessons(self):
        """lesson_count excludes deactivated lessons."""
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        inactive = LessonFactory(course=course, order=2)
        inactive.deactivate()
        assert course.lesson_count == 1

    def test_default_values(self):
        """Default field values are set correctly."""
        course = TrainingCourseFactory()
        assert course.total_lessons == 5
        assert course.is_default is False

    def test_is_default_flag(self):
        """is_default can be set to True."""
        course = TrainingCourseFactory(is_default=True)
        assert course.is_default is True

    def test_created_by_relationship(self):
        """created_by links to a Member."""
        member = MemberFactory()
        course = TrainingCourseFactory(created_by=member)
        assert course.created_by == member
        assert course in member.created_courses.all()


@pytest.mark.django_db
class TestLessonModel:
    """Tests for Lesson model."""

    def test_create_lesson(self):
        """Lesson creation works."""
        lesson = LessonFactory()
        assert lesson.id is not None
        assert lesson.title is not None

    def test_str(self):
        """String representation shows order and title."""
        lesson = LessonFactory(order=3, title='Les fondements de la foi')
        assert str(lesson) == 'Le\u00e7on 3: Les fondements de la foi'

    def test_unique_together_course_order(self):
        """Cannot create two lessons with same course and order."""
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        with pytest.raises(Exception):
            LessonFactory(course=course, order=1)

    def test_different_courses_same_order(self):
        """Different courses can have lessons with the same order number."""
        course1 = TrainingCourseFactory()
        course2 = TrainingCourseFactory()
        lesson1 = LessonFactory(course=course1, order=1)
        lesson2 = LessonFactory(course=course2, order=1)
        assert lesson1.id != lesson2.id

    def test_default_duration(self):
        """Default duration is 90 minutes."""
        lesson = LessonFactory()
        assert lesson.duration_minutes == 90

    def test_course_relationship(self):
        """Lesson is accessible via course.lessons."""
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        assert lesson in course.lessons.all()


@pytest.mark.django_db
class TestMemberTrainingModel:
    """Tests for MemberTraining model."""

    def test_create_training(self):
        """MemberTraining creation works."""
        training = MemberTrainingFactory()
        assert training.id is not None

    def test_str(self):
        """String representation shows member name and course name."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        course = TrainingCourseFactory(name='Parcours Alpha')
        training = MemberTrainingFactory(member=member, course=course)
        assert str(training) == 'Jean Dupont - Parcours Alpha'

    def test_progress_percentage_no_lessons(self):
        """progress_percentage returns 0 when no scheduled lessons."""
        training = MemberTrainingFactory()
        assert training.progress_percentage == 0

    def test_progress_percentage_none_completed(self):
        """progress_percentage returns 0 when no lessons completed."""
        training = MemberTrainingFactory()
        course = training.course
        lesson = LessonFactory(course=course, order=1)
        ScheduledLessonFactory(
            training=training,
            lesson=lesson,
            status=LessonStatus.UPCOMING,
        )
        assert training.progress_percentage == 0

    def test_progress_percentage_half_completed(self):
        """progress_percentage returns 50 when half of lessons completed."""
        training = MemberTrainingFactory()
        course = training.course
        lesson1 = LessonFactory(course=course, order=1)
        lesson2 = LessonFactory(course=course, order=2)
        ScheduledLessonFactory(
            training=training,
            lesson=lesson1,
            status=LessonStatus.COMPLETED,
        )
        ScheduledLessonFactory(
            training=training,
            lesson=lesson2,
            status=LessonStatus.UPCOMING,
        )
        assert training.progress_percentage == 50

    def test_progress_percentage_all_completed(self):
        """progress_percentage returns 100 when all lessons completed."""
        training = MemberTrainingFactory()
        course = training.course
        lesson1 = LessonFactory(course=course, order=1)
        lesson2 = LessonFactory(course=course, order=2)
        ScheduledLessonFactory(
            training=training,
            lesson=lesson1,
            status=LessonStatus.COMPLETED,
        )
        ScheduledLessonFactory(
            training=training,
            lesson=lesson2,
            status=LessonStatus.COMPLETED,
        )
        assert training.progress_percentage == 100

    def test_completed_count(self):
        """completed_count returns count of completed lessons."""
        training = MemberTrainingFactory()
        course = training.course
        lesson1 = LessonFactory(course=course, order=1)
        lesson2 = LessonFactory(course=course, order=2)
        lesson3 = LessonFactory(course=course, order=3)
        ScheduledLessonFactory(
            training=training,
            lesson=lesson1,
            status=LessonStatus.COMPLETED,
        )
        ScheduledLessonFactory(
            training=training,
            lesson=lesson2,
            status=LessonStatus.COMPLETED,
        )
        ScheduledLessonFactory(
            training=training,
            lesson=lesson3,
            status=LessonStatus.UPCOMING,
        )
        assert training.completed_count == 2

    def test_total_count(self):
        """total_count returns total scheduled lessons."""
        training = MemberTrainingFactory()
        course = training.course
        lesson1 = LessonFactory(course=course, order=1)
        lesson2 = LessonFactory(course=course, order=2)
        ScheduledLessonFactory(training=training, lesson=lesson1)
        ScheduledLessonFactory(training=training, lesson=lesson2)
        assert training.total_count == 2

    def test_absent_count(self):
        """absent_count returns count of absent lessons."""
        training = MemberTrainingFactory()
        course = training.course
        lesson1 = LessonFactory(course=course, order=1)
        lesson2 = LessonFactory(course=course, order=2)
        lesson3 = LessonFactory(course=course, order=3)
        ScheduledLessonFactory(
            training=training,
            lesson=lesson1,
            status=LessonStatus.COMPLETED,
        )
        ScheduledLessonFactory(
            training=training,
            lesson=lesson2,
            status=LessonStatus.ABSENT,
        )
        ScheduledLessonFactory(
            training=training,
            lesson=lesson3,
            status=LessonStatus.ABSENT,
        )
        assert training.absent_count == 2

    def test_unique_together_member_course(self):
        """Cannot enroll same member in same course twice."""
        training = MemberTrainingFactory()
        with pytest.raises(Exception):
            MemberTrainingFactory(
                member=training.member,
                course=training.course,
            )

    def test_is_completed_default_false(self):
        """is_completed defaults to False."""
        training = MemberTrainingFactory()
        assert training.is_completed is False

    def test_completed_at_default_none(self):
        """completed_at defaults to None."""
        training = MemberTrainingFactory()
        assert training.completed_at is None


@pytest.mark.django_db
class TestScheduledLessonModel:
    """Tests for ScheduledLesson model."""

    def test_create_scheduled_lesson(self):
        """ScheduledLesson creation works."""
        sl = ScheduledLessonFactory()
        assert sl.id is not None

    def test_str(self):
        """String representation shows lesson title and date."""
        now = timezone.now()
        training = MemberTrainingFactory()
        lesson = LessonFactory(course=training.course, title='Introduction', order=1)
        sl = ScheduledLessonFactory(
            training=training,
            lesson=lesson,
            scheduled_date=now,
        )
        expected = f'Introduction - {now:%Y-%m-%d %H:%M}'
        assert str(sl) == expected

    def test_default_status(self):
        """Default status is UPCOMING."""
        sl = ScheduledLessonFactory()
        assert sl.status == LessonStatus.UPCOMING

    def test_reminder_flags_default_false(self):
        """All reminder flags default to False."""
        sl = ScheduledLessonFactory()
        assert sl.reminder_3days_sent is False
        assert sl.reminder_1day_sent is False
        assert sl.reminder_sameday_sent is False


@pytest.mark.django_db
class TestInterviewModel:
    """Tests for Interview model."""

    def test_create_interview(self):
        """Interview creation works."""
        interview = InterviewFactory()
        assert interview.id is not None

    def test_str(self):
        """String representation shows member name and status display."""
        member = MemberFactory(first_name='Marie', last_name='Tremblay')
        interview = InterviewFactory(
            member=member,
            status=InterviewStatus.PROPOSED,
        )
        result = str(interview)
        assert 'Marie Tremblay' in result
        assert 'Date propos' in result

    def test_final_date_returns_confirmed_date_when_set(self):
        """final_date returns confirmed_date when it is set."""
        proposed = timezone.now() + timezone.timedelta(days=7)
        confirmed = timezone.now() + timezone.timedelta(days=10)
        interview = InterviewFactory(
            proposed_date=proposed,
            confirmed_date=confirmed,
        )
        assert interview.final_date == confirmed

    def test_final_date_returns_proposed_date_when_no_confirmed(self):
        """final_date returns proposed_date when confirmed_date is None."""
        proposed = timezone.now() + timezone.timedelta(days=7)
        interview = InterviewFactory(
            proposed_date=proposed,
            confirmed_date=None,
        )
        assert interview.final_date == proposed

    def test_default_status(self):
        """Default status is PROPOSED."""
        interview = InterviewFactory()
        assert interview.status == InterviewStatus.PROPOSED

    def test_reminder_flags_default_false(self):
        """All reminder flags default to False."""
        interview = InterviewFactory()
        assert interview.reminder_3days_sent is False
        assert interview.reminder_1day_sent is False
        assert interview.reminder_sameday_sent is False

    def test_counter_proposed_date_default_none(self):
        """counter_proposed_date defaults to None."""
        interview = InterviewFactory()
        assert interview.counter_proposed_date is None

    def test_completed_at_default_none(self):
        """completed_at defaults to None."""
        interview = InterviewFactory()
        assert interview.completed_at is None
