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


@pytest.mark.django_db
class TestMemberModelMissedLines:
    """Tests covering missed lines in members/models.py."""

    def test_family_str(self):
        """Family.__str__ returns family name (line 58)."""
        family = FamilyFactory(name='Famille Dupont')
        assert str(family) == 'Famille Dupont'

    def test_days_remaining_for_form_no_deadline(self):
        """days_remaining_for_form returns None when no form_deadline (line 322)."""
        member = MemberFactory(form_deadline=None)
        assert member.days_remaining_for_form is None

    def test_is_form_expired_no_deadline(self):
        """is_form_expired returns False when no form_deadline (line 331)."""
        member = MemberFactory(form_deadline=None)
        assert member.is_form_expired is False

    def test_is_form_expired_with_past_deadline(self):
        """is_form_expired returns True when form_deadline has passed (line 333)."""
        from django.utils import timezone
        member = MemberFactory(
            form_deadline=timezone.now() - timezone.timedelta(days=1)
        )
        assert member.is_form_expired is True

    def test_is_form_expired_with_future_deadline(self):
        """is_form_expired returns False when form_deadline is in the future."""
        from django.utils import timezone
        member = MemberFactory(
            form_deadline=timezone.now() + timezone.timedelta(days=10)
        )
        assert member.is_form_expired is False

    def test_days_remaining_for_form_with_future_deadline(self):
        """days_remaining_for_form returns positive days when deadline is in the future (lines 323-325)."""
        from django.utils import timezone
        member = MemberFactory(
            form_deadline=timezone.now() + timezone.timedelta(days=15)
        )
        result = member.days_remaining_for_form
        assert result is not None
        assert result >= 14  # roughly 15 days, account for execution time

    def test_days_remaining_for_form_with_past_deadline(self):
        """days_remaining_for_form returns 0 when deadline has passed."""
        from django.utils import timezone
        member = MemberFactory(
            form_deadline=timezone.now() - timezone.timedelta(days=5)
        )
        assert member.days_remaining_for_form == 0

    def test_can_use_qr(self):
        """can_use_qr returns True for members in allowed statuses (line 343)."""
        from apps.core.constants import MembershipStatus
        active_member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        assert active_member.can_use_qr is True

        registered_member = MemberFactory(membership_status=MembershipStatus.REGISTERED)
        assert registered_member.can_use_qr is True

        suspended_member = MemberFactory(membership_status=MembershipStatus.SUSPENDED)
        assert suspended_member.can_use_qr is False

    def test_is_2fa_overdue_with_past_deadline(self):
        """is_2fa_overdue returns True when deadline passed and 2FA not enabled (lines 355-356)."""
        from django.utils import timezone
        member = MemberFactory(
            two_factor_deadline=timezone.now() - timezone.timedelta(days=1),
            two_factor_enabled=False,
        )
        assert member.is_2fa_overdue is True

    def test_is_2fa_overdue_with_2fa_enabled(self):
        """is_2fa_overdue returns False when 2FA is already enabled."""
        from django.utils import timezone
        member = MemberFactory(
            two_factor_deadline=timezone.now() - timezone.timedelta(days=1),
            two_factor_enabled=True,
        )
        assert member.is_2fa_overdue is False

    def test_is_2fa_overdue_no_deadline(self):
        """is_2fa_overdue returns False when no deadline set."""
        member = MemberFactory(two_factor_deadline=None)
        assert member.is_2fa_overdue is False

    def test_can_manage_finances(self):
        """can_manage_finances for treasurer and admin roles (line 364)."""
        from apps.core.constants import Roles
        treasurer = MemberFactory(role=Roles.TREASURER)
        admin = MemberFactory(role=Roles.ADMIN)
        regular = MemberFactory(role=Roles.MEMBER)

        assert treasurer.can_manage_finances is True
        assert admin.can_manage_finances is True
        assert regular.can_manage_finances is False

    def test_get_groups(self):
        """get_groups returns active groups for member (line 368)."""
        member = MemberFactory()
        group1 = GroupFactory()
        group2 = GroupFactory()
        GroupMembershipFactory(member=member, group=group1)
        inactive_membership = GroupMembershipFactory(member=member, group=group2)
        inactive_membership.is_active = False
        inactive_membership.save()

        groups = member.get_groups()
        assert group1 in groups
        assert group2 not in groups

    def test_group_membership_str(self):
        """GroupMembership.__str__ returns member name and group name (line 484)."""
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        group = GroupFactory(name='Prayer Group')
        membership = GroupMembershipFactory(member=member, group=group)
        result = str(membership)
        assert 'Jean Dupont' in result
        assert 'Prayer Group' in result

    def test_directory_privacy_str(self):
        """DirectoryPrivacy.__str__ returns formatted string (line 534)."""
        member = MemberFactory(first_name='Marie', last_name='Martin')
        privacy = member.privacy_settings
        result = str(privacy)
        assert 'Marie Martin' in result
        assert 'Confidentialité' in result


@pytest.mark.django_db
class TestMemberAdminMethods:
    """Tests for admin display methods (admin.py lines 113, 150, 186)."""

    def test_member_admin_full_name(self):
        """MemberAdmin.full_name returns member's full name (line 113)."""
        from django.contrib import admin
        from apps.members.admin import MemberAdmin
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        admin_obj = MemberAdmin(Member, admin.site)
        assert admin_obj.full_name(member) == 'Jean Dupont'

    def test_family_admin_member_count(self):
        """FamilyAdmin.member_count returns family's member count (line 150)."""
        from django.contrib import admin
        from apps.members.admin import FamilyAdmin
        family = FamilyFactory()
        MemberFactory(family=family)
        MemberFactory(family=family)
        admin_obj = FamilyAdmin(Family, admin.site)
        assert admin_obj.member_count(family) == 2

    def test_group_admin_member_count(self):
        """GroupAdmin.member_count returns group's member count (line 186)."""
        from django.contrib import admin
        from apps.members.admin import GroupAdmin
        from apps.members.models import Group
        group = GroupFactory()
        GroupMembershipFactory(group=group)
        GroupMembershipFactory(group=group)
        admin_obj = GroupAdmin(Group, admin.site)
        assert admin_obj.member_count(group) == 2
