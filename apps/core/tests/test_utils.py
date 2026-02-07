"""Tests for core utilities."""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.core.utils import (
    format_phone,
    format_postal_code,
    format_currency,
    get_current_week_range,
    get_current_month_range,
    get_date_range,
)


class TestFormatPhone:
    """Tests for format_phone function."""

    def test_format_10_digit_phone(self):
        """Formats 10-digit phone numbers."""
        assert format_phone('5141234567') == '(514) 123-4567'

    def test_format_phone_with_existing_formatting(self):
        """Formats phone with existing punctuation."""
        assert format_phone('514-123-4567') == '(514) 123-4567'

    def test_format_11_digit_phone(self):
        """Formats 11-digit phone numbers with country code."""
        assert format_phone('15141234567') == '1-(514) 123-4567'

    def test_format_empty_phone(self):
        """Returns empty string for empty phone."""
        assert format_phone('') == ''
        assert format_phone(None) == ''

    def test_format_invalid_phone(self):
        """Returns original for invalid phone."""
        assert format_phone('123') == '123'


class TestFormatPostalCode:
    """Tests for format_postal_code function."""

    def test_format_postal_code(self):
        """Formats postal codes with space."""
        assert format_postal_code('H1A1A1') == 'H1A 1A1'

    def test_format_postal_code_with_space(self):
        """Preserves postal code with existing space."""
        assert format_postal_code('H1A 1A1') == 'H1A 1A1'

    def test_format_lowercase_postal_code(self):
        """Uppercases lowercase postal codes."""
        assert format_postal_code('h1a1a1') == 'H1A 1A1'

    def test_format_empty_postal_code(self):
        """Returns empty string for empty postal code."""
        assert format_postal_code('') == ''
        assert format_postal_code(None) == ''


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_format_currency(self):
        """Formats currency with dollar sign and commas."""
        assert format_currency(100) == '$100.00'
        assert format_currency(1000) == '$1,000.00'
        assert format_currency(1234.56) == '$1,234.56'

    def test_format_currency_decimal(self):
        """Formats Decimal currency values."""
        assert format_currency(Decimal('100.00')) == '$100.00'

    def test_format_currency_none(self):
        """Returns $0.00 for None."""
        assert format_currency(None) == '$0.00'


class TestGetCurrentWeekRange:
    """Tests for get_current_week_range function."""

    def test_returns_monday_to_sunday(self):
        """Returns Monday to Sunday date range."""
        start, end = get_current_week_range()

        assert start.weekday() == 0
        assert end.weekday() == 6
        assert (end - start).days == 6


class TestGetCurrentMonthRange:
    """Tests for get_current_month_range function."""

    def test_returns_first_and_last_day(self):
        """Returns first and last day of month."""
        start, end = get_current_month_range()

        assert start.day == 1
        next_month = (end + timedelta(days=1))
        assert next_month.day == 1


class TestGetDateRange:
    """Tests for get_date_range function."""

    def test_today_range(self):
        """'today' period returns today for both start and end."""
        start, end = get_date_range('today')
        today = date.today()

        assert start == today
        assert end == today

    def test_week_range(self):
        """'week' period returns Monday to Sunday."""
        start, end = get_date_range('week')

        assert start.weekday() == 0
        assert end.weekday() == 6

    def test_month_range(self):
        """'month' period starts on first of month."""
        start, end = get_date_range('month')

        assert start.day == 1

    def test_year_range(self):
        """'year' period returns Jan 1 to Dec 31."""
        start, end = get_date_range('year')
        today = date.today()

        assert start == date(today.year, 1, 1)
        assert end == date(today.year, 12, 31)

    def test_invalid_period_raises(self):
        """Invalid period raises ValueError."""
        with pytest.raises(ValueError):
            get_date_range('invalid')


# ==============================================================================
# Edge case tests for number generation, birthdays, month ranges, and formatting
# ==============================================================================

from unittest.mock import patch
from freezegun import freeze_time
from django.utils import timezone

from apps.core.utils import (
    generate_member_number,
    generate_donation_number,
    generate_request_number,
    generate_receipt_number,
    get_week_birthdays,
    get_upcoming_birthdays,
    get_month_birthdays,
    get_today_birthdays,
)
from apps.members.tests.factories import MemberFactory
from apps.donations.tests.factories import DonationFactory, TaxReceiptFactory
from apps.help_requests.tests.factories import HelpRequestFactory


