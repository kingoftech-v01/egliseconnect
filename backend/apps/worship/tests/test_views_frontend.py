"""Tests for worship frontend views."""
import json
import uuid

import pytest
from datetime import date, time, timedelta

from django.utils import timezone

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


def _staff_login(client):
    """Create a pastor with user and log them in."""
    pastor = PastorFactory()
    user = UserFactory()
    pastor.user = user
    pastor.save()
    client.force_login(user)
    return pastor


def _member_login(client):
    """Create a regular member with user and log them in."""
    member = MemberWithUserFactory(role=Roles.MEMBER)
    client.force_login(member.user)
    return member


def _login_no_profile(client):
    """Log in a user without a member profile."""
    user = UserFactory()
    client.force_login(user)
    return user


# ==================================================================
# Service List
# ==================================================================

@pytest.mark.django_db
class TestServiceList:
    """Tests for service_list view."""

    def test_get(self, client):
        _staff_login(client)
        WorshipServiceFactory()
        response = client.get('/worship/services/')
        assert response.status_code == 200

    def test_filter_by_status(self, client):
        _staff_login(client)
        WorshipServiceFactory(status=WorshipServiceStatus.PLANNED)
        WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        response = client.get('/worship/services/?status=planned')
        assert response.status_code == 200

    def test_filter_upcoming(self, client):
        _staff_login(client)
        response = client.get('/worship/services/?upcoming=1')
        assert response.status_code == 200

    def test_filter_date_range(self, client):
        _staff_login(client)
        WorshipServiceFactory(date=date(2026, 3, 1))
        WorshipServiceFactory(date=date(2026, 6, 1))
        response = client.get('/worship/services/?date_from=2026-02-01&date_to=2026-04-01')
        assert response.status_code == 200

    def test_filter_date_from_only(self, client):
        _staff_login(client)
        response = client.get('/worship/services/?date_from=2026-05-01')
        assert response.status_code == 200

    def test_filter_date_to_only(self, client):
        _staff_login(client)
        response = client.get('/worship/services/?date_to=2026-05-01')
        assert response.status_code == 200

    def test_member_can_view(self, client):
        _member_login(client)
        response = client.get('/worship/services/')
        assert response.status_code == 200

    def test_unauthenticated_redirect(self, client):
        response = client.get('/worship/services/')
        assert response.status_code == 302

    def test_no_profile_redirect(self, client):
        _login_no_profile(client)
        response = client.get('/worship/services/')
        assert response.status_code == 302

    def test_pagination(self, client):
        _staff_login(client)
        for i in range(25):
            WorshipServiceFactory(date=date(2026, 1, 1) + timedelta(days=i))
        response = client.get('/worship/services/?page=2')
        assert response.status_code == 200


# ==================================================================
# Service Detail
# ==================================================================

