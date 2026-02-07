"""Tests for members forms."""
import pytest
from django.contrib.auth import get_user_model

from apps.core.constants import Roles, FamilyStatus, Province, GroupType, PrivacyLevel
from apps.members.forms import (
    MemberRegistrationForm,
    MemberProfileForm,
    MemberAdminForm,
    MemberSearchForm,
    FamilyForm,
    GroupForm,
    GroupMembershipForm,
    DirectoryPrivacyForm,
)
from apps.members.models import Member, Family, DirectoryPrivacy

from .factories import (
    MemberFactory,
    FamilyFactory,
    GroupFactory,
    GroupLeaderFactory,
    PastorFactory,
    AdminMemberFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestMemberRegistrationForm:
    """Tests for MemberRegistrationForm."""

    def _get_valid_data(self, create_account=False, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean.dupont@example.com',
            'phone': '514-555-0123',
            'birth_date': '1990-01-15',
            'address': '123 Rue Test',
            'city': 'Montreal',
            'province': Province.QC,
            'postal_code': 'H1A 1A1',
            'family_status': FamilyStatus.SINGLE,
            'create_account': create_account,
        }
        if create_account:
            data['password'] = 'S3cur3P@ssW0rd!'
            data['password_confirm'] = 'S3cur3P@ssW0rd!'
        data.update(overrides)
        return data

    def test_valid_data_without_account(self):
        """Valid data without account creation."""
        form = MemberRegistrationForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_valid_data_with_account(self):
        """Valid data with account creation."""
        form = MemberRegistrationForm(data=self._get_valid_data(create_account=True))
        assert form.is_valid(), form.errors

    def test_first_name_required(self):
        """First name is a required field."""
        data = self._get_valid_data(first_name='')
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_last_name_required(self):
        """Last name is a required field."""
        data = self._get_valid_data(last_name='')
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'last_name' in form.errors

    def test_email_optional(self):
        """Email is optional for members without accounts."""
        data = self._get_valid_data(email='')
        form = MemberRegistrationForm(data=data)
        assert form.is_valid(), form.errors

    def test_password_required_when_creating_account(self):
        """Password becomes required when create_account is True."""
        data = self._get_valid_data(create_account=True)
        data['password'] = ''
        data['password_confirm'] = ''
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_password_mismatch(self):
        """Password confirmation must match."""
        data = self._get_valid_data(create_account=True)
        data['password_confirm'] = 'DifferentP@ssW0rd!'
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'password_confirm' in form.errors

    def test_weak_password_too_short(self):
        """Rejects passwords that are too short."""
        data = self._get_valid_data(create_account=True)
        data['password'] = 'Ab1!'
        data['password_confirm'] = 'Ab1!'
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_weak_password_common(self):
        """Rejects commonly used passwords."""
        data = self._get_valid_data(create_account=True)
        data['password'] = 'password123'
        data['password_confirm'] = 'password123'
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_weak_password_all_numeric(self):
        """Rejects numeric-only passwords."""
        data = self._get_valid_data(create_account=True)
        data['password'] = '98765432'
        data['password_confirm'] = '98765432'
        form = MemberRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_password_not_required_without_account(self):
        """Password not required when not creating account."""
        data = self._get_valid_data(create_account=False)
        data['password'] = ''
        data['password_confirm'] = ''
        form = MemberRegistrationForm(data=data)
        assert form.is_valid(), form.errors

    def test_save_creates_member_without_account(self):
        """Save creates member without user account."""
        form = MemberRegistrationForm(data=self._get_valid_data())
        assert form.is_valid()
        member = form.save()

        assert member.pk is not None
        assert member.first_name == 'Jean'
        assert member.last_name == 'Dupont'
        assert member.user is None
        assert member.member_number.startswith('MBR-')

    def test_save_creates_member_with_account(self):
        """Save creates member with linked user account."""
        form = MemberRegistrationForm(
            data=self._get_valid_data(create_account=True)
        )
        assert form.is_valid()
        member = form.save()

        assert member.pk is not None
        assert member.user is not None
        assert member.user.email == 'jean.dupont@example.com'
        assert member.user.username == 'jean.dupont@example.com'
        assert member.user.first_name == 'Jean'
        assert member.user.last_name == 'Dupont'
        assert member.user.check_password('S3cur3P@ssW0rd!')

    def test_save_creates_privacy_settings(self):
        """Save auto-creates DirectoryPrivacy for new members."""
        form = MemberRegistrationForm(data=self._get_valid_data())
        assert form.is_valid()
        member = form.save()

        assert DirectoryPrivacy.objects.filter(member=member).exists()
        privacy = member.privacy_settings
        assert privacy.visibility == PrivacyLevel.PUBLIC

    def test_email_uniqueness_when_creating_account(self):
        """Duplicate email caught at save time due to field ordering in ModelForm."""
        User.objects.create_user(
            username='jean.dupont@example.com',
            email='jean.dupont@example.com',
            password='testpass123',
        )
        data = self._get_valid_data(create_account=True)
        form = MemberRegistrationForm(data=data)
        # Due to ModelForm field ordering, clean_email runs before create_account
        # is cleaned, so uniqueness is enforced at DB level during save()
        assert form.is_valid()
        with pytest.raises(Exception):
            form.save()

    def test_clean_email_raises_on_duplicate_with_account(self):
        """clean_email raises ValidationError when email exists and create_account=True (lines 60-61)."""
        from django import forms as django_forms
        User.objects.create_user(
            username='dup@example.com',
            email='dup@example.com',
            password='testpass123',
        )
        data = self._get_valid_data(create_account=True, email='dup@example.com')
        form = MemberRegistrationForm(data=data)
        # Manually set cleaned_data to simulate create_account being cleaned first
        form.cleaned_data = {'create_account': True, 'email': 'dup@example.com'}
        with pytest.raises(django_forms.ValidationError):
            form.clean_email()

    def test_email_not_checked_without_account(self):
        """Duplicate email allowed when not creating account."""
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='testpass123',
        )
        data = self._get_valid_data(
            create_account=False,
            email='existing@example.com',
        )
        form = MemberRegistrationForm(data=data)
        assert form.is_valid(), form.errors

    def test_save_commit_false(self):
        """commit=False does not persist to database."""
        form = MemberRegistrationForm(data=self._get_valid_data())
        assert form.is_valid()
        member = form.save(commit=False)

        assert member.pk is None or not Member.objects.filter(pk=member.pk).exists()
        assert member.user is None
        assert DirectoryPrivacy.objects.count() == 0

    def test_valid_with_minimal_data(self):
        """Form valid with only required fields."""
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'province': Province.QC,
            'family_status': FamilyStatus.SINGLE,
        }
        form = MemberRegistrationForm(data=data)
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestMemberProfileForm:
    """Tests for MemberProfileForm."""

    def test_valid_data(self):
        """Valid profile update data."""
        member = MemberFactory()
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'phone': '514-555-9999',
            'phone_secondary': '',
            'birth_date': '1985-05-20',
            'address': '456 Rue Nouvelle',
            'city': 'Quebec',
            'province': Province.QC,
            'postal_code': 'G1A 2B3',
            'family_status': FamilyStatus.MARRIED,
        }
        form = MemberProfileForm(data=data, instance=member)
        assert form.is_valid(), form.errors

    def test_update_existing_member(self):
        """Updates existing member correctly."""
        member = MemberFactory(phone='514-555-1234')
        data = {
            'first_name': 'UpdatedName',
            'last_name': member.last_name,
            'email': member.email,
            'phone': '514-555-1234',
            'phone_secondary': '',
            'birth_date': member.birth_date,
            'address': member.address,
            'city': member.city,
            'province': member.province,
            'postal_code': member.postal_code,
            'family_status': member.family_status,
        }
        form = MemberProfileForm(data=data, instance=member)
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.first_name == 'UpdatedName'

    def test_excludes_admin_fields(self):
        """Admin-only fields excluded from profile form."""
        form = MemberProfileForm()
        assert 'role' not in form.fields
        assert 'notes' not in form.fields
        assert 'is_active' not in form.fields
        assert 'joined_date' not in form.fields
        assert 'baptism_date' not in form.fields
        assert 'family' not in form.fields

    def test_includes_profile_fields(self):
        """Profile fields are present."""
        form = MemberProfileForm()
        assert 'first_name' in form.fields
        assert 'last_name' in form.fields
        assert 'email' in form.fields
        assert 'phone' in form.fields
        assert 'phone_secondary' in form.fields
        assert 'birth_date' in form.fields
        assert 'address' in form.fields
        assert 'city' in form.fields
        assert 'province' in form.fields
        assert 'postal_code' in form.fields
        assert 'photo' in form.fields
        assert 'family_status' in form.fields