@pytest.mark.django_db
class TestGenerateMemberNumberEdgeCases:
    """Tests for generate_member_number ValueError/IndexError fallback."""

    def test_member_number_invalid_sequence_resets_to_one(self):
        """When existing member_number has non-numeric suffix, reset to 0001."""
        member = MemberFactory()
        year = timezone.now().year
        member.member_number = f'MBR-{year}-INVALID'
        member.save(update_fields=['member_number'])

        result = generate_member_number()
        assert result == f'MBR-{year}-0001'

    def test_member_number_normal_increment(self):
        """Normal sequence increments correctly."""
        member = MemberFactory()
        year = timezone.now().year
        member.member_number = f'MBR-{year}-0005'
        member.save(update_fields=['member_number'])

        result = generate_member_number()
        assert result == f'MBR-{year}-0006'

    def test_member_number_no_existing(self):
        """When no members with matching prefix exist, start at 0001."""
        # Clear all member numbers for this year
        from apps.members.models import Member
        year = timezone.now().year
        Member.all_objects.filter(
            member_number__startswith=f'MBR-{year}'
        ).update(member_number='CLEARED')

        result = generate_member_number()
        assert result == f'MBR-{year}-0001'


@pytest.mark.django_db
class TestGenerateDonationNumberEdgeCases:
    """Tests for generate_donation_number ValueError/IndexError fallback."""

    def test_donation_number_invalid_sequence_resets_to_one(self):
        """When existing donation_number has non-numeric suffix, reset to 0001."""
        donation = DonationFactory()
        now = timezone.now()
        base = f'DON-{now.strftime("%Y%m")}'
        donation.donation_number = f'{base}-BADVAL'
        donation.save(update_fields=['donation_number'])

        result = generate_donation_number()
        assert result == f'{base}-0001'

    def test_donation_number_normal_increment(self):
        """Normal sequence increments correctly."""
        donation = DonationFactory()
        now = timezone.now()
        base = f'DON-{now.strftime("%Y%m")}'
        donation.donation_number = f'{base}-0010'
        donation.save(update_fields=['donation_number'])

        result = generate_donation_number()
        assert result == f'{base}-0011'


@pytest.mark.django_db
class TestGenerateRequestNumberEdgeCases:
    """Tests for generate_request_number ValueError/IndexError fallback."""

    def test_request_number_invalid_sequence_resets_to_one(self):
        """When existing request_number has non-numeric suffix, reset to 0001."""
        help_request = HelpRequestFactory()
        now = timezone.now()
        base = f'HR-{now.strftime("%Y%m")}'
        help_request.request_number = f'{base}-CORRUPT'
        help_request.save(update_fields=['request_number'])

        result = generate_request_number()
        assert result == f'{base}-0001'

    def test_request_number_normal_increment(self):
        """Normal sequence increments correctly."""
        help_request = HelpRequestFactory()
        now = timezone.now()
        base = f'HR-{now.strftime("%Y%m")}'
        help_request.request_number = f'{base}-0003'
        help_request.save(update_fields=['request_number'])

        result = generate_request_number()
        assert result == f'{base}-0004'


@pytest.mark.django_db
class TestGenerateReceiptNumberEdgeCases:
    """Tests for generate_receipt_number ValueError/IndexError fallback."""

    def test_receipt_number_invalid_sequence_resets_to_one(self):
        """When existing receipt_number has non-numeric suffix, reset to 0001."""
        receipt = TaxReceiptFactory()
        year = timezone.now().year
        receipt.receipt_number = f'REC-{year}-BROKEN'
        receipt.save(update_fields=['receipt_number'])

        result = generate_receipt_number()
        assert result == f'REC-{year}-0001'

    def test_receipt_number_normal_increment(self):
        """Normal sequence increments correctly."""
        receipt = TaxReceiptFactory()
        year = timezone.now().year
        receipt.receipt_number = f'REC-{year}-0020'
        receipt.save(update_fields=['receipt_number'])

        result = generate_receipt_number()
        assert result == f'REC-{year}-0021'


