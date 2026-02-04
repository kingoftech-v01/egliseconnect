"""Reports services - Business logic for generating reports and statistics."""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear, ExtractMonth
from django.utils import timezone


class DashboardService:
    """Service for generating dashboard statistics."""

    @staticmethod
    def get_member_stats():
        """Get member statistics."""
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

        # Role breakdown
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
        """Get donation statistics."""
        from apps.donations.models import Donation

        year = year or timezone.now().year
        donations = Donation.objects.filter(date__year=year)

        total_amount = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_count = donations.count()
        average_amount = donations.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')

        # Monthly breakdown
        monthly = donations.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')

        # By type
        by_type = donations.values('donation_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        # By payment method
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
        """Get event statistics."""
        from apps.events.models import Event, EventRSVP

        year = year or timezone.now().year
        events = Event.objects.filter(start_datetime__year=year)

        total_events = events.count()
        upcoming = Event.objects.filter(
            start_datetime__gte=timezone.now(),
            is_cancelled=False
        ).count()
        cancelled = events.filter(is_cancelled=True).count()

        # By type
        by_type = events.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # RSVP stats
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
        """Get volunteer statistics."""
        from apps.volunteers.models import (
            VolunteerPosition, VolunteerSchedule, VolunteerAvailability
        )

        positions = VolunteerPosition.objects.filter(is_active=True)
        total_positions = positions.count()

        # Volunteers per position
        availability = VolunteerAvailability.objects.filter(
            is_available=True
        ).values('position__name').annotate(
            count=Count('member', distinct=True)
        ).order_by('-count')

        # Upcoming schedules
        upcoming_schedules = VolunteerSchedule.objects.filter(
            date__gte=date.today(),
            date__lte=date.today() + timedelta(days=30)
        ).count()

        # Confirmed vs pending
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
        """Get help request statistics."""
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

        # By urgency
        by_urgency = HelpRequest.objects.filter(
            status__in=['new', 'in_progress']
        ).values('urgency').annotate(
            count=Count('id')
        ).order_by('urgency')

        # By category
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
        """Get upcoming birthdays."""
        from apps.core.utils import get_upcoming_birthdays

        birthdays = get_upcoming_birthdays(days)
        return [
            {
                'member_id': str(member.id),
                'member_name': member.full_name,
                'birthday': bd.isoformat(),
                'age': bd.year - member.birth_date.year if member.birth_date else None
            }
            for member, bd in birthdays
        ]

    @staticmethod
    def get_dashboard_summary():
        """Get complete dashboard summary."""
        return {
            'members': DashboardService.get_member_stats(),
            'donations': DashboardService.get_donation_stats(),
            'events': DashboardService.get_event_stats(),
            'volunteers': DashboardService.get_volunteer_stats(),
            'help_requests': DashboardService.get_help_request_stats(),
            'upcoming_birthdays': DashboardService.get_upcoming_birthdays(),
            'generated_at': timezone.now().isoformat(),
        }


class ReportService:
    """Service for generating detailed reports."""

    @staticmethod
    def get_attendance_report(start_date=None, end_date=None):
        """Get attendance report for events."""
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
        """Get detailed annual donation report."""
        from apps.donations.models import Donation
        from apps.members.models import Member

        donations = Donation.objects.filter(date__year=year)

        # Monthly totals
        monthly = []
        for month in range(1, 13):
            month_donations = donations.filter(date__month=month)
            monthly.append({
                'month': month,
                'total': month_donations.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
                'count': month_donations.count(),
            })

        # Top donors (anonymized)
        top_donors = donations.values('member').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]

        donor_data = []
        for i, d in enumerate(top_donors, 1):
            donor_data.append({
                'rank': i,
                'total': d['total'],
            })

        # Campaign performance
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
    def get_volunteer_report(start_date=None, end_date=None):
        """Get volunteer activity report."""
        from apps.volunteers.models import VolunteerSchedule, VolunteerPosition

        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        schedules = VolunteerSchedule.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        # By position
        by_position = schedules.values('position__name').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            no_show=Count('id', filter=Q(status='no_show'))
        ).order_by('-total')

        # Most active volunteers
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
