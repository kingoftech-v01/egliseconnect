"""Tests for worship API views."""
import pytest
from datetime import date, time

from rest_framework.test import APIClient

from apps.core.constants import (
    Roles, AssignmentStatus, WorshipServiceStatus, ServiceSectionType,
)
from apps.members.tests.factories import (
    MemberWithUserFactory, PastorFactory, UserFactory, MemberFactory,
)
from .factories import (
    WorshipServiceFactory, ServiceSectionFactory, ServiceAssignmentFactory,
    EligibleMemberListFactory,
)


def _api_staff_login():
    """Create a staff member with user and return (client, member)."""
    pastor = PastorFactory()
    user = UserFactory()
    pastor.user = user
    pastor.save()
    client = APIClient()
    client.force_authenticate(user=user)
    return client, pastor


def _api_member_login():
    """Create a regular member with user and return (client, member)."""
    member = MemberWithUserFactory(role=Roles.MEMBER)
    client = APIClient()
    client.force_authenticate(user=member.user)
    return client, member


def _api_no_auth():
    """Return an unauthenticated API client."""
    return APIClient()


# ==================================================================
# WorshipServiceViewSet
# ==================================================================

@pytest.mark.django_db
class TestWorshipServiceAPI:
    """Tests for WorshipServiceViewSet."""

    def test_list_authenticated(self):
        client, member = _api_member_login()
        WorshipServiceFactory()
        response = client.get('/api/v1/worship/services/')
        assert response.status_code == 200

    def test_list_unauthenticated(self):
        client = _api_no_auth()
        response = client.get('/api/v1/worship/services/')
        assert response.status_code in (401, 403)

    def test_retrieve(self):
        client, member = _api_member_login()
        service = WorshipServiceFactory()
        response = client.get(f'/api/v1/worship/services/{service.pk}/')
        assert response.status_code == 200
        assert response.data['theme'] == service.theme

    def test_create_staff(self):
        client, pastor = _api_staff_login()
        response = client.post('/api/v1/worship/services/', {
            'date': '2026-05-01',
            'start_time': '10:00',
            'duration_minutes': 120,
            'status': 'draft',
        })
        assert response.status_code == 201

    def test_create_member_denied(self):
        client, member = _api_member_login()
        response = client.post('/api/v1/worship/services/', {
            'date': '2026-05-01',
            'start_time': '10:00',
            'duration_minutes': 120,
            'status': 'draft',
        })
        assert response.status_code == 403

    def test_update_staff(self):
        client, pastor = _api_staff_login()
        service = WorshipServiceFactory()
        response = client.patch(f'/api/v1/worship/services/{service.pk}/', {
            'theme': 'Nouveau',
        })
        assert response.status_code == 200
        service.refresh_from_db()
        assert service.theme == 'Nouveau'

    def test_delete_staff(self):
        client, pastor = _api_staff_login()
        service = WorshipServiceFactory()
        response = client.delete(f'/api/v1/worship/services/{service.pk}/')
        assert response.status_code == 204

    def test_delete_member_denied(self):
        client, member = _api_member_login()
        service = WorshipServiceFactory()
        response = client.delete(f'/api/v1/worship/services/{service.pk}/')
        assert response.status_code == 403

    def test_filter_by_status(self):
        client, member = _api_member_login()
        WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        WorshipServiceFactory(status=WorshipServiceStatus.PLANNED)
        response = client.get('/api/v1/worship/services/?status=planned')
        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_search_by_theme(self):
        client, member = _api_member_login()
        WorshipServiceFactory(theme='Résurrection')
        WorshipServiceFactory(theme='Pentecôte')
        response = client.get('/api/v1/worship/services/?search=Résurrection')
        assert response.status_code == 200
        assert len(response.data['results']) == 1


# ==================================================================
# ServiceSectionViewSet
# ==================================================================

@pytest.mark.django_db
class TestServiceSectionAPI:
    """Tests for ServiceSectionViewSet."""

    def test_list(self):
        client, member = _api_member_login()
        ServiceSectionFactory()
        response = client.get('/api/v1/worship/sections/')
        assert response.status_code == 200

    def test_retrieve(self):
        client, member = _api_member_login()
        section = ServiceSectionFactory()
        response = client.get(f'/api/v1/worship/sections/{section.pk}/')
        assert response.status_code == 200

    def test_create_staff(self):
        client, pastor = _api_staff_login()
        service = WorshipServiceFactory()
        response = client.post('/api/v1/worship/sections/', {
            'service': str(service.pk),
            'name': 'Louange',
            'order': 1,
            'section_type': 'louange',
            'duration_minutes': 20,
        })
        assert response.status_code == 201

    def test_create_member_denied(self):
        client, member = _api_member_login()
        service = WorshipServiceFactory()
        response = client.post('/api/v1/worship/sections/', {
            'service': str(service.pk),
            'name': 'Louange',
            'order': 1,
            'section_type': 'louange',
            'duration_minutes': 20,
        })
        assert response.status_code == 403

    def test_filter_by_service(self):
        client, member = _api_member_login()
        service = WorshipServiceFactory()
        ServiceSectionFactory(service=service, order=1)
        ServiceSectionFactory()  # different service
        response = client.get(f'/api/v1/worship/sections/?service={service.pk}')
        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_delete_staff(self):
        client, pastor = _api_staff_login()
        section = ServiceSectionFactory()
        response = client.delete(f'/api/v1/worship/sections/{section.pk}/')
        assert response.status_code == 204


