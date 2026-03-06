"""Tests for communication model __str__ methods."""
import pytest

from apps.core.constants import NewsletterStatus
from apps.communication.models import Newsletter
from apps.communication.tests.factories import NewsletterFactory

pytestmark = pytest.mark.django_db


class TestNewsletterStr:
    """Tests for Newsletter.__str__."""

    def test_str_returns_subject_and_status(self):
        newsletter = NewsletterFactory(
            subject='Weekly Update',
            status=NewsletterStatus.DRAFT,
        )
        result = str(newsletter)
        assert 'Weekly Update' in result
        # get_status_display() returns the human-readable label
        assert newsletter.get_status_display() in result

    def test_str_with_sent_status(self):
        newsletter = NewsletterFactory(
            subject='Monthly Report',
            status=NewsletterStatus.SENT,
        )
        result = str(newsletter)
        assert 'Monthly Report' in result
        assert newsletter.get_status_display() in result

    def test_str_format_is_subject_status_display(self):
        newsletter = NewsletterFactory(
            subject='Test Newsletter',
            status=NewsletterStatus.DRAFT,
        )
        expected = f'{newsletter.subject} ({newsletter.get_status_display()})'
        assert str(newsletter) == expected
