"""Factories for worship app tests."""
import factory
from datetime import time, timedelta

from django.utils import timezone

from apps.core.constants import (
    WorshipServiceStatus, ServiceSectionType, AssignmentStatus,
)
from apps.members.tests.factories import MemberFactory
from apps.worship.models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
)


class WorshipServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorshipService

    date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=14)).date())
    start_time = factory.LazyFunction(lambda: time(10, 0))
    duration_minutes = 120
    status = WorshipServiceStatus.DRAFT
    theme = factory.Sequence(lambda n: f'Thème {n}')
    created_by = factory.SubFactory(MemberFactory)


class ServiceSectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceSection

    service = factory.SubFactory(WorshipServiceFactory)
    name = factory.Sequence(lambda n: f'Section {n}')
    order = factory.Sequence(lambda n: n + 1)
    section_type = ServiceSectionType.LOUANGE
    duration_minutes = 15


class ServiceAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceAssignment

    section = factory.SubFactory(ServiceSectionFactory)
    member = factory.SubFactory(MemberFactory)
    status = AssignmentStatus.ASSIGNED


class EligibleMemberListFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EligibleMemberList

    section_type = ServiceSectionType.LOUANGE
