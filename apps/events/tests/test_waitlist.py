"""Tests for waitlist, volunteer needs, templates, photos, and surveys."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.core.constants import RSVPStatus, VolunteerSignupStatus, EventType
from apps.events.models import (
    Event, EventRSVP, EventWaitlist, EventTemplate,
    EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)
from apps.events.tests.factories import (
    EventFactory, EventRSVPFactory, EventWaitlistFactory,
    EventTemplateFactory, EventVolunteerNeedFactory,
    EventVolunteerSignupFactory, EventPhotoFactory,
    EventSurveyFactory, SurveyResponseFactory,
)
from apps.members.tests.factories import MemberFactory


pytestmark = pytest.mark.django_db


# ── Waitlist Tests ──

class TestEventWaitlistModel:
    def test_create_waitlist_entry(self):
        event = EventFactory(max_attendees=1)
        member = MemberFactory()
        entry = EventWaitlist.objects.create(event=event, member=member, position=1)
        assert entry.position == 1
        assert entry.promoted_at is None

    def test_str(self):
        entry = EventWaitlistFactory()
        assert entry.member.full_name in str(entry)
        assert entry.event.title in str(entry)

    def test_unique_event_member(self):
        entry = EventWaitlistFactory()
        with pytest.raises(Exception):
            EventWaitlist.objects.create(
                event=entry.event, member=entry.member, position=2,
            )

    def test_ordering_by_position(self):
        event = EventFactory()
        m1 = MemberFactory()
        m2 = MemberFactory()
        m3 = MemberFactory()
        EventWaitlist.objects.create(event=event, member=m3, position=3)
        EventWaitlist.objects.create(event=event, member=m1, position=1)
        EventWaitlist.objects.create(event=event, member=m2, position=2)
        entries = list(event.waitlist_entries.order_by('position'))
        assert entries[0].position == 1
        assert entries[2].position == 3

    def test_event_waitlist_count_property(self):
        event = EventFactory()
        EventWaitlistFactory(event=event, position=1)
        EventWaitlistFactory(event=event, position=2)
        assert event.waitlist_count == 2


class TestWaitlistPromotion:
    def test_promote_creates_rsvp(self):
        event = EventFactory(max_attendees=2)
        member = MemberFactory()
        EventRSVPFactory(event=event, member=MemberFactory(), status=RSVPStatus.CONFIRMED)
        entry = EventWaitlistFactory(event=event, member=member, position=1)

        EventRSVP.objects.update_or_create(
            event=event, member=member,
            defaults={'status': RSVPStatus.CONFIRMED},
        )
        entry.promoted_at = timezone.now()
        entry.save()

        assert EventRSVP.objects.filter(event=event, member=member, status=RSVPStatus.CONFIRMED).exists()
        entry.refresh_from_db()
        assert entry.promoted_at is not None


# ── Event Template Tests ──

class TestEventTemplateModel:
    def test_create_template(self):
        tpl = EventTemplate.objects.create(
            name='Culte dominical',
            event_type=EventType.WORSHIP,
            default_duration=timedelta(hours=2),
            default_capacity=200,
            default_location='Sanctuaire',
            requires_rsvp=False,
        )
        assert str(tpl) == 'Culte dominical'

    def test_factory(self):
        tpl = EventTemplateFactory()
        assert tpl.pk is not None
        assert tpl.default_duration == timedelta(hours=2)

    def test_create_event_from_template(self):
        tpl = EventTemplateFactory(
            name='Bible Study',
            event_type=EventType.GROUP,
            default_duration=timedelta(hours=1, minutes=30),
            default_capacity=20,
            default_location='Salle B',
        )
        start = timezone.now() + timedelta(days=1)
        end = start + tpl.default_duration
        event = Event.objects.create(
            title=tpl.name,
            event_type=tpl.event_type,
            start_datetime=start,
            end_datetime=end,
            max_attendees=tpl.default_capacity,
            location=tpl.default_location,
            requires_rsvp=tpl.requires_rsvp,
        )
        assert event.title == 'Bible Study'
        assert event.max_attendees == 20


# ── Volunteer Needs Tests ──

class TestEventVolunteerNeedModel:
    def test_create_need(self):
        event = EventFactory()
        need = EventVolunteerNeed.objects.create(
            event=event, position_name='Accueil', required_count=3,
        )
        assert need.filled_count == 0
        assert need.is_filled is False
        assert need.remaining == 3

    def test_str(self):
        need = EventVolunteerNeedFactory(position_name='Technicien AV')
        assert 'Technicien AV' in str(need)

    def test_filled_count_with_confirmed_signups(self):
        need = EventVolunteerNeedFactory(required_count=2)
        EventVolunteerSignupFactory(need=need, status=VolunteerSignupStatus.CONFIRMED)
        EventVolunteerSignupFactory(need=need, status=VolunteerSignupStatus.PENDING)
        assert need.filled_count == 1
        assert need.is_filled is False

    def test_is_filled_when_count_met(self):
        need = EventVolunteerNeedFactory(required_count=1)
        EventVolunteerSignupFactory(need=need, status=VolunteerSignupStatus.CONFIRMED)
        assert need.is_filled is True
        assert need.remaining == 0


class TestEventVolunteerSignupModel:
    def test_create_signup(self):
        signup = EventVolunteerSignupFactory()
        assert signup.pk is not None
        assert signup.status == VolunteerSignupStatus.PENDING

    def test_str(self):
        signup = EventVolunteerSignupFactory()
        assert signup.member.full_name in str(signup)

    def test_unique_need_member(self):
        signup = EventVolunteerSignupFactory()
        with pytest.raises(Exception):
            EventVolunteerSignup.objects.create(
                need=signup.need, member=signup.member,
            )


# ── Event Photo Tests ──

class TestEventPhotoModel:
    def test_create_photo(self):
        photo = EventPhotoFactory()
        assert photo.pk is not None
        assert photo.is_approved is True

    def test_str(self):
        photo = EventPhotoFactory(caption='Photo de groupe')
        assert 'Photo de groupe' in str(photo)

    def test_unapproved_by_default_in_model(self):
        event = EventFactory()
        member = MemberFactory()
        photo = EventPhoto.objects.create(
            event=event,
            image='test.jpg',
            uploaded_by=member,
        )
        assert photo.is_approved is False

    def test_event_photos_relation(self):
        event = EventFactory()
        EventPhotoFactory(event=event)
        EventPhotoFactory(event=event)
        assert event.photos.count() == 2


# ── Survey Tests ──

class TestEventSurveyModel:
    def test_create_survey(self):
        survey = EventSurveyFactory()
        assert survey.pk is not None
        assert len(survey.questions_json) == 2

    def test_str(self):
        survey = EventSurveyFactory(title='Sondage satisfaction')
        assert 'Sondage satisfaction' in str(survey)

    def test_default_send_after_hours(self):
        survey = EventSurveyFactory()
        assert survey.send_after_hours == 24


class TestSurveyResponseModel:
    def test_create_response(self):
        response = SurveyResponseFactory()
        assert response.pk is not None
        assert 'q_1' in response.answers_json

    def test_str(self):
        response = SurveyResponseFactory()
        assert response.member.full_name in str(response)

    def test_unique_survey_member(self):
        response = SurveyResponseFactory()
        with pytest.raises(Exception):
            SurveyResponse.objects.create(
                survey=response.survey,
                member=response.member,
                answers_json={},
            )

    def test_survey_response_count(self):
        survey = EventSurveyFactory()
        SurveyResponseFactory(survey=survey)
        SurveyResponseFactory(survey=survey)
        assert survey.responses.count() == 2


# ── Event Available Spots Property ──

class TestEventProperties:
    def test_available_spots_with_max(self):
        event = EventFactory(max_attendees=10)
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        assert event.available_spots == 8

    def test_available_spots_without_max(self):
        event = EventFactory(max_attendees=None)
        assert event.available_spots is None

    def test_is_full(self):
        event = EventFactory(max_attendees=1)
        EventRSVPFactory(event=event, status=RSVPStatus.CONFIRMED)
        assert event.is_full is True

    def test_not_full(self):
        event = EventFactory(max_attendees=10)
        assert event.is_full is False
