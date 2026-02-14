"""Tests for Custom Fields model and views."""
import pytest

from apps.core.constants import Roles, CustomFieldType
from apps.members.models import CustomField, CustomFieldValue

from .factories import (
    UserFactory,
    MemberFactory,
    AdminMemberFactory,
    PastorFactory,
    CustomFieldFactory,
    CustomFieldValueFactory,
)


@pytest.mark.django_db
class TestCustomFieldModel:
    """Tests for CustomField model."""

    def test_create_custom_field(self):
        """CustomField creation with required fields."""
        field = CustomFieldFactory()
        assert field.id is not None
        assert field.name
        assert field.field_type == CustomFieldType.TEXT

    def test_custom_field_ordering(self):
        """Custom fields ordered by 'order' field."""
        f2 = CustomFieldFactory(order=2, name='Second')
        f1 = CustomFieldFactory(order=1, name='First')
        fields = list(CustomField.objects.all())
        assert fields[0] == f1
        assert fields[1] == f2


@pytest.mark.django_db
class TestCustomFieldValueModel:
    """Tests for CustomFieldValue model."""

    def test_create_value(self):
        """CustomFieldValue creation."""
        value = CustomFieldValueFactory()
        assert value.id is not None
        assert value.member is not None
        assert value.custom_field is not None
        assert value.value

    def test_unique_member_field(self):
        """Each member can have only one value per custom field."""
        member = MemberFactory()
        field = CustomFieldFactory()
        CustomFieldValueFactory(member=member, custom_field=field)
        with pytest.raises(Exception):
            CustomFieldValueFactory(member=member, custom_field=field)


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'custom_field_list.html',
        'custom_field_form.html',
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
def staff_user():
    """Staff member (non-admin) with linked user account."""
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
class TestCustomFieldViews:
    """Tests for custom field views."""

    def test_list_admin(self, client, admin_user):
        """Admin can view custom field list."""
        user, member = admin_user
        CustomFieldFactory()
        client.force_login(user)
        response = client.get('/members/custom-fields/')
        assert response.status_code == 200

    def test_list_denied_staff(self, client, staff_user):
        """Non-admin staff redirected from custom fields."""
        user, member = staff_user
        client.force_login(user)
        response = client.get('/members/custom-fields/')
        assert response.status_code == 302

    def test_list_denied_regular(self, client, regular_user):
        """Regular member redirected from custom fields."""
        user, member = regular_user
        client.force_login(user)
        response = client.get('/members/custom-fields/')
        assert response.status_code == 302

    def test_create_get(self, client, admin_user):
        """Admin can access creation form."""
        user, member = admin_user
        client.force_login(user)
        response = client.get('/members/custom-fields/create/')
        assert response.status_code == 200

    def test_create_post(self, client, admin_user):
        """Admin can create a custom field."""
        user, member = admin_user
        client.force_login(user)
        response = client.post('/members/custom-fields/create/', data={
            'name': 'Test Field',
            'field_type': CustomFieldType.TEXT,
            'is_required': False,
            'order': 1,
        })
        assert response.status_code == 302
        assert CustomField.objects.filter(name='Test Field').exists()

    def test_edit_get(self, client, admin_user):
        """Admin can access edit form."""
        user, member = admin_user
        field = CustomFieldFactory()
        client.force_login(user)
        response = client.get(f'/members/custom-fields/{field.pk}/edit/')
        assert response.status_code == 200

    def test_edit_post(self, client, admin_user):
        """Admin can edit a custom field."""
        user, member = admin_user
        field = CustomFieldFactory(name='Original')
        client.force_login(user)
        response = client.post(f'/members/custom-fields/{field.pk}/edit/', data={
            'name': 'Updated',
            'field_type': field.field_type,
            'is_required': False,
            'order': field.order,
        })
        assert response.status_code == 302
        field.refresh_from_db()
        assert field.name == 'Updated'

    def test_delete_post(self, client, admin_user):
        """Admin can soft-delete a custom field."""
        user, member = admin_user
        field = CustomFieldFactory()
        client.force_login(user)
        response = client.post(f'/members/custom-fields/{field.pk}/delete/')
        assert response.status_code == 302
        field.refresh_from_db()
        assert field.is_active is False