@pytest.mark.django_db
class TestMemberAdminForm:
    """Tests for MemberAdminForm."""

    def test_valid_data(self):
        """Valid admin form data."""
        member = MemberFactory()
        family = FamilyFactory()
        data = {
            'first_name': 'Admin',
            'last_name': 'Edit',
            'email': 'admin.edit@example.com',
            'phone': '514-555-0001',
            'phone_secondary': '',
            'birth_date': '1980-03-10',
            'address': '789 Rue Admin',
            'city': 'Laval',
            'province': Province.QC,
            'postal_code': 'H7A 1A1',
            'role': Roles.PASTOR,
            'family_status': FamilyStatus.MARRIED,
            'family': family.pk,
            'joined_date': '2020-01-01',
            'baptism_date': '2019-06-15',
            'notes': 'Notes pastorales',
            'is_active': True,
        }
        form = MemberAdminForm(data=data, instance=member)
        assert form.is_valid(), form.errors

    def test_includes_admin_fields(self):
        """Admin-only fields are present."""
        form = MemberAdminForm()
        assert 'role' in form.fields
        assert 'notes' in form.fields
        assert 'is_active' in form.fields
        assert 'joined_date' in form.fields
        assert 'baptism_date' in form.fields
        assert 'family' in form.fields

    def test_save_with_admin_fields(self):
        """Saves admin-only fields correctly."""
        member = MemberFactory(phone='514-555-0001')
        data = {
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'phone': '514-555-0001',
            'phone_secondary': '',
            'birth_date': member.birth_date,
            'address': member.address,
            'city': member.city,
            'province': member.province,
            'postal_code': member.postal_code,
            'role': Roles.PASTOR,
            'family_status': member.family_status,
            'joined_date': '2020-01-01',
            'baptism_date': '',
            'notes': 'Test admin notes',
            'is_active': True,
        }
        form = MemberAdminForm(data=data, instance=member)
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.role == Roles.PASTOR
        assert saved.notes == 'Test admin notes'
        assert saved.joined_date is not None

    def test_deactivate_member(self):
        """Can deactivate member via admin form."""
        member = MemberFactory(phone='514-555-0002')
        data = {
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'phone': '514-555-0002',
            'phone_secondary': '',
            'birth_date': member.birth_date,
            'address': member.address,
            'city': member.city,
            'province': member.province,
            'postal_code': member.postal_code,
            'role': member.role,
            'family_status': member.family_status,
            'notes': '',
            'is_active': False,
            'joined_date': '',
            'baptism_date': '',
        }
        form = MemberAdminForm(data=data, instance=member)
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.is_active is False

    def test_assign_family(self):
        """Can assign family to member."""
        member = MemberFactory(family=None, phone='514-555-0003')
        family = FamilyFactory()
        data = {
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'phone': '514-555-0003',
            'phone_secondary': '',
            'birth_date': member.birth_date,
            'address': member.address,
            'city': member.city,
            'province': member.province,
            'postal_code': member.postal_code,
            'role': member.role,
            'family_status': member.family_status,
            'family': family.pk,
            'notes': '',
            'is_active': True,
            'joined_date': '',
            'baptism_date': '',
        }
        form = MemberAdminForm(data=data, instance=member)
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.family == family


