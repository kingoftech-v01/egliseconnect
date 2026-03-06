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

    # ------------------------------------------------------------------
    # TODO 6: Communication analytics
    # ------------------------------------------------------------------

    @staticmethod
    def get_communication_stats():
        """Get newsletter/communication analytics for Chart.js."""
        from apps.communication.models import Newsletter, NewsletterRecipient

        newsletters = Newsletter.objects.filter(status='sent').order_by('sent_at')

        monthly_sends = {}
        monthly_opens = {}
        for nl in newsletters:
            if nl.sent_at:
                key = nl.sent_at.strftime('%b %Y')
                monthly_sends[key] = monthly_sends.get(key, 0) + 1
                monthly_opens[key] = monthly_opens.get(key, 0) + nl.opened_count

        labels = list(monthly_sends.keys())[-12:]
        sends = [monthly_sends.get(l, 0) for l in labels]
        opens = [monthly_opens.get(l, 0) for l in labels]

        total_sent = Newsletter.objects.filter(status='sent').count()
        total_recipients = NewsletterRecipient.objects.filter(
            newsletter__status='sent'
        ).count()
        total_opened = NewsletterRecipient.objects.filter(
            newsletter__status='sent',
            opened_at__isnull=False,
        ).count()
        open_rate = round(total_opened / total_recipients * 100, 1) if total_recipients > 0 else 0

        return {
            'labels': labels,
            'sends': sends,
            'opens': opens,
            'total_sent': total_sent,
            'total_recipients': total_recipients,
            'total_opened': total_opened,
            'open_rate': open_rate,
        }

    # ------------------------------------------------------------------
    # TODO 14: Year-over-Year Comparison
    # ------------------------------------------------------------------

    @staticmethod
    def get_yoy_comparison(year):
        """Full YoY comparison across all metrics."""
        from apps.members.models import Member
        from apps.donations.models import Donation
        from apps.events.models import Event
        from apps.volunteers.models import VolunteerSchedule

        prev_year = year - 1

        # Members
        members_current = Member.objects.filter(created_at__year=year).count()
        members_prev = Member.objects.filter(created_at__year=prev_year).count()

        # Donations
        donations_current = Donation.objects.filter(date__year=year).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        donations_prev = Donation.objects.filter(date__year=prev_year).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        donation_count_current = Donation.objects.filter(date__year=year).count()
        donation_count_prev = Donation.objects.filter(date__year=prev_year).count()

        # Events
        events_current = Event.objects.filter(
            start_datetime__year=year, is_cancelled=False).count()
        events_prev = Event.objects.filter(
            start_datetime__year=prev_year, is_cancelled=False).count()

        # Volunteers
        vol_current = VolunteerSchedule.objects.filter(
            date__year=year, status='completed').count()
        vol_prev = VolunteerSchedule.objects.filter(
            date__year=prev_year, status='completed').count()

        def _change_pct(current, previous):
            if previous > 0:
                return round((current - previous) / previous * 100, 1)
            return 0

        return {
            'year': year,
            'prev_year': prev_year,
            'members': {
                'current': members_current,
                'previous': members_prev,
                'change_pct': _change_pct(members_current, members_prev),
            },
            'donations': {
                'current': float(donations_current),
                'previous': float(donations_prev),
                'change_pct': _change_pct(float(donations_current), float(donations_prev)),
            },
            'donation_count': {
                'current': donation_count_current,
                'previous': donation_count_prev,
                'change_pct': _change_pct(donation_count_current, donation_count_prev),
            },
            'events': {
                'current': events_current,
                'previous': events_prev,
                'change_pct': _change_pct(events_current, events_prev),
            },
            'volunteers': {
                'current': vol_current,
                'previous': vol_prev,
                'change_pct': _change_pct(vol_current, vol_prev),
            },
        }

    # ------------------------------------------------------------------
    # TODO 15: Giving Trend Analysis
    # ------------------------------------------------------------------

    @staticmethod
    def get_giving_trends():
        """Donor retention, avg gift size trend, lapsed donors, frequency."""
        from apps.donations.models import Donation

        now = timezone.now()
        current_year = now.year
        prev_year = current_year - 1

        # Donor retention
        current_donors = set(
            Donation.objects.filter(date__year=current_year)
            .values_list('member_id', flat=True).distinct()
        )
        prev_donors = set(
            Donation.objects.filter(date__year=prev_year)
            .values_list('member_id', flat=True).distinct()
        )
        retained = current_donors & prev_donors
        retention_rate = round(len(retained) / len(prev_donors) * 100, 1) if prev_donors else 0

        # Lapsed donors (gave last year, not this year)
        lapsed = prev_donors - current_donors
        lapsed_count = len(lapsed)

        # Average gift size per month (last 12 months)
        avg_labels = []
        avg_values = []
        for i in range(11, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now + timedelta(days=1)

            avg = Donation.objects.filter(
                date__gte=month_start.date(),
                date__lt=month_end.date(),
            ).aggregate(avg=Avg('amount'))['avg'] or Decimal('0')

            avg_labels.append(month_start.strftime('%b %Y'))
            avg_values.append(float(avg))

        # Giving frequency distribution
        from django.db.models import Count as DjCount
        freq_dist = (
            Donation.objects.filter(date__year=current_year)
            .values('member_id')
            .annotate(gift_count=DjCount('id'))
            .values_list('gift_count', flat=True)
        )
        freq_buckets = {'1': 0, '2-3': 0, '4-6': 0, '7-12': 0, '13+': 0}
        for count in freq_dist:
            if count == 1:
                freq_buckets['1'] += 1
            elif count <= 3:
                freq_buckets['2-3'] += 1
            elif count <= 6:
                freq_buckets['4-6'] += 1
            elif count <= 12:
                freq_buckets['7-12'] += 1
            else:
                freq_buckets['13+'] += 1

        return {
            'retention_rate': retention_rate,
            'retained_count': len(retained),
            'prev_donor_count': len(prev_donors),
            'current_donor_count': len(current_donors),
            'lapsed_count': lapsed_count,
            'avg_gift_labels': avg_labels,
            'avg_gift_values': avg_values,
            'frequency_distribution': freq_buckets,
        }

    # ------------------------------------------------------------------
    # TODO 17: Predictive Analytics (simple linear regression)
    # ------------------------------------------------------------------

    @staticmethod
    def get_predictive_analytics():
        """Forecast giving and membership growth using simple linear regression."""
        from apps.donations.models import Donation
        from apps.members.models import Member

        now = timezone.now()

        # Collect monthly totals for last 12 months
        donation_values = []
        member_values = []
        labels = []
        for i in range(11, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now + timedelta(days=1)

            total = Donation.objects.filter(
                date__gte=month_start.date(),
                date__lt=month_end.date(),
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            donation_values.append(float(total))

            member_count = Member.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).count()
            member_values.append(member_count)
            labels.append(month_start.strftime('%b %Y'))

        def _linear_forecast(values, periods=3):
            """Simple linear regression forecast."""
            n = len(values)
            if n < 2:
                return values[-1:] * periods if values else [0] * periods

            x_mean = (n - 1) / 2.0
            y_mean = sum(values) / n

            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return [y_mean] * periods

            slope = numerator / denominator
            intercept = y_mean - slope * x_mean

            forecasts = []
            for j in range(periods):
                val = slope * (n + j) + intercept
                forecasts.append(round(max(val, 0), 2))
            return forecasts

        donation_forecast = _linear_forecast(donation_values, 3)
        member_forecast = _linear_forecast(member_values, 3)

        # Generate future labels
        forecast_labels = []
        for j in range(1, 4):
            future = now + timedelta(days=30 * j)
            forecast_labels.append(future.strftime('%b %Y'))

        return {
            'historical_labels': labels,
            'donation_historical': donation_values,
            'donation_forecast': donation_forecast,
            'member_historical': member_values,
            'member_forecast': member_forecast,
            'forecast_labels': forecast_labels,
        }

    # ------------------------------------------------------------------
    # TODO 18: BI Tool Integration
    # ------------------------------------------------------------------

    @staticmethod
    def get_bi_data(report_type='summary'):
        """Generate Metabase/Grafana-compatible JSON data."""
        if report_type == 'members':
            return DashboardService.get_member_stats()
        elif report_type == 'donations':
            stats = DashboardService.get_donation_stats()
            # Convert Decimal to float for JSON
            stats['total_amount'] = float(stats['total_amount'])
            stats['average_amount'] = float(stats['average_amount'])
            for item in stats.get('monthly_breakdown', []):
                if 'total' in item:
                    item['total'] = float(item['total'])
            for item in stats.get('by_type', []):
                if 'total' in item:
                    item['total'] = float(item['total'])
            for item in stats.get('by_payment_method', []):
                if 'total' in item:
                    item['total'] = float(item['total'])
            return stats
        elif report_type == 'events':
            return DashboardService.get_event_stats()
        elif report_type == 'volunteers':
            return DashboardService.get_volunteer_stats()
        elif report_type == 'help_requests':
            return DashboardService.get_help_request_stats()
        else:
            # Summary
            summary = DashboardService.get_dashboard_summary()
            summary['donations']['total_amount'] = float(summary['donations']['total_amount'])
            summary['donations']['average_amount'] = float(summary['donations']['average_amount'])
            return summary

    # ------------------------------------------------------------------
    # TODO 19: Church Health Scorecard
    # ------------------------------------------------------------------

    @staticmethod
    def get_church_health_scorecard():
        """Composite church health metric from multiple dimensions."""
        from apps.members.models import Member
        from apps.donations.models import Donation
        from apps.events.models import Event, EventRSVP
        from apps.volunteers.models import VolunteerSchedule

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # 1. Attendance score (0-100)
        total_events_month = Event.objects.filter(
            start_datetime__gte=thirty_days_ago,
            is_cancelled=False,
        ).count()
        confirmed_rsvps_month = EventRSVP.objects.filter(
            event__start_datetime__gte=thirty_days_ago,
            status='confirmed',
        ).count()
        total_members = Member.objects.filter(is_active=True).count() or 1
        attendance_score = min(round(confirmed_rsvps_month / total_members * 100, 1), 100)

        # 2. Giving score (0-100) based on donor participation
        donors_month = Donation.objects.filter(
            date__gte=thirty_days_ago.date(),
        ).values('member').distinct().count()
        giving_score = min(round(donors_month / total_members * 100, 1), 100)

        # 3. Volunteering score (0-100)
        vol_completed = VolunteerSchedule.objects.filter(
            date__gte=thirty_days_ago.date(),
            status='completed',
        ).count()
        vol_total = VolunteerSchedule.objects.filter(
            date__gte=thirty_days_ago.date(),
        ).count() or 1
        volunteering_score = min(round(vol_completed / vol_total * 100, 1), 100)

        # 4. New members score (0-100)
        new_members = Member.objects.filter(
            created_at__gte=thirty_days_ago,
        ).count()
        new_member_score = min(round(new_members / max(total_members * 0.05, 1) * 100, 1), 100)

        # 5. Engagement score (0-100): members who attended or donated or volunteered
        engaged_members = set()
        engaged_members.update(
            EventRSVP.objects.filter(
                event__start_datetime__gte=thirty_days_ago,
                status='confirmed',
            ).values_list('member_id', flat=True)
        )
        engaged_members.update(
            Donation.objects.filter(
                date__gte=thirty_days_ago.date(),
            ).values_list('member_id', flat=True)
        )
        engaged_members.update(
            VolunteerSchedule.objects.filter(
                date__gte=thirty_days_ago.date(),
                status='completed',
            ).values_list('member_id', flat=True)
        )
        engagement_score = min(round(len(engaged_members) / total_members * 100, 1), 100)

        # Composite score (weighted average)
        composite = round(
            attendance_score * 0.25 +
            giving_score * 0.25 +
            volunteering_score * 0.20 +
            new_member_score * 0.15 +
            engagement_score * 0.15,
            1
        )

        return {
            'attendance_score': attendance_score,
            'giving_score': giving_score,
            'volunteering_score': volunteering_score,
            'new_member_score': new_member_score,
            'engagement_score': engagement_score,
            'composite_score': composite,
            'total_members': total_members,
            'events_this_month': total_events_month,
            'donors_this_month': donors_month,
            'new_members_this_month': new_members,
        }

    # ------------------------------------------------------------------
    # TODO 13: Saved Report Preview
    # ------------------------------------------------------------------

    @staticmethod
    def generate_saved_report_preview(saved_report):
        """Generate preview data for a saved report based on its type and filters."""
        report_type = saved_report.report_type

        if report_type == 'member_stats':
            return DashboardService.get_member_stats()
        elif report_type == 'donation_summary':
            year = saved_report.filters_json.get('year', date.today().year)
            return {
                'stats': DashboardService.get_donation_stats(year),
            }
        elif report_type == 'event_attendance':
            return ReportService.get_attendance_report()
        elif report_type == 'volunteer_hours':
            return ReportService.get_volunteer_report()
        elif report_type == 'help_requests':
            return DashboardService.get_help_request_stats()
        elif report_type == 'communication':
            return ReportService.get_communication_stats()
        else:
            return {'message': 'Rapport personnalise - apercu non disponible.'}
