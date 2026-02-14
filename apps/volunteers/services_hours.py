"""Service functions for volunteer hour tracking, summaries, and export."""
from datetime import date
from decimal import Decimal

from django.db.models import Sum, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.export import export_queryset_csv

from .models import VolunteerHours


def log_hours(member, position, work_date, hours_worked, description='', approved_by=None):
    """
    Log volunteer hours for a member.

    Args:
        member: Member instance
        position: VolunteerPosition instance
        work_date: date of the work
        hours_worked: Decimal or float hours
        description: optional description
        approved_by: optional Member who approved

    Returns:
        VolunteerHours instance
    """
    entry = VolunteerHours.objects.create(
        member=member,
        position=position,
        date=work_date,
        hours_worked=Decimal(str(hours_worked)),
        description=description,
        approved_by=approved_by,
        approved_at=timezone.now() if approved_by else None,
    )
    return entry


def summarize_by_member(member, date_from=None, date_to=None):
    """
    Summarize total volunteer hours for a member, optionally filtered by date range.

    Returns:
        dict with total_hours, by_position list, count
    """
    qs = VolunteerHours.objects.filter(member=member)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    total = qs.aggregate(total=Sum('hours_worked'))['total'] or Decimal('0')

    by_position = list(
        qs.values(
            position_name=F('position__name'),
            pos_id=F('position__id'),
        ).annotate(
            total_hours=Sum('hours_worked'),
        ).order_by('-total_hours')
    )

    return {
        'total_hours': total,
        'by_position': by_position,
        'count': qs.count(),
    }


def summarize_by_position(position, date_from=None, date_to=None):
    """
    Summarize volunteer hours for a position across all members.

    Returns:
        dict with total_hours, by_member list, count
    """
    qs = VolunteerHours.objects.filter(position=position)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    total = qs.aggregate(total=Sum('hours_worked'))['total'] or Decimal('0')

    by_member = list(
        qs.values(
            member_name=F('member__first_name'),
            member_last=F('member__last_name'),
            mem_id=F('member__id'),
        ).annotate(
            total_hours=Sum('hours_worked'),
        ).order_by('-total_hours')
    )

    return {
        'total_hours': total,
        'by_member': by_member,
        'count': qs.count(),
    }


def get_admin_report(date_from=None, date_to=None, position=None):
    """
    Get a full admin report of all volunteer hours.

    Returns:
        queryset of VolunteerHours with related objects
    """
    qs = VolunteerHours.objects.select_related('member', 'position', 'approved_by')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if position:
        qs = qs.filter(position=position)
    return qs.order_by('-date')


def export_report(queryset):
    """Export volunteer hours queryset to CSV."""
    return export_queryset_csv(
        queryset=queryset,
        fields=[
            lambda obj: obj.member.full_name,
            lambda obj: obj.position.name,
            'date',
            'hours_worked',
            'description',
            lambda obj: obj.approved_by.full_name if obj.approved_by else '',
        ],
        filename='rapport_heures_benevoles',
        headers=[
            'Membre', 'Poste', 'Date', 'Heures', 'Description', 'Approuve par',
        ],
    )
