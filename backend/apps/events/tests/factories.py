"""Test factories for events app — all models."""
import factory
from datetime import timedelta
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.core.constants import (
    EventType, RSVPStatus, BookingStatus, RecurrenceFrequency,
    VolunteerSignupStatus,
)
from apps.members.tests.factories import MemberFactory

from apps.events.models import (
    Event, EventRSVP, Room, RoomBooking, EventTemplate,
    RegistrationForm, RegistrationEntry,
    EventWaitlist, EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)


class EventFactory(DjangoModelFactory):
    """Creates test events with sensible defaults."""

    class Meta:
        model = Event

    title = factory.Sequence(lambda n: f'Event {n}')
    description = factory.Faker('paragraph')
    event_type = EventType.WORSHIP
    start_datetime = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    end_datetime = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7, hours=2))
    location = factory.Faker('address')
    is_published = True
    is_cancelled = False


class EventRSVPFactory(DjangoModelFactory):
    """Creates test RSVPs linked to events and members."""

    class Meta:
        model = EventRSVP

    event = factory.SubFactory(EventFactory)
    member = factory.SubFactory(MemberFactory)
    status = RSVPStatus.CONFIRMED
    guests = 0


class RoomFactory(DjangoModelFactory):
    """Creates test rooms."""

    class Meta:
        model = Room

    name = factory.Sequence(lambda n: f'Salle {n}')
    capacity = 50
    location = factory.Faker('address')
    description = factory.Faker('sentence')
    amenities_json = factory.LazyFunction(lambda: ['projecteur', 'wifi', 'tableau'])


class RoomBookingFactory(DjangoModelFactory):
    """Creates test room bookings."""

    class Meta:
        model = RoomBooking

    room = factory.SubFactory(RoomFactory)
    booked_by = factory.SubFactory(MemberFactory)
    start_datetime = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    end_datetime = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1, hours=2))
    status = BookingStatus.PENDING
    notes = ''


class EventTemplateFactory(DjangoModelFactory):
    """Creates test event templates."""

    class Meta:
        model = EventTemplate

    name = factory.Sequence(lambda n: f'Template {n}')
    event_type = EventType.WORSHIP
    default_duration = timedelta(hours=2)
    default_description = factory.Faker('paragraph')
    default_capacity = 100
    default_location = 'Sanctuaire principal'
    requires_rsvp = False


class RegistrationFormFactory(DjangoModelFactory):
    """Creates test registration forms."""

    class Meta:
        model = RegistrationForm

    event = factory.SubFactory(EventFactory)
    title = factory.Sequence(lambda n: f'Formulaire {n}')
    fields_json = factory.LazyFunction(lambda: [
        {'name': 'dietary', 'type': 'text', 'label': 'Restrictions alimentaires', 'required': False},
        {'name': 'tshirt', 'type': 'dropdown', 'label': 'Taille t-shirt', 'required': True, 'options': ['S', 'M', 'L', 'XL']},
    ])


class RegistrationEntryFactory(DjangoModelFactory):
    """Creates test registration entries."""

    class Meta:
        model = RegistrationEntry

    form = factory.SubFactory(RegistrationFormFactory)
    member = factory.SubFactory(MemberFactory)
    data_json = factory.LazyFunction(lambda: {'dietary': 'Aucune', 'tshirt': 'M'})


class EventWaitlistFactory(DjangoModelFactory):
    """Creates test waitlist entries."""

    class Meta:
        model = EventWaitlist

    event = factory.SubFactory(EventFactory)
    member = factory.SubFactory(MemberFactory)
    position = factory.Sequence(lambda n: n + 1)


class EventVolunteerNeedFactory(DjangoModelFactory):
    """Creates test volunteer needs."""

    class Meta:
        model = EventVolunteerNeed

    event = factory.SubFactory(EventFactory)
    position_name = factory.Sequence(lambda n: f'Poste {n}')
    required_count = 3
    description = factory.Faker('sentence')


class EventVolunteerSignupFactory(DjangoModelFactory):
    """Creates test volunteer signups."""

    class Meta:
        model = EventVolunteerSignup

    need = factory.SubFactory(EventVolunteerNeedFactory)
    member = factory.SubFactory(MemberFactory)
    status = VolunteerSignupStatus.PENDING


class EventPhotoFactory(DjangoModelFactory):
    """Creates test event photos."""

    class Meta:
        model = EventPhoto

    event = factory.SubFactory(EventFactory)
    image = factory.django.ImageField(color='blue')
    caption = factory.Faker('sentence')
    uploaded_by = factory.SubFactory(MemberFactory)
    is_approved = True


class EventSurveyFactory(DjangoModelFactory):
    """Creates test event surveys."""

    class Meta:
        model = EventSurvey

    event = factory.SubFactory(EventFactory)
    title = factory.Sequence(lambda n: f'Sondage {n}')
    questions_json = factory.LazyFunction(lambda: [
        {'question': 'Comment avez-vous trouvé l\'événement?', 'type': 'rating', 'required': True},
        {'question': 'Commentaires', 'type': 'text', 'required': False},
    ])
    send_after_hours = 24


class SurveyResponseFactory(DjangoModelFactory):
    """Creates test survey responses."""

    class Meta:
        model = SurveyResponse

    survey = factory.SubFactory(EventSurveyFactory)
    member = factory.SubFactory(MemberFactory)
    answers_json = factory.LazyFunction(lambda: {'q_1': '5', 'q_2': 'Excellent!'})
