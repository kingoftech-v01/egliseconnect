"""Tests for help_requests API views."""
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
        user, member = member_user
        api_client.force_authenticate(user=user)
        HelpRequestCategoryFactory.create_batch(3)
        response = api_client.get('/api/v1/help-requests/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3


@pytest.mark.django_db
class TestHelpRequestAPI:
    """Tests for HelpRequest API."""

    def test_create_help_request(self, api_client, member_user):
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
        created = HelpRequest.objects.filter(member=member).first()
        assert created.request_number.startswith('HR-')

    def test_list_own_requests(self, api_client, member_user):
        user, member = member_user
        api_client.force_authenticate(user=user)
        HelpRequestFactory.create_batch(2, member=member)
        HelpRequestFactory.create_batch(3)  # other member's
        response = api_client.get('/api/v1/help-requests/requests/my_requests/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_pastor_sees_all_requests(self, api_client, pastor_user):
        user, member = pastor_user
        api_client.force_authenticate(user=user)
        HelpRequestFactory.create_batch(5)
        response = api_client.get('/api/v1/help-requests/requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 5

    def test_assign_request(self, api_client, pastor_user):
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
        """Regular members cannot create internal comments; forced to public."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        request = HelpRequestFactory(member=member)
        response = api_client.post(
            f'/api/v1/help-requests/requests/{request.id}/comment/',
            {'content': 'Internal note', 'is_internal': True}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_internal'] is False

    def test_confidential_request_hidden_from_regular_member(self, api_client, member_user):
        """Confidential requests from others are hidden from regular members."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        HelpRequestFactory(is_confidential=True)  # another member's
        HelpRequestFactory(member=member)  # own request
        response = api_client.get('/api/v1/help-requests/requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
