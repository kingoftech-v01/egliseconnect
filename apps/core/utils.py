"""
Core utilities - Utility functions for ÉgliseConnect.

This module provides utility functions used across the application.
"""
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone


# =============================================================================
# NUMBER GENERATION
# =============================================================================

def generate_member_number():
    """
    Generate a unique member number.

    Format: MBR-YYYY-XXXX (e.g., MBR-2026-0001)

    Uses select_for_update to prevent race conditions when multiple
    concurrent requests generate numbers simultaneously.

    Returns:
        str: Unique member number
    """
    from django.db import transaction
    from apps.members.models import Member

    prefix = getattr(settings, 'MEMBER_NUMBER_PREFIX', 'MBR')
    year = timezone.now().year
    base = f'{prefix}-{year}'

    with transaction.atomic():
        # Lock rows to prevent race conditions
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


def generate_donation_number():
    """
    Generate a unique donation number.

    Format: DON-YYYYMM-XXXX (e.g., DON-202601-0001)

    Uses select_for_update to prevent race conditions.

    Returns:
        str: Unique donation number
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


def generate_request_number():
    """
    Generate a unique help request number.

    Format: HR-YYYYMM-XXXX (e.g., HR-202601-0001)

    Uses select_for_update to prevent race conditions.

    Returns:
        str: Unique request number
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


def generate_receipt_number(year=None):
    """
    Generate a unique tax receipt number.

    Format: REC-YYYY-XXXX (e.g., REC-2026-0001)

    Uses select_for_update to prevent race conditions.

    Args:
        year: Year for the receipt (defaults to current year)

    Returns:
        str: Unique receipt number
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


# =============================================================================
# BIRTHDAY UTILITIES
# =============================================================================

def get_today_birthdays():
    """
    Get all members with birthdays today.

    Returns:
        QuerySet: Members with birthdays today
    """
    from apps.members.models import Member

    today = date.today()
    return Member.objects.filter(
        birth_date__month=today.month,
        birth_date__day=today.day
    ).order_by('last_name', 'first_name')


def get_week_birthdays():
    """
    Get all members with birthdays this week.

    Returns:
        QuerySet: Members with birthdays this week
    """
    from apps.members.models import Member
    from django.db.models import Q

    today = date.today()
    week_end = today + timedelta(days=7)

    # Handle year boundary
    if week_end.year > today.year:
        # Birthdays in December
        december_q = Q(
            birth_date__month=12,
            birth_date__day__gte=today.day
        )
        # Birthdays in January
        january_q = Q(
            birth_date__month=1,
            birth_date__day__lte=week_end.day
        )
        return Member.objects.filter(december_q | january_q)

    # Same month
    if today.month == week_end.month:
        return Member.objects.filter(
            birth_date__month=today.month,
            birth_date__day__gte=today.day,
            birth_date__day__lte=week_end.day
        )

    # Different months (same year)
    current_month_q = Q(
        birth_date__month=today.month,
        birth_date__day__gte=today.day
    )
    next_month_q = Q(
        birth_date__month=week_end.month,
        birth_date__day__lte=week_end.day
    )
    return Member.objects.filter(current_month_q | next_month_q)


def get_month_birthdays(month=None, year=None):
    """
    Get all members with birthdays in a specific month.

    Args:
        month: Month number (1-12), defaults to current month
        year: Year (not used for filtering, just for context)

    Returns:
        QuerySet: Members with birthdays in the specified month
    """
    from apps.members.models import Member

    month = month or date.today().month

    return Member.objects.filter(
        birth_date__month=month
    ).order_by('birth_date__day', 'last_name', 'first_name')


def get_upcoming_birthdays(days=30):
    """
    Get all members with birthdays in the next N days.

    Uses SQL-level filtering to avoid loading all members into Python.

    Args:
        days: Number of days to look ahead

    Returns:
        list: List of (member, birthday_date) tuples sorted by date
    """
    from apps.members.models import Member
    from django.db.models import Q

    today = date.today()
    end_date = today + timedelta(days=days)

    # Build month/day range queries at the SQL level
    if today.month == end_date.month and today.year == end_date.year:
        # Same month
        q = Q(
            birth_date__month=today.month,
            birth_date__day__gte=today.day,
            birth_date__day__lte=end_date.day,
        )
    elif end_date.year > today.year:
        # Year boundary crossing (e.g., Dec -> Jan)
        q = Q(
            birth_date__month=today.month,
            birth_date__day__gte=today.day,
        )
        for m in range(today.month + 1, 13):
            q |= Q(birth_date__month=m)
        for m in range(1, end_date.month):
            q |= Q(birth_date__month=m)
        q |= Q(
            birth_date__month=end_date.month,
            birth_date__day__lte=end_date.day,
        )
    else:
        # Different months, same year
        q = Q(
            birth_date__month=today.month,
            birth_date__day__gte=today.day,
        )
        for m in range(today.month + 1, end_date.month):
            q |= Q(birth_date__month=m)
        q |= Q(
            birth_date__month=end_date.month,
            birth_date__day__lte=end_date.day,
        )

    members = Member.objects.filter(q).exclude(birth_date__isnull=True)

    # Calculate actual birthday dates for sorting
    upcoming = []
    for member in members:
        try:
            birthday_this_year = member.birth_date.replace(year=today.year)
        except ValueError:
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


# =============================================================================
# DATE UTILITIES
# =============================================================================

def get_current_week_range():
    """
    Get the start and end dates of the current week (Monday to Sunday).

    Returns:
        tuple: (start_date, end_date)
    """
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_current_month_range():
    """
    Get the start and end dates of the current month.

    Returns:
        tuple: (start_date, end_date)
    """
    today = date.today()
    start = today.replace(day=1)

    # Get last day of month
    if today.month == 12:
        end = today.replace(day=31)
    else:
        end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    return start, end


def get_date_range(period):
    """
    Get date range for a given period.

    Args:
        period: 'today', 'week', 'month', 'year'

    Returns:
        tuple: (start_date, end_date)
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


# =============================================================================
# FORMATTING UTILITIES
# =============================================================================

def format_phone(phone):
    """
    Format a phone number for display.

    Args:
        phone: Raw phone number string

    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ''

    # Remove non-digits
    digits = ''.join(filter(str.isdigit, phone))

    # Format as (XXX) XXX-XXXX for 10 digits
    if len(digits) == 10:
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'

    # Format as X-XXX-XXX-XXXX for 11 digits
    if len(digits) == 11:
        return f'{digits[0]}-({digits[1:4]}) {digits[4:7]}-{digits[7:]}'

    # Return as-is if doesn't match patterns
    return phone


def format_postal_code(postal_code):
    """
    Format a Canadian postal code.

    Args:
        postal_code: Raw postal code string

    Returns:
        str: Formatted postal code (A1A 1A1)
    """
    if not postal_code:
        return ''

    # Remove spaces and convert to uppercase
    clean = postal_code.replace(' ', '').upper()

    # Format as A1A 1A1
    if len(clean) == 6:
        return f'{clean[:3]} {clean[3:]}'

    return postal_code


def format_currency(amount):
    """
    Format an amount as Canadian currency.

    Args:
        amount: Decimal or float amount

    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return '$0.00'

    return f'${amount:,.2f}'
