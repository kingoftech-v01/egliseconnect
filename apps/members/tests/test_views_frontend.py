"""Tests for members frontend views."""
import pytest
from unittest.mock import patch
from django.http import HttpResponse

from apps.core.constants import Roles, FamilyStatus, Province, GroupType, PrivacyLevel
from apps.members.models import Member, Family, Group, GroupMembership, DirectoryPrivacy

from .factories import (
    UserFactory,
    MemberFactory,
    MemberWithUserFactory,
    PastorFactory,
    AdminMemberFactory,
    GroupLeaderFactory,
    FamilyFactory,
    GroupFactory,
    GroupMembershipFactory,
)


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs for frontend view rendering."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'member_list.html',
        'member_detail.html',
        'member_form.html',
        'birthday_list.html',
        'directory.html',
        'privacy_settings.html',
        'group_list.html',
        'group_detail.html',
        'family_detail.html',
    ]
    for name in template_names:
        (members_dir / name).write_text('{{ page_title|default:"test" }}')
    settings.TEMPLATES = [
        {
            **settings.TEMPLATES[0],
            'DIRS': [str(tmp_path)] + [
                str(d) for d in settings.TEMPLATES[0].get('DIRS', [])
            ],
        }
    ]


@pytest.fixture
def regular_user_with_member():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.fixture
def pastor_user_with_member():
    """Pastor with linked user account."""
    user = UserFactory()
    member = PastorFactory(user=user)
    return user, member


