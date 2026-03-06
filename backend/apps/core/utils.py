"""Utility functions for number generation, birthday queries, date ranges, and formatting."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone


def generate_member_number() -> str:
    """
    Generate unique member number (MBR-YYYY-XXXX).
    Uses select_for_update to prevent race conditions in concurrent requests.
    """
    from django.db import transaction
    from apps.members.models import Member

    prefix = getattr(settings, 'MEMBER_NUMBER_PREFIX', 'MBR')
    year = timezone.now().year
    base = f'{prefix}-{year}'

    with transaction.atomic():
        last_member = (
            Member.all_objects
            .select_for_update()
            .filter(member_number__startswith=base)
            .order_by('-member_number')
            .first()
        )

        if last_member:
            try:
                last_seq = int(last_member.member_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

    return f'{base}-{next_seq:04d}'


def generate_donation_number() -> str:
    """
    Generate unique donation number (DON-YYYYMM-XXXX).
    Uses select_for_update to prevent race conditions.
    """
    from django.db import transaction
    from apps.donations.models import Donation

    prefix = getattr(settings, 'DONATION_NUMBER_PREFIX', 'DON')
    now = timezone.now()
    base = f'{prefix}-{now.strftime("%Y%m")}'

    with transaction.atomic():
        last_donation = (
            Donation.all_objects
            .select_for_update()
            .filter(donation_number__startswith=base)
            .order_by('-donation_number')
            .first()
        )

        if last_donation:
            try:
                last_seq = int(last_donation.donation_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

    return f'{base}-{next_seq:04d}'


def generate_request_number() -> str:
    """
    Generate unique help request number (HR-YYYYMM-XXXX).
    Uses select_for_update to prevent race conditions.
    """
    from django.db import transaction
    from apps.help_requests.models import HelpRequest

    prefix = getattr(settings, 'HELP_REQUEST_NUMBER_PREFIX', 'HR')
    now = timezone.now()
    base = f'{prefix}-{now.strftime("%Y%m")}'

    with transaction.atomic():
        last_request = (
            HelpRequest.all_objects
            .select_for_update()
            .filter(request_number__startswith=base)
            .order_by('-request_number')
            .first()
        )

        if last_request:
            try:
                last_seq = int(last_request.request_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

    return f'{base}-{next_seq:04d}'


def generate_receipt_number(year: Optional[int] = None) -> str:
    """
    Generate unique tax receipt number (REC-YYYY-XXXX).
    Uses select_for_update to prevent race conditions.
    """
    from django.db import transaction
    from apps.donations.models import TaxReceipt

    prefix = getattr(settings, 'TAX_RECEIPT_NUMBER_PREFIX', 'REC')
    year = year or timezone.now().year
    base = f'{prefix}-{year}'

    with transaction.atomic():
        last_receipt = (
            TaxReceipt.all_objects
            .select_for_update()
            .filter(receipt_number__startswith=base)
            .order_by('-receipt_number')
            .first()
        )

        if last_receipt:
            try:
                last_seq = int(last_receipt.receipt_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

    return f'{base}-{next_seq:04d}'


def get_today_birthdays() -> QuerySet:
    """Get members with birthdays today."""
    from apps.members.models import Member

    today = date.today()
    return Member.objects.filter(
        birth_date__month=today.month,
        birth_date__day=today.day
    ).order_by('last_name', 'first_name')


def get_week_birthdays() -> QuerySet:
    """Get members with birthdays in the next 7 days."""
    from apps.members.models import Member
    from django.db.models import Q

    today = date.today()
    week_end = today + timedelta(days=7)

    # Year boundary (Dec -> Jan)
    if week_end.year > today.year:
        december_q = Q(birth_date__month=12, birth_date__day__gte=today.day)
        january_q = Q(birth_date__month=1, birth_date__day__lte=week_end.day)
        return Member.objects.filter(december_q | january_q)

    # Same month
    if today.month == week_end.month:
        return Member.objects.filter(
            birth_date__month=today.month,
            birth_date__day__gte=today.day,
            birth_date__day__lte=week_end.day
        )

    # Different months, same year
    current_month_q = Q(birth_date__month=today.month, birth_date__day__gte=today.day)
    next_month_q = Q(birth_date__month=week_end.month, birth_date__day__lte=week_end.day)
    return Member.objects.filter(current_month_q | next_month_q)


def get_month_birthdays(month: Optional[int] = None, year: Optional[int] = None) -> QuerySet:
    """Get members with birthdays in a specific month."""
    from apps.members.models import Member

    month = month or date.today().month
    return Member.objects.filter(
        birth_date__month=month
    ).order_by('birth_date__day', 'last_name', 'first_name')


def get_upcoming_birthdays(days: int = 30) -> list[tuple]:
    """
    Get members with birthdays in the next N days.
    Filters at SQL level to avoid loading all members into Python.
    Returns list of (member, birthday_date) tuples sorted by date.
    """
    from apps.members.models import Member
    from django.db.models import Q

    today = date.today()
    end_date = today + timedelta(days=days)

    # Build month/day range queries at SQL level
    if today.month == end_date.month and today.year == end_date.year:
        q = Q(
            birth_date__month=today.month,
            birth_date__day__gte=today.day,
            birth_date__day__lte=end_date.day,
        )
    elif end_date.year > today.year:
        # Year boundary (e.g., Dec -> Jan)
        q = Q(birth_date__month=today.month, birth_date__day__gte=today.day)
        for m in range(today.month + 1, 13):
            q |= Q(birth_date__month=m)
        for m in range(1, end_date.month):
            q |= Q(birth_date__month=m)
        q |= Q(birth_date__month=end_date.month, birth_date__day__lte=end_date.day)
    else:
        q = Q(birth_date__month=today.month, birth_date__day__gte=today.day)
        for m in range(today.month + 1, end_date.month):
            q |= Q(birth_date__month=m)
        q |= Q(birth_date__month=end_date.month, birth_date__day__lte=end_date.day)

    members = Member.objects.filter(q).exclude(birth_date__isnull=True)

    # Calculate actual birthday dates for sorting
    upcoming = []
    for member in members:
        try:
            birthday_this_year = member.birth_date.replace(year=today.year)
        except ValueError:
            # Feb 29 in non-leap year -> use March 1
            birthday_this_year = date(today.year, 3, 1)

        if birthday_this_year < today:
            try:
                birthday_this_year = member.birth_date.replace(year=today.year + 1)
            except ValueError:
                birthday_this_year = date(today.year + 1, 3, 1)

        days_until = (birthday_this_year - today).days
        if 0 <= days_until <= days:
            upcoming.append((member, birthday_this_year, days_until))

    upcoming.sort(key=lambda x: x[2])
    return [(m, d) for m, d, _ in upcoming]


def get_current_week_range() -> tuple[date, date]:
    """Get Monday-Sunday date range for current week."""
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_current_month_range() -> tuple[date, date]:
    """Get first-last day date range for current month."""
    today = date.today()
    start = today.replace(day=1)

    if today.month == 12:
        end = today.replace(day=31)
    else:
        end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    return start, end


def get_date_range(period: str) -> tuple[date, date]:
    """
    Get date range for period: 'today', 'week', 'month', or 'year'.
    Raises ValueError for invalid period.
    """
    today = date.today()

    if period == 'today':
        return today, today
    if period == 'week':
        return get_current_week_range()
    if period == 'month':
        return get_current_month_range()
    if period == 'year':
        return date(today.year, 1, 1), date(today.year, 12, 31)

    raise ValueError(f"Invalid period: {period}")


def format_phone(phone: Optional[str]) -> str:
    """Format phone number as (XXX) XXX-XXXX for 10 digits or X-(XXX) XXX-XXXX for 11."""
    if not phone:
        return ''

    digits = ''.join(filter(str.isdigit, phone))

    if len(digits) == 10:
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
    if len(digits) == 11:
        return f'{digits[0]}-({digits[1:4]}) {digits[4:7]}-{digits[7:]}'

    return phone


def format_postal_code(postal_code: Optional[str]) -> str:
    """Format Canadian postal code as A1A 1A1."""
    if not postal_code:
        return ''

    clean = postal_code.replace(' ', '').upper()
    if len(clean) == 6:
        return f'{clean[:3]} {clean[3:]}'

    return postal_code


def format_currency(amount: Optional[float]) -> str:
    """Format amount as Canadian currency ($X,XXX.XX)."""
    if amount is None:
        return '$0.00'
    return f'${amount:,.2f}'