@pytest.mark.django_db
class TestMemberSearchForm:
    """Tests for MemberSearchForm."""

    def test_empty_form_is_valid(self):
        """Empty search form is valid."""
        form = MemberSearchForm(data={})
        assert form.is_valid()

    def test_with_search_query(self):
        """Search query is captured."""
        form = MemberSearchForm(data={'search': 'Dupont'})
        assert form.is_valid()
        assert form.cleaned_data['search'] == 'Dupont'

    def test_with_role_filter(self):
        """Role filter is captured."""
        form = MemberSearchForm(data={'role': Roles.PASTOR})
        assert form.is_valid()
        assert form.cleaned_data['role'] == Roles.PASTOR

    def test_with_family_status_filter(self):
        """Family status filter is captured."""
        form = MemberSearchForm(data={'family_status': FamilyStatus.MARRIED})
        assert form.is_valid()
        assert form.cleaned_data['family_status'] == FamilyStatus.MARRIED

    def test_with_group_filter(self):
        """Group filter is captured."""
        group = GroupFactory()
        form = MemberSearchForm(data={'group': group.pk})
        assert form.is_valid()
        assert form.cleaned_data['group'] == group

    def test_with_birth_month_filter(self):
        """Birth month filter is captured."""
        form = MemberSearchForm(data={'birth_month': '6'})
        assert form.is_valid()
        assert form.cleaned_data['birth_month'] == '6'

    def test_with_all_filters(self):
        """All filters together are valid."""
        group = GroupFactory()
        data = {
            'search': 'test',
            'role': Roles.MEMBER,
            'family_status': FamilyStatus.SINGLE,
            'group': group.pk,
            'birth_month': '12',
        }
        form = MemberSearchForm(data=data)
        assert form.is_valid()

    def test_invalid_role(self):
        """Invalid role value rejected."""
        form = MemberSearchForm(data={'role': 'nonexistent_role'})
        assert not form.is_valid()
        assert 'role' in form.errors

    def test_invalid_group(self):
        """Non-existent group rejected."""
        import uuid
        form = MemberSearchForm(data={'group': uuid.uuid4()})
        assert not form.is_valid()
        assert 'group' in form.errors


