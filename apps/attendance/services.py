"""Services for attendance analytics, engagement scoring, and predictions."""
import math
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncWeek, TruncMonth
from django.utils import timezone

from apps.core.constants import AttendanceSessionType


class AttendanceAnalyticsService:
    """Computes attendance analytics, trends, and statistics."""

    @staticmethod
    def get_attendance_trends(period='weekly', weeks_back=12):
        """Get attendance trends over time (weekly or monthly counts).

        Returns list of {'period': date, 'count': int} dicts.
        """
        from .models import AttendanceRecord, AttendanceSession

        start_date = timezone.now().date() - timedelta(weeks=weeks_back)

        records = AttendanceRecord.objects.filter(
            session__date__gte=start_date
        )

        if period == 'monthly':
            data = (
                records
                .annotate(period=TruncMonth('session__date'))
                .values('period')
                .annotate(count=Count('id'))
                .order_by('period')
            )
        else:
            data = (
                records
                .annotate(period=TruncWeek('session__date'))
                .values('period')
                .annotate(count=Count('id'))
                .order_by('period')
            )

        return list(data)

    @staticmethod
    def get_average_attendance_by_type():
        """Get average attendance per session type.

        Returns dict of {session_type: avg_count}.
        """
        from .models import AttendanceSession

        sessions = AttendanceSession.objects.filter(
            is_active=True
        ).annotate(
            record_count=Count('records')
        )

        by_type = defaultdict(list)
        for session in sessions:
            by_type[session.session_type].append(session.record_count)

        result = {}
        for session_type, counts in by_type.items():
            if counts:
                result[session_type] = round(sum(counts) / len(counts), 1)
            else:
                result[session_type] = 0

        return result

    @staticmethod
    def get_member_attendance_rate(member, days=90):
        """Calculate attendance rate for a specific member over N days.

        Returns dict with attended, total, rate.
        """
        from .models import AttendanceSession, AttendanceRecord

        start_date = timezone.now().date() - timedelta(days=days)

        total_sessions = AttendanceSession.objects.filter(
            date__gte=start_date,
            is_active=True,
        ).count()

        attended = AttendanceRecord.objects.filter(
            member=member,
            session__date__gte=start_date,
        ).count()

        rate = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 0

        return {
            'attended': attended,
            'total_sessions': total_sessions,
            'rate': rate,
        }

    @staticmethod
    def get_growth_indicators(weeks_back=12):
        """Calculate growth/decline percentage over recent weeks.

        Compares last half period vs first half period.
        Returns dict with current_avg, previous_avg, change_pct, trend.
        """
        from .models import AttendanceRecord

        now = timezone.now().date()
        midpoint = now - timedelta(weeks=weeks_back // 2)
        start = now - timedelta(weeks=weeks_back)

        recent_count = AttendanceRecord.objects.filter(
            session__date__gte=midpoint,
            session__date__lte=now,
        ).count()

        earlier_count = AttendanceRecord.objects.filter(
            session__date__gte=start,
            session__date__lt=midpoint,
        ).count()

        half_weeks = weeks_back // 2 or 1
        recent_avg = round(recent_count / half_weeks, 1)
        earlier_avg = round(earlier_count / half_weeks, 1)

        if earlier_avg > 0:
            change_pct = round(((recent_avg - earlier_avg) / earlier_avg) * 100, 1)
        else:
            change_pct = 100.0 if recent_avg > 0 else 0.0

        if change_pct > 0:
            trend = 'growth'
        elif change_pct < 0:
            trend = 'decline'
        else:
            trend = 'stable'

        return {
            'current_avg': recent_avg,
            'previous_avg': earlier_avg,
            'change_pct': change_pct,
            'trend': trend,
        }

    @staticmethod
    def get_seasonal_trends(years_back=2):
        """Analyze seasonal attendance patterns.

        Returns list of {'month': int, 'avg_attendance': float} dicts.
        """
        from .models import AttendanceRecord

        start_date = timezone.now().date() - timedelta(days=365 * years_back)

        records = AttendanceRecord.objects.filter(
            session__date__gte=start_date
        ).values(
            month=F('session__date__month')
        ).annotate(
            total=Count('id')
        ).order_by('month')

        # Average over years
        monthly = defaultdict(list)
        for r in records:
            monthly[r['month']].append(r['total'])

        result = []
        for month in range(1, 13):
            counts = monthly.get(month, [0])
            avg = round(sum(counts) / max(len(counts), 1), 1)
            result.append({'month': month, 'avg_attendance': avg})

        return result

    @staticmethod
    def get_session_duration_report(days=90):
        """Calculate average session duration from check-out data.

        Returns dict with avg_minutes, total_records, early_departures.
        """
        from .models import AttendanceRecord

        start_date = timezone.now().date() - timedelta(days=days)

        records_with_checkout = AttendanceRecord.objects.filter(
            session__date__gte=start_date,
            checked_out_at__isnull=False,
        )

        total = records_with_checkout.count()
        if total == 0:
            return {
                'avg_minutes': 0,
                'total_records': 0,
                'early_departures': 0,
            }

        total_minutes = 0
        early_departures = 0
        for record in records_with_checkout:
            duration = record.duration_minutes
            if duration is not None:
                total_minutes += duration
            if record.is_early_departure:
                early_departures += 1

        avg_minutes = round(total_minutes / total, 1) if total > 0 else 0

        return {
            'avg_minutes': avg_minutes,
            'total_records': total,
            'early_departures': early_departures,
        }


class EngagementScoringService:
    """Calculates attendance-based engagement scores."""

    @staticmethod
    def calculate_consistency_score(member, days=90):
        """Calculate attendance consistency score (attended / total in period).

        Returns float 0.0 to 1.0.
        """
        from .models import AttendanceSession, AttendanceRecord

        start_date = timezone.now().date() - timedelta(days=days)

        total = AttendanceSession.objects.filter(
            date__gte=start_date,
            session_type=AttendanceSessionType.WORSHIP,
            is_active=True,
        ).count()

        if total == 0:
            return 0.0

        attended = AttendanceRecord.objects.filter(
            member=member,
            session__date__gte=start_date,
            session__session_type=AttendanceSessionType.WORSHIP,
        ).count()

        return round(min(attended / total, 1.0), 2)

    @staticmethod
    def get_attendance_streak(member):
        """Get current and longest attendance streak for a member.

        Returns dict with current_streak, longest_streak.
        """
        from .models import AttendanceStreak

        try:
            streak = AttendanceStreak.objects.get(member=member)
            return {
                'current_streak': streak.current_streak,
                'longest_streak': streak.longest_streak,
            }
        except AttendanceStreak.DoesNotExist:
            return {
                'current_streak': 0,
                'longest_streak': 0,
            }

    @staticmethod
    def calculate_engagement_score(member):
        """Calculate overall engagement score (0-100) from attendance data.

        Score breakdown:
        - Consistency (40%): regular attendance ratio
        - Streak (30%): current streak weeks
        - Variety (20%): attending different session types
        - Recent (10%): attended in last 2 weeks
        """
        from .models import AttendanceRecord, AttendanceStreak

        # Consistency component (40 points)
        consistency = EngagementScoringService.calculate_consistency_score(member)
        consistency_score = consistency * 40

        # Streak component (30 points, max at 12 weeks)
        streak_data = EngagementScoringService.get_attendance_streak(member)
        streak_weeks = min(streak_data['current_streak'], 12)
        streak_score = (streak_weeks / 12) * 30

        # Variety component (20 points)
        ninety_days_ago = timezone.now().date() - timedelta(days=90)
        distinct_types = AttendanceRecord.objects.filter(
            member=member,
            session__date__gte=ninety_days_ago,
        ).values('session__session_type').distinct().count()

        total_types = len(AttendanceSessionType.CHOICES)
        variety_score = min(distinct_types / max(total_types, 1), 1.0) * 20

        # Recency component (10 points)
        two_weeks_ago = timezone.now().date() - timedelta(days=14)
        recent = AttendanceRecord.objects.filter(
            member=member,
            session__date__gte=two_weeks_ago,
        ).exists()
        recency_score = 10 if recent else 0

        total = round(consistency_score + streak_score + variety_score + recency_score, 1)
        return min(total, 100)


class AttendancePredictionService:
    """Predicts expected attendance for planning purposes."""

    @staticmethod
    def predict_attendance(session_type, day_of_week=None, weeks_back=12):
        """Predict expected attendance for a session type.

        Uses historical average for session type + optional day of week filter.
        Returns dict with predicted, min_attendance, max_attendance, sample_size.
        """
        from .models import AttendanceSession

        start_date = timezone.now().date() - timedelta(weeks=weeks_back)

        sessions = AttendanceSession.objects.filter(
            session_type=session_type,
            date__gte=start_date,
            is_active=True,
        ).annotate(
            record_count=Count('records')
        )

        if day_of_week is not None:
            sessions = sessions.filter(date__week_day=day_of_week)

        if not sessions.exists():
            return {
                'predicted': 0,
                'min_attendance': 0,
                'max_attendance': 0,
                'sample_size': 0,
            }

        counts = [s.record_count for s in sessions]
        predicted = round(sum(counts) / len(counts), 0)

        return {
            'predicted': int(predicted),
            'min_attendance': min(counts),
            'max_attendance': max(counts),
            'sample_size': len(counts),
        }

    @staticmethod
    def get_actual_vs_predicted(session_type, weeks_back=12):
        """Compare actual vs predicted attendance over time.

        Returns list of {'date': date, 'actual': int, 'predicted': int} dicts.
        """
        from .models import AttendanceSession

        start_date = timezone.now().date() - timedelta(weeks=weeks_back)

        sessions = AttendanceSession.objects.filter(
            session_type=session_type,
            date__gte=start_date,
            is_active=True,
        ).annotate(
            record_count=Count('records')
        ).order_by('date')

        if not sessions.exists():
            return []

        # Build a running average for prediction
        running_counts = []
        results = []
        for session in sessions:
            predicted = round(sum(running_counts) / len(running_counts), 0) if running_counts else 0
            results.append({
                'date': session.date,
                'actual': session.record_count,
                'predicted': int(predicted),
            })
            running_counts.append(session.record_count)

        return results

    @staticmethod
    def get_resource_recommendations(session_type):
        """Generate resource planning recommendations based on predictions.

        Returns dict with predicted, recommendation.
        """
        prediction = AttendancePredictionService.predict_attendance(session_type)
        predicted = prediction['predicted']

        recommendations = []
        if predicted > 0:
            recommendations.append(
                f"Préparer {predicted} chaises/places assises."
            )
            # Bulletins
            bulletins = int(predicted * 1.1)
            recommendations.append(
                f"Imprimer {bulletins} bulletins (marge de 10%)."
            )
            # Children's ministry
            children_ratio = 0.15
            children_est = int(predicted * children_ratio)
            if children_est > 0:
                recommendations.append(
                    f"Prévoir {children_est} places en ministère des enfants."
                )
            # Volunteers
            if predicted > 50:
                recommendations.append(
                    "Prévoir une équipe d'accueil renforcée."
                )

        return {
            'predicted': predicted,
            'recommendations': recommendations,
        }


class FamilyCheckInService:
    """Service for family/household check-in functionality."""

    @staticmethod
    def get_family_members(family):
        """Get all members belonging to a family.

        Returns queryset of Members in the family.
        """
        from apps.members.models import Member
        return Member.objects.filter(family=family, is_active=True)

    @staticmethod
    def check_in_family(family, session, checked_in_by=None):
        """Check in all members of a family to a session.

        Returns list of (member, created) tuples.
        """
        from .models import AttendanceRecord
        from apps.core.constants import CheckInMethod

        members = FamilyCheckInService.get_family_members(family)
        results = []

        for member in members:
            record, created = AttendanceRecord.objects.get_or_create(
                session=session,
                member=member,
                defaults={
                    'checked_in_by': checked_in_by,
                    'method': CheckInMethod.KIOSK,
                }
            )
            results.append((member, created))

        return results

    @staticmethod
    def get_family_attendance_summary(family, days=90):
        """Get attendance summary for a family.

        Returns dict with member stats.
        """
        members = FamilyCheckInService.get_family_members(family)
        summary = []

        for member in members:
            stats = AttendanceAnalyticsService.get_member_attendance_rate(member, days)
            summary.append({
                'member': member,
                'attended': stats['attended'],
                'total_sessions': stats['total_sessions'],
                'rate': stats['rate'],
            })

        return summary
