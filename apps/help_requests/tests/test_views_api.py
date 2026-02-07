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


@pytest.mark.django_db
class TestHelpRequestViewSetMissedBranches:
    """Tests covering uncovered branches in HelpRequestViewSet."""

    def test_queryset_no_member_profile(self, api_client):
        """User without member_profile gets empty queryset (line 45)."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        HelpRequestFactory()  # someone else's request
        response = api_client.get('/api/v1/help-requests/requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_queryset_group_leader(self, api_client):
        """Group leader sees own + group members' non-confidential requests (lines 53-58)."""
        from apps.members.tests.factories import GroupFactory, GroupMembershipFactory

        leader_user = UserFactory()
        leader = MemberFactory(user=leader_user, role='group_leader')
        group = GroupFactory(leader=leader)
        group_member = MemberFactory()
        GroupMembershipFactory(member=group_member, group=group)

        own_req = HelpRequestFactory(member=leader)
        member_req = HelpRequestFactory(member=group_member, is_confidential=False)
        confidential_req = HelpRequestFactory(member=group_member, is_confidential=True)
        other_req = HelpRequestFactory()  # unrelated member

        api_client.force_authenticate(user=leader_user)
        response = api_client.get('/api/v1/help-requests/requests/')
        assert response.status_code == status.HTTP_200_OK
        ids = [r['id'] for r in response.data['results']]
        assert str(own_req.pk) in ids
        assert str(member_req.pk) in ids
        assert str(confidential_req.pk) not in ids
        assert str(other_req.pk) not in ids

    def test_my_requests_no_profile(self, api_client):
        """User without member_profile gets 400 on my_requests (line 81)."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/v1/help-requests/requests/my_requests/')
        assert response.status_code == 400
        assert 'Member profile required' in response.data['detail']

    def test_assign_nonexistent_member(self, api_client, pastor_user):
        """Assign to non-existent member returns 404 (lines 97-98)."""
        import uuid
        user, pastor = pastor_user
        api_client.force_authenticate(user=user)
        hr = HelpRequestFactory(status='new')
        response = api_client.post(
            f'/api/v1/help-requests/requests/{hr.pk}/assign/',
            {'assigned_to': str(uuid.uuid4())}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Member not found' in response.data['detail']

    def test_comment_no_member_profile(self, api_client):
        """User without member_profile gets 400 on comment (line 123)."""
        from unittest import mock
        from apps.help_requests.views_api import HelpRequestViewSet

        user = UserFactory()
        api_client.force_authenticate(user=user)
        hr = HelpRequestFactory()
        # Mock get_object to bypass empty queryset (user has no profile)
        with mock.patch.object(HelpRequestViewSet, 'get_object', return_value=hr):
            response = api_client.post(
                f'/api/v1/help-requests/requests/{hr.pk}/comment/',
                {'content': 'test comment'}
            )
        assert response.status_code == 400
        assert 'Member profile required' in response.data['detail']

    def test_comments_action_non_staff_filters_internal(self, api_client, member_user):
        """Non-staff user should not see internal comments (lines 147-157)."""
        user, member = member_user
        api_client.force_authenticate(user=user)
        hr = HelpRequestFactory(member=member)
        HelpRequestComment.objects.create(
            help_request=hr, author=member, content='public comment', is_internal=False
        )
        HelpRequestComment.objects.create(
            help_request=hr, author=member, content='internal comment', is_internal=True
        )
        response = api_client.get(f'/api/v1/help-requests/requests/{hr.pk}/comments/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['content'] == 'public comment'

    def test_comments_action_staff_sees_all(self, api_client, pastor_user):
        """Staff user sees all comments including internal (lines 147-157)."""
        user, pastor = pastor_user
        api_client.force_authenticate(user=user)
        hr = HelpRequestFactory()
        HelpRequestComment.objects.create(
            help_request=hr, author=pastor, content='public', is_internal=False
        )
        HelpRequestComment.objects.create(
            help_request=hr, author=pastor, content='internal', is_internal=True
        )
        response = api_client.get(f'/api/v1/help-requests/requests/{hr.pk}/comments/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
