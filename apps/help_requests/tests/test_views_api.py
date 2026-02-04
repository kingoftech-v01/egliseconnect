"""Help Requests API view tests."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.help_requests.models import HelpRequest, HelpRequestComment
from .factories import HelpRequestFactory, HelpRequestCategoryFactory, HelpRequestCommentFactory
from apps.members.tests.factories import MemberFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user():
    user = UserFactory()
    member = MemberFactory(user=user, role='member')
    return user, member


@pytest.fixture
def pastor_user():
    user = UserFactory()
    member = MemberFactory(user=user, role='pastor')
    return user, member


@pytest.mark.django_db
class TestHelpRequestCategoryAPI:
    """Tests for HelpRequestCategory API."""

    def test_list_categories(self, api_client, member_user):
        """Test listing help request categories."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        HelpRequestCategoryFactory.create_batch(3)

        response = api_client.get('/api/v1/help-requests/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3


@pytest.mark.django_db
class TestHelpRequestAPI:
    """Tests for HelpRequest API."""

    def test_create_help_request(self, api_client, member_user):
        """Test creating a help request."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        category = HelpRequestCategoryFactory()

        data = {
            'category': str(category.id),
            'title': 'Need help with groceries',
            'description': 'Unable to go shopping due to illness',
            'urgency': 'medium',
            'is_confidential': False
        }

        response = api_client.post('/api/v1/help-requests/requests/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Need help with groceries'
        assert response.data['request_number'].startswith('HR-')

    def test_list_own_requests(self, api_client, member_user):
        """Test listing user's own requests."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        # Create requests for this member
        HelpRequestFactory.create_batch(2, member=member)
        # Create requests for another member
        HelpRequestFactory.create_batch(3)

        response = api_client.get('/api/v1/help-requests/requests/my_requests/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_pastor_sees_all_requests(self, api_client, pastor_user):
        """Test pastor can see all requests."""
        user, member = pastor_user
        api_client.force_authenticate(user=user)

        HelpRequestFactory.create_batch(5)

        response = api_client.get('/api/v1/help-requests/requests/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 5

    def test_assign_request(self, api_client, pastor_user):
        """Test assigning a request."""
        user, pastor = pastor_user
        api_client.force_authenticate(user=user)

        request = HelpRequestFactory(status='new')
        staff = MemberFactory(role='pastor')

        response = api_client.post(
            f'/api/v1/help-requests/requests/{request.id}/assign/',
            {'assigned_to': str(staff.id)}
        )
        assert response.status_code == status.HTTP_200_OK

        request.refresh_from_db()
        assert request.assigned_to == staff
        assert request.status == 'in_progress'

    def test_resolve_request(self, api_client, pastor_user):
        """Test resolving a request."""
        user, pastor = pastor_user
        api_client.force_authenticate(user=user)

        request = HelpRequestFactory(status='in_progress')

        response = api_client.post(
            f'/api/v1/help-requests/requests/{request.id}/resolve/',
            {'resolution_notes': 'Completed successfully'}
        )
        assert response.status_code == status.HTTP_200_OK

        request.refresh_from_db()
        assert request.status == 'resolved'
        assert request.resolution_notes == 'Completed successfully'

    def test_add_comment(self, api_client, member_user):
        """Test adding a comment to a request."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        request = HelpRequestFactory(member=member)

        response = api_client.post(
            f'/api/v1/help-requests/requests/{request.id}/comment/',
            {'content': 'Thank you for the help!', 'is_internal': False}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Thank you for the help!'

    def test_member_cannot_create_internal_comment(self, api_client, member_user):
        """Test member cannot create internal comments."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        request = HelpRequestFactory(member=member)

        response = api_client.post(
            f'/api/v1/help-requests/requests/{request.id}/comment/',
            {'content': 'Internal note', 'is_internal': True}
        )
        assert response.status_code == status.HTTP_201_CREATED
        # Should be forced to non-internal
        assert response.data['is_internal'] is False

    def test_confidential_request_hidden_from_regular_member(self, api_client, member_user):
        """Test confidential requests are hidden from regular members."""
        user, member = member_user
        api_client.force_authenticate(user=user)

        # Create confidential request by another member
        HelpRequestFactory(is_confidential=True)
        # Create own request
        HelpRequestFactory(member=member)

        response = api_client.get('/api/v1/help-requests/requests/')
        assert response.status_code == status.HTTP_200_OK
        # Should only see own request
        assert len(response.data) == 1
