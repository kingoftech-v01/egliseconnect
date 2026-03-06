"""Giving analytics and reporting service."""
import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Avg, Count, Q, F
from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear, ExtractYear

logger = logging.getLogger(__name__)


class GivingAnalyticsService:
    """Analytics service for donation trends, retention, and comparisons."""

    @classmethod
    def giving_trends(cls, period='monthly', year=None):
        """
        Get giving totals grouped by period.

        Args:
            period: 'monthly', 'quarterly', or 'yearly'
            year: optional year filter

        Returns:
            list of dicts with 'period', 'total', 'count'
        """
        from .models import Donation

        queryset = Donation.objects.filter(is_active=True)
        if year:
            queryset = queryset.filter(date__year=year)

        if period == 'monthly':
            data = queryset.annotate(
                period=TruncMonth('date')
            ).values('period').annotate(
                total=Sum('amount'),
                count=Count('id'),
                avg=Avg('amount'),
            ).order_by('period')
        elif period == 'quarterly':
            data = queryset.annotate(
                period=TruncQuarter('date')
            ).values('period').annotate(
                total=Sum('amount'),
                count=Count('id'),
                avg=Avg('amount'),
            ).order_by('period')
        else:  # yearly
            data = queryset.annotate(
                period=TruncYear('date')
            ).values('period').annotate(
                total=Sum('amount'),
                count=Count('id'),
                avg=Avg('amount'),
            ).order_by('period')

        return list(data)

    @classmethod
    def yoy_comparison(cls, year):
        """
        Year-over-year comparison: this year vs last year by month.

        Returns dict with 'current_year', 'previous_year' monthly data.
        """
        from .models import Donation

        current = Donation.objects.filter(
            date__year=year, is_active=True
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id'),
        ).order_by('month')

        previous = Donation.objects.filter(
            date__year=year - 1, is_active=True
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id'),
        ).order_by('month')

        return {
            'current_year': year,
            'previous_year': year - 1,
            'current_data': list(current),
            'previous_data': list(previous),
        }

    @classmethod
    def donor_retention(cls, year):
        """
        Analyze donor retention: new, returning, and lapsed donors.

        Returns dict with 'new_donors', 'returning_donors', 'lapsed_donors'.
        """
        from .models import Donation

        # Donors who gave this year
        current_donors = set(
            Donation.objects.filter(
                date__year=year, is_active=True
            ).values_list('member_id', flat=True).distinct()
        )

        # Donors who gave last year
        previous_donors = set(
            Donation.objects.filter(
                date__year=year - 1, is_active=True
            ).values_list('member_id', flat=True).distinct()
        )

        # Donors who gave any year before this one
        ever_donors = set(
            Donation.objects.filter(
                date__year__lt=year, is_active=True
            ).values_list('member_id', flat=True).distinct()
        )

        new_donors = current_donors - ever_donors
        returning_donors = current_donors & previous_donors
        lapsed_donors = previous_donors - current_donors

        return {
            'year': year,
            'new_donors': len(new_donors),
            'returning_donors': len(returning_donors),
            'lapsed_donors': len(lapsed_donors),
            'total_current_donors': len(current_donors),
            'retention_rate': (
                round(len(returning_donors) / len(previous_donors) * 100, 1)
                if previous_donors else 0
            ),
        }

    @classmethod
    def avg_gift_size(cls, year=None, period='monthly'):
        """
        Average gift size trends over time.

        Returns list of dicts with 'period', 'avg_amount'.
        """
        from .models import Donation

        queryset = Donation.objects.filter(is_active=True)
        if year:
            queryset = queryset.filter(date__year=year)

        if period == 'monthly':
            data = queryset.annotate(
                period=TruncMonth('date')
            ).values('period').annotate(
                avg_amount=Avg('amount'),
                count=Count('id'),
            ).order_by('period')
        else:
            data = queryset.annotate(
                period=TruncYear('date')
            ).values('period').annotate(
                avg_amount=Avg('amount'),
                count=Count('id'),
            ).order_by('period')

        return list(data)

    @classmethod
    def first_time_donors(cls, year):
        """
        Identify first-time donors in a given year.

        Returns list of member info for members whose first donation was in this year.
        """
        from .models import Donation
        from apps.members.models import Member

        # Members whose earliest donation is in this year
        first_timers = (
            Donation.objects.filter(is_active=True)
            .values('member_id')
            .annotate(first_date=Count('date'))
        )

        # Get members who have no donations before this year
        members_with_prior = set(
            Donation.objects.filter(
                date__year__lt=year, is_active=True
            ).values_list('member_id', flat=True).distinct()
        )

        current_donors = set(
            Donation.objects.filter(
                date__year=year, is_active=True
            ).values_list('member_id', flat=True).distinct()
        )

        first_time_ids = current_donors - members_with_prior

        members = Member.objects.filter(
            pk__in=first_time_ids, is_active=True
        ).order_by('last_name', 'first_name')

        result = []
        for member in members:
            first_donation = Donation.objects.filter(
                member=member, date__year=year, is_active=True
            ).order_by('date').first()

            total = Donation.objects.filter(
                member=member, date__year=year, is_active=True
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            result.append({
                'member_id': str(member.pk),
                'member_name': member.full_name,
                'first_donation_date': first_donation.date if first_donation else None,
                'total_given': total,
            })

        return result

    @classmethod
    def top_donors(cls, year, limit=10):
        """
        Top donors by total giving for a year.

        Returns list of dicts with 'member_name', 'total_amount', 'donation_count'.
        """
        from .models import Donation

        data = (
            Donation.objects.filter(date__year=year, is_active=True)
            .values('member_id', 'member__first_name', 'member__last_name')
            .annotate(
                total_amount=Sum('amount'),
                donation_count=Count('id'),
            )
            .order_by('-total_amount')[:limit]
        )

        return [{
            'member_id': str(item['member_id']),
            'member_name': f"{item['member__first_name']} {item['member__last_name']}",
            'total_amount': item['total_amount'],
            'donation_count': item['donation_count'],
        } for item in data]

    @classmethod
    def dashboard_summary(cls, year):
        """
        Combined analytics data suitable for a dashboard view.

        Returns dict with all analytics data.
        """
        from .models import Donation

        # Overall stats for the year
        overall = Donation.objects.filter(
            date__year=year, is_active=True
        ).aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            avg_amount=Avg('amount'),
        )

        return {
            'year': year,
            'total_amount': overall['total_amount'] or Decimal('0.00'),
            'total_count': overall['total_count'] or 0,
            'avg_amount': overall['avg_amount'] or Decimal('0.00'),
            'monthly_trends': cls.giving_trends('monthly', year),
            'yoy_comparison': cls.yoy_comparison(year),
            'retention': cls.donor_retention(year),
            'top_donors': cls.top_donors(year, 10),
            'first_time_donors': cls.first_time_donors(year),
        }
