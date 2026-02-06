"""Test factories for onboarding app."""
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

from apps.members.tests.factories import MemberFactory, PastorFactory
from apps.onboarding.models import (
    TrainingCourse,
    Lesson,
    MemberTraining,
    ScheduledLesson,
    Interview,
)
from apps.core.constants import LessonStatus, InterviewStatus


class TrainingCourseFactory(DjangoModelFactory):
    """Creates TrainingCourse instances for testing."""

    class Meta:
        model = TrainingCourse

    name = factory.Sequence(lambda n: f'Parcours {n}')
    description = factory.Faker('paragraph')
    total_lessons = 5
    is_default = False
    created_by = factory.SubFactory(MemberFactory)


class LessonFactory(DjangoModelFactory):
    """Creates Lesson instances linked to a TrainingCourse."""

    class Meta:
        model = Lesson

    course = factory.SubFactory(TrainingCourseFactory)
    order = factory.Sequence(lambda n: n + 1)
    title = factory.Sequence(lambda n: f'Lecon {n}')
    description = factory.Faker('paragraph')
    duration_minutes = 90


class MemberTrainingFactory(DjangoModelFactory):
    """Creates MemberTraining enrollment instances."""

    class Meta:
        model = MemberTraining

    member = factory.SubFactory(MemberFactory)
    course = factory.SubFactory(TrainingCourseFactory)
    assigned_by = factory.SubFactory(PastorFactory)


class ScheduledLessonFactory(DjangoModelFactory):
    """Creates ScheduledLesson instances."""

    class Meta:
        model = ScheduledLesson

    training = factory.SubFactory(MemberTrainingFactory)
    lesson = factory.SubFactory(LessonFactory)
    scheduled_date = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=7)
    )
    status = LessonStatus.UPCOMING


class InterviewFactory(DjangoModelFactory):
    """Creates Interview instances."""

    class Meta:
        model = Interview

    member = factory.SubFactory(MemberFactory)
    training = factory.SubFactory(MemberTrainingFactory)
    status = InterviewStatus.PROPOSED
    proposed_date = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=14)
    )
    interviewer = factory.SubFactory(PastorFactory)
