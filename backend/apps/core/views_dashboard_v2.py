"""Dashboard stats API v2 endpoint."""
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class DashboardStatsView(APIView):
    """GET /api/v2/core/dashboard/ - Returns all dashboard statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # Import models
        from apps.members.models import Member
        from apps.donations.models import Donation
        from apps.events.models import Event
        from apps.volunteers.models import VolunteerProfile
        from apps.help_requests.models import HelpRequest
        from apps.attendance.models import AttendanceRecord, AttendanceSession

        # Members stats
        total_members = Member.objects.count()
        active_members = Member.objects.filter(membership_status='active').count()
        new_this_month = Member.objects.filter(created_at__gte=month_start).count()

        prev_month_count = Member.objects.filter(created_at__lt=month_start).count()
        growth_rate = round((new_this_month / max(prev_month_count, 1)) * 100, 1)

        # Donations stats
        donations_this_month = Donation.objects.filter(date__gte=month_start)
        donations_this_year = Donation.objects.filter(date__gte=year_start)
        donation_month_agg = donations_this_month.aggregate(
            total=Sum('amount'),
            count=Count('id'),
            average=Avg('amount'),
        )
        donation_year_total = donations_this_year.aggregate(total=Sum('amount'))['total'] or 0

        # Events stats
        upcoming_events = Event.objects.filter(start_date__gte=now).count()
        events_this_month = Event.objects.filter(start_date__gte=month_start, start_date__lte=now.replace(day=28) + timedelta(days=4)).count()

        # Attendance stats
        try:
            last_sunday_sessions = AttendanceSession.objects.filter(
                session_type='worship',
                date__gte=now - timedelta(days=7),
            )
            last_sunday_count = AttendanceRecord.objects.filter(
                session__in=last_sunday_sessions
            ).count()
        except Exception:
            last_sunday_count = 0

        # Volunteers stats
        try:
            active_volunteers = VolunteerProfile.objects.filter(is_active=True).count()
        except Exception:
            active_volunteers = 0

        # Help requests stats
        try:
            open_help = HelpRequest.objects.filter(
                status__in=['new', 'in_progress']
            ).count()
            resolved_this_month = HelpRequest.objects.filter(
                status='resolved',
                updated_at__gte=month_start,
            ).count()
        except Exception:
            open_help = 0
            resolved_this_month = 0

        # Recent activities (last 10 events from across the system)
        recent_activities = self._get_recent_activities(now)

        # Upcoming events (next 5)
        upcoming_events_list = self._get_upcoming_events(now)

        # Monthly giving trends (last 6 months)
        giving_trends = self._get_giving_trends(month_start)

        return Response({
            'members': {
                'total': total_members,
                'active': active_members,
                'new_this_month': new_this_month,
                'growth_rate': growth_rate,
            },
            'donations': {
                'total_this_month': str(donation_month_agg['total'] or 0),
                'total_this_year': str(donation_year_total),
                'count_this_month': donation_month_agg['count'] or 0,
                'average': str(round(donation_month_agg['average'] or 0, 2)),
            },
            'events': {
                'upcoming_count': upcoming_events,
                'this_month_count': events_this_month,
                'total_attendees_this_month': 0,
            },
            'attendance': {
                'average_rate': 0,
                'last_sunday_count': last_sunday_count,
            },
            'volunteers': {
                'active_count': active_volunteers,
                'hours_this_month': 0,
            },
            'help_requests': {
                'open_count': open_help,
                'resolved_this_month': resolved_this_month,
            },
            'recent_activities': recent_activities,
            'upcoming_events': upcoming_events_list,
            'giving_trends': giving_trends,
        })

    def _get_recent_activities(self, now):
        """Gather recent activities from across the system."""
        from apps.members.models import Member
        from apps.donations.models import Donation
        from apps.events.models import Event
        from apps.help_requests.models import HelpRequest

        activities = []
        cutoff = now - timedelta(days=7)

        # New members
        for m in Member.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:3]:
            activities.append({
                'id': str(m.pk),
                'type': 'member',
                'description': 'Nouveau membre inscrit',
                'name': m.full_name,
                'time': m.created_at.isoformat(),
            })

        # Recent donations
        for d in Donation.objects.filter(date__gte=cutoff.date()).order_by('-date')[:3]:
            activities.append({
                'id': str(d.pk),
                'type': 'donation',
                'description': 'Don reçu',
                'name': f'{d.amount} $',
                'time': d.created_at.isoformat() if hasattr(d, 'created_at') and d.created_at else d.date.isoformat(),
            })

        # Recent events created
        for e in Event.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:2]:
            activities.append({
                'id': str(e.pk),
                'type': 'event',
                'description': 'Événement créé',
                'name': e.title,
                'time': e.created_at.isoformat(),
            })

        # Resolved help requests
        for h in HelpRequest.objects.filter(status='resolved', updated_at__gte=cutoff).order_by('-updated_at')[:2]:
            activities.append({
                'id': str(h.pk),
                'type': 'help',
                'description': "Demande d'aide résolue",
                'name': h.subject,
                'time': h.updated_at.isoformat(),
            })

        # Sort by time descending, take top 10
        activities.sort(key=lambda a: a['time'], reverse=True)
        return activities[:10]

    def _get_upcoming_events(self, now):
        """Get the next 5 upcoming events."""
        from apps.events.models import Event, EventRSVP

        events = Event.objects.filter(
            start_date__gte=now,
            is_published=True,
            is_cancelled=False,
        ).order_by('start_date')[:5]

        result = []
        for event in events:
            attendees = EventRSVP.objects.filter(event=event, status='confirmed').count()
            result.append({
                'id': str(event.pk),
                'title': event.title,
                'date': event.start_date.isoformat(),
                'type': event.event_type,
                'attendees': attendees,
            })
        return result

    def _get_giving_trends(self, month_start):
        """Get monthly giving totals for the last 6 months."""
        from apps.donations.models import Donation

        trends = []
        for i in range(5, -1, -1):
            m_start = (month_start - timedelta(days=1)).replace(day=1)
            # Calculate month boundaries
            if i > 0:
                target = month_start
                for _ in range(i):
                    target = (target - timedelta(days=1)).replace(day=1)
                m_start = target
                m_end = (m_start + timedelta(days=32)).replace(day=1)
            else:
                m_start = month_start
                m_end = (m_start + timedelta(days=32)).replace(day=1)

            total = Donation.objects.filter(
                date__gte=m_start.date(),
                date__lt=m_end.date(),
            ).aggregate(total=Sum('amount'))['total'] or 0

            trends.append({
                'month': m_start.strftime('%b'),
                'amount': float(total),
            })

        # Calculate percentages relative to max
        max_amount = max((t['amount'] for t in trends), default=1) or 1
        for t in trends:
            t['pct'] = round((t['amount'] / max_amount) * 100)

        return trends