@pytest.mark.django_db
class TestServiceDetail:
    """Tests for service_detail view."""

    def test_get(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/')
        assert response.status_code == 200

    def test_with_sections(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        ServiceSectionFactory(service=service, order=1)
        ServiceSectionFactory(service=service, order=2)
        response = client.get(f'/worship/services/{service.pk}/')
        assert response.status_code == 200

    def test_404_invalid_pk(self, client):
        _staff_login(client)
        response = client.get(f'/worship/services/{uuid.uuid4()}/')
        assert response.status_code == 404

    def test_no_profile_redirect(self, client):
        _login_no_profile(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/')
        assert response.status_code == 302

    def test_confirmation_rate_in_context(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        section = ServiceSectionFactory(service=service, order=1)
        ServiceAssignmentFactory(section=section, status=AssignmentStatus.CONFIRMED)
        ServiceAssignmentFactory(section=section, status=AssignmentStatus.ASSIGNED)
        response = client.get(f'/worship/services/{service.pk}/')
        assert response.status_code == 200
        assert response.context['service'].confirmation_rate == 50


# ==================================================================
# Service Create
# ==================================================================

@pytest.mark.django_db
class TestServiceCreate:
    """Tests for service_create view."""

    def test_get_form(self, client):
        _staff_login(client)
        response = client.get('/worship/services/create/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        response = client.post('/worship/services/create/', {
            'date': '2026-04-05',
            'start_time': '10:00',
            'duration_minutes': 120,
            'theme': 'Pâques',
        })
        assert response.status_code == 302
        from apps.worship.models import WorshipService
        assert WorshipService.objects.count() == 1

    def test_post_invalid(self, client):
        _staff_login(client)
        response = client.post('/worship/services/create/', {
            'date': '',
            'start_time': '',
        })
        assert response.status_code == 200  # re-render form

    def test_non_staff_denied(self, client):
        _member_login(client)
        response = client.get('/worship/services/create/')
        assert response.status_code == 302  # Redirect

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        response = client.get('/worship/services/create/')
        assert response.status_code == 302


# ==================================================================
# Service Edit
# ==================================================================

@pytest.mark.django_db
class TestServiceEdit:
    """Tests for service_edit view."""

    def test_get_form(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/edit/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(f'/worship/services/{service.pk}/edit/', {
            'date': '2026-05-01',
            'start_time': '09:30',
            'duration_minutes': 90,
            'theme': 'Nouveau thème',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.theme == 'Nouveau thème'

    def test_post_invalid(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(f'/worship/services/{service.pk}/edit/', {
            'date': '',
            'start_time': '',
        })
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/edit/')
        assert response.status_code == 302


# ==================================================================
# Service Delete
# ==================================================================

@pytest.mark.django_db
class TestServiceDelete:
    """Tests for service_delete view."""

    def test_get_confirmation(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/delete/')
        assert response.status_code == 200

    def test_post_deletes(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(f'/worship/services/{service.pk}/delete/')
        assert response.status_code == 302
        from apps.worship.models import WorshipService
        assert not WorshipService.objects.filter(pk=service.pk).exists()

    def test_non_staff_denied(self, client):
        _member_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/delete/')
        assert response.status_code == 302

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/delete/')
        assert response.status_code == 302

    def test_404_invalid_pk(self, client):
        _staff_login(client)
        response = client.get(f'/worship/services/{uuid.uuid4()}/delete/')
        assert response.status_code == 404


# ==================================================================
# Service Publish / Status Change
# ==================================================================

@pytest.mark.django_db
class TestServicePublish:
    """Tests for service_publish view."""

    def test_publish_draft_to_planned(self, client):
        _staff_login(client)
        service = WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        response = client.post(f'/worship/services/{service.pk}/publish/', {
            'status': 'planned',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.PLANNED

    def test_publish_planned_to_confirmed(self, client):
        _staff_login(client)
        service = WorshipServiceFactory(status=WorshipServiceStatus.PLANNED)
        response = client.post(f'/worship/services/{service.pk}/publish/', {
            'status': 'confirmed',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.CONFIRMED

    def test_publish_confirmed_to_completed(self, client):
        _staff_login(client)
        service = WorshipServiceFactory(status=WorshipServiceStatus.CONFIRMED)
        response = client.post(f'/worship/services/{service.pk}/publish/', {
            'status': 'completed',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.COMPLETED

    def test_cancel_service(self, client):
        _staff_login(client)
        service = WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        response = client.post(f'/worship/services/{service.pk}/publish/', {
            'status': 'cancelled',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.CANCELLED

    def test_invalid_status(self, client):
        _staff_login(client)
        service = WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        response = client.post(f'/worship/services/{service.pk}/publish/', {
            'status': 'invalid_status',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.DRAFT

    def test_non_staff_denied(self, client):
        _member_login(client)
        service = WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        response = client.post(f'/worship/services/{service.pk}/publish/', {
            'status': 'planned',
        })
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.DRAFT

    def test_get_redirects(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/publish/')
        assert response.status_code == 302


# ==================================================================
# Service Print
# ==================================================================

@pytest.mark.django_db
class TestServicePrint:
    """Tests for service_print view."""

    def test_get(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        ServiceSectionFactory(service=service, order=1)
        response = client.get(f'/worship/services/{service.pk}/print/')
        assert response.status_code == 200

    def test_member_can_view(self, client):
        _member_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/print/')
        assert response.status_code == 200

    def test_no_profile_redirect(self, client):
        _login_no_profile(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/print/')
        assert response.status_code == 302

    def test_404(self, client):
        _staff_login(client)
        response = client.get(f'/worship/services/{uuid.uuid4()}/print/')
        assert response.status_code == 404

    def test_empty_sections(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/print/')
        assert response.status_code == 200


# ==================================================================
# Service Duplicate
# ==================================================================

@pytest.mark.django_db
class TestServiceDuplicate:
    """Tests for service_duplicate view."""

    def test_get_form(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        ServiceSectionFactory(service=service, order=1, name='Louange')
        ServiceSectionFactory(service=service, order=2, name='Prédication')
        response = client.get(f'/worship/services/{service.pk}/duplicate/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        ServiceSectionFactory(service=service, order=1, name='Louange')
        ServiceSectionFactory(service=service, order=2, name='Prédication')
        response = client.post(f'/worship/services/{service.pk}/duplicate/', {
            'date': '2026-06-01',
            'start_time': '10:00',
            'duration_minutes': 120,
        })
        assert response.status_code == 302
        from apps.worship.models import WorshipService
        assert WorshipService.objects.count() == 2
        new_service = WorshipService.objects.exclude(pk=service.pk).first()
        assert new_service.sections.count() == 2

    def test_post_invalid(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(f'/worship/services/{service.pk}/duplicate/', {
            'date': '',
            'start_time': '',
        })
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/duplicate/')
        assert response.status_code == 302

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/duplicate/')
        assert response.status_code == 302


# ==================================================================
# Section Manage (add)
# ==================================================================

@pytest.mark.django_db
class TestSectionManage:
    """Tests for section_manage view."""

    def test_get_form(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/sections/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(f'/worship/services/{service.pk}/sections/', {
            'name': 'Louange',
            'order': 1,
            'section_type': 'louange',
            'duration_minutes': 20,
        })
        assert response.status_code == 302
        assert service.sections.count() == 1

    def test_post_invalid(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(f'/worship/services/{service.pk}/sections/', {
            'name': '',
        })
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/sections/')
        assert response.status_code == 302


# ==================================================================
# Section Edit
# ==================================================================

@pytest.mark.django_db
class TestSectionEdit:
    """Tests for section_edit view."""

    def test_get_form(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/edit/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        response = client.post(f'/worship/sections/{section.pk}/edit/', {
            'name': 'Louange modifiée',
            'order': section.order,
            'section_type': 'louange',
            'duration_minutes': 25,
        })
        assert response.status_code == 302
        section.refresh_from_db()
        assert section.name == 'Louange modifiée'

    def test_post_invalid(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        response = client.post(f'/worship/sections/{section.pk}/edit/', {
            'name': '',
        })
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/edit/')
        assert response.status_code == 302

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/edit/')
        assert response.status_code == 302

    def test_404(self, client):
        _staff_login(client)
        response = client.get(f'/worship/sections/{uuid.uuid4()}/edit/')
        assert response.status_code == 404


# ==================================================================
# Section Delete
# ==================================================================

@pytest.mark.django_db
class TestSectionDelete:
    """Tests for section_delete view."""

    def test_get_confirmation(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/delete/')
        assert response.status_code == 200

    def test_post_deletes(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        service_pk = section.service.pk
        response = client.post(f'/worship/sections/{section.pk}/delete/')
        assert response.status_code == 302
        from apps.worship.models import ServiceSection
        assert not ServiceSection.objects.filter(pk=section.pk).exists()

    def test_non_staff_denied(self, client):
        _member_login(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/delete/')
        assert response.status_code == 302

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/delete/')
        assert response.status_code == 302

    def test_404(self, client):
        _staff_login(client)
        response = client.get(f'/worship/sections/{uuid.uuid4()}/delete/')
        assert response.status_code == 404


# ==================================================================
# Section Reorder (AJAX)
# ==================================================================

@pytest.mark.django_db
class TestSectionReorder:
    """Tests for section_reorder AJAX view."""

    def test_reorder(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        s1 = ServiceSectionFactory(service=service, order=1)
        s2 = ServiceSectionFactory(service=service, order=2)
        s3 = ServiceSectionFactory(service=service, order=3)

        response = client.post(
            f'/worship/services/{service.pk}/sections/reorder/',
            data=json.dumps({'order': [str(s3.pk), str(s1.pk), str(s2.pk)]}),
            content_type='application/json',
        )
        assert response.status_code == 200
        s1.refresh_from_db()
        s2.refresh_from_db()
        s3.refresh_from_db()
        assert s3.order == 1
        assert s1.order == 2
        assert s2.order == 3

    def test_reorder_non_staff_denied(self, client):
        _member_login(client)
        service = WorshipServiceFactory()
        response = client.post(
            f'/worship/services/{service.pk}/sections/reorder/',
            data=json.dumps({'order': []}),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_reorder_no_profile(self, client):
        _login_no_profile(client)
        service = WorshipServiceFactory()
        response = client.post(
            f'/worship/services/{service.pk}/sections/reorder/',
            data=json.dumps({'order': []}),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_reorder_empty_list(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(
            f'/worship/services/{service.pk}/sections/reorder/',
            data=json.dumps({'order': []}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_reorder_invalid_json(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(
            f'/worship/services/{service.pk}/sections/reorder/',
            data='invalid json',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_reorder_invalid_section_id(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.post(
            f'/worship/services/{service.pk}/sections/reorder/',
            data=json.dumps({'order': [str(uuid.uuid4())]}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_get_not_allowed(self, client):
        _staff_login(client)
        service = WorshipServiceFactory()
        response = client.get(f'/worship/services/{service.pk}/sections/reorder/')
        assert response.status_code == 405


# ==================================================================
# Assign Members
# ==================================================================

@pytest.mark.django_db
class TestAssignMembers:
    """Tests for assign_members view."""

    def test_get_form(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/assign/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        member = MemberFactory(is_active=True)
        response = client.post(f'/worship/sections/{section.pk}/assign/', {
            'member': str(member.pk),
        })
        assert response.status_code == 302
        assert section.assignments.count() == 1

    def test_post_duplicate(self, client):
        _staff_login(client)
        section = ServiceSectionFactory()
        member = MemberFactory(is_active=True)
        ServiceAssignmentFactory(section=section, member=member)
        response = client.post(f'/worship/sections/{section.pk}/assign/', {
            'member': str(member.pk),
        })
        assert response.status_code == 302
        assert section.assignments.count() == 1  # No duplicate

    def test_non_staff_denied(self, client):
        _member_login(client)
        section = ServiceSectionFactory()
        response = client.get(f'/worship/sections/{section.pk}/assign/')
        assert response.status_code == 302


# ==================================================================
# Assignment Remove
# ==================================================================

@pytest.mark.django_db
class TestAssignmentRemove:
    """Tests for assignment_remove view."""

    def test_get_confirmation(self, client):
        _staff_login(client)
        assignment = ServiceAssignmentFactory()
        response = client.get(f'/worship/assignments/{assignment.pk}/remove/')
        assert response.status_code == 200

    def test_post_removes(self, client):
        _staff_login(client)
        assignment = ServiceAssignmentFactory()
        response = client.post(f'/worship/assignments/{assignment.pk}/remove/')
        assert response.status_code == 302
        from apps.worship.models import ServiceAssignment
        assert not ServiceAssignment.objects.filter(pk=assignment.pk).exists()

    def test_non_staff_denied(self, client):
        _member_login(client)
        assignment = ServiceAssignmentFactory()
        response = client.get(f'/worship/assignments/{assignment.pk}/remove/')
        assert response.status_code == 302

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        assignment = ServiceAssignmentFactory()
        response = client.get(f'/worship/assignments/{assignment.pk}/remove/')
        assert response.status_code == 302

    def test_404(self, client):
        _staff_login(client)
        response = client.get(f'/worship/assignments/{uuid.uuid4()}/remove/')
        assert response.status_code == 404


# ==================================================================
# My Assignments
# ==================================================================

@pytest.mark.django_db
class TestMyAssignments:
    """Tests for my_assignments view."""

    def test_get(self, client):
        member = _member_login(client)
        ServiceAssignmentFactory(member=member)
        response = client.get('/worship/my-assignments/')
        assert response.status_code == 200

    def test_empty(self, client):
        _member_login(client)
        response = client.get('/worship/my-assignments/')
        assert response.status_code == 200

    def test_no_profile_redirect(self, client):
        _login_no_profile(client)
        response = client.get('/worship/my-assignments/')
        assert response.status_code == 302


# ==================================================================
# Assignment Respond
# ==================================================================

@pytest.mark.django_db
class TestAssignmentRespond:
    """Tests for assignment_respond view."""

    def test_confirm(self, client):
        member = _member_login(client)
        assignment = ServiceAssignmentFactory(member=member)
        response = client.post(
            f'/worship/assignments/{assignment.pk}/respond/',
            {'action': 'confirm'},
        )
        assert response.status_code == 302
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.CONFIRMED

    def test_decline(self, client):
        member = _member_login(client)
        assignment = ServiceAssignmentFactory(member=member)
        response = client.post(
            f'/worship/assignments/{assignment.pk}/respond/',
            {'action': 'decline'},
        )
        assert response.status_code == 302
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.DECLINED

    def test_cannot_respond_other_member(self, client):
        _member_login(client)
        other_member = MemberFactory()
        assignment = ServiceAssignmentFactory(member=other_member)
        response = client.post(
            f'/worship/assignments/{assignment.pk}/respond/',
            {'action': 'confirm'},
        )
        assert response.status_code == 404

    def test_no_action(self, client):
        member = _member_login(client)
        assignment = ServiceAssignmentFactory(member=member)
        response = client.post(
            f'/worship/assignments/{assignment.pk}/respond/',
            {},
        )
        assert response.status_code == 302
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.ASSIGNED  # Unchanged

    def test_no_profile_redirect(self, client):
        _login_no_profile(client)
        assignment = ServiceAssignmentFactory()
        response = client.post(
            f'/worship/assignments/{assignment.pk}/respond/',
            {'action': 'confirm'},
        )
        assert response.status_code == 302


# ==================================================================
# Eligible List
# ==================================================================

@pytest.mark.django_db
class TestEligibleList:
    """Tests for eligible_list view."""

    def test_get(self, client):
        _staff_login(client)
        EligibleMemberListFactory()
        response = client.get('/worship/eligible/')
        assert response.status_code == 200

    def test_empty(self, client):
        _staff_login(client)
        response = client.get('/worship/eligible/')
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        response = client.get('/worship/eligible/')
        assert response.status_code == 302

    def test_no_profile_denied(self, client):
        _login_no_profile(client)
        response = client.get('/worship/eligible/')
        assert response.status_code == 302


# ==================================================================
# Eligible List Create
# ==================================================================

@pytest.mark.django_db
class TestEligibleListCreate:
    """Tests for eligible_list_create view."""

    def test_get_form(self, client):
        _staff_login(client)
        response = client.get('/worship/eligible/create/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        response = client.post('/worship/eligible/create/', {
            'section_type': ServiceSectionType.PREDICATION,
        })
        assert response.status_code == 302
        from apps.worship.models import EligibleMemberList
        assert EligibleMemberList.objects.count() == 1

    def test_post_invalid(self, client):
        _staff_login(client)
        response = client.post('/worship/eligible/create/', {
            'section_type': '',
        })
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        response = client.get('/worship/eligible/create/')
        assert response.status_code == 302


# ==================================================================
# Eligible List Edit
# ==================================================================

@pytest.mark.django_db
class TestEligibleListEdit:
    """Tests for eligible_list_edit view."""

    def test_get_form(self, client):
        _staff_login(client)
        eligible = EligibleMemberListFactory()
        response = client.get(f'/worship/eligible/{eligible.pk}/edit/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        _staff_login(client)
        eligible = EligibleMemberListFactory(section_type=ServiceSectionType.PREDICATION)
        member = MemberFactory()
        response = client.post(f'/worship/eligible/{eligible.pk}/edit/', {
            'section_type': ServiceSectionType.PREDICATION,
            'members': [str(member.pk)],
        })
        assert response.status_code == 302
        eligible.refresh_from_db()
        assert eligible.members.count() == 1

    def test_post_invalid(self, client):
        _staff_login(client)
        eligible = EligibleMemberListFactory()
        response = client.post(f'/worship/eligible/{eligible.pk}/edit/', {
            'section_type': '',
        })
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        _member_login(client)
        eligible = EligibleMemberListFactory()
        response = client.get(f'/worship/eligible/{eligible.pk}/edit/')
        assert response.status_code == 302

    def test_404(self, client):
        _staff_login(client)
        response = client.get(f'/worship/eligible/{uuid.uuid4()}/edit/')
        assert response.status_code == 404


# ==================================================================
# Eligible List Delete
# ==================================================================

@pytest.mark.django_db
class TestEligibleListDelete:
    """Tests for eligible_list_delete view."""

    def test_get_confirmation(self, client):
        _staff_login(client)
        eligible = EligibleMemberListFactory()
        response = client.get(f'/worship/eligible/{eligible.pk}/delete/')
        assert response.status_code == 200

    def test_post_deletes(self, client):
        _staff_login(client)
        eligible = EligibleMemberListFactory()
        response = client.post(f'/worship/eligible/{eligible.pk}/delete/')
        assert response.status_code == 302
        from apps.worship.models import EligibleMemberList
        assert not EligibleMemberList.objects.filter(pk=eligible.pk).exists()

    def test_non_staff_denied(self, client):
        _member_login(client)
        eligible = EligibleMemberListFactory()
        response = client.get(f'/worship/eligible/{eligible.pk}/delete/')
        assert response.status_code == 302

    def test_404(self, client):
        _staff_login(client)
        response = client.get(f'/worship/eligible/{uuid.uuid4()}/delete/')
        assert response.status_code == 404
