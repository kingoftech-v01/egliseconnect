"""Tests for worship models."""
import pytest
from datetime import date, time, timedelta

from django.utils import timezone

from apps.core.constants import (
    WorshipServiceStatus, ServiceSectionType, AssignmentStatus,
)
from apps.members.tests.factories import MemberFactory
from .factories import (
    WorshipServiceFactory, ServiceSectionFactory,
    ServiceAssignmentFactory, EligibleMemberListFactory,
)


@pytest.mark.django_db
class TestWorshipService:
    """Tests for WorshipService model."""

    def test_create(self):
        service = WorshipServiceFactory()
        assert service.id is not None
        assert service.status == WorshipServiceStatus.DRAFT

    def test_str(self):
        service = WorshipServiceFactory(
            date=date(2026, 3, 15), start_time=time(10, 0)
        )
        assert '15/03/2026' in str(service)
        assert '10:00' in str(service)

    def test_auto_validation_deadline(self):
        service = WorshipServiceFactory(
            date=date(2026, 4, 1), validation_deadline=None
        )
        assert service.validation_deadline == date(2026, 3, 18)

    def test_explicit_validation_deadline_kept(self):
        deadline = date(2026, 3, 20)
        service = WorshipServiceFactory(
            date=date(2026, 4, 1), validation_deadline=deadline
        )
        assert service.validation_deadline == deadline

    def test_ordering(self):
        s1 = WorshipServiceFactory(date=date(2026, 1, 1))
        s2 = WorshipServiceFactory(date=date(2026, 2, 1))
        from apps.worship.models import WorshipService
        services = list(WorshipService.objects.all())
        assert services[0].pk == s2.pk  # Newest first

    def test_confirmation_rate_zero(self):
        service = WorshipServiceFactory()
        assert service.confirmation_rate == 0

    def test_confirmation_rate(self):
        service = WorshipServiceFactory()
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(section=section, status=AssignmentStatus.CONFIRMED)
        ServiceAssignmentFactory(section=section, status=AssignmentStatus.ASSIGNED)
        assert service.confirmation_rate == 50

    def test_total_assignments(self):
        service = WorshipServiceFactory()
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(section=section)
        ServiceAssignmentFactory(section=section)
        assert service.total_assignments == 2

    def test_confirmed_assignments(self):
        service = WorshipServiceFactory()
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(section=section, status=AssignmentStatus.CONFIRMED)
        ServiceAssignmentFactory(section=section, status=AssignmentStatus.ASSIGNED)
        assert service.confirmed_assignments == 1


@pytest.mark.django_db
class TestServiceSection:
    """Tests for ServiceSection model."""

    def test_create(self):
        section = ServiceSectionFactory()
        assert section.id is not None

    def test_str(self):
        section = ServiceSectionFactory(order=1, name='Louange')
        assert str(section) == '1. Louange'

    def test_ordering(self):
        service = WorshipServiceFactory()
        s2 = ServiceSectionFactory(service=service, order=2, name='B')
        s1 = ServiceSectionFactory(service=service, order=1, name='A')
        from apps.worship.models import ServiceSection
        sections = list(ServiceSection.objects.filter(service=service))
        assert sections[0].pk == s1.pk

    def test_unique_together(self):
        service = WorshipServiceFactory()
        ServiceSectionFactory(service=service, order=1)
        with pytest.raises(Exception):
            ServiceSectionFactory(service=service, order=1)


@pytest.mark.django_db
class TestServiceAssignment:
    """Tests for ServiceAssignment model."""

    def test_create(self):
        assignment = ServiceAssignmentFactory()
        assert assignment.id is not None
        assert assignment.status == AssignmentStatus.ASSIGNED

    def test_str(self):
        member = MemberFactory(first_name='Jean', last_name='Dupont')
        section = ServiceSectionFactory(name='Louange')
        assignment = ServiceAssignmentFactory(section=section, member=member)
        assert 'Jean Dupont' in str(assignment)
        assert 'Louange' in str(assignment)

    def test_unique_together(self):
        section = ServiceSectionFactory()
        member = MemberFactory()
        ServiceAssignmentFactory(section=section, member=member)
        with pytest.raises(Exception):
            ServiceAssignmentFactory(section=section, member=member)

    def test_default_reminder_flags(self):
        assignment = ServiceAssignmentFactory()
        assert assignment.reminder_5days_sent is False
        assert assignment.reminder_3days_sent is False
        assert assignment.reminder_1day_sent is False
        assert assignment.reminder_sameday_sent is False


@pytest.mark.django_db
class TestEligibleMemberList:
    """Tests for EligibleMemberList model."""

    def test_create(self):
        eligible = EligibleMemberListFactory()
        assert eligible.id is not None

    def test_str(self):
        eligible = EligibleMemberListFactory(section_type=ServiceSectionType.LOUANGE)
        assert 'Louange' in str(eligible)

    def test_unique_section_type(self):
        EligibleMemberListFactory(section_type=ServiceSectionType.LOUANGE)
        with pytest.raises(Exception):
            EligibleMemberListFactory(section_type=ServiceSectionType.LOUANGE)

    def test_add_members(self):
        eligible = EligibleMemberListFactory()
        m1 = MemberFactory()
        m2 = MemberFactory()
        eligible.members.add(m1, m2)
        assert eligible.members.count() == 2