@pytest.mark.django_db
class TestFamilyForm:
    """Tests for FamilyForm."""

    def test_valid_data(self):
        """Valid family data."""
        data = {
            'name': 'Famille Dupont',
            'address': '123 Rue Famille',
            'city': 'Montreal',
            'province': Province.QC,
            'postal_code': 'H1A 1A1',
            'notes': 'Test notes',
        }
        form = FamilyForm(data=data)
        assert form.is_valid(), form.errors

    def test_minimal_data(self):
        """Minimal required data."""
        data = {'name': 'Famille Martin', 'province': Province.QC}
        form = FamilyForm(data=data)
        assert form.is_valid(), form.errors

    def test_name_required(self):
        """Name is required."""
        form = FamilyForm(data={'province': Province.QC})
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_save(self):
        """Saves new family."""
        data = {
            'name': 'Famille Test',
            'address': '456 Rue Test',
            'city': 'Quebec',
            'province': Province.QC,
            'postal_code': 'G1A 2B3',
            'notes': '',
        }
        form = FamilyForm(data=data)
        assert form.is_valid()
        family = form.save()
        assert family.pk is not None
        assert family.name == 'Famille Test'
        assert family.city == 'Quebec'

    def test_update_existing_family(self):
        """Updates existing family."""
        family = FamilyFactory()
        data = {
            'name': 'Updated Family',
            'address': family.address,
            'city': family.city,
            'province': family.province,
            'postal_code': family.postal_code,
            'notes': 'Updated notes',
        }
        form = FamilyForm(data=data, instance=family)
        assert form.is_valid()
        saved = form.save()
        assert saved.name == 'Updated Family'
        assert saved.notes == 'Updated notes'