@pytest.mark.django_db
class TestGetWeekBirthdaysYearBoundary:
    """Tests for get_week_birthdays year-boundary and cross-month branches."""

    @freeze_time('2026-12-28')
    def test_year_boundary_dec_to_jan(self):
        """Birthdays spanning Dec 28 to Jan 4 should be found (year boundary)."""
        # Member with birthday on Dec 30 (in range)
        dec_member = MemberFactory(birth_date=date(1990, 12, 30))
        # Member with birthday on Jan 2 (in range, next year side)
        jan_member = MemberFactory(birth_date=date(1985, 1, 2))
        # Member with birthday on Jan 10 (out of range)
        out_member = MemberFactory(birth_date=date(1988, 1, 10))

        result = get_week_birthdays()
        result_pks = list(result.values_list('pk', flat=True))

        assert dec_member.pk in result_pks
        assert jan_member.pk in result_pks
        assert out_member.pk not in result_pks

    @freeze_time('2026-03-10')
    def test_same_month_range(self):
        """When start and end are in the same month, only that month range is queried."""
        # March 12 (in range)
        in_member = MemberFactory(birth_date=date(1992, 3, 12))
        # March 20 (out of range - more than 7 days away)
        out_member = MemberFactory(birth_date=date(1992, 3, 20))

        result = get_week_birthdays()
        result_pks = list(result.values_list('pk', flat=True))

        assert in_member.pk in result_pks
        assert out_member.pk not in result_pks

    @freeze_time('2026-01-28')
    def test_cross_month_boundary_same_year(self):
        """When the 7-day range spans two different months in the same year."""
        # Jan 30 (in range)
        jan_member = MemberFactory(birth_date=date(1990, 1, 30))
        # Feb 2 (in range, next month)
        feb_member = MemberFactory(birth_date=date(1993, 2, 2))
        # Feb 10 (out of range)
        out_member = MemberFactory(birth_date=date(1991, 2, 10))

        result = get_week_birthdays()
        result_pks = list(result.values_list('pk', flat=True))

        assert jan_member.pk in result_pks
        assert feb_member.pk in result_pks
        assert out_member.pk not in result_pks


