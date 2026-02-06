"""Tests for members models."""
import pytest
from datetime import date, timedelta

from apps.core.constants import Roles
from apps.members.models import Member, Family, Group, GroupMembership, DirectoryPrivacy

from .factories import (
    MemberFactory,
    MemberWithUserFactory,
    FamilyFactory,
    GroupFactory,
    GroupMembershipFactory,
    PastorFactory,
)


@pytest.mark.django_db
class TestMemberModel:
    """Tests for Member model."""

    def test_create_member(self):
        """Member creation auto-generates member number."""
        member = MemberFactory()
        assert member.id is not None
        assert member.member_number is not None
        assert member.member_number.startswith('MBR-')

    def test_member_number_auto_generated(self):
        """Member number generated on save if not set."""
        member = Member(first_name='Test', last_name='User')
        member.save()

        assert member.member_number is not None
        assert member.member_number.startswith('MBR-')

    def test_member_number_unique(self):
        """Each member gets a unique member number."""
        member1 = MemberFactory()
        member2 = MemberFactory()

        assert member1.member_number != member2.member_number

    def test_full_name_property(self):
        """full_name combines first and last name."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        assert member.full_name == 'Jean Dupont'

    def test_age_property(self):
        """age calculates from birth_date."""
        today = date.today()
        birth_date = today.replace(year=today.year - 30)
        member = MemberFactory(birth_date=birth_date)

        assert member.age == 30

    def test_age_property_none_without_birth_date(self):
        """age returns None when birth_date not set."""
        member = MemberFactory(birth_date=None)
        assert member.age is None

    def test_is_staff_member_property(self):
        """is_staff_member identifies staff roles."""
        regular_member = MemberFactory(role=Roles.MEMBER)
        pastor = PastorFactory()

        assert regular_member.is_staff_member is False
        assert pastor.is_staff_member is True

    def test_member_str(self):
        """String representation includes name and member number."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        assert 'Jean Dupont' in str(member)
        assert member.member_number in str(member)

    def test_soft_delete(self):
        """Soft delete hides from default queryset but keeps in all_objects."""
        member = MemberFactory()
        pk = member.pk
        member.delete()

        assert not Member.objects.filter(pk=pk).exists()
        assert Member.all_objects.filter(pk=pk).exists()

        deleted_member = Member.all_objects.get(pk=pk)
        assert deleted_member.is_deleted is True

    def test_member_with_user(self):
        """Member linked to user has bidirectional relationship."""
        member = MemberWithUserFactory()

        assert member.user is not None
        assert member.user.member_profile == member


@pytest.mark.django_db
class TestFamilyModel:
    """Tests for Family model."""

    def test_create_family(self):
        """Family creation works."""
        family = FamilyFactory()
        assert family.id is not None
        assert family.name is not None

    def test_family_member_count(self):
        """member_count counts family members."""
        family = FamilyFactory()
        MemberFactory(family=family)
        MemberFactory(family=family)

        assert family.member_count == 2

    def test_full_address_property(self):
        """full_address combines address fields."""
        family = FamilyFactory(
            address='123 Rue Test',
            city='Montreal',
            province='QC',
            postal_code='H1A 1A1'
        )

        assert '123 Rue Test' in family.full_address
        assert 'Montreal' in family.full_address


@pytest.mark.django_db
class TestGroupModel:
    """Tests for Group model."""

    def test_create_group(self):
        """Group creation works."""
        group = GroupFactory()
        assert group.id is not None
        assert group.name is not None

    def test_group_member_count(self):
        """member_count counts group members."""
        group = GroupFactory()
        GroupMembershipFactory(group=group)
        GroupMembershipFactory(group=group)

        assert group.member_count == 2

    def test_group_str(self):
        """String representation includes name."""
        group = GroupFactory(name='Test Group')
        assert 'Test Group' in str(group)


@pytest.mark.django_db
class TestGroupMembershipModel:
    """Tests for GroupMembership model."""

    def test_create_membership(self):
        """Membership creation works."""
        membership = GroupMembershipFactory()
        assert membership.id is not None

    def test_unique_together(self):
        """Member can only be in a group once."""
        membership = GroupMembershipFactory()

        with pytest.raises(Exception):
            GroupMembershipFactory(
                member=membership.member,
                group=membership.group
            )


@pytest.mark.django_db
class TestDirectoryPrivacyModel:
    """Tests for DirectoryPrivacy model."""

    def test_create_privacy_settings(self):
        """Privacy settings created via factory post_generation."""
        member = MemberFactory()
        privacy = member.privacy_settings

        assert privacy.id is not None
        assert privacy.visibility == 'public'

    def test_default_values(self):
        """Default privacy values protect address by default."""
        member = MemberFactory()
        privacy = member.privacy_settings

        assert privacy.show_email is True
        assert privacy.show_phone is True
        assert privacy.show_address is False
        assert privacy.show_birth_date is True
        assert privacy.show_photo is True
