"""Tests for worship admin configuration."""
import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.members.tests.factories import UserFactory
from apps.worship.admin import (
    WorshipServiceAdmin, ServiceSectionAdmin,
    ServiceAssignmentAdmin, EligibleMemberListAdmin,
)
from apps.worship.models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
)
from .factories import (
    WorshipServiceFactory, ServiceSectionFactory,
    ServiceAssignmentFactory, EligibleMemberListFactory,
)


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def admin_request(rf):
    request = rf.get('/')
    request.user = UserFactory(is_staff=True, is_superuser=True)
    return request


@pytest.mark.django_db
class TestWorshipServiceAdmin:
    """Tests for WorshipServiceAdmin."""

    def test_list_display(self, admin_site):
        admin = WorshipServiceAdmin(WorshipService, admin_site)
        assert 'date' in admin.list_display
        assert 'status' in admin.list_display
        assert 'theme' in admin.list_display

    def test_list_filter(self, admin_site):
        admin = WorshipServiceAdmin(WorshipService, admin_site)
        assert 'status' in admin.list_filter
        assert 'date' in admin.list_filter

    def test_search_fields(self, admin_site):
        admin = WorshipServiceAdmin(WorshipService, admin_site)
        assert 'theme' in admin.search_fields
        assert 'notes' in admin.search_fields

    def test_inlines(self, admin_site):
        admin = WorshipServiceAdmin(WorshipService, admin_site)
        inline_classes = [i.__name__ for i in admin.inlines]
        assert 'ServiceSectionInline' in inline_classes

    def test_confirmation_rate_display(self, admin_site):
        admin = WorshipServiceAdmin(WorshipService, admin_site)
        service = WorshipServiceFactory()
        result = admin.confirmation_rate_display(service)
        assert '%' in result

    def test_total_assignments_method(self, admin_site):
        admin = WorshipServiceAdmin(WorshipService, admin_site)
        service = WorshipServiceFactory()
        section = ServiceSectionFactory(service=service, order=1)
        ServiceAssignmentFactory(section=section)
        result = admin.total_assignments(service)
        assert result == 1

    def test_changelist(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(user)
        WorshipServiceFactory()
        response = client.get('/admin/worship/worshipservice/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestServiceSectionAdmin:
    """Tests for ServiceSectionAdmin."""

    def test_list_display(self, admin_site):
        admin = ServiceSectionAdmin(ServiceSection, admin_site)
        assert 'name' in admin.list_display
        assert 'order' in admin.list_display
        assert 'section_type' in admin.list_display

    def test_list_filter(self, admin_site):
        admin = ServiceSectionAdmin(ServiceSection, admin_site)
        assert 'section_type' in admin.list_filter

    def test_search_fields(self, admin_site):
        admin = ServiceSectionAdmin(ServiceSection, admin_site)
        assert 'name' in admin.search_fields

    def test_inlines(self, admin_site):
        admin = ServiceSectionAdmin(ServiceSection, admin_site)
        inline_classes = [i.__name__ for i in admin.inlines]
        assert 'ServiceAssignmentInline' in inline_classes

    def test_changelist(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(user)
        ServiceSectionFactory()
        response = client.get('/admin/worship/servicesection/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestServiceAssignmentAdmin:
    """Tests for ServiceAssignmentAdmin."""

    def test_list_display(self, admin_site):
        admin = ServiceAssignmentAdmin(ServiceAssignment, admin_site)
        assert 'member' in admin.list_display
        assert 'status' in admin.list_display

    def test_list_filter(self, admin_site):
        admin = ServiceAssignmentAdmin(ServiceAssignment, admin_site)
        assert 'status' in admin.list_filter

    def test_search_fields(self, admin_site):
        admin = ServiceAssignmentAdmin(ServiceAssignment, admin_site)
        assert 'member__first_name' in admin.search_fields

    def test_changelist(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(user)
        ServiceAssignmentFactory()
        response = client.get('/admin/worship/serviceassignment/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestEligibleMemberListAdmin:
    """Tests for EligibleMemberListAdmin."""

    def test_list_display(self, admin_site):
        admin = EligibleMemberListAdmin(EligibleMemberList, admin_site)
        assert 'section_type' in admin.list_display
        assert 'department' in admin.list_display

    def test_member_count(self, admin_site):
        admin = EligibleMemberListAdmin(EligibleMemberList, admin_site)
        eligible = EligibleMemberListFactory()
        assert admin.member_count(eligible) == 0

    def test_changelist(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(user)
        EligibleMemberListFactory()
        response = client.get('/admin/worship/eligiblememberlist/')
        assert response.status_code == 200
