"""Test factories for volunteers app."""
import factory
from datetime import time
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.core.constants import (
    VolunteerRole, ScheduleStatus, VolunteerFrequency,
    BackgroundCheckStatus, SkillProficiency, MilestoneType,
)
from apps.members.tests.factories import MemberFactory

from apps.volunteers.models import (
    VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest,
    PlannedAbsence, VolunteerHours, VolunteerBackgroundCheck, TeamAnnouncement,
    PositionChecklist, ChecklistProgress, Skill, VolunteerSkill,
    Milestone, MilestoneAchievement, AvailabilitySlot, CrossTraining,
)


class VolunteerPositionFactory(DjangoModelFactory):
    """Creates test volunteer positions."""

    class Meta:
        model = VolunteerPosition

    name = factory.Sequence(lambda n: f'Position {n}')
    role_type = VolunteerRole.WORSHIP
    description = factory.Faker('paragraph')
    min_volunteers = 1


class VolunteerAvailabilityFactory(DjangoModelFactory):
    """Creates test availability records linking members to positions."""

    class Meta:
        model = VolunteerAvailability

    member = factory.SubFactory(MemberFactory)
    position = factory.SubFactory(VolunteerPositionFactory)
    is_available = True
    frequency = VolunteerFrequency.MONTHLY


class VolunteerScheduleFactory(DjangoModelFactory):
    """Creates test schedule entries for volunteer shifts."""

    class Meta:
        model = VolunteerSchedule

    member = factory.SubFactory(MemberFactory)
    position = factory.SubFactory(VolunteerPositionFactory)
    date = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=7))
    status = ScheduleStatus.SCHEDULED


class PlannedAbsenceFactory(DjangoModelFactory):
    """Creates test planned absence records."""

    class Meta:
        model = PlannedAbsence

    member = factory.SubFactory(MemberFactory)
    start_date = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=7))
    end_date = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=14))
    reason = factory.Faker('sentence')


class SwapRequestFactory(DjangoModelFactory):
    """Creates test swap requests between volunteers."""

    class Meta:
        model = SwapRequest

    original_schedule = factory.SubFactory(VolunteerScheduleFactory)
    requested_by = factory.SubFactory(MemberFactory)
    swap_with = factory.SubFactory(MemberFactory)
    status = 'pending'
    reason = factory.Faker('sentence')


class VolunteerHoursFactory(DjangoModelFactory):
    """Creates test volunteer hour log entries."""

    class Meta:
        model = VolunteerHours

    member = factory.SubFactory(MemberFactory)
    position = factory.SubFactory(VolunteerPositionFactory)
    date = factory.LazyFunction(lambda: timezone.now().date())
    hours_worked = factory.LazyFunction(lambda: __import__('decimal').Decimal('3.50'))
    description = factory.Faker('sentence')


class VolunteerBackgroundCheckFactory(DjangoModelFactory):
    """Creates test background check records."""

    class Meta:
        model = VolunteerBackgroundCheck

    member = factory.SubFactory(MemberFactory)
    position = factory.SubFactory(VolunteerPositionFactory)
    status = BackgroundCheckStatus.PENDING
    check_date = factory.LazyFunction(lambda: timezone.now().date())
    expiry_date = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=365))


class TeamAnnouncementFactory(DjangoModelFactory):
    """Creates test team announcements."""

    class Meta:
        model = TeamAnnouncement

    position = factory.SubFactory(VolunteerPositionFactory)
    author = factory.SubFactory(MemberFactory)
    title = factory.Sequence(lambda n: f'Annonce {n}')
    body = factory.Faker('paragraph')
    sent_at = factory.LazyFunction(timezone.now)


class PositionChecklistFactory(DjangoModelFactory):
    """Creates test checklist items for positions."""

    class Meta:
        model = PositionChecklist

    position = factory.SubFactory(VolunteerPositionFactory)
    title = factory.Sequence(lambda n: f'Checklist Item {n}')
    description = factory.Faker('sentence')
    order = factory.Sequence(lambda n: n)
    is_required = True


class ChecklistProgressFactory(DjangoModelFactory):
    """Creates test checklist progress records."""

    class Meta:
        model = ChecklistProgress

    member = factory.SubFactory(MemberFactory)
    checklist_item = factory.SubFactory(PositionChecklistFactory)
    completed_at = None
    verified_by = None


class SkillFactory(DjangoModelFactory):
    """Creates test skill records."""

    class Meta:
        model = Skill

    name = factory.Sequence(lambda n: f'Skill {n}')
    category = factory.Faker('word')
    description = factory.Faker('sentence')


class VolunteerSkillFactory(DjangoModelFactory):
    """Creates test volunteer skill assignments."""

    class Meta:
        model = VolunteerSkill

    member = factory.SubFactory(MemberFactory)
    skill = factory.SubFactory(SkillFactory)
    proficiency_level = SkillProficiency.BEGINNER
    certified_at = None


class MilestoneFactory(DjangoModelFactory):
    """Creates test milestone definitions."""

    class Meta:
        model = Milestone

    name = factory.Sequence(lambda n: f'Milestone {n}')
    milestone_type = MilestoneType.HOURS
    threshold = 100
    description = factory.Faker('sentence')
    badge_icon = 'fas fa-star'


class MilestoneAchievementFactory(DjangoModelFactory):
    """Creates test milestone achievement records."""

    class Meta:
        model = MilestoneAchievement

    member = factory.SubFactory(MemberFactory)
    milestone = factory.SubFactory(MilestoneFactory)
    achieved_at = factory.LazyFunction(timezone.now)
    notified = False


class AvailabilitySlotFactory(DjangoModelFactory):
    """Creates test availability slot records."""

    class Meta:
        model = AvailabilitySlot

    member = factory.SubFactory(MemberFactory)
    day_of_week = 0  # Monday
    time_start = time(9, 0)
    time_end = time(17, 0)
    is_available = True


class CrossTrainingFactory(DjangoModelFactory):
    """Creates test cross-training records."""

    class Meta:
        model = CrossTraining

    member = factory.SubFactory(MemberFactory)
    original_position = factory.SubFactory(VolunteerPositionFactory)
    trained_position = factory.SubFactory(VolunteerPositionFactory)
    certified_at = factory.LazyFunction(lambda: timezone.now().date())
    notes = factory.Faker('sentence')
