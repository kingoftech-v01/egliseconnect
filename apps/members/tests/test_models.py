"""
Tests for members models.
"""
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
        """Test creating a member."""
        member = MemberFactory()
        assert member.id is not None
        assert member.member_number is not None
        assert member.member_number.startswith('MBR-')

    def test_member_number_auto_generated(self):
        """Test that member number is auto-generated."""
        member = Member(first_name='Test', last_name='User')
        member.save()

        assert member.member_number is not None
        assert member.member_number.startswith('MBR-')

    def test_member_number_unique(self):
        """Test that member numbers are unique."""
        member1 = MemberFactory()
        member2 = MemberFactory()

        assert member1.member_number != member2.member_number

    def test_full_name_property(self):
        """Test full_name property."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        assert member.full_name == 'Jean Dupont'

    def test_age_property(self):
        """Test age calculation."""
        today = date.today()
        birth_date = today.replace(year=today.year - 30)
        member = MemberFactory(birth_date=birth_date)

        assert member.age == 30

    def test_age_property_none_without_birth_date(self):
        """Test age returns None without birth date."""
        member = MemberFactory(birth_date=None)
        assert member.age is None

    def test_is_staff_member_property(self):
        """Test is_staff_member property."""
        regular_member = MemberFactory(role=Roles.MEMBER)
        pastor = PastorFactory()

        assert regular_member.is_staff_member is False
        assert pastor.is_staff_member is True

    def test_member_str(self):
        """Test member string representation."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        assert 'Jean Dupont' in str(member)
        assert member.member_number in str(member)

    def test_soft_delete(self):
        """Test soft delete functionality."""
        member = MemberFactory()
        pk = member.pk
        member.delete()

        # Should not appear in default queryset
        assert not Member.objects.filter(pk=pk).exists()

        # Should appear in all_objects
        assert Member.all_objects.filter(pk=pk).exists()

        deleted_member = Member.all_objects.get(pk=pk)
        assert deleted_member.is_deleted is True

    def test_member_with_user(self):
        """Test member with linked user account."""
        member = MemberWithUserFactory()

        assert member.user is not None
        assert member.user.member_profile == member


@pytest.mark.django_db
class TestFamilyModel:
    """Tests for Family model."""

    def test_create_family(self):
        """Test creating a family."""
        family = FamilyFactory()
        assert family.id is not None
        assert family.name is not None

    def test_family_member_count(self):
        """Test member_count property."""
        family = FamilyFactory()
        MemberFactory(family=family)
        MemberFactory(family=family)

        assert family.member_count == 2

    def test_full_address_property(self):
        """Test full_address property."""
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
        """Test creating a group."""
        group = GroupFactory()
        assert group.id is not None
        assert group.name is not None

    def test_group_member_count(self):
        """Test member_count property."""
        group = GroupFactory()
        GroupMembershipFactory(group=group)
        GroupMembershipFactory(group=group)

        assert group.member_count == 2

    def test_group_str(self):
        """Test group string representation."""
        group = GroupFactory(name='Test Group')
        assert 'Test Group' in str(group)


@pytest.mark.django_db
class TestGroupMembershipModel:
    """Tests for GroupMembership model."""

    def test_create_membership(self):
        """Test creating a group membership."""
        membership = GroupMembershipFactory()
        assert membership.id is not None

    def test_unique_together(self):
        """Test that member can only be in a group once."""
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
        """Test creating privacy settings."""
        member = MemberFactory()
        # MemberFactory auto-creates privacy via post_generation
        privacy = member.privacy_settings

        assert privacy.id is not None
        assert privacy.visibility == 'public'  # default

    def test_default_values(self):
        """Test default privacy values."""
        member = MemberFactory()
        # MemberFactory auto-creates privacy via post_generation
        privacy = member.privacy_settings

        assert privacy.show_email is True
        assert privacy.show_phone is True
        assert privacy.show_address is False  # More private by default
        assert privacy.show_birth_date is True
        assert privacy.show_photo is True
