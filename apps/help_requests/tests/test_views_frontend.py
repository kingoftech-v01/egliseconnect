"""Help requests frontend view tests."""
import uuid

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.constants import Roles, HelpRequestStatus, HelpRequestUrgency
from apps.help_requests.models import HelpRequest, HelpRequestComment
from apps.members.models import GroupMembership
from .factories import (
    HelpRequestFactory,
    HelpRequestCategoryFactory,
    HelpRequestCommentFactory,
)
from apps.members.tests.factories import (
    MemberFactory,
    UserFactory,
    GroupFactory,
    GroupMembershipFactory,
)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def member_user():
    """Regular member with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.fixture
def pastor_user():
    """Pastor with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.PASTOR)
    return user, member


@pytest.fixture
def admin_user():
    """Admin with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.ADMIN)
    return user, member


@pytest.fixture
def group_leader_user():
    """Group leader with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.GROUP_LEADER)
    return user, member


@pytest.fixture
def user_no_profile():
    """Authenticated user without member profile."""
    return UserFactory()


@pytest.fixture
def category():
    """Active help request category."""
    return HelpRequestCategoryFactory()


# =============================================================================
# REQUEST CREATE VIEW
# =============================================================================


@pytest.mark.django_db
class TestRequestCreateView:
    """Tests for request_create view."""

    def test_get_form(self, client, member_user, category):
        """Member can access the creation form."""
        user, member = member_user
        client.force_login(user)

        response = client.get(reverse('frontend:help_requests:request_create'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'categories' in response.context

    def test_post_valid_form(self, client, member_user, category):
        """Valid POST creates a help request."""
        user, member = member_user
        client.force_login(user)

        data = {
            'category': str(category.id),
            'title': 'Need help moving',
            'description': 'Moving to a new apartment this weekend',
            'urgency': HelpRequestUrgency.MEDIUM,
            'is_confidential': False,
        }

        response = client.post(
            reverse('frontend:help_requests:request_create'), data
        )
        assert response.status_code == 302

        hr = HelpRequest.objects.get(title='Need help moving')
        assert hr.member == member
        assert hr.category == category
        assert hr.request_number.startswith('HR-')

    def test_post_invalid_form(self, client, member_user):
        """Invalid POST re-renders form with errors."""
        user, _ = member_user
        client.force_login(user)

        data = {
            'title': '',  # required
            'description': 'Missing title',
            'urgency': HelpRequestUrgency.LOW,
        }

        response = client.post(
            reverse('frontend:help_requests:request_create'), data
        )
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_no_member_profile_redirects(self, client, user_no_profile):
        """User without member profile is redirected."""
        client.force_login(user_no_profile)

        response = client.get(reverse('frontend:help_requests:request_create'))
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:help_requests:request_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# REQUEST LIST VIEW
# =============================================================================


@pytest.mark.django_db
class TestRequestListView:
    """Tests for request_list view (staff only)."""

    def test_pastor_sees_all(self, client, pastor_user):
        """Pastor sees all help requests."""
        user, _ = pastor_user
        client.force_login(user)

        HelpRequestFactory.create_batch(5)

        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 5

    def test_admin_sees_all(self, client, admin_user):
        """Admin sees all help requests."""
        user, _ = admin_user
        client.force_login(user)

        HelpRequestFactory.create_batch(3)

        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 3

    def test_member_redirected_to_my_requests(self, client, member_user):
        """Regular member is redirected to my_requests."""
        user, _ = member_user
        client.force_login(user)

        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 302

    def test_no_profile_redirected(self, client, user_no_profile):
        """User without profile is redirected."""
        client.force_login(user_no_profile)

        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 302

    def test_filter_by_status(self, client, pastor_user):
        """Can filter by status."""
        user, _ = pastor_user
        client.force_login(user)

        HelpRequestFactory(status=HelpRequestStatus.NEW)
        HelpRequestFactory(status=HelpRequestStatus.NEW)
        HelpRequestFactory(status=HelpRequestStatus.RESOLVED)

        response = client.get(
            reverse('frontend:help_requests:request_list') + '?status=new'
        )
        assert response.status_code == 200
        assert len(response.context['requests']) == 2
        assert response.context['current_status'] == 'new'

    def test_filter_by_urgency(self, client, pastor_user):
        """Can filter by urgency."""
        user, _ = pastor_user
        client.force_login(user)

        HelpRequestFactory(urgency=HelpRequestUrgency.HIGH)
        HelpRequestFactory(urgency=HelpRequestUrgency.LOW)

        response = client.get(
            reverse('frontend:help_requests:request_list') + '?urgency=high'
        )
        assert response.status_code == 200
        assert len(response.context['requests']) == 1
        assert response.context['current_urgency'] == 'high'

    def test_filter_by_category(self, client, pastor_user, category):
        """Can filter by category."""
        user, _ = pastor_user
        client.force_login(user)

        other_category = HelpRequestCategoryFactory()
        HelpRequestFactory(category=category)
        HelpRequestFactory(category=category)
        HelpRequestFactory(category=other_category)

        response = client.get(
            reverse('frontend:help_requests:request_list')
            + f'?category={category.id}'
        )
        assert response.status_code == 200
        assert len(response.context['requests']) == 2
        assert response.context['current_category'] == str(category.id)

    def test_categories_in_context(self, client, pastor_user):
        """Active categories are in context."""
        user, _ = pastor_user
        client.force_login(user)

        HelpRequestCategoryFactory(is_active=True)
        HelpRequestCategoryFactory(is_active=True)

        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 200
        assert len(response.context['categories']) >= 2

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# REQUEST DETAIL VIEW
# =============================================================================


@pytest.mark.django_db
class TestRequestDetailView:
    """Tests for request_detail view."""

    def test_owner_can_view(self, client, member_user):
        """Owner can view their own request."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory(member=member)

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200
        assert response.context['help_request'] == hr
        assert response.context['can_manage'] is False

    def test_pastor_can_view_any(self, client, pastor_user):
        """Pastor can view any request."""
        user, _ = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory()

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200
        assert response.context['can_manage'] is True

    def test_admin_can_view_any(self, client, admin_user):
        """Admin can view any request."""
        user, _ = admin_user
        client.force_login(user)

        hr = HelpRequestFactory()

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200
        assert response.context['can_manage'] is True

    def test_group_leader_can_view_group_member_request(
        self, client, group_leader_user
    ):
        """Group leader can view non-confidential requests of group members."""
        user, leader = group_leader_user
        client.force_login(user)

        group = GroupFactory(leader=leader)
        group_member = MemberFactory(role=Roles.MEMBER)
        GroupMembershipFactory(member=group_member, group=group)

        hr = HelpRequestFactory(member=group_member, is_confidential=False)

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200

    def test_group_leader_cannot_view_confidential(self, client, group_leader_user):
        """Group leader cannot view confidential requests of group members."""
        user, leader = group_leader_user
        client.force_login(user)

        group = GroupFactory(leader=leader)
        group_member = MemberFactory(role=Roles.MEMBER)
        GroupMembershipFactory(member=group_member, group=group)

        hr = HelpRequestFactory(member=group_member, is_confidential=True)

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302  # redirected

    def test_non_owner_member_denied(self, client, member_user):
        """Regular member cannot view other's request."""
        user, _ = member_user
        client.force_login(user)

        hr = HelpRequestFactory()  # another member's request

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302  # redirected to my_requests

    def test_no_member_profile_redirects(self, client, user_no_profile):
        """User without member profile is redirected."""
        client.force_login(user_no_profile)

        hr = HelpRequestFactory()

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302

    def test_not_found(self, client, member_user):
        """Non-existent request returns 404."""
        user, _ = member_user
        client.force_login(user)

        fake_pk = uuid.uuid4()

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': fake_pk})
        )
        assert response.status_code == 404

    def test_pastor_sees_internal_comments(self, client, pastor_user):
        """Pastor sees both internal and public comments."""
        user, pastor = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory()
        HelpRequestCommentFactory(help_request=hr, is_internal=False)
        HelpRequestCommentFactory(help_request=hr, is_internal=True)

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200
        assert len(response.context['comments']) == 2

    def test_member_sees_only_public_comments(self, client, member_user):
        """Regular member sees only public comments on their own request."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory(member=member)
        HelpRequestCommentFactory(help_request=hr, is_internal=False)
        HelpRequestCommentFactory(help_request=hr, is_internal=True)

        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200
        assert len(response.context['comments']) == 1

    def test_assign_form_for_staff_only(self, client, member_user, pastor_user):
        """Assign form is provided only for pastor/admin."""
        m_user, member = member_user
        p_user, pastor = pastor_user

        hr = HelpRequestFactory(member=member)

        # Member does not get assign form
        client.force_login(m_user)
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.context['assign_form'] is None

        # Pastor gets assign form
        client.force_login(p_user)
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.context['assign_form'] is not None

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        hr = HelpRequestFactory()
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# MY REQUESTS VIEW
# =============================================================================


@pytest.mark.django_db
class TestMyRequestsView:
    """Tests for my_requests view."""

    def test_member_sees_own_requests(self, client, member_user):
        """Member sees only their own requests."""
        user, member = member_user
        client.force_login(user)

        HelpRequestFactory.create_batch(3, member=member)
        HelpRequestFactory.create_batch(2)  # other member's requests

        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 3

    def test_no_member_profile_redirects(self, client, user_no_profile):
        """User without member profile is redirected."""
        client.force_login(user_no_profile)

        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_empty_list(self, client, member_user):
        """Member with no requests sees empty list."""
        user, _ = member_user
        client.force_login(user)

        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 0


# =============================================================================
# REQUEST UPDATE VIEW
# =============================================================================


@pytest.mark.django_db
class TestRequestUpdateView:
    """Tests for request_update view."""

    def test_assign_action(self, client, pastor_user):
        """Pastor can assign a request."""
        user, pastor = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory(status=HelpRequestStatus.NEW)
        staff = MemberFactory(role=Roles.PASTOR)

        data = {
            'action': 'assign',
            'assigned_to': str(staff.id),
        }

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        hr.refresh_from_db()
        assert hr.assigned_to == staff
        assert hr.status == HelpRequestStatus.IN_PROGRESS

    def test_resolve_action(self, client, pastor_user):
        """Pastor can resolve a request."""
        user, _ = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory(status=HelpRequestStatus.IN_PROGRESS)

        data = {
            'action': 'resolve',
            'resolution_notes': 'Problem solved',
        }

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        hr.refresh_from_db()
        assert hr.status == HelpRequestStatus.RESOLVED
        assert hr.resolution_notes == 'Problem solved'
        assert hr.resolved_at is not None

    def test_close_action(self, client, pastor_user):
        """Pastor can close a request."""
        user, _ = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory(status=HelpRequestStatus.RESOLVED)

        data = {'action': 'close'}

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        hr.refresh_from_db()
        assert hr.status == 'closed'

    def test_member_denied(self, client, member_user):
        """Regular member cannot update requests."""
        user, _ = member_user
        client.force_login(user)

        hr = HelpRequestFactory()

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            {'action': 'close'},
        )
        assert response.status_code == 302  # redirected to my_requests

    def test_no_profile_denied(self, client, user_no_profile):
        """User without profile is denied."""
        client.force_login(user_no_profile)

        hr = HelpRequestFactory()

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            {'action': 'close'},
        )
        assert response.status_code == 302

    def test_not_found(self, client, pastor_user):
        """Non-existent request returns 404."""
        user, _ = pastor_user
        client.force_login(user)

        fake_pk = uuid.uuid4()

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': fake_pk}),
            {'action': 'close'},
        )
        assert response.status_code == 404

    def test_resolve_without_notes(self, client, pastor_user):
        """Resolving without notes uses empty string."""
        user, _ = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory(status=HelpRequestStatus.IN_PROGRESS)

        data = {'action': 'resolve'}

        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        hr.refresh_from_db()
        assert hr.status == HelpRequestStatus.RESOLVED
        assert hr.resolution_notes == ''

    def test_get_request_redirects(self, client, pastor_user):
        """GET on update view redirects back to detail (since only POST is handled)."""
        user, _ = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory()

        response = client.get(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk})
        )
        # The view always redirects at the end, regardless of method
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            {'action': 'close'},
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# =============================================================================
# REQUEST COMMENT VIEW
# =============================================================================


@pytest.mark.django_db
class TestRequestCommentView:
    """Tests for request_comment view."""

    def test_owner_can_comment(self, client, member_user):
        """Owner can comment on their own request."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory(member=member)

        data = {
            'content': 'Thank you for the help!',
            'is_internal': False,
        }

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        assert HelpRequestComment.objects.filter(
            help_request=hr, author=member, content='Thank you for the help!'
        ).exists()

    def test_pastor_can_comment(self, client, pastor_user):
        """Pastor can comment on any request."""
        user, pastor = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory()

        data = {
            'content': 'We will address this.',
            'is_internal': False,
        }

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        assert HelpRequestComment.objects.filter(
            help_request=hr, author=pastor
        ).exists()

    def test_pastor_can_create_internal_comment(self, client, pastor_user):
        """Pastor can create internal comments."""
        user, pastor = pastor_user
        client.force_login(user)

        hr = HelpRequestFactory()

        data = {
            'content': 'Internal note for staff',
            'is_internal': True,
        }

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        comment = HelpRequestComment.objects.get(
            help_request=hr, author=pastor
        )
        assert comment.is_internal is True

    def test_member_internal_comment_forced_to_public(self, client, member_user):
        """Regular member's internal comment is forced to public."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory(member=member)

        data = {
            'content': 'Trying to make internal',
            'is_internal': True,
        }

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302

        comment = HelpRequestComment.objects.get(
            help_request=hr, author=member
        )
        assert comment.is_internal is False

    def test_non_owner_non_staff_denied(self, client, member_user):
        """Non-owner regular member cannot comment."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory()  # another member's request

        data = {
            'content': 'Should not work',
            'is_internal': False,
        }

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302  # redirected to my_requests
        assert not HelpRequestComment.objects.filter(author=member).exists()

    def test_no_member_profile_redirects(self, client, user_no_profile):
        """User without member profile is redirected."""
        client.force_login(user_no_profile)

        hr = HelpRequestFactory()

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            {'content': 'Test', 'is_internal': False},
        )
        assert response.status_code == 302

    def test_not_found(self, client, member_user):
        """Non-existent request returns 404."""
        user, _ = member_user
        client.force_login(user)

        fake_pk = uuid.uuid4()

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': fake_pk}),
            {'content': 'Test', 'is_internal': False},
        )
        assert response.status_code == 404

    def test_invalid_form_redirects(self, client, member_user):
        """Invalid form submission still redirects to detail."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory(member=member)

        # Empty content is invalid
        data = {
            'content': '',
            'is_internal': False,
        }

        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        # View always redirects regardless of form validity
        assert response.status_code == 302
        # No comment was created
        assert not HelpRequestComment.objects.filter(help_request=hr).exists()

    def test_get_redirects(self, client, member_user):
        """GET on comment view redirects (only POST creates comment)."""
        user, member = member_user
        client.force_login(user)

        hr = HelpRequestFactory(member=member)

        response = client.get(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk})
        )
        # View always redirects at the end
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user is redirected to login."""
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            {'content': 'Test', 'is_internal': False},
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
