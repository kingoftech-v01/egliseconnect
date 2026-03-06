"""Test factories for help_requests app."""
import factory
from datetime import timedelta
from django.utils import timezone
from factory.django import DjangoModelFactory
from apps.help_requests.models import (
    HelpRequest, HelpRequestCategory, HelpRequestComment,
    PastoralCare, PrayerRequest, CareTeam, CareTeamMember,
    BenevolenceRequest, BenevolenceFund,
    MealTrain, MealSignup,
    CrisisProtocol, CrisisResource,
)
from apps.members.tests.factories import MemberFactory


class HelpRequestCategoryFactory(DjangoModelFactory):
    """Creates test help request categories."""

    class Meta:
        model = HelpRequestCategory

    name = factory.Sequence(lambda n: f'Category {n}')
    name_fr = factory.Sequence(lambda n: f'Categorie {n}')
    description = factory.Faker('paragraph')
    icon = 'help-circle'
    is_active = True
    order = factory.Sequence(lambda n: n)


class HelpRequestFactory(DjangoModelFactory):
    """Creates test help requests with auto-generated request numbers."""

    class Meta:
        model = HelpRequest

    member = factory.SubFactory(MemberFactory)
    category = factory.SubFactory(HelpRequestCategoryFactory)
    title = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('paragraph')
    urgency = 'medium'
    status = 'new'
    is_confidential = False


class HelpRequestCommentFactory(DjangoModelFactory):
    """Creates test comments on help requests."""

    class Meta:
        model = HelpRequestComment

    help_request = factory.SubFactory(HelpRequestFactory)
    author = factory.SubFactory(MemberFactory)
    content = factory.Faker('paragraph')
    is_internal = False


# ─── Pastoral Care Factories ─────────────────────────────────────────────────


class PastoralCareFactory(DjangoModelFactory):
    """Creates test pastoral care records."""

    class Meta:
        model = PastoralCare

    care_type = 'home_visit'
    member = factory.SubFactory(MemberFactory)
    assigned_to = factory.SubFactory(MemberFactory)
    date = factory.LazyFunction(timezone.now)
    notes = factory.Faker('paragraph')
    follow_up_date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=7)).date())
    status = 'open'
    created_by = factory.SubFactory(MemberFactory)


# ─── Prayer Request Factories ────────────────────────────────────────────────


class PrayerRequestFactory(DjangoModelFactory):
    """Creates test prayer requests."""

    class Meta:
        model = PrayerRequest

    title = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('paragraph')
    member = factory.SubFactory(MemberFactory)
    is_anonymous = False
    is_public = True
    status = 'active'
    is_approved = True


# ─── Care Team Factories ─────────────────────────────────────────────────────


class CareTeamFactory(DjangoModelFactory):
    """Creates test care teams."""

    class Meta:
        model = CareTeam

    name = factory.Sequence(lambda n: f'Care Team {n}')
    description = factory.Faker('paragraph')
    leader = factory.SubFactory(MemberFactory)


class CareTeamMemberFactory(DjangoModelFactory):
    """Creates test care team memberships."""

    class Meta:
        model = CareTeamMember

    team = factory.SubFactory(CareTeamFactory)
    member = factory.SubFactory(MemberFactory)


# ─── Benevolence Factories ───────────────────────────────────────────────────


class BenevolenceFundFactory(DjangoModelFactory):
    """Creates test benevolence funds."""

    class Meta:
        model = BenevolenceFund

    name = factory.Sequence(lambda n: f'Fonds {n}')
    total_balance = 5000.00
    description = factory.Faker('paragraph')


class BenevolenceRequestFactory(DjangoModelFactory):
    """Creates test benevolence requests."""

    class Meta:
        model = BenevolenceRequest

    member = factory.SubFactory(MemberFactory)
    fund = factory.SubFactory(BenevolenceFundFactory)
    amount_requested = 500.00
    reason = factory.Faker('paragraph')
    status = 'submitted'


# ─── Meal Train Factories ────────────────────────────────────────────────────


class MealTrainFactory(DjangoModelFactory):
    """Creates test meal trains."""

    class Meta:
        model = MealTrain

    recipient = factory.SubFactory(MemberFactory)
    reason = factory.Faker('sentence')
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=14)).date())
    dietary_restrictions = ''
    status = 'active'


class MealSignupFactory(DjangoModelFactory):
    """Creates test meal sign-ups."""

    class Meta:
        model = MealSignup

    meal_train = factory.SubFactory(MealTrainFactory)
    volunteer = factory.SubFactory(MemberFactory)
    date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=1)).date())
    confirmed = False
    notes = ''


# ─── Crisis Factories ────────────────────────────────────────────────────────


class CrisisProtocolFactory(DjangoModelFactory):
    """Creates test crisis protocols."""

    class Meta:
        model = CrisisProtocol

    title = factory.Sequence(lambda n: f'Protocol {n}')
    protocol_type = 'death'
    steps_json = ['Step 1', 'Step 2', 'Step 3']
    is_active = True


class CrisisResourceFactory(DjangoModelFactory):
    """Creates test crisis resources."""

    class Meta:
        model = CrisisResource

    title = factory.Sequence(lambda n: f'Resource {n}')
    description = factory.Faker('paragraph')
    contact_info = factory.Faker('phone_number')
    url = factory.Faker('url')
    category = 'grief_support'
