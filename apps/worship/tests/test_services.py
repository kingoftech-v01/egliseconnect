"""Tests for worship service layer."""
import pytest
from datetime import date, time, timedelta

from django.utils import timezone

from apps.core.constants import (
    WorshipServiceStatus, ServiceSectionType, AssignmentStatus, Roles,
)
from apps.communication.models import Notification
from apps.members.tests.factories import MemberFactory, PastorFactory
from apps.worship.services import WorshipServiceManager
from .factories import (
    WorshipServiceFactory, ServiceSectionFactory, ServiceAssignmentFactory,
)


@pytest.mark.django_db
class TestWorshipServiceManagerCreateService:
    """Tests for WorshipServiceManager.create_service."""

    def test_create_service(self):
        member = PastorFactory()
        service = WorshipServiceManager.create_service(
            date=date(2026, 4, 5),
            start_time=time(10, 0),
            created_by=member,
            theme='Pâques',
        )
        assert service.id is not None
        assert service.status == WorshipServiceStatus.DRAFT
        assert service.theme == 'Pâques'
        assert service.created_by == member

    def test_auto_validation_deadline(self):
        service = WorshipServiceManager.create_service(
            date=date(2026, 5, 10),
            start_time=time(10, 0),
            created_by=PastorFactory(),
        )
        assert service.validation_deadline == date(2026, 4, 26)

    def test_with_end_time(self):
        service = WorshipServiceManager.create_service(
            date=date(2026, 5, 10),
            start_time=time(10, 0),
            end_time=time(12, 0),
            created_by=PastorFactory(),
        )
        assert service.end_time == time(12, 0)


@pytest.mark.django_db
class TestWorshipServiceManagerAddSection:
    """Tests for WorshipServiceManager.add_section."""

    def test_add_section(self):
        service = WorshipServiceFactory()
        section = WorshipServiceManager.add_section(
            service=service,
            name='Louange',
            order=1,
            section_type=ServiceSectionType.LOUANGE,
            duration_minutes=20,
        )
        assert section.id is not None
        assert section.service == service
        assert section.name == 'Louange'
        assert section.order == 1

    def test_add_section_with_notes(self):
        service = WorshipServiceFactory()
        section = WorshipServiceManager.add_section(
            service=service,
            name='Prédication',
            order=2,
            section_type=ServiceSectionType.PREDICATION,
            notes='Pasteur principal',
        )
        assert section.notes == 'Pasteur principal'


@pytest.mark.django_db
class TestWorshipServiceManagerAssignMember:
    """Tests for WorshipServiceManager.assign_member."""

    def test_assign_member(self):
        section = ServiceSectionFactory()
        member = MemberFactory()
        assignment = WorshipServiceManager.assign_member(
            section=section, member=member,
        )
        assert assignment.id is not None
        assert assignment.status == AssignmentStatus.ASSIGNED
        assert assignment.member == member

    def test_assign_member_creates_notification(self):
        section = ServiceSectionFactory()
        member = MemberFactory()
        WorshipServiceManager.assign_member(section=section, member=member)
        assert Notification.objects.filter(
            member=member, title='Nouvelle assignation de culte'
        ).exists()

    def test_assign_with_notes(self):
        section = ServiceSectionFactory()
        member = MemberFactory()
        assignment = WorshipServiceManager.assign_member(
            section=section, member=member, notes='Caméra 1',
        )
        assert assignment.notes == 'Caméra 1'


@pytest.mark.django_db
class TestWorshipServiceManagerMemberRespond:
    """Tests for WorshipServiceManager.member_respond."""

    def test_confirm(self):
        assignment = ServiceAssignmentFactory()
        WorshipServiceManager.member_respond(assignment, accepted=True)
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.CONFIRMED
        assert assignment.responded_at is not None

    def test_decline(self):
        assignment = ServiceAssignmentFactory()
        WorshipServiceManager.member_respond(assignment, accepted=False)
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.DECLINED

    def test_decline_notifies_admins(self):
        pastor = PastorFactory()
        assignment = ServiceAssignmentFactory()
        WorshipServiceManager.member_respond(assignment, accepted=False)
        assert Notification.objects.filter(
            member=pastor, title='Assignation déclinée'
        ).exists()

    def test_confirm_does_not_notify_admins(self):
        pastor = PastorFactory()
        initial_count = Notification.objects.filter(member=pastor).count()
        assignment = ServiceAssignmentFactory()
        WorshipServiceManager.member_respond(assignment, accepted=True)
        assert Notification.objects.filter(member=pastor).count() == initial_count


@pytest.mark.django_db
class TestWorshipServiceManagerUpdateStatus:
    """Tests for WorshipServiceManager.update_service_status."""

    def test_update_to_planned(self):
        service = WorshipServiceFactory(status=WorshipServiceStatus.DRAFT)
        WorshipServiceManager.update_service_status(
            service, WorshipServiceStatus.PLANNED
        )
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.PLANNED

    def test_update_to_confirmed(self):
        service = WorshipServiceFactory(status=WorshipServiceStatus.PLANNED)
        WorshipServiceManager.update_service_status(
            service, WorshipServiceStatus.CONFIRMED
        )
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.CONFIRMED

    def test_update_to_completed(self):
        service = WorshipServiceFactory(status=WorshipServiceStatus.CONFIRMED)
        WorshipServiceManager.update_service_status(
            service, WorshipServiceStatus.COMPLETED
        )
        service.refresh_from_db()
        assert service.status == WorshipServiceStatus.COMPLETED