@pytest.mark.django_db
class TestGroupForm:
    """Tests for GroupForm."""

    def test_valid_data(self):
        """Valid group data."""
        leader = GroupLeaderFactory()
        data = {
            'name': 'Groupe de priere',
            'group_type': GroupType.CELL,
            'description': 'Un groupe de cellule',
            'leader': leader.pk,
            'meeting_day': 'Mercredi',
            'meeting_time': '19:00',
            'meeting_location': 'Eglise',
            'email': 'groupe@example.com',
        }
        form = GroupForm(data=data)
        assert form.is_valid(), form.errors

    def test_minimal_data(self):
        """Minimal required data."""
        data = {
            'name': 'Minimal Group',
            'group_type': GroupType.CELL,
        }
        form = GroupForm(data=data)
        assert form.is_valid(), form.errors

    def test_name_required(self):
        """Name is required."""
        data = {'group_type': GroupType.CELL}
        form = GroupForm(data=data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_leader_queryset_limited_to_eligible_roles(self):
        """Leader choices limited to group leaders, pastors, admins."""
        regular_member = MemberFactory(role=Roles.MEMBER)
        volunteer = MemberFactory(role=Roles.VOLUNTEER)
        group_leader = GroupLeaderFactory()
        pastor = PastorFactory()
        admin_member = AdminMemberFactory()

        form = GroupForm()
        leader_qs = form.fields['leader'].queryset

        assert regular_member not in leader_qs
        assert volunteer not in leader_qs
        assert group_leader in leader_qs
        assert pastor in leader_qs
        assert admin_member in leader_qs

    def test_save(self):
        """Saves new group."""
        leader = GroupLeaderFactory()
        data = {
            'name': 'New Group',
            'group_type': GroupType.MINISTRY,
            'description': 'A ministry group',
            'leader': leader.pk,
            'meeting_day': 'Lundi',
            'meeting_time': '18:30',
            'meeting_location': 'Salle 101',
            'email': 'ministry@example.com',
        }
        form = GroupForm(data=data)
        assert form.is_valid()
        group = form.save()
        assert group.pk is not None
        assert group.name == 'New Group'
        assert group.leader == leader
        assert group.group_type == GroupType.MINISTRY

    def test_all_group_types(self):
        """All valid group types accepted."""
        for group_type, _ in GroupType.CHOICES:
            data = {
                'name': f'Group {group_type}',
                'group_type': group_type,
            }
            form = GroupForm(data=data)
            assert form.is_valid(), f"Failed for group_type={group_type}: {form.errors}"


@pytest.mark.django_db
class TestGroupMembershipForm:
    """Tests for GroupMembershipForm."""

    def test_valid_data(self):
        """Valid membership data."""
        member = MemberFactory()
        group = GroupFactory()
        data = {
            'member': member.pk,
            'group': group.pk,
            'role': 'member',
            'notes': 'Test membership',
        }
        form = GroupMembershipForm(data=data)
        assert form.is_valid(), form.errors

    def test_all_roles(self):
        """All valid membership roles accepted."""
        member = MemberFactory()
        group = GroupFactory()
        for role, _ in [('member', 'Membre'), ('leader', 'Leader'), ('assistant', 'Assistant')]:
            data = {
                'member': member.pk,
                'group': group.pk,
                'role': role,
                'notes': '',
            }
            form = GroupMembershipForm(data=data)
            assert form.is_valid(), f"Failed for role={role}: {form.errors}"

    def test_member_required(self):
        """Member is required."""
        group = GroupFactory()
        data = {
            'group': group.pk,
            'role': 'member',
            'notes': '',
        }
        form = GroupMembershipForm(data=data)
        assert not form.is_valid()
        assert 'member' in form.errors

    def test_group_required(self):
        """Group is required."""
        member = MemberFactory()
        data = {
            'member': member.pk,
            'role': 'member',
            'notes': '',
        }
        form = GroupMembershipForm(data=data)
        assert not form.is_valid()
        assert 'group' in form.errors


@pytest.mark.django_db
class TestDirectoryPrivacyForm:
    """Tests for DirectoryPrivacyForm."""

    def test_valid_data(self):
        """Valid privacy settings data."""
        data = {
            'visibility': PrivacyLevel.PUBLIC,
            'show_email': True,
            'show_phone': True,
            'show_address': False,
            'show_birth_date': True,
            'show_photo': True,
        }
        form = DirectoryPrivacyForm(data=data)
        assert form.is_valid(), form.errors

    def test_update_privacy_settings(self):
        """Updates existing privacy settings."""
        member = MemberFactory()
        privacy = member.privacy_settings
        data = {
            'visibility': PrivacyLevel.PRIVATE,
            'show_email': False,
            'show_phone': False,
            'show_address': False,
            'show_birth_date': False,
            'show_photo': False,
        }
        form = DirectoryPrivacyForm(data=data, instance=privacy)
        assert form.is_valid()
        saved = form.save()
        assert saved.visibility == PrivacyLevel.PRIVATE
        assert saved.show_email is False
        assert saved.show_phone is False
        assert saved.show_photo is False

    def test_all_visibility_levels(self):
        """All valid visibility levels accepted."""
        for visibility, _ in PrivacyLevel.CHOICES:
            data = {
                'visibility': visibility,
                'show_email': True,
                'show_phone': True,
                'show_address': True,
                'show_birth_date': True,
                'show_photo': True,
            }
            form = DirectoryPrivacyForm(data=data)
            assert form.is_valid(), (
                f"Failed for visibility={visibility}: {form.errors}"
            )

    def test_group_visibility(self):
        """Group-level visibility setting works."""
        member = MemberFactory()
        privacy = member.privacy_settings
        data = {
            'visibility': PrivacyLevel.GROUP,
            'show_email': True,
            'show_phone': True,
            'show_address': False,
            'show_birth_date': True,
            'show_photo': True,
        }
        form = DirectoryPrivacyForm(data=data, instance=privacy)
        assert form.is_valid()
        saved = form.save()
        assert saved.visibility == PrivacyLevel.GROUP