@pytest.fixture
def admin_user_with_member():
    """Admin with linked user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def group_leader_user_with_member():
    """Group leader with linked user account."""
    user = UserFactory()
    member = GroupLeaderFactory(user=user)
    return user, member


@pytest.fixture
def staff_user():
    """Django staff user without member profile."""
    user = UserFactory(is_staff=True)
    return user


@pytest.mark.django_db
class TestMemberListView:
    """Tests for member_list view."""

    url = '/members/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_view_list(self, client, pastor_user_with_member):
        """Pastors can access the member list."""
        user, member = pastor_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_view_list(self, client, admin_user_with_member):
        """Admins can access the member list."""
        user, member = admin_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_redirected(self, client, regular_user_with_member):
        """Regular members are redirected to their own profile."""
        user, member = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert str(member.pk) in response.url

    def test_user_without_profile_not_staff_redirected(self, client):
        """User without member profile and not staff is redirected."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == '/'

    def test_staff_user_without_profile_can_view(self, client, staff_user):
        """Django staff users without member profile can view list."""
        client.force_login(staff_user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_search_filtering(self, client, pastor_user_with_member):
        """Search query filters members."""
        user, _ = pastor_user_with_member
        client.force_login(user)
        MemberFactory(first_name='Unique', last_name='Searchable')
        MemberFactory(first_name='Other', last_name='Person')

        response = client.get(self.url, {'search': 'Searchable'})
        assert response.status_code == 200
        assert response.context['search'] == 'Searchable'

    def test_role_filtering(self, client, pastor_user_with_member):
        """Role filter works."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url, {'role': Roles.PASTOR})
        assert response.status_code == 200
        assert response.context['role_filter'] == Roles.PASTOR

    def test_family_status_filtering(self, client, pastor_user_with_member):
        """Family status filter works."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url, {'family_status': FamilyStatus.MARRIED})
        assert response.status_code == 200
        assert response.context['family_status_filter'] == FamilyStatus.MARRIED

    def test_group_filtering(self, client, pastor_user_with_member):
        """Group filter works."""
        user, _ = pastor_user_with_member
        client.force_login(user)
        group = GroupFactory()

        response = client.get(self.url, {'group': str(group.pk)})
        assert response.status_code == 200

    def test_sort_by_valid_field(self, client, pastor_user_with_member):
        """Sorting by a valid field works."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url, {'sort': '-created_at'})
        assert response.status_code == 200
        assert response.context['sort_by'] == '-created_at'

    def test_sort_by_invalid_field_defaults(self, client, pastor_user_with_member):
        """Invalid sort field defaults to last_name."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url, {'sort': 'invalid_field'})
        assert response.status_code == 200
        assert response.context['sort_by'] == 'last_name'

    def test_sort_descending(self, client, pastor_user_with_member):
        """Sort with descending prefix works."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url, {'sort': '-last_name'})
        assert response.status_code == 200
        assert response.context['sort_by'] == '-last_name'

    def test_pagination(self, client, pastor_user_with_member):
        """Pagination of results works."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url, {'page': 1})
        assert response.status_code == 200
        assert 'members' in response.context

    def test_context_data(self, client, pastor_user_with_member):
        """Proper context data is passed."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        response = client.get(self.url)
        assert 'members' in response.context
        assert 'total_count' in response.context
        assert 'form' in response.context
        assert 'sort_by' in response.context
        assert 'page_title' in response.context

    def test_group_leader_redirected(self, client, group_leader_user_with_member):
        """Group leaders are redirected from member list."""
        user, member = group_leader_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert str(member.pk) in response.url


@pytest.mark.django_db
class TestMemberDetailView:
    """Tests for member_detail view."""

    def _url(self, pk):
        return f'/members/{pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        member = MemberFactory()
        response = client.get(self._url(member.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_own_profile_viewable(self, client, regular_user_with_member):
        """Member can view their own profile."""
        user, member = regular_user_with_member
        client.force_login(user)
        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert response.context['member'] == member
        assert response.context['can_edit'] is True

    def test_staff_can_view_any_profile(self, client, staff_user):
        """Django staff can view any member profile."""
        client.force_login(staff_user)
        member = MemberFactory()
        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert response.context['can_edit'] is True

    def test_pastor_can_view_any_profile(self, client, pastor_user_with_member):
        """Pastors can view any member profile."""
        user, _ = pastor_user_with_member
        client.force_login(user)
        other_member = MemberFactory()
        response = client.get(self._url(other_member.pk))
        assert response.status_code == 200
        assert response.context['can_edit'] is True

    def test_admin_can_view_any_profile(self, client, admin_user_with_member):
        """Admins can view any member profile."""
        user, _ = admin_user_with_member
        client.force_login(user)
        other_member = MemberFactory()
        response = client.get(self._url(other_member.pk))
        assert response.status_code == 200
        assert response.context['can_edit'] is True

    def test_group_leader_can_view_group_member(self, client, group_leader_user_with_member):
        """Group leader can view profile of member in their group."""
        user, leader_member = group_leader_user_with_member
        client.force_login(user)

        group = GroupFactory(leader=leader_member)
        target_member = MemberFactory()
        GroupMembershipFactory(member=target_member, group=group)

        response = client.get(self._url(target_member.pk))
        assert response.status_code == 200
        assert response.context['can_edit'] is False

    def test_group_leader_cannot_view_non_group_member(
        self, client, group_leader_user_with_member
    ):
        """Group leader cannot view profile of member not in their group."""
        user, leader_member = group_leader_user_with_member
        client.force_login(user)

        non_group_member = MemberFactory()

        response = client.get(self._url(non_group_member.pk))
        assert response.status_code == 302
        assert response.url == '/'

    def test_regular_member_cannot_view_other(self, client, regular_user_with_member):
        """Regular member cannot view other member profiles."""
        user, _ = regular_user_with_member
        client.force_login(user)
        other_member = MemberFactory()

        response = client.get(self._url(other_member.pk))
        assert response.status_code == 302
        assert response.url == '/'

    def test_nonexistent_member_404(self, client, pastor_user_with_member):
        """404 for non-existent member."""
        import uuid
        user, _ = pastor_user_with_member
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404

    def test_context_includes_groups(self, client, regular_user_with_member):
        """Context includes member groups."""
        user, member = regular_user_with_member
        client.force_login(user)
        group = GroupFactory()
        GroupMembershipFactory(member=member, group=group)

        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert 'groups' in response.context

    def test_context_includes_family_members(self, client, regular_user_with_member):
        """Context includes family members when member has a family."""
        user, member = regular_user_with_member
        family = FamilyFactory()
        member.family = family
        member.save(update_fields=['family'])
        sibling = MemberFactory(family=family)

        client.force_login(user)
        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        family_members = list(response.context['family_members'])
        assert sibling in family_members

    def test_context_no_family(self, client, regular_user_with_member):
        """Context when member has no family."""
        user, member = regular_user_with_member
        member.family = None
        member.save(update_fields=['family'])

        client.force_login(user)
        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert list(response.context['family_members']) == []

    def test_user_without_profile_not_staff_redirected(self, client):
        """User without member_profile and not staff is redirected."""
        user = UserFactory()
        client.force_login(user)
        member = MemberFactory()
        response = client.get(self._url(member.pk))
        assert response.status_code == 302
        assert response.url == '/'


@pytest.mark.django_db
class TestMemberCreateView:
    """Tests for member_create view (public registration)."""

    url = '/members/register/'

    def test_get_form_anonymous(self, client):
        """GET returns form even for anonymous users (public registration)."""
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_get_form_authenticated(self, client, regular_user_with_member):
        """GET works for authenticated users too."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_post_valid_without_account(self, client):
        """POST creates member without user account."""
        data = {
            'first_name': 'Marie',
            'last_name': 'Martin',
            'email': 'marie@example.com',
            'phone': '514-555-0123',
            'birth_date': '1990-01-15',
            'address': '123 Rue Test',
            'city': 'Montreal',
            'province': Province.QC,
            'postal_code': 'H1A 1A1',
            'family_status': FamilyStatus.SINGLE,
            'create_account': False,
        }
        response = client.post(self.url, data)
        assert response.status_code == 302
        member = Member.objects.get(first_name='Marie', last_name='Martin')
        assert member.user is None
        assert str(member.pk) in response.url

    def test_post_valid_with_account(self, client):
        """POST creates member with user account and logs in."""
        data = {
            'first_name': 'Pierre',
            'last_name': 'Tremblay',
            'email': 'pierre@example.com',
            'phone': '514-555-0456',
            'birth_date': '1985-06-20',
            'address': '456 Rue Test',
            'city': 'Quebec',
            'province': Province.QC,
            'postal_code': 'G1A 2B3',
            'family_status': FamilyStatus.MARRIED,
            'create_account': True,
            'password': 'S3cur3P@ssW0rd!',
            'password_confirm': 'S3cur3P@ssW0rd!',
        }
        response = client.post(self.url, data)
        assert response.status_code == 302
        member = Member.objects.get(first_name='Pierre', last_name='Tremblay')
        assert member.user is not None
        assert member.user.email == 'pierre@example.com'
        assert str(member.pk) in response.url

    def test_post_invalid_data(self, client):
        """POST with invalid data re-renders form."""
        data = {
            'first_name': '',
            'last_name': '',
            'province': Province.QC,
            'family_status': FamilyStatus.SINGLE,
        }
        response = client.post(self.url, data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_post_minimal_data(self, client):
        """POST with minimal required data succeeds."""
        data = {
            'first_name': 'Test',
            'last_name': 'Minimal',
            'province': Province.QC,
            'family_status': FamilyStatus.SINGLE,
        }
        response = client.post(self.url, data)
        assert response.status_code == 302
        assert Member.objects.filter(
            first_name='Test', last_name='Minimal'
        ).exists()

    def test_context_data(self, client):
        """Context includes form title and submit text."""
        response = client.get(self.url)
        assert response.context['form_title'] is not None
        assert response.context['submit_text'] is not None
        assert response.context['page_title'] is not None


@pytest.mark.django_db
class TestMemberUpdateView:
    """Tests for member_update view."""

    def _url(self, pk):
        return f'/members/{pk}/edit/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        member = MemberFactory()
        response = client.get(self._url(member.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_own_profile_editable(self, client, regular_user_with_member):
        """Member can edit their own profile (uses profile form)."""
        user, member = regular_user_with_member
        client.force_login(user)
        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert 'role' not in response.context['form'].fields

    def test_staff_can_edit_any(self, client, staff_user):
        """Django staff can edit any member (uses admin form)."""
        client.force_login(staff_user)
        member = MemberFactory()
        response = client.get(self._url(member.pk))
        assert response.status_code == 200
        assert 'role' in response.context['form'].fields

    def test_pastor_can_edit_any(self, client, pastor_user_with_member):
        """Pastors can edit any member (uses admin form)."""
        user, _ = pastor_user_with_member
        client.force_login(user)
        other_member = MemberFactory()
        response = client.get(self._url(other_member.pk))
        assert response.status_code == 200
        assert 'role' in response.context['form'].fields

    def test_admin_can_edit_any(self, client, admin_user_with_member):
        """Admins can edit any member (uses admin form)."""
        user, _ = admin_user_with_member
        client.force_login(user)
        other_member = MemberFactory()
        response = client.get(self._url(other_member.pk))
        assert response.status_code == 200
        assert 'role' in response.context['form'].fields

    def test_regular_member_cannot_edit_other(self, client, regular_user_with_member):
        """Regular member cannot edit other member profiles."""
        user, _ = regular_user_with_member
        client.force_login(user)
        other_member = MemberFactory()

        response = client.get(self._url(other_member.pk))
        assert response.status_code == 302
        assert str(other_member.pk) in response.url

    def test_post_valid_update_own_profile(self, client):
        """POST updates own profile."""
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, phone='514-555-0200')
        client.force_login(user)
        data = {
            'first_name': 'Updated',
            'last_name': member.last_name,
            'email': member.email,
            'phone': '514-555-0200',
            'phone_secondary': '',
            'birth_date': member.birth_date or '',
            'address': member.address,
            'city': member.city,
            'province': member.province,
            'postal_code': member.postal_code,
            'family_status': member.family_status,
        }
        response = client.post(self._url(member.pk), data)
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.first_name == 'Updated'

    def test_post_valid_update_as_admin(self, client, pastor_user_with_member):
        """POST updates member as admin with admin fields."""
        user, _ = pastor_user_with_member
        client.force_login(user)
        member = MemberFactory(phone='514-555-0100')
        data = {
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'phone': '514-555-0100',
            'phone_secondary': '',
            'birth_date': member.birth_date or '',
            'address': member.address,
            'city': member.city,
            'province': member.province,
            'postal_code': member.postal_code,
            'role': Roles.VOLUNTEER,
            'family_status': member.family_status,
            'notes': 'Admin note',
            'is_active': True,
            'joined_date': '',
            'baptism_date': '',
        }
        response = client.post(self._url(member.pk), data)
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.role == Roles.VOLUNTEER
        assert member.notes == 'Admin note'

    def test_post_invalid_data(self, client, regular_user_with_member):
        """POST with invalid data re-renders form."""
        user, member = regular_user_with_member
        client.force_login(user)
        data = {
            'first_name': '',
            'last_name': '',
            'province': Province.QC,
            'family_status': FamilyStatus.SINGLE,
        }
        response = client.post(self._url(member.pk), data)
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_nonexistent_member_404(self, client, pastor_user_with_member):
        """404 for non-existent member."""
        import uuid
        user, _ = pastor_user_with_member
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404

    def test_context_data(self, client, regular_user_with_member):
        """Proper context data is passed."""
        user, member = regular_user_with_member
        client.force_login(user)
        response = client.get(self._url(member.pk))
        assert 'form' in response.context
        assert 'member' in response.context
        assert 'form_title' in response.context
        assert 'submit_text' in response.context
        assert response.context['member'] == member

    def test_group_leader_cannot_edit_other(self, client, group_leader_user_with_member):
        """Group leader cannot edit other members."""
        user, leader_member = group_leader_user_with_member
        client.force_login(user)
        other_member = MemberFactory()
        response = client.get(self._url(other_member.pk))
        assert response.status_code == 302

    def test_user_without_profile_not_staff_redirected(self, client):
        """User without member profile and not staff is redirected."""
        user = UserFactory()
        client.force_login(user)
        member = MemberFactory()
        response = client.get(self._url(member.pk))
        assert response.status_code == 302
        assert str(member.pk) in response.url


@pytest.mark.django_db
class TestBirthdayListView:
    """Tests for birthday_list view."""

    url = '/members/birthdays/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_default_period_is_week(self, client, regular_user_with_member):
        """Default period is 'week'."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context['period'] == 'week'

    def test_period_today(self, client, regular_user_with_member):
        """Birthdays today."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'today'})
        assert response.status_code == 200
        assert response.context['period'] == 'today'

    def test_period_week(self, client, regular_user_with_member):
        """Birthdays this week."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'week'})
        assert response.status_code == 200
        assert response.context['period'] == 'week'

    def test_period_month_default(self, client, regular_user_with_member):
        """Birthdays for current month (no specific month)."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'month'})
        assert response.status_code == 200
        assert response.context['period'] == 'month'
        assert response.context['selected_month'] is None

    def test_period_month_specific(self, client, regular_user_with_member):
        """Birthdays for a specific month."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'month', 'month': '6'})
        assert response.status_code == 200
        assert response.context['period'] == 'month'
        assert response.context['selected_month'] == '6'

    def test_period_month_invalid_string(self, client, regular_user_with_member):
        """Invalid month string falls back to current month."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'month', 'month': 'abc'})
        assert response.status_code == 200
        assert response.context['period'] == 'month'

    def test_period_month_out_of_range(self, client, regular_user_with_member):
        """Out-of-range month (>12) falls back to current month."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'month', 'month': '13'})
        assert response.status_code == 200
        assert response.context['period'] == 'month'

    def test_period_month_zero(self, client, regular_user_with_member):
        """Month=0 falls back to current month."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'period': 'month', 'month': '0'})
        assert response.status_code == 200
        assert response.context['period'] == 'month'

    def test_context_data(self, client, regular_user_with_member):
        """Proper context data."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert 'members' in response.context
        assert 'title' in response.context
        assert 'page_title' in response.context

    def test_all_valid_months(self, client, regular_user_with_member):
        """All 12 months are accepted."""
        user, _ = regular_user_with_member
        client.force_login(user)
        for month in range(1, 13):
            response = client.get(
                self.url, {'period': 'month', 'month': str(month)}
            )
            assert response.status_code == 200


@pytest.mark.django_db
class TestDirectoryView:
    """Tests for directory view."""

    url = '/members/directory/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_basic_access(self, client, regular_user_with_member):
        """Basic directory access."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'members' in response.context

    def test_search(self, client, regular_user_with_member):
        """Directory search functionality."""
        user, _ = regular_user_with_member
        client.force_login(user)
        MemberFactory(first_name='Unique', last_name='DirectoryTest')

        response = client.get(self.url, {'search': 'DirectoryTest'})
        assert response.status_code == 200
        assert response.context['search'] == 'DirectoryTest'

    def test_staff_role_sees_all(self, client, pastor_user_with_member):
        """Staff roles see all members regardless of privacy."""
        user, _ = pastor_user_with_member
        client.force_login(user)

        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(
            visibility=PrivacyLevel.PRIVATE
        )

        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_privacy_filtering(self, client, regular_user_with_member):
        """Regular members only see public/group profiles."""
        user, current_member = regular_user_with_member
        client.force_login(user)

        public_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=public_member).update(
            visibility=PrivacyLevel.PUBLIC
        )

        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(
            visibility=PrivacyLevel.PRIVATE
        )

        response = client.get(self.url)
        assert response.status_code == 200
        member_ids = [m.pk for m in response.context['members']]
        assert public_member.pk in member_ids
        assert private_member.pk not in member_ids

    def test_group_visibility(self, client, regular_user_with_member):
        """Members with group visibility are seen by group mates."""
        user, current_member = regular_user_with_member
        client.force_login(user)

        group = GroupFactory()
        GroupMembershipFactory(member=current_member, group=group)

        group_mate = MemberFactory()
        GroupMembershipFactory(member=group_mate, group=group)
        DirectoryPrivacy.objects.filter(member=group_mate).update(
            visibility=PrivacyLevel.GROUP
        )

        response = client.get(self.url)
        assert response.status_code == 200
        member_ids = [m.pk for m in response.context['members']]
        assert group_mate.pk in member_ids

    def test_staff_user_without_profile_sees_all(self, client, staff_user):
        """Django staff user without member profile sees all members."""
        client.force_login(staff_user)
        MemberFactory()
        response = client.get(self.url)
        assert response.status_code == 200

    def test_user_without_profile_not_staff_sees_public_only(self, client):
        """User without member profile and not staff sees only public."""
        user = UserFactory()
        client.force_login(user)

        public_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=public_member).update(
            visibility=PrivacyLevel.PUBLIC
        )

        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(
            visibility=PrivacyLevel.PRIVATE
        )

        response = client.get(self.url)
        assert response.status_code == 200
        member_ids = [m.pk for m in response.context['members']]
        assert public_member.pk in member_ids
        assert private_member.pk not in member_ids

    def test_self_always_visible(self, client, regular_user_with_member):
        """Current member always sees themselves in directory."""
        user, current_member = regular_user_with_member
        client.force_login(user)

        DirectoryPrivacy.objects.filter(member=current_member).update(
            visibility=PrivacyLevel.PRIVATE
        )

        response = client.get(self.url)
        assert response.status_code == 200
        member_ids = [m.pk for m in response.context['members']]
        assert current_member.pk in member_ids

    def test_context_data(self, client, regular_user_with_member):
        """Proper context data."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert 'members' in response.context
        assert 'search' in response.context
        assert 'total_count' in response.context
        assert 'page_title' in response.context

    def test_pagination(self, client, regular_user_with_member):
        """Directory pagination."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url, {'page': '1'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestPrivacySettingsView:
    """Tests for privacy_settings view."""

    url = '/members/privacy-settings/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_no_member_profile_redirects(self, client):
        """User without member profile is redirected to create."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert 'register' in response.url

    def test_get_with_existing_settings(self, client, regular_user_with_member):
        """GET with existing privacy settings."""
        user, member = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_get_creates_default_settings(self, client):
        """GET auto-creates default privacy settings if missing."""
        user = UserFactory()
        member = MemberFactory(user=user)
        DirectoryPrivacy.objects.filter(member=member).delete()

        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert DirectoryPrivacy.objects.filter(member=member).exists()

    def test_post_valid_update(self, client, regular_user_with_member):
        """POST updates privacy settings."""
        user, member = regular_user_with_member
        client.force_login(user)
        data = {
            'visibility': PrivacyLevel.PRIVATE,
            'show_email': False,
            'show_phone': False,
            'show_address': False,
            'show_birth_date': False,
            'show_photo': False,
        }
        response = client.post(self.url, data)
        assert response.status_code == 302

        privacy = member.privacy_settings
        privacy.refresh_from_db()
        assert privacy.visibility == PrivacyLevel.PRIVATE
        assert privacy.show_email is False

    def test_post_invalid_data(self, client, regular_user_with_member):
        """POST with invalid data re-renders form."""
        user, _ = regular_user_with_member
        client.force_login(user)
        data = {
            'visibility': 'invalid_choice',
        }
        response = client.post(self.url, data)
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_redirects_to_profile(self, client, regular_user_with_member):
        """Successful POST redirects to member detail."""
        user, member = regular_user_with_member
        client.force_login(user)
        data = {
            'visibility': PrivacyLevel.PUBLIC,
            'show_email': True,
            'show_phone': True,
            'show_address': True,
            'show_birth_date': True,
            'show_photo': True,
        }
        response = client.post(self.url, data)
        assert response.status_code == 302
        assert str(member.pk) in response.url


@pytest.mark.django_db
class TestGroupListView:
    """Tests for group_list view."""

    url = '/members/groups/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_basic_list(self, client, regular_user_with_member):
        """Basic group listing."""
        user, _ = regular_user_with_member
        client.force_login(user)
        GroupFactory.create_batch(3)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'groups' in response.context

    def test_filter_by_type(self, client, regular_user_with_member):
        """Filtering groups by type."""
        user, _ = regular_user_with_member
        client.force_login(user)
        GroupFactory(group_type=GroupType.CELL)
        GroupFactory(group_type=GroupType.MINISTRY)

        response = client.get(self.url, {'type': GroupType.CELL})
        assert response.status_code == 200
        assert response.context['group_type_filter'] == GroupType.CELL
        for group in response.context['groups']:
            assert group.group_type == GroupType.CELL

    def test_no_filter(self, client, regular_user_with_member):
        """Listing without type filter shows all active groups."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context['group_type_filter'] is None

    def test_context_data(self, client, regular_user_with_member):
        """Proper context data."""
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self.url)
        assert 'groups' in response.context
        assert 'group_type_filter' in response.context
        assert 'page_title' in response.context


