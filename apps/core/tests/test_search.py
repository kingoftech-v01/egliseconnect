"""Tests for global search view."""
import pytest
from django.contrib.auth import get_user_model

from apps.members.tests.factories import MemberWithUserFactory
from apps.core.constants import Roles

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
