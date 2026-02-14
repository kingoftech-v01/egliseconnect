"""Tests for Campus model and views."""
import pytest
from django.contrib.auth import get_user_model

from apps.core.constants import Roles
from apps.core.models_extended import Campus
from apps.members.tests.factories import MemberWithUserFactory, MemberFactory

User = get_user_model()


@pytest.mark.django_db
class TestCampusModel:
    def test_create_campus(self):
        campus = Campus.objects.create(
            name='Campus Principal',
            city='Montreal',
            province='QC',
            is_main=True,
        )
        assert campus.name == 'Campus Principal'
        assert campus.is_main is True
        assert campus.is_active is True

    def test_str_representation(self):
        campus = Campus.objects.create(name='Test Campus')
        assert str(campus) == 'Test Campus'

    def test_only_one_main_campus(self):
        c1 = Campus.objects.create(name='First', is_main=True)
        c2 = Campus.objects.create(name='Second', is_main=True)

        c1.refresh_from_db()
        assert c1.is_main is False
        assert c2.is_main is True

    def test_ordering(self):
        c1 = Campus.objects.create(name='Non-main', is_main=False)
        c2 = Campus.objects.create(name='Main', is_main=True)
        campuses = list(Campus.objects.all())
        assert campuses[0].is_main is True

    def test_pastor_nullable(self):
        campus = Campus.objects.create(name='No Pastor')
        assert campus.pastor is None

    def test_pastor_assignment(self):
        pastor = MemberFactory(role=Roles.PASTOR)
        campus = Campus.objects.create(
            name='With Pastor',
            pastor=pastor,
        )
        assert campus.pastor == pastor

    def test_optional_fields(self):
        campus = Campus.objects.create(name='Minimal')
        assert campus.address == ''
        assert campus.city == ''
        assert campus.phone == ''
        assert campus.email == ''


@pytest.mark.django_db
class TestCampusListView:
    def test_requires_login(self, client):
        response = client.get('/settings/campus/')
        assert response.status_code == 302

    def test_requires_admin(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/settings/campus/')
        assert response.status_code == 302

    def test_admin_can_view(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/settings/campus/')
        assert response.status_code == 200
