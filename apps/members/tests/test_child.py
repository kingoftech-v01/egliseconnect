"""Tests for Child model and views."""
import pytest
from datetime import date, timedelta

from apps.core.constants import Roles
from apps.members.models import Child

from .factories import (
    UserFactory,
    MemberFactory,
    MemberWithUserFactory,
    PastorFactory,
    AdminMemberFactory,
    FamilyFactory,
    ChildFactory,
)


@pytest.mark.django_db
class TestChildModel:
    """Tests for Child model."""

    def test_create_child(self):
        """Child creation with required fields."""
        child = ChildFactory()
        assert child.id is not None
        assert child.first_name
        assert child.last_name

    def test_child_full_name(self):
        """full_name combines first and last name."""
        child = ChildFactory(first_name='Marie', last_name='Dupont')
        assert child.full_name == 'Marie Dupont'

    def test_child_age(self):
        """age calculated from date_of_birth."""
        today = date.today()
        birth = today.replace(year=today.year - 5)
        child = ChildFactory(date_of_birth=birth)
        assert child.age == 5

    def test_child_age_none_without_birthdate(self):
        """age returns None when date_of_birth not set."""
        child = ChildFactory(date_of_birth=None)
        assert child.age is None

    def test_child_str(self):
        """String representation."""
        child = ChildFactory(first_name='Paul', last_name='Martin')
        assert str(child) == 'Paul Martin'

    def test_child_family_relation(self):
        """Child linked to family."""
        family = FamilyFactory()
        child = ChildFactory(family=family)
        assert child.family == family
        assert child in family.children.all()

    def test_child_ordering(self):
        """Children ordered by last_name, first_name."""
        family = FamilyFactory()
        c2 = ChildFactory(family=family, last_name='Zeta', first_name='Alice')
        c1 = ChildFactory(family=family, last_name='Alpha', first_name='Bob')
        children = list(Child.objects.filter(family=family))
        assert children[0] == c1
        assert children[1] == c2


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'child_list.html',
        'child_form.html',
        'child_delete.html',
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
def staff_user():
    """Staff member with linked user account."""
    user = UserFactory()
    member = PastorFactory(user=user)
    return user, member


@pytest.fixture
def regular_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.mark.django_db
class TestChildViews:
    """Tests for child CRUD views."""

    def test_child_list(self, client, staff_user):
        """Staff can view child list for a family."""
        user, member = staff_user
        family = FamilyFactory()
        ChildFactory(family=family)
        ChildFactory(family=family)
        client.force_login(user)
        response = client.get(f'/members/families/{family.pk}/children/')
        assert response.status_code == 200

    def test_child_create_get(self, client, staff_user):
        """Staff can access child creation form."""
        user, member = staff_user
        family = FamilyFactory()
        client.force_login(user)
        response = client.get(f'/members/families/{family.pk}/children/create/')
        assert response.status_code == 200

    def test_child_create_post(self, client, staff_user):
        """Staff can create a child."""
        user, member = staff_user
        family = FamilyFactory()
        client.force_login(user)
        response = client.post(
            f'/members/families/{family.pk}/children/create/',
            data={'first_name': 'TestChild', 'last_name': 'Family'},
        )
        assert response.status_code == 302
        assert Child.objects.filter(first_name='TestChild').exists()

    def test_child_create_by_family_member(self, client, regular_user):
        """Family member can create child in their own family."""
        user, member = regular_user
        family = FamilyFactory()
        member.family = family
        member.save()
        client.force_login(user)
        response = client.post(
            f'/members/families/{family.pk}/children/create/',
            data={'first_name': 'MyChild', 'last_name': 'Test'},
        )
        assert response.status_code == 302
        assert Child.objects.filter(first_name='MyChild').exists()

    def test_child_create_denied_for_other_family(self, client, regular_user):
        """Non-family member cannot create child in another family."""
        user, member = regular_user
        family = FamilyFactory()
        client.force_login(user)
        response = client.post(
            f'/members/families/{family.pk}/children/create/',
            data={'first_name': 'Blocked', 'last_name': 'Child'},
        )
        assert response.status_code == 302
        assert not Child.objects.filter(first_name='Blocked').exists()

    def test_child_edit(self, client, staff_user):
        """Staff can edit a child."""
        user, member = staff_user
        child = ChildFactory(first_name='Original')
        client.force_login(user)
        response = client.post(
            f'/members/children/{child.pk}/edit/',
            data={'first_name': 'Updated', 'last_name': child.last_name},
        )
        assert response.status_code == 302
        child.refresh_from_db()
        assert child.first_name == 'Updated'

    def test_child_delete_get(self, client, staff_user):
        """Staff can access delete confirmation."""
        user, member = staff_user
        child = ChildFactory()
        client.force_login(user)
        response = client.get(f'/members/children/{child.pk}/delete/')
        assert response.status_code == 200

    def test_child_delete_post(self, client, staff_user):
        """Staff can delete a child."""
        user, member = staff_user
        child = ChildFactory()
        client.force_login(user)
        response = client.post(f'/members/children/{child.pk}/delete/')
        assert response.status_code == 302
        assert not Child.objects.filter(pk=child.pk).exists()