# ==================================================================
# ServiceAssignmentViewSet
# ==================================================================

@pytest.mark.django_db
class TestServiceAssignmentAPI:
    """Tests for ServiceAssignmentViewSet."""

    def test_list(self):
        client, member = _api_member_login()
        ServiceAssignmentFactory()
        response = client.get('/api/v1/worship/assignments/')
        assert response.status_code == 200

    def test_my_assignments(self):
        client, member = _api_member_login()
        ServiceAssignmentFactory(member=member)
        ServiceAssignmentFactory()  # other member
        response = client.get('/api/v1/worship/assignments/my-assignments/')
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_my_assignments_no_profile(self):
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/v1/worship/assignments/my-assignments/')
        assert response.status_code == 404

    def test_confirm_own_assignment(self):
        client, member = _api_member_login()
        assignment = ServiceAssignmentFactory(member=member)
        response = client.post(f'/api/v1/worship/assignments/{assignment.pk}/confirm/')
        assert response.status_code == 200
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.CONFIRMED

    def test_confirm_other_member_denied(self):
        client, member = _api_member_login()
        other = MemberFactory()
        assignment = ServiceAssignmentFactory(member=other)
        response = client.post(f'/api/v1/worship/assignments/{assignment.pk}/confirm/')
        assert response.status_code == 403

    def test_decline_own_assignment(self):
        client, member = _api_member_login()
        assignment = ServiceAssignmentFactory(member=member)
        response = client.post(f'/api/v1/worship/assignments/{assignment.pk}/decline/')
        assert response.status_code == 200
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.DECLINED

    def test_decline_other_member_denied(self):
        client, member = _api_member_login()
        other = MemberFactory()
        assignment = ServiceAssignmentFactory(member=other)
        response = client.post(f'/api/v1/worship/assignments/{assignment.pk}/decline/')
        assert response.status_code == 403

    def test_create_staff(self):
        client, pastor = _api_staff_login()
        section = ServiceSectionFactory()
        member = MemberFactory()
        response = client.post('/api/v1/worship/assignments/', {
            'section': str(section.pk),
            'member': str(member.pk),
            'status': 'assigned',
        })
        assert response.status_code == 201

    def test_create_member_denied(self):
        client, member = _api_member_login()
        section = ServiceSectionFactory()
        response = client.post('/api/v1/worship/assignments/', {
            'section': str(section.pk),
            'member': str(member.pk),
            'status': 'assigned',
        })
        assert response.status_code == 403

    def test_filter_by_status(self):
        client, member = _api_member_login()
        ServiceAssignmentFactory(status=AssignmentStatus.CONFIRMED)
        ServiceAssignmentFactory(status=AssignmentStatus.ASSIGNED)
        response = client.get('/api/v1/worship/assignments/?status=confirmed')
        assert response.status_code == 200
        assert len(response.data['results']) == 1


# ==================================================================
# EligibleMemberListViewSet
# ==================================================================

@pytest.mark.django_db
class TestEligibleMemberListAPI:
    """Tests for EligibleMemberListViewSet."""

    def test_list(self):
        client, member = _api_member_login()
        EligibleMemberListFactory()
        response = client.get('/api/v1/worship/eligible/')
        assert response.status_code == 200

    def test_retrieve(self):
        client, member = _api_member_login()
        eligible = EligibleMemberListFactory()
        response = client.get(f'/api/v1/worship/eligible/{eligible.pk}/')
        assert response.status_code == 200

    def test_create_staff(self):
        client, pastor = _api_staff_login()
        response = client.post('/api/v1/worship/eligible/', {
            'section_type': ServiceSectionType.PREDICATION,
        })
        assert response.status_code == 201

    def test_create_member_denied(self):
        client, member = _api_member_login()
        response = client.post('/api/v1/worship/eligible/', {
            'section_type': ServiceSectionType.PREDICATION,
        })
        assert response.status_code == 403

    def test_delete_staff(self):
        client, pastor = _api_staff_login()
        eligible = EligibleMemberListFactory()
        response = client.delete(f'/api/v1/worship/eligible/{eligible.pk}/')
        assert response.status_code == 204

    def test_filter_by_section_type(self):
        client, member = _api_member_login()
        EligibleMemberListFactory(section_type=ServiceSectionType.LOUANGE)
        EligibleMemberListFactory(section_type=ServiceSectionType.PREDICATION)
        response = client.get(f'/api/v1/worship/eligible/?section_type={ServiceSectionType.LOUANGE}')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
