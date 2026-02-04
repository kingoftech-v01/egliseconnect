"""Help Requests model tests."""
import pytest
from django.utils import timezone
from apps.help_requests.models import HelpRequest, HelpRequestCategory
from .factories import HelpRequestFactory, HelpRequestCategoryFactory, HelpRequestCommentFactory
from apps.members.tests.factories import MemberFactory


@pytest.mark.django_db
class TestHelpRequestCategory:
    """Tests for HelpRequestCategory model."""

    def test_create_category(self):
        """Test creating a help request category."""
        category = HelpRequestCategoryFactory(
            name='Prayer Request',
            name_fr='Demande de prière'
        )
        assert category.name == 'Prayer Request'
        assert category.name_fr == 'Demande de prière'
        assert category.is_active is True

    def test_category_str(self):
        """Test category string representation."""
        category = HelpRequestCategoryFactory(name='Financial Help')
        assert str(category) == 'Financial Help'


@pytest.mark.django_db
class TestHelpRequest:
    """Tests for HelpRequest model."""

    def test_create_help_request(self):
        """Test creating a help request."""
        request = HelpRequestFactory(
            title='Need prayer for healing',
            urgency='high'
        )
        assert request.title == 'Need prayer for healing'
        assert request.urgency == 'high'
        assert request.status == 'new'
        assert request.request_number.startswith('HR-')

    def test_request_number_auto_generation(self):
        """Test auto-generation of request number."""
        request = HelpRequestFactory()
        assert request.request_number is not None
        assert request.request_number.startswith('HR-')
        # Format: HR-YYYYMM-XXXX
        parts = request.request_number.split('-')
        assert len(parts) == 3
        assert len(parts[1]) == 6  # YYYYMM
        assert len(parts[2]) == 4  # XXXX

    def test_help_request_str(self):
        """Test help request string representation."""
        request = HelpRequestFactory(title='Test Request')
        assert request.title in str(request)
        assert request.request_number in str(request)

    def test_mark_resolved(self):
        """Test marking request as resolved."""
        request = HelpRequestFactory(status='in_progress')
        request.mark_resolved(notes='Helped with groceries')

        assert request.status == 'resolved'
        assert request.resolved_at is not None
        assert request.resolution_notes == 'Helped with groceries'

    def test_assign_to(self):
        """Test assigning request to staff."""
        request = HelpRequestFactory(status='new')
        staff = MemberFactory(role='pastor')

        request.assign_to(staff)

        assert request.assigned_to == staff
        assert request.status == 'in_progress'

    def test_confidential_request(self):
        """Test confidential request flag."""
        request = HelpRequestFactory(is_confidential=True)
        assert request.is_confidential is True


@pytest.mark.django_db
class TestHelpRequestComment:
    """Tests for HelpRequestComment model."""

    def test_create_comment(self):
        """Test creating a comment."""
        comment = HelpRequestCommentFactory(
            content='We will help you this week.',
            is_internal=False
        )
        assert comment.content == 'We will help you this week.'
        assert comment.is_internal is False

    def test_internal_comment(self):
        """Test internal staff comment."""
        comment = HelpRequestCommentFactory(is_internal=True)
        assert comment.is_internal is True

    def test_comment_str(self):
        """Test comment string representation."""
        comment = HelpRequestCommentFactory()
        assert comment.help_request.request_number in str(comment)
