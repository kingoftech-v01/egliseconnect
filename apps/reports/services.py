"""Reports services."""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear, ExtractMonth
from django.utils import timezone


class DashboardService:
    """Aggregates statistics for the admin dashboard."""

    @staticmethod
    def get_member_stats():
        from apps.members.models import Member

        total = Member.objects.count()
        active = Member.objects.filter(is_active=True).count()
        new_this_month = Member.objects.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()
        new_this_year = Member.objects.filter(
            created_at__year=timezone.now().year
        ).count()

        role_breakdown = Member.objects.values('role').annotate(
            count=Count('id')
        ).order_by('role')

        return {
            'total': total,
            'active': active,
            'inactive': total - active,
            'new_this_month': new_this_month,
            'new_this_year': new_this_year,
            'role_breakdown': list(role_breakdown),
        }

    @staticmethod
    def get_donation_stats(year=None):
        from apps.donations.models import Donation

        year = year or timezone.now().year
        donations = Donation.objects.filter(date__year=year)

        total_amount = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_count = donations.count()
        average_amount = donations.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')

        monthly = donations.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')

        by_type = donations.values('donation_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        by_method = donations.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        return {
            'year': year,
            'total_amount': total_amount,
            'total_count': total_count,
            'average_amount': average_amount,
            'monthly_breakdown': list(monthly),
            'by_type': list(by_type),
            'by_payment_method': list(by_method),
        }

    @staticmethod
    def get_event_stats(year=None):
        from apps.events.models import Event, EventRSVP

        year = year or timezone.now().year
        events = Event.objects.filter(start_datetime__year=year)

        total_events = events.count()
        upcoming = Event.objects.filter(
            start_datetime__gte=timezone.now(),
            is_cancelled=False
        ).count()
        cancelled = events.filter(is_cancelled=True).count()

        by_type = events.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')

        rsvps = EventRSVP.objects.filter(event__start_datetime__year=year)
        total_rsvps = rsvps.count()
        confirmed_rsvps = rsvps.filter(status='confirmed').count()

        return {
            'year': year,
            'total_events': total_events,
            'upcoming': upcoming,
            'cancelled': cancelled,
            'by_type': list(by_type),
            'total_rsvps': total_rsvps,
            'confirmed_rsvps': confirmed_rsvps,
        }

    @staticmethod
    def get_volunteer_stats():
        from apps.volunteers.models import (
            VolunteerPosition, VolunteerSchedule, VolunteerAvailability
        )

        positions = VolunteerPosition.objects.filter(is_active=True)
        total_positions = positions.count()

        availability = VolunteerAvailability.objects.filter(
            is_available=True
        ).values('position__name').annotate(
            count=Count('member', distinct=True)
        ).order_by('-count')

        upcoming_schedules = VolunteerSchedule.objects.filter(
            date__gte=date.today(),
            date__lte=date.today() + timedelta(days=30)
        ).count()

        this_month = VolunteerSchedule.objects.filter(
            date__month=timezone.now().month,
            date__year=timezone.now().year
        )
        confirmed = this_month.filter(status='confirmed').count()
        pending = this_month.filter(status='scheduled').count()

        return {
            'total_positions': total_positions,
            'volunteers_by_position': list(availability),
            'upcoming_schedules': upcoming_schedules,
            'confirmed_this_month': confirmed,
            'pending_this_month': pending,
        }

    @staticmethod
    def get_help_request_stats():
        from apps.help_requests.models import HelpRequest

        total = HelpRequest.objects.count()
        open_requests = HelpRequest.objects.filter(
            status__in=['new', 'in_progress']
        ).count()
        resolved_this_month = HelpRequest.objects.filter(
            status='resolved',
            resolved_at__month=timezone.now().month,
            resolved_at__year=timezone.now().year
        ).count()

        by_urgency = HelpRequest.objects.filter(
            status__in=['new', 'in_progress']
        ).values('urgency').annotate(
            count=Count('id')
        ).order_by('urgency')

        by_category = HelpRequest.objects.values(
            'category__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        return {
            'total': total,
            'open': open_requests,
            'resolved_this_month': resolved_this_month,
            'by_urgency': list(by_urgency),
            'by_category': list(by_category),
        }

    @staticmethod
    def get_upcoming_birthdays(days=7):
        from apps.core.utils import get_upcoming_birthdays

        birthdays = get_upcoming_birthdays(days)
        return [
            {
                'member_id': str(member.id),
                'member_name': member.full_name,
                'birthday': bd.isoformat(),
                'age': bd.year - member.birth_date.year if member.birth_date else None,
                'email': member.email or '',
            }
            for member, bd in birthdays
        ]

    @staticmethod
    def get_dashboard_summary():
        return {
            'members': DashboardService.get_member_stats(),
            'donations': DashboardService.get_donation_stats(),
            'events': DashboardService.get_event_stats(),
            'volunteers': DashboardService.get_volunteer_stats(),
            'help_requests': DashboardService.get_help_request_stats(),
            'upcoming_birthdays': DashboardService.get_upcoming_birthdays(),
            'generated_at': timezone.now().isoformat(),
        }

    @staticmethod
    def get_onboarding_pipeline_stats():
        """Get onboarding pipeline counts for dashboard widget."""
        from apps.members.models import Member
        from apps.core.constants import MembershipStatus

        return {
            'registered': Member.objects.filter(
                membership_status=MembershipStatus.REGISTERED
            ).count(),
            'form_submitted': Member.objects.filter(
                membership_status=MembershipStatus.FORM_SUBMITTED
            ).count(),
            'in_training': Member.objects.filter(
                membership_status=MembershipStatus.IN_TRAINING
            ).count(),
            'interview_scheduled': Member.objects.filter(
                membership_status=MembershipStatus.INTERVIEW_SCHEDULED
            ).count(),
            'total_in_process': Member.objects.filter(
                membership_status__in=MembershipStatus.IN_PROCESS
            ).count(),
        }

    @staticmethod
    def get_financial_summary():
        """Monthly giving trend for dashboard financial widget."""
        from apps.donations.models import Donation

        now = timezone.now()
        months_data = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now

            total = Donation.objects.filter(
                date__gte=month_start.date(),
                date__lt=month_end.date() if i > 0 else (now.date() + timedelta(days=1)),
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            months_data.append({
                'month': month_start.strftime('%b %Y'),
                'total': float(total),
            })

        return {
            'monthly_trend': months_data,
            'labels': [m['month'] for m in months_data],
            'values': [m['total'] for m in months_data],
        }

    @staticmethod
    def get_member_growth_trend():
        """Monthly member registrations for the last 12 months."""
        from apps.members.models import Member

        now = timezone.now()
        labels = []
        counts = []
        for i in range(11, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now

            count = Member.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end if i > 0 else (now + timedelta(days=1)),
            ).count()

            labels.append(month_start.strftime('%b %Y'))
            counts.append(count)

        return {
            'labels': labels,
            'counts': counts,
        }


class ReportService:
    """Generates detailed reports for export or display."""

    @staticmethod
    def get_attendance_report(start_date=None, end_date=None):
        from apps.events.models import Event, EventRSVP

        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        events = Event.objects.filter(
            start_datetime__date__gte=start_date,
            start_datetime__date__lte=end_date,
            is_cancelled=False
        ).select_related('organizer')

        report_data = []
        for event in events:
            rsvps = event.rsvps.all()
            report_data.append({
                'event_id': str(event.id),
                'title': event.title,
                'date': event.start_datetime.date().isoformat(),
                'event_type': event.event_type,
                'total_rsvps': rsvps.count(),
                'confirmed': rsvps.filter(status='confirmed').count(),
                'declined': rsvps.filter(status='declined').count(),
                'total_guests': sum(r.guests for r in rsvps.filter(status='confirmed')),
            })

        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_events': len(report_data),
            'events': report_data,
        }

    @staticmethod
    def get_donation_report(year):
        from apps.donations.models import Donation
        from apps.members.models import Member

        donations = Donation.objects.filter(date__year=year)

        monthly = []
        for month in range(1, 13):
            month_donations = donations.filter(date__month=month)
            monthly.append({
                'month': month,
                'total': month_donations.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
                'count': month_donations.count(),
            })

        # Top donors shown by rank only (anonymized for privacy)
        top_donors = donations.values('member').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]

        donor_data = []
        for i, d in enumerate(top_donors, 1):
            donor_data.append({
                'rank': i,
                'total': d['total'],
            })

        campaign_data = donations.exclude(campaign__isnull=True).values(
            'campaign__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        return {
            'year': year,
            'total': donations.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
            'total_count': donations.count(),
            'unique_donors': donations.values('member').distinct().count(),
            'monthly': monthly,
            'top_donors': donor_data,
            'campaigns': list(campaign_data),
        }

    @staticmethod
    def get_attendance_session_stats(start_date=None, end_date=None):
        """Get attendance session statistics for richer analytics."""
        from apps.attendance.models import AttendanceSession, AttendanceRecord

        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = AttendanceSession.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
        )

        total_sessions = sessions.count()

        by_type = sessions.values('session_type').annotate(
            count=Count('id')
        ).order_by('-count')

        total_checkins = AttendanceRecord.objects.filter(
            session__date__gte=start_date,
            session__date__lte=end_date,
        ).count()

        by_method = AttendanceRecord.objects.filter(
            session__date__gte=start_date,
            session__date__lte=end_date,
        ).values('method').annotate(
            count=Count('id')
        ).order_by('-count')

        avg_per_session = round(total_checkins / total_sessions, 1) if total_sessions > 0 else 0

        return {
            'total_sessions': total_sessions,
            'total_checkins': total_checkins,
            'avg_per_session': avg_per_session,
            'by_type': list(by_type),
            'by_method': list(by_method),
        }

    @staticmethod
    def get_volunteer_report(start_date=None, end_date=None):
        from apps.volunteers.models import VolunteerSchedule, VolunteerPosition

        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        schedules = VolunteerSchedule.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        by_position = schedules.values('position__name').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            no_show=Count('id', filter=Q(status='no_show'))
        ).order_by('-total')

        top_volunteers = schedules.filter(
            status='completed'
        ).values('member__first_name', 'member__last_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_shifts': schedules.count(),
            'completed': schedules.filter(status='completed').count(),
            'no_shows': schedules.filter(status='no_show').count(),
            'by_position': list(by_position),
            'top_volunteers': list(top_volunteers),
        }
