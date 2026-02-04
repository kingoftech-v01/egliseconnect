"""
Tests for core utilities.
"""
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


# =============================================================================
# FORMATTING TESTS
# =============================================================================

class TestFormatPhone:
    """Tests for format_phone function."""

    def test_format_10_digit_phone(self):
        """Test formatting 10-digit phone numbers."""
        assert format_phone('5141234567') == '(514) 123-4567'

    def test_format_phone_with_existing_formatting(self):
        """Test formatting phone with existing punctuation."""
        assert format_phone('514-123-4567') == '(514) 123-4567'

    def test_format_11_digit_phone(self):
        """Test formatting 11-digit phone numbers."""
        assert format_phone('15141234567') == '1-(514) 123-4567'

    def test_format_empty_phone(self):
        """Test formatting empty phone."""
        assert format_phone('') == ''
        assert format_phone(None) == ''

    def test_format_invalid_phone(self):
        """Test formatting invalid phone returns original."""
        assert format_phone('123') == '123'


class TestFormatPostalCode:
    """Tests for format_postal_code function."""

    def test_format_postal_code(self):
        """Test formatting postal codes."""
        assert format_postal_code('H1A1A1') == 'H1A 1A1'

    def test_format_postal_code_with_space(self):
        """Test formatting postal code with existing space."""
        assert format_postal_code('H1A 1A1') == 'H1A 1A1'

    def test_format_lowercase_postal_code(self):
        """Test formatting lowercase postal codes."""
        assert format_postal_code('h1a1a1') == 'H1A 1A1'

    def test_format_empty_postal_code(self):
        """Test formatting empty postal code."""
        assert format_postal_code('') == ''
        assert format_postal_code(None) == ''


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_format_currency(self):
        """Test formatting currency."""
        assert format_currency(100) == '$100.00'
        assert format_currency(1000) == '$1,000.00'
        assert format_currency(1234.56) == '$1,234.56'

    def test_format_currency_decimal(self):
        """Test formatting Decimal currency."""
        assert format_currency(Decimal('100.00')) == '$100.00'

    def test_format_currency_none(self):
        """Test formatting None returns $0.00."""
        assert format_currency(None) == '$0.00'


# =============================================================================
# DATE UTILITIES TESTS
# =============================================================================

class TestGetCurrentWeekRange:
    """Tests for get_current_week_range function."""

    def test_returns_monday_to_sunday(self):
        """Test that it returns Monday to Sunday."""
        start, end = get_current_week_range()

        # Start should be Monday
        assert start.weekday() == 0

        # End should be Sunday
        assert end.weekday() == 6

        # Should be 6 days apart
        assert (end - start).days == 6


class TestGetCurrentMonthRange:
    """Tests for get_current_month_range function."""

    def test_returns_first_and_last_day(self):
        """Test that it returns first and last day of month."""
        start, end = get_current_month_range()

        # Start should be first day
        assert start.day == 1

        # End should be last day of month
        # Next month first day minus one day
        next_month = (end + timedelta(days=1))
        assert next_month.day == 1


class TestGetDateRange:
    """Tests for get_date_range function."""

    def test_today_range(self):
        """Test 'today' period."""
        start, end = get_date_range('today')
        today = date.today()

        assert start == today
        assert end == today

    def test_week_range(self):
        """Test 'week' period."""
        start, end = get_date_range('week')

        assert start.weekday() == 0
        assert end.weekday() == 6

    def test_month_range(self):
        """Test 'month' period."""
        start, end = get_date_range('month')

        assert start.day == 1

    def test_year_range(self):
        """Test 'year' period."""
        start, end = get_date_range('year')
        today = date.today()

        assert start == date(today.year, 1, 1)
        assert end == date(today.year, 12, 31)

    def test_invalid_period_raises(self):
        """Test that invalid period raises ValueError."""
        with pytest.raises(ValueError):
            get_date_range('invalid')