@pytest.mark.django_db
class TestGetUpcomingBirthdaysEdgeCases:
    """Tests for get_upcoming_birthdays year-boundary, past-birthday, and Feb 29 branches."""

    @freeze_time('2026-11-15')
    def test_year_boundary_upcoming(self):
        """Upcoming birthdays spanning Nov into Jan of next year (exercises loop body line 212)."""
        # Dec 10 (in range)
        dec_member = MemberFactory(birth_date=date(1990, 12, 10))
        # Jan 5 (in range with 60-day window: Nov 15 + 60 = Jan 14, 2027)
        jan_member = MemberFactory(birth_date=date(1988, 1, 5))
        # Feb 15 (out of range)
        out_member = MemberFactory(birth_date=date(1992, 2, 15))

        # end_date = 2027-01-14, year boundary branch:
        #   range(today.month + 1, 13) = range(12, 13) = [12] -> loop body (line 212) executes
        #   range(1, end_date.month) = range(1, 1) = [] -> empty
        result = get_upcoming_birthdays(days=60)
        result_pks = [m.pk for m, d in result]
        assert dec_member.pk in result_pks
        assert jan_member.pk in result_pks
        assert out_member.pk not in result_pks

    @freeze_time('2026-02-25')
    def test_feb_29_birthday_in_non_leap_year(self):
        """Feb 29 birthday in a non-leap year should fall back to March 1."""
        # 2026 is not a leap year. Member born Feb 29.
        # Freeze at Feb 25 so the SQL filter includes month=2 day>=25 (catches Feb 29)
        member = MemberFactory(birth_date=date(2000, 2, 29))

        result = get_upcoming_birthdays(days=10)
        result_pks = [m.pk for m, d in result]
        result_dates = {m.pk: d for m, d in result}

        assert member.pk in result_pks
        # Birthday should be mapped to March 1 in non-leap year
        assert result_dates[member.pk] == date(2026, 3, 1)

    @freeze_time('2026-06-15')
    def test_birthday_past_this_year_wraps_to_next(self):
        """Birthday earlier in the year should wrap to next year."""
        # Member born Jan 10 - birthday already passed by June 15
        member = MemberFactory(birth_date=date(1990, 1, 10))

        # Check with 30-day window - Jan 10 is far in the past, won't be in 30-day window
        result = get_upcoming_birthdays(days=30)
        result_pks = [m.pk for m, d in result]
        # The birthday would be Jan 10 next year = 2027, which is ~209 days away
        # So it should NOT appear in a 30-day window
        assert member.pk not in result_pks

    @freeze_time('2026-12-15')
    def test_feb_29_birthday_past_wraps_to_next_year_non_leap(self):
        """Feb 29 birthday past this year wraps to next year (2027 is not leap).

        Exercises lines 234-237: the except ValueError branch when
        birthday_this_year < today and next year is also not a leap year.
        """
        member = MemberFactory(birth_date=date(2000, 2, 29))

        # From Dec 15, 2026: end_date = 2027-03-15 (91 days)
        # Year boundary branch covers months Dec->Jan->Feb->Mar
        # Feb 29 birthday: replace(year=2026) -> ValueError -> March 1, 2026
        # March 1, 2026 < Dec 15, 2026 -> enters lines 234-237
        # replace(year=2027) -> ValueError -> March 1, 2027
        # days_until = (March 1 2027 - Dec 15 2026).days = 76, within 91
        result = get_upcoming_birthdays(days=91)
        result_dates = {m.pk: d for m, d in result}

        assert member.pk in result_dates
        # 2027 is not a leap year, so should map to March 1
        assert result_dates[member.pk] == date(2027, 3, 1)

    @freeze_time('2026-09-01')
    def test_upcoming_multi_month_span(self):
        """Test range spanning multiple months within the same year (exercises loop body line 219)."""
        # Oct 15 (in range)
        oct_member = MemberFactory(birth_date=date(1990, 10, 15))
        # Nov 15 (in range with 90-day window: Sep 1 + 90 = Nov 30)
        nov_member = MemberFactory(birth_date=date(1985, 11, 15))
        # Jan 15 (out of range)
        out_member = MemberFactory(birth_date=date(1988, 1, 15))

        # end_date = 2026-11-30, same year, else branch:
        #   range(today.month + 1, end_date.month) = range(10, 11) = [10] -> loop body (line 219) runs
        result = get_upcoming_birthdays(days=90)
        result_pks = [m.pk for m, d in result]
        assert oct_member.pk in result_pks
        assert nov_member.pk in result_pks
        assert out_member.pk not in result_pks


@pytest.mark.django_db
class TestGetCurrentMonthRangeDecember:
    """Test get_current_month_range for the December special case."""

    @freeze_time('2026-12-15')
    def test_december_range(self):
        """December should return Dec 1 to Dec 31."""
        start, end = get_current_month_range()
        assert start == date(2026, 12, 1)
        assert end == date(2026, 12, 31)

    @freeze_time('2026-12-01')
    def test_december_first_day(self):
        """December 1st should also return Dec 1 to Dec 31."""
        start, end = get_current_month_range()
        assert start == date(2026, 12, 1)
        assert end == date(2026, 12, 31)

    @freeze_time('2026-12-31')
    def test_december_last_day(self):
        """December 31st should return Dec 1 to Dec 31."""
        start, end = get_current_month_range()
        assert start == date(2026, 12, 1)
        assert end == date(2026, 12, 31)


class TestFormatPostalCodeEdgeCases:
    """Test format_postal_code with non-6-character input."""

    def test_non_6_char_returns_original(self):
        """Postal code not 6 chars after cleanup should be returned as-is."""
        assert format_postal_code('ABC') == 'ABC'

    def test_too_long_returns_original(self):
        """Postal code longer than 6 chars should be returned as-is."""
        assert format_postal_code('H1A1A1X') == 'H1A1A1X'

    def test_single_char_returns_original(self):
        """Single character postal code returned as-is."""
        assert format_postal_code('X') == 'X'

    def test_five_chars_returns_original(self):
        """Five character input returned as-is."""
        assert format_postal_code('H1A1A') == 'H1A1A'
