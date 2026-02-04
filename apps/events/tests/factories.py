"""
Test factories for events app.
"""
import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.core.constants import EventType, RSVPStatus
from apps.members.tests.factories import MemberFactory

from apps.events.models import Event, EventRSVP


class EventFactory(DjangoModelFactory):
    """Factory for Event model."""

    class Meta:
        model = Event

    title = factory.Sequence(lambda n: f'Event {n}')
    description = factory.Faker('paragraph')
    event_type = EventType.WORSHIP
    start_datetime = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7))
    end_datetime = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7, hours=2))
    location = factory.Faker('address')
    is_published = True
    is_cancelled = False


class EventRSVPFactory(DjangoModelFactory):
    """Factory for EventRSVP model."""

    class Meta:
        model = EventRSVP

    event = factory.SubFactory(EventFactory)
    member = factory.SubFactory(MemberFactory)
    status = RSVPStatus.CONFIRMED
    guests = 0
