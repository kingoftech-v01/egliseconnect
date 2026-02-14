"""Business logic for worship service planning."""
from datetime import timedelta
from collections import Counter

from django.utils import timezone
from django.db.models import Count, Q

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
                f'Vous \u00eates assign\u00e9(e) \u00e0 "{section.name}" pour le culte du '
                f'{service.date:%d/%m/%Y}. Veuillez confirmer votre pr\u00e9sence.'
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
                    title='Assignation d\u00e9clin\u00e9e',
                    message=(
                        f'{assignment.member.full_name} a d\u00e9clin\u00e9 son assignation '
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


class SongUsageTracker:
    """Track song usage when services are completed."""

    @staticmethod
    def record_service_songs(service):
        """Increment play_count and update last_played for all songs in a service's setlist."""
        from .models import Setlist

        try:
            setlist = Setlist.objects.get(service=service)
        except Setlist.DoesNotExist:
            return 0

        count = 0
        for setlist_song in setlist.songs.select_related('song').all():
            song = setlist_song.song
            song.play_count += 1
            song.last_played = service.date
            song.save(update_fields=['play_count', 'last_played', 'updated_at'])
            count += 1
        return count


class SongRotationService:
    """Suggest songs that haven't been played recently."""

    @staticmethod
    def get_rotation_suggestions(weeks=6, limit=20):
        """Return songs not played in the last X weeks, ordered by last_played."""
        from .models import Song

        cutoff = timezone.now().date() - timedelta(weeks=weeks)
        return Song.objects.filter(
            Q(last_played__lt=cutoff) | Q(last_played__isnull=True)
        ).order_by('last_played', 'title')[:limit]


class AutoScheduleService:
    """Auto-schedule volunteers based on eligibility and rotation fairness."""

    @staticmethod
    def generate_schedule(service):
        """
        Auto-assign eligible members to unfilled sections of a service.
        Uses round-robin based on assignment count (least-assigned first).
        Returns list of created assignments.
        """
        from .models import (
            ServiceSection, ServiceAssignment, EligibleMemberList,
            VolunteerPreference,
        )

        created = []
        sections = service.sections.all().order_by('order')

        for section in sections:
            # Skip sections that already have assignments
            if section.assignments.exists():
                continue

            # Find eligible members for this section type
            try:
                eligible_list = EligibleMemberList.objects.get(
                    section_type=section.section_type
                )
            except EligibleMemberList.DoesNotExist:
                continue

            eligible_members = list(eligible_list.members.filter(is_active=True))
            if not eligible_members:
                continue

            # Filter out blackout dates
            service_date_str = service.date.isoformat()
            available = []
            for m in eligible_members:
                try:
                    pref = m.worship_preference
                    if service_date_str in pref.blackout_dates:
                        continue
                except VolunteerPreference.DoesNotExist:
                    pass
                available.append(m)

            if not available:
                continue

            # Filter out members already assigned to another section in this service
            already_assigned = set(
                ServiceAssignment.objects.filter(
                    section__service=service
                ).values_list('member_id', flat=True)
            )
            available = [m for m in available if m.pk not in already_assigned]

            if not available:
                continue

            # Sort by assignment count (least-assigned first for fairness)
            assignment_counts = Counter()
            for m in available:
                assignment_counts[m.pk] = ServiceAssignment.objects.filter(
                    member=m,
                    section__service__date__gte=timezone.now().date() - timedelta(days=90),
                ).count()

            available.sort(key=lambda m: assignment_counts[m.pk])

            # Assign the least-assigned member
            chosen = available[0]
            assignment = ServiceAssignment.objects.create(
                section=section,
                member=chosen,
                status=AssignmentStatus.ASSIGNED,
            )
            created.append(assignment)

        return created

    @staticmethod
    def detect_conflicts(service):
        """Detect members assigned to multiple sections in the same service."""
        from .models import ServiceAssignment

        assignments = ServiceAssignment.objects.filter(
            section__service=service
        ).values('member').annotate(count=Count('id')).filter(count__gt=1)

        conflicts = []
        for entry in assignments:
            member_assignments = ServiceAssignment.objects.filter(
                section__service=service,
                member_id=entry['member'],
            ).select_related('section', 'member')
            conflicts.append({
                'member_id': entry['member'],
                'member_name': member_assignments.first().member.full_name,
                'sections': [a.section.name for a in member_assignments],
                'count': entry['count'],
            })
        return conflicts
