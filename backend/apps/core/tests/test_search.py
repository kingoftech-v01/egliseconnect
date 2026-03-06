"""Tests for global search view and GlobalSearchService."""
import pytest
from django.contrib.auth import get_user_model

from apps.core.constants import Roles
from apps.core.services_search import GlobalSearchService
from apps.members.tests.factories import (
    MemberWithUserFactory, MemberFactory, GroupFactory, UserFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestSearchView:
    def test_requires_login(self, client):
        response = client.get('/search/')
        assert response.status_code == 302

    def test_get_without_query(self, client):
        member = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(member.user)
        response = client.get('/search/')
        assert response.status_code == 200
        assert 'query' in response.context

    def test_search_members_by_name(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN, first_name='Jean', last_name='Tremblay')
        MemberWithUserFactory(role=Roles.MEMBER, first_name='Marie', last_name='Dupont')
        client.force_login(admin.user)
        response = client.get('/search/?q=Marie')
        assert response.status_code == 200
        assert response.context['total_count'] >= 1

    def test_short_query_returns_no_results(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/search/?q=a')
        assert response.status_code == 200
        assert response.context['total_count'] == 0

    def test_empty_query(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/search/?q=')
        assert response.status_code == 200
        assert response.context['total_count'] == 0

    def test_redirects_without_member_profile(self, client):
        user = User.objects.create_user(username='nopmember', password='test123')
        client.force_login(user)
        response = client.get('/search/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestSearchAutocomplete:
    def test_requires_login(self, client):
        response = client.get('/search/autocomplete/?q=test')
        assert response.status_code == 302

    def test_returns_json(self, client):
        member = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(member.user)
        response = client.get('/search/autocomplete/?q=test')
        assert response.status_code == 200
        data = response.json()
        assert 'suggestions' in data

    def test_returns_empty_for_short_query(self, client):
        member = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(member.user)
        response = client.get('/search/autocomplete/?q=a')
        data = response.json()
        assert data['suggestions'] == []

    def test_returns_empty_without_member_profile(self, client):
        user = User.objects.create_user(username='noprofile', password='test123')
        client.force_login(user)
        response = client.get('/search/autocomplete/?q=test')
        data = response.json()
        assert data['suggestions'] == []

    def test_returns_member_suggestions(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN, first_name='Jean', last_name='Tremblay')
        MemberFactory(first_name='Julien', last_name='TestUnique')
        client.force_login(admin.user)
        response = client.get('/search/autocomplete/?q=TestUnique')
        data = response.json()
        assert len(data['suggestions']) >= 1
        assert data['suggestions'][0]['category'] == 'Membre'


@pytest.mark.django_db
class TestGlobalSearchService:
    def test_empty_query(self):
        user = UserFactory()
        service = GlobalSearchService(user)
        results = service.search('')
        assert results == {}

    def test_short_query(self):
        user = UserFactory()
        service = GlobalSearchService(user)
        results = service.search('a')
        assert results == {}

    def test_search_returns_members(self):
        member = MemberWithUserFactory(role=Roles.ADMIN, first_name='Unique', last_name='SearchName')
        service = GlobalSearchService(member.user)
        results = service.search('SearchName')
        assert 'members' in results
        assert len(results['members']) >= 1

    def test_staff_user_sees_help_requests(self):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        service = GlobalSearchService(admin.user)
        assert service.is_staff is True
        results = service.search('test')
        assert 'help_requests' in results or 'donations' in results

    def test_member_no_help_requests(self):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        service = GlobalSearchService(member.user)
        assert service.is_staff is False
        results = service.search('test')
        assert 'help_requests' not in results
        assert 'donations' not in results

    def test_superuser_is_staff(self):
        user = UserFactory(is_superuser=True)
        service = GlobalSearchService(user)
        assert service.is_staff is True

    def test_autocomplete_returns_list(self):
        admin = MemberWithUserFactory(role=Roles.ADMIN, first_name='AutoTest')
        service = GlobalSearchService(admin.user)
        suggestions = service.search_autocomplete('AutoTest')
        assert isinstance(suggestions, list)

    def test_autocomplete_limit(self):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        service = GlobalSearchService(admin.user)
        suggestions = service.search_autocomplete('test', limit=2)
        assert len(suggestions) <= 2

    def test_get_total_count(self):
        results = {'members': [1, 2, 3], 'events': [4, 5]}
        assert GlobalSearchService.get_total_count(results) == 5

    def test_get_total_count_empty(self):
        assert GlobalSearchService.get_total_count({}) == 0

    def test_search_groups(self):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        group = GroupFactory(name='UniqueGroupSearch')
        service = GlobalSearchService(admin.user)
        results = service.search('UniqueGroupSearch')
        assert 'groups' in results
        assert len(results['groups']) >= 1