@pytest.mark.django_db
class TestGroupDetailView:
    """Tests for group_detail view."""

    def _url(self, pk):
        return f'/members/groups/{pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        group = GroupFactory()
        response = client.get(self._url(group.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_view_group(self, client, regular_user_with_member):
        """Viewing group details."""
        user, _ = regular_user_with_member
        client.force_login(user)
        group = GroupFactory()
        response = client.get(self._url(group.pk))
        assert response.status_code == 200
        assert response.context['group'] == group

    def test_leader_flag_true(self, client, group_leader_user_with_member):
        """is_leader flag is True when current user is the leader."""
        user, leader_member = group_leader_user_with_member
        client.force_login(user)
        group = GroupFactory(leader=leader_member)
        response = client.get(self._url(group.pk))
        assert response.status_code == 200
        assert response.context['is_leader'] is True

    def test_leader_flag_false(self, client, regular_user_with_member):
        """is_leader flag is False for non-leader members."""
        user, _ = regular_user_with_member
        client.force_login(user)
        group = GroupFactory()
        response = client.get(self._url(group.pk))
        assert response.status_code == 200
        assert response.context['is_leader'] is False

    def test_nonexistent_group_404(self, client, regular_user_with_member):
        """404 for non-existent group."""
        import uuid
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404

    def test_context_includes_memberships(self, client, regular_user_with_member):
        """Context includes group memberships."""
        user, _ = regular_user_with_member
        client.force_login(user)
        group = GroupFactory()
        member = MemberFactory()
        GroupMembershipFactory(member=member, group=group)
        response = client.get(self._url(group.pk))
        assert response.status_code == 200
        assert 'memberships' in response.context

    def test_context_data(self, client, regular_user_with_member):
        """Proper context data."""
        user, _ = regular_user_with_member
        client.force_login(user)
        group = GroupFactory()
        response = client.get(self._url(group.pk))
        assert 'group' in response.context
        assert 'memberships' in response.context
        assert 'is_leader' in response.context
        assert 'page_title' in response.context

    def test_user_without_profile_not_leader(self, client, staff_user):
        """User without member profile has is_leader=False."""
        client.force_login(staff_user)
        group = GroupFactory()
        response = client.get(self._url(group.pk))
        assert response.status_code == 200
        assert response.context['is_leader'] is False


@pytest.mark.django_db
class TestFamilyDetailView:
    """Tests for family_detail view."""

    def _url(self, pk):
        return f'/members/families/{pk}/'

    def test_login_required(self, client):
        """Anonymous users are redirected to login."""
        family = FamilyFactory()
        response = client.get(self._url(family.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_view_family(self, client, regular_user_with_member):
        """Viewing family details."""
        user, _ = regular_user_with_member
        client.force_login(user)
        family = FamilyFactory()
        response = client.get(self._url(family.pk))
        assert response.status_code == 200
        assert response.context['family'] == family

    def test_family_member_flag_true(self, client, regular_user_with_member):
        """is_family_member flag when user belongs to this family."""
        user, member = regular_user_with_member
        family = FamilyFactory()
        member.family = family
        member.save(update_fields=['family'])

        client.force_login(user)
        response = client.get(self._url(family.pk))
        assert response.status_code == 200
        assert response.context['is_family_member'] is True

    def test_family_member_flag_false(self, client, regular_user_with_member):
        """is_family_member flag when user does not belong to this family."""
        user, _ = regular_user_with_member
        client.force_login(user)
        family = FamilyFactory()
        response = client.get(self._url(family.pk))
        assert response.status_code == 200
        assert response.context['is_family_member'] is False

    def test_nonexistent_family_404(self, client, regular_user_with_member):
        """404 for non-existent family."""
        import uuid
        user, _ = regular_user_with_member
        client.force_login(user)
        response = client.get(self._url(uuid.uuid4()))
        assert response.status_code == 404

    def test_context_includes_members(self, client, regular_user_with_member):
        """Context includes family members."""
        user, _ = regular_user_with_member
        client.force_login(user)
        family = FamilyFactory()
        MemberFactory(family=family)
        MemberFactory(family=family)

        response = client.get(self._url(family.pk))
        assert response.status_code == 200
        assert 'members' in response.context

    def test_context_data(self, client, regular_user_with_member):
        """Proper context data."""
        user, _ = regular_user_with_member
        client.force_login(user)
        family = FamilyFactory()
        response = client.get(self._url(family.pk))
        assert 'family' in response.context
        assert 'members' in response.context
        assert 'is_family_member' in response.context
        assert 'page_title' in response.context

    def test_user_without_profile_not_family_member(self, client, staff_user):
        """User without member profile has is_family_member=False."""
        client.force_login(staff_user)
        family = FamilyFactory()
        response = client.get(self._url(family.pk))
        assert response.status_code == 200
        assert response.context['is_family_member'] is False
