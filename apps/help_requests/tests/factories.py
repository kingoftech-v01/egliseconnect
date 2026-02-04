"""Help Requests test factories."""
import factory
from factory.django import DjangoModelFactory
from apps.help_requests.models import HelpRequest, HelpRequestCategory, HelpRequestComment
from apps.members.tests.factories import MemberFactory


class HelpRequestCategoryFactory(DjangoModelFactory):
    """Factory for HelpRequestCategory."""

    class Meta:
        model = HelpRequestCategory

    name = factory.Sequence(lambda n: f'Category {n}')
    name_fr = factory.Sequence(lambda n: f'Catégorie {n}')
    description = factory.Faker('paragraph')
    icon = 'help-circle'
    is_active = True
    order = factory.Sequence(lambda n: n)


class HelpRequestFactory(DjangoModelFactory):
    """Factory for HelpRequest."""

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
    """Factory for HelpRequestComment."""

    class Meta:
        model = HelpRequestComment

    help_request = factory.SubFactory(HelpRequestFactory)
    author = factory.SubFactory(MemberFactory)
    content = factory.Faker('paragraph')
    is_internal = False
