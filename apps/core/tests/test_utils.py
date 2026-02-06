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
