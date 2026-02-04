"""
Test factories for members app.
"""
import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from apps.core.constants import Roles, FamilyStatus, GroupType, Province
from apps.members.models import Member, Family, Group, GroupMembership, DirectoryPrivacy

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for Django User model."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class FamilyFactory(DjangoModelFactory):
    """Factory for Family model."""

    class Meta:
        model = Family

    name = factory.Faker('last_name')
    address = factory.Faker('street_address')
    city = factory.Faker('city')
    province = Province.QC
    postal_code = factory.Faker('postcode')


class MemberFactory(DjangoModelFactory):
    """Factory for Member model."""

    class Meta:
        model = Member

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(
        lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@example.com'
    )
    phone = factory.Faker('phone_number')
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)
    address = factory.Faker('street_address')
    city = factory.Faker('city')
    province = Province.QC
    postal_code = factory.Faker('postcode')
    role = Roles.MEMBER
    family_status = FamilyStatus.SINGLE

    @factory.post_generation
    def create_privacy(self, create, extracted, **kwargs):
        """Create default privacy settings."""
        if create:
            DirectoryPrivacy.objects.get_or_create(member=self)


class MemberWithUserFactory(MemberFactory):
    """Factory for Member with linked User account."""

    user = factory.SubFactory(UserFactory)


class PastorFactory(MemberFactory):
    """Factory for pastor members."""

    role = Roles.PASTOR


class AdminMemberFactory(MemberFactory):
    """Factory for admin members."""

    role = Roles.ADMIN


class TreasurerFactory(MemberFactory):
    """Factory for treasurer members."""

    role = Roles.TREASURER


class GroupLeaderFactory(MemberFactory):
    """Factory for group leader members."""

    role = Roles.GROUP_LEADER


class VolunteerFactory(MemberFactory):
    """Factory for volunteer members."""

    role = Roles.VOLUNTEER


class GroupFactory(DjangoModelFactory):
    """Factory for Group model."""

    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f'Groupe {n}')
    group_type = GroupType.CELL
    description = factory.Faker('paragraph')
    leader = factory.SubFactory(GroupLeaderFactory)
    meeting_day = 'Mercredi'
    meeting_time = '19:00'


class GroupMembershipFactory(DjangoModelFactory):
    """Factory for GroupMembership model."""

    class Meta:
        model = GroupMembership

    member = factory.SubFactory(MemberFactory)
    group = factory.SubFactory(GroupFactory)
    role = 'member'


class DirectoryPrivacyFactory(DjangoModelFactory):
    """Factory for DirectoryPrivacy model."""

    class Meta:
        model = DirectoryPrivacy

    member = factory.SubFactory(MemberFactory)
    visibility = 'public'
    show_email = True
    show_phone = True
    show_address = False
    show_birth_date = True
    show_photo = True
