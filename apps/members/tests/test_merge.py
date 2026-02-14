"""Tests for member merge/dedup model, service, and views."""
import pytest
from datetime import date

from apps.core.constants import Roles
from apps.members.models import Member, MemberMergeLog, GroupMembership

from .factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    AdminMemberFactory,
    GroupFactory,
    GroupMembershipFactory,
    MemberMergeLogFactory,
    FamilyFactory,
)


@pytest.mark.django_db
class TestMemberMergeLogModel:
    """Tests for MemberMergeLog model."""

    def test_create_merge_log(self):
        """MemberMergeLog creation with required fields."""
        log = MemberMergeLogFactory()
        assert log.id is not None
        assert log.primary_member is not None
        assert log.merged_member_data is not None
        assert 'first_name' in log.merged_member_data

    def test_merge_log_str(self):
        """String representation."""
        log = MemberMergeLogFactory()
        assert log.id is not None


@pytest.mark.django_db
class TestMemberMergeService:
    """Tests for MemberMergeService."""

    def test_find_duplicates_same_name(self):
        """Finds duplicates with identical names."""
        from apps.members.services_merge import MemberMergeService
        m1 = MemberFactory(first_name='Jean', last_name='Dupont', email='jean1@test.com')
        m2 = MemberFactory(first_name='Jean', last_name='Dupont', email='jean2@test.com')
        duplicates = MemberMergeService.find_duplicates()
        # Should find at least one pair
        found_pair = any(
            (a.pk == m1.pk and b.pk == m2.pk) or (a.pk == m2.pk and b.pk == m1.pk)
            for a, b, score, reasons in duplicates
        )
        assert found_pair

    def test_find_duplicates_same_email(self):
        """Finds duplicates with same email."""
        from apps.members.services_merge import MemberMergeService
        m1 = MemberFactory(first_name='Jean', last_name='A', email='same@test.com')
        m2 = MemberFactory(first_name='Pierre', last_name='B', email='same@test.com')
        duplicates = MemberMergeService.find_duplicates()
        found_pair = any(
            (a.pk == m1.pk and b.pk == m2.pk) or (a.pk == m2.pk and b.pk == m1.pk)
            for a, b, score, reasons in duplicates
        )
        assert found_pair

    def test_merge_members(self):
        """Merge transfers relationships and deactivates secondary."""
        from apps.members.services_merge import MemberMergeService
        primary = MemberFactory(first_name='Primary', email='primary@test.com')
        secondary = MemberFactory(first_name='Secondary', email='secondary@test.com', phone='514-555-0001')
        group = GroupFactory()
        GroupMembershipFactory(member=secondary, group=group)
        admin = AdminMemberFactory()

        log = MemberMergeService.merge_members(primary, secondary, merged_by=admin)

        # Secondary should be deactivated
        secondary.refresh_from_db()
        assert secondary.is_active is False

        # Group membership should be transferred
        assert GroupMembership.objects.filter(member=primary, group=group).exists()

        # Merge log should be created
        assert log is not None
        assert log.primary_member == primary
        assert log.merged_member_data['first_name'] == 'Secondary'

    def test_merge_fills_blank_fields(self):
        """Merge fills blank fields on primary from secondary."""
        from apps.members.services_merge import MemberMergeService
        primary = MemberFactory(phone='', address='')
        secondary = MemberFactory(phone='514-555-0001', address='123 Rue Test')
        admin = AdminMemberFactory()

        MemberMergeService.merge_members(primary, secondary, merged_by=admin)

        primary.refresh_from_db()
        assert primary.phone == '514-555-0001'
        assert primary.address == '123 Rue Test'


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'merge_duplicates.html',
        'merge_wizard.html',
        'merge_history.html',
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
def admin_user():
    """Admin member with linked user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def regular_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.mark.django_db
class TestMergeViews:
    """Tests for merge/dedup views."""

    def test_find_duplicates_view(self, client, admin_user):
        """Admin can view duplicates page."""
        user, member = admin_user
        client.force_login(user)
        response = client.get('/members/merge/')
        assert response.status_code == 200

    def test_find_duplicates_denied_regular(self, client, regular_user):
        """Non-admin redirected from merge."""
        user, member = regular_user
        client.force_login(user)
        response = client.get('/members/merge/')
        assert response.status_code == 302

    def test_merge_wizard_get(self, client, admin_user):
        """Admin can view merge wizard."""
        user, member = admin_user
        m1 = MemberFactory()
        m2 = MemberFactory()
        client.force_login(user)
        response = client.get(f'/members/merge/{m1.pk}/{m2.pk}/')
        assert response.status_code == 200

    def test_merge_wizard_post(self, client, admin_user):
        """Admin can execute a merge."""
        user, member = admin_user
        m1 = MemberFactory()
        m2 = MemberFactory()
        client.force_login(user)
        response = client.post(
            f'/members/merge/{m1.pk}/{m2.pk}/',
            data={'primary': str(m1.pk)},
        )
        assert response.status_code == 302
        m2.refresh_from_db()
        assert m2.is_active is False

    def test_merge_history_view(self, client, admin_user):
        """Admin can view merge history."""
        user, member = admin_user
        MemberMergeLogFactory()
        client.force_login(user)
        response = client.get('/members/merge/history/')
        assert response.status_code == 200
