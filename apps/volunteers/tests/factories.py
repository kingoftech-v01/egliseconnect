"""Test factories for volunteers app."""
import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.core.constants import VolunteerRole, ScheduleStatus, VolunteerFrequency
from apps.members.tests.factories import MemberFactory

from apps.volunteers.models import (
    VolunteerPosition, VolunteerAvailability, VolunteerSchedule, SwapRequest
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


class SwapRequestFactory(DjangoModelFactory):
    """Creates test swap requests between volunteers."""

    class Meta:
        model = SwapRequest

    original_schedule = factory.SubFactory(VolunteerScheduleFactory)
    requested_by = factory.SubFactory(MemberFactory)
    swap_with = factory.SubFactory(MemberFactory)
    status = 'pending'
    reason = factory.Faker('sentence')
