"""Tests for help request category CRUD frontend views."""
import pytest

from apps.help_requests.models import HelpRequestCategory
from apps.members.tests.factories import MemberWithUserFactory
from .factories import HelpRequestCategoryFactory, HelpRequestFactory


@pytest.mark.django_db
class TestCategoryListView:
    """Tests for category list view."""

    def test_list_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/categories/')
        assert response.status_code == 302

    def test_list_accessible_by_pastor(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/categories/')
        assert response.status_code == 200

    def test_list_accessible_by_admin(self, client):
        admin = MemberWithUserFactory(role='admin')
        client.force_login(admin.user)
        response = client.get('/help-requests/categories/')
        assert response.status_code == 200

    def test_list_shows_categories(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        HelpRequestCategoryFactory(name='Prayer')
        HelpRequestCategoryFactory(name='Financial')
        response = client.get('/help-requests/categories/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestCategoryCreateView:
    """Tests for category create view."""

    def test_create_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/categories/create/')
        assert response.status_code == 200

    def test_create_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.post('/help-requests/categories/create/', {
            'name': 'New Category',
            'name_fr': 'Nouvelle Catégorie',
            'description': 'A test category',
            'icon': 'star',
            'order': 1,
            'is_active': True,
        })
        assert response.status_code == 302
        assert HelpRequestCategory.objects.filter(name='New Category').exists()

    def test_create_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.post('/help-requests/categories/create/', {
            'name': 'Unauthorized',
            'order': 1,
            'is_active': True,
        })
        assert response.status_code == 302
        assert not HelpRequestCategory.objects.filter(name='Unauthorized').exists()


@pytest.mark.django_db
class TestCategoryEditView:
    """Tests for category edit view."""

    def test_edit_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        category = HelpRequestCategoryFactory()
        response = client.get(f'/help-requests/categories/{category.pk}/edit/')
        assert response.status_code == 200

    def test_edit_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        category = HelpRequestCategoryFactory(name='Old Name')
        response = client.post(f'/help-requests/categories/{category.pk}/edit/', {
            'name': 'New Name',
            'name_fr': 'Nouveau Nom',
            'description': 'Updated',
            'icon': 'star',
            'order': 2,
            'is_active': True,
        })
        assert response.status_code == 302
        category.refresh_from_db()
        assert category.name == 'New Name'


@pytest.mark.django_db
class TestCategoryDeleteView:
    """Tests for category delete view."""

    def test_delete_confirmation_page(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        category = HelpRequestCategoryFactory()
        response = client.get(f'/help-requests/categories/{category.pk}/delete/')
        assert response.status_code == 200

    def test_delete_category_without_requests(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        category = HelpRequestCategoryFactory()
        response = client.post(f'/help-requests/categories/{category.pk}/delete/')
        assert response.status_code == 302
        assert not HelpRequestCategory.all_objects.filter(pk=category.pk).exists()

    def test_deactivate_category_with_requests(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        category = HelpRequestCategoryFactory()
        HelpRequestFactory(category=category)

        response = client.post(f'/help-requests/categories/{category.pk}/delete/')
        assert response.status_code == 302
        category.refresh_from_db()
        assert category.is_active is False  # Deactivated, not deleted

    def test_delete_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        category = HelpRequestCategoryFactory()
        response = client.post(f'/help-requests/categories/{category.pk}/delete/')
        assert response.status_code == 302
        assert HelpRequestCategory.objects.filter(pk=category.pk).exists()
