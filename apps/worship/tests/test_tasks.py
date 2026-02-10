"""Tests for worship Celery tasks."""
import pytest
from datetime import date, time, timedelta

from django.utils import timezone

from apps.core.constants import (
    WorshipServiceStatus, AssignmentStatus, Roles,
)
from apps.communication.models import Notification
from apps.members.tests.factories import MemberFactory, PastorFactory
from apps.worship.tasks import (
    send_service_assignment_reminders, check_validation_deadlines,
)
from .factories import (
    WorshipServiceFactory, ServiceSectionFactory, ServiceAssignmentFactory,
)


@pytest.mark.django_db
class TestSendServiceAssignmentReminders:
    """Tests for send_service_assignment_reminders task."""

    def test_5day_reminder(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=5),
            status=WorshipServiceStatus.PLANNED,
        )
        section = ServiceSectionFactory(service=service)
        member = MemberFactory()
        assignment = ServiceAssignmentFactory(
            section=section, member=member,
            status=AssignmentStatus.ASSIGNED,
        )

        total = send_service_assignment_reminders()
        assert total >= 1

        assignment.refresh_from_db()
        assert assignment.reminder_5days_sent is True
        assert Notification.objects.filter(
            member=member, title='Rappel de culte'
        ).exists()

    def test_3day_reminder(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=3),
            status=WorshipServiceStatus.CONFIRMED,
        )
        section = ServiceSectionFactory(service=service)
        member = MemberFactory()
        assignment = ServiceAssignmentFactory(
            section=section, member=member,
            status=AssignmentStatus.CONFIRMED,
            reminder_5days_sent=True,
        )

        total = send_service_assignment_reminders()
        assert total >= 1

        assignment.refresh_from_db()
        assert assignment.reminder_3days_sent is True

    def test_1day_reminder(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=1),
            status=WorshipServiceStatus.CONFIRMED,
        )
        section = ServiceSectionFactory(service=service)
        member = MemberFactory()
        assignment = ServiceAssignmentFactory(
            section=section, member=member,
            status=AssignmentStatus.ASSIGNED,
            reminder_5days_sent=True,
            reminder_3days_sent=True,
        )

        total = send_service_assignment_reminders()
        assert total >= 1

        assignment.refresh_from_db()
        assert assignment.reminder_1day_sent is True

    def test_sameday_reminder(self):
        service = WorshipServiceFactory(
            date=timezone.now().date(),
            status=WorshipServiceStatus.CONFIRMED,
        )
        section = ServiceSectionFactory(service=service)
        member = MemberFactory()
        assignment = ServiceAssignmentFactory(
            section=section, member=member,
            status=AssignmentStatus.ASSIGNED,
            reminder_5days_sent=True,
            reminder_3days_sent=True,
            reminder_1day_sent=True,
        )

        total = send_service_assignment_reminders()
        assert total >= 1

        assignment.refresh_from_db()
        assert assignment.reminder_sameday_sent is True

    def test_no_duplicate_reminders(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=5),
            status=WorshipServiceStatus.PLANNED,
        )
        section = ServiceSectionFactory(service=service)
        member = MemberFactory()
        ServiceAssignmentFactory(
            section=section, member=member,
            status=AssignmentStatus.ASSIGNED,
            reminder_5days_sent=True,
        )

        total = send_service_assignment_reminders()
        # 5-day already sent, next would be 3-day at <=3 days
        # At 5 days out, only 5-day applies — so 0 sent
        assert total == 0

    def test_no_reminders_for_past_services(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() - timedelta(days=1),
            status=WorshipServiceStatus.COMPLETED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(section=section)

        total = send_service_assignment_reminders()
        assert total == 0

    def test_no_reminders_for_cancelled(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=3),
            status=WorshipServiceStatus.CANCELLED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(section=section)

        total = send_service_assignment_reminders()
        assert total == 0

    def test_no_reminders_for_declined(self):
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=3),
            status=WorshipServiceStatus.PLANNED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(
            section=section, status=AssignmentStatus.DECLINED,
        )

        total = send_service_assignment_reminders()
        assert total == 0


@pytest.mark.django_db
class TestCheckValidationDeadlines:
    """Tests for check_validation_deadlines task."""

    def test_overdue_alerts_admins(self):
        pastor = PastorFactory()
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=7),
            validation_deadline=timezone.now().date() - timedelta(days=1),
            status=WorshipServiceStatus.PLANNED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(
            section=section, status=AssignmentStatus.ASSIGNED,
        )

        check_validation_deadlines()
        assert Notification.objects.filter(
            member=pastor,
            title='Deadline de validation dépassée',
        ).exists()

    def test_no_alert_if_all_confirmed(self):
        pastor = PastorFactory()
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=7),
            validation_deadline=timezone.now().date() - timedelta(days=1),
            status=WorshipServiceStatus.PLANNED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(
            section=section, status=AssignmentStatus.CONFIRMED,
        )

        check_validation_deadlines()
        assert not Notification.objects.filter(
            member=pastor,
            title='Deadline de validation dépassée',
        ).exists()

    def test_no_alert_if_not_overdue(self):
        pastor = PastorFactory()
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=21),
            validation_deadline=timezone.now().date() + timedelta(days=7),
            status=WorshipServiceStatus.PLANNED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(
            section=section, status=AssignmentStatus.ASSIGNED,
        )

        check_validation_deadlines()
        assert not Notification.objects.filter(
            member=pastor,
            title='Deadline de validation dépassée',
        ).exists()

    def test_no_alert_for_confirmed_service(self):
        pastor = PastorFactory()
        service = WorshipServiceFactory(
            date=timezone.now().date() + timedelta(days=7),
            validation_deadline=timezone.now().date() - timedelta(days=1),
            status=WorshipServiceStatus.CONFIRMED,
        )
        section = ServiceSectionFactory(service=service)
        ServiceAssignmentFactory(
            section=section, status=AssignmentStatus.ASSIGNED,
        )

        check_validation_deadlines()
        assert not Notification.objects.filter(
            member=pastor,
            title='Deadline de validation dépassée',
        ).exists()
