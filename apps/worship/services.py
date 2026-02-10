"""Business logic for worship service planning."""
from datetime import timedelta

from django.utils import timezone

from apps.core.constants import (
    WorshipServiceStatus, AssignmentStatus, Roles,
)
from apps.communication.models import Notification


class WorshipServiceManager:
    """Manages worship service lifecycle."""

    @staticmethod
    def create_service(date, start_time, created_by, theme='', notes='',
                       duration_minutes=120, end_time=None):
        """Create a new worship service with auto validation deadline."""
        from .models import WorshipService

        service = WorshipService.objects.create(
            date=date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            theme=theme,
            notes=notes,
            created_by=created_by,
            status=WorshipServiceStatus.DRAFT,
        )
        return service

    @staticmethod
    def add_section(service, name, order, section_type, duration_minutes=15,
                    department=None, notes=''):
        """Add a section to a service."""
        from .models import ServiceSection

        section = ServiceSection.objects.create(
            service=service,
            name=name,
            order=order,
            section_type=section_type,
            duration_minutes=duration_minutes,
            department=department,
            notes=notes,
        )
        return section

    @staticmethod
    def assign_member(section, member, task_type=None, notes=''):
        """Assign a member to a section and notify them."""
        from .models import ServiceAssignment

        assignment = ServiceAssignment.objects.create(
            section=section,
            member=member,
            task_type=task_type,
            notes=notes,
            status=AssignmentStatus.ASSIGNED,
        )

        service = section.service
        Notification.objects.create(
            member=member,
            title='Nouvelle assignation de culte',
            message=(
                f'Vous êtes assigné(e) à "{section.name}" pour le culte du '
                f'{service.date:%d/%m/%Y}. Veuillez confirmer votre présence.'
            ),
            notification_type='general',
            link='/worship/my-assignments/',
        )
        return assignment

    @staticmethod
    def member_respond(assignment, accepted):
        """Member confirms or declines an assignment."""
        assignment.responded_at = timezone.now()

        if accepted:
            assignment.status = AssignmentStatus.CONFIRMED
        else:
            assignment.status = AssignmentStatus.DECLINED

        assignment.save(update_fields=['status', 'responded_at', 'updated_at'])

        # Notify admin if declined
        if not accepted:
            from apps.members.models import Member
            admins = Member.objects.filter(role__in=[Roles.ADMIN, Roles.PASTOR])
            service = assignment.section.service
            for admin in admins:
                Notification.objects.create(
                    member=admin,
                    title='Assignation déclinée',
                    message=(
                        f'{assignment.member.full_name} a décliné son assignation '
                        f'"{assignment.section.name}" pour le culte du '
                        f'{service.date:%d/%m/%Y}.'
                    ),
                    notification_type='general',
                    link=f'/worship/services/{service.pk}/',
                )

        return assignment

    @staticmethod
    def update_service_status(service, new_status):
        """Update a service's status."""
        service.status = new_status
        service.save(update_fields=['status', 'updated_at'])
        return service
