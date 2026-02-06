"""Test factories for help_requests app."""
import factory
from factory.django import DjangoModelFactory
from apps.help_requests.models import HelpRequest, HelpRequestCategory, HelpRequestComment
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
