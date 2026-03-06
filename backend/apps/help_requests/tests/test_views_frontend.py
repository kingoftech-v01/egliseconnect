"""Tests for help_requests frontend views."""
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
    """User without member profile."""
    return UserFactory()


@pytest.fixture
def category():
    """Active help request category."""
    return HelpRequestCategoryFactory()


@pytest.mark.django_db
class TestRequestCreateView:
    """Tests for request_create view."""

    def test_get_form(self, client, member_user, category):
        user, member = member_user
        client.force_login(user)
        response = client.get(reverse('frontend:help_requests:request_create'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'categories' in response.context

    def test_post_valid_form(self, client, member_user, category):
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
        user, _ = member_user
        client.force_login(user)
        data = {
            'title': '',
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
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:help_requests:request_create'))
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:help_requests:request_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestRequestListView:
    """Tests for request_list view (staff only)."""

    def test_pastor_sees_all(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestFactory.create_batch(5)
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 5

    def test_admin_sees_all(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        HelpRequestFactory.create_batch(3)
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 3

    def test_member_redirected_to_my_requests(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 302

    def test_no_profile_redirected(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 302

    def test_filter_by_status(self, client, pastor_user):
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
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestCategoryFactory(is_active=True)
        HelpRequestCategoryFactory(is_active=True)
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 200
        assert len(response.context['categories']) >= 2

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:help_requests:request_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestRequestDetailView:
    """Tests for request_detail view."""

    def test_owner_can_view(self, client, member_user):
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
        user, _ = pastor_user
        client.force_login(user)
        hr = HelpRequestFactory()
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 200
        assert response.context['can_manage'] is True

    def test_admin_can_view_any(self, client, admin_user):
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
        """Group leader cannot view confidential requests even from group members."""
        user, leader = group_leader_user
        client.force_login(user)
        group = GroupFactory(leader=leader)
        group_member = MemberFactory(role=Roles.MEMBER)
        GroupMembershipFactory(member=group_member, group=group)
        hr = HelpRequestFactory(member=group_member, is_confidential=True)
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302

    def test_non_owner_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        hr = HelpRequestFactory()
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        hr = HelpRequestFactory()
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302

    def test_not_found(self, client, member_user):
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
        """Member sees only public comments on their own request."""
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
        m_user, member = member_user
        p_user, pastor = pastor_user
        hr = HelpRequestFactory(member=member)

        client.force_login(m_user)
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.context['assign_form'] is None

        client.force_login(p_user)
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.context['assign_form'] is not None

    def test_unauthenticated_redirects(self, client):
        hr = HelpRequestFactory()
        response = client.get(
            reverse('frontend:help_requests:request_detail', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestMyRequestsView:
    """Tests for my_requests view."""

    def test_member_sees_own_requests(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        HelpRequestFactory.create_batch(3, member=member)
        HelpRequestFactory.create_batch(2)
        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 3

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_empty_list(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse('frontend:help_requests:my_requests'))
        assert response.status_code == 200
        assert len(response.context['requests']) == 0


@pytest.mark.django_db
class TestRequestUpdateView:
    """Tests for request_update view."""

    def test_assign_action(self, client, pastor_user):
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
        user, _ = member_user
        client.force_login(user)
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            {'action': 'close'},
        )
        assert response.status_code == 302

    def test_no_profile_denied(self, client, user_no_profile):
        client.force_login(user_no_profile)
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            {'action': 'close'},
        )
        assert response.status_code == 302

    def test_not_found(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        fake_pk = uuid.uuid4()
        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': fake_pk}),
            {'action': 'close'},
        )
        assert response.status_code == 404

    def test_resolve_without_notes(self, client, pastor_user):
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
        user, _ = pastor_user
        client.force_login(user)
        hr = HelpRequestFactory()
        response = client.get(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_update', kwargs={'pk': hr.pk}),
            {'action': 'close'},
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestRequestCommentView:
    """Tests for request_comment view."""

    def test_owner_can_comment(self, client, member_user):
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
        user, member = member_user
        client.force_login(user)
        hr = HelpRequestFactory()
        data = {
            'content': 'Should not work',
            'is_internal': False,
        }
        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302
        assert not HelpRequestComment.objects.filter(author=member).exists()

    def test_no_member_profile_redirects(self, client, user_no_profile):
        client.force_login(user_no_profile)
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            {'content': 'Test', 'is_internal': False},
        )
        assert response.status_code == 302

    def test_not_found(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        fake_pk = uuid.uuid4()
        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': fake_pk}),
            {'content': 'Test', 'is_internal': False},
        )
        assert response.status_code == 404

    def test_invalid_form_redirects(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        hr = HelpRequestFactory(member=member)
        data = {
            'content': '',
            'is_internal': False,
        }
        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            data,
        )
        assert response.status_code == 302
        assert not HelpRequestComment.objects.filter(help_request=hr).exists()

    def test_get_redirects(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        hr = HelpRequestFactory(member=member)
        response = client.get(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk})
        )
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        hr = HelpRequestFactory()
        response = client.post(
            reverse('frontend:help_requests:request_comment', kwargs={'pk': hr.pk}),
            {'content': 'Test', 'is_internal': False},
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestRequestListSearch:
    """Tests for search functionality in request_list."""

    def test_search_by_title(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestFactory(title="Need prayer support")
        HelpRequestFactory(title="Financial assistance needed")
        response = client.get(
            reverse("frontend:help_requests:request_list") + "?q=prayer"
        )
        assert response.status_code == 200
        assert len(response.context["requests"]) == 1
        assert response.context["search_query"] == "prayer"

    def test_search_by_description(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestFactory(title="Request A", description="urgent medical need")
        HelpRequestFactory(title="Request B", description="something else")
        response = client.get(
            reverse("frontend:help_requests:request_list") + "?q=medical"
        )
        assert response.status_code == 200
        assert len(response.context["requests"]) == 1

    def test_empty_search_shows_all(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestFactory.create_batch(3)
        response = client.get(
            reverse("frontend:help_requests:request_list") + "?q="
        )
        assert response.status_code == 200
        assert len(response.context["requests"]) == 3

    def test_stats_in_context(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestFactory(status=HelpRequestStatus.NEW)
        HelpRequestFactory(status=HelpRequestStatus.NEW)
        HelpRequestFactory(status=HelpRequestStatus.IN_PROGRESS)
        HelpRequestFactory(status=HelpRequestStatus.RESOLVED)
        response = client.get(reverse("frontend:help_requests:request_list"))
        assert response.status_code == 200
        stats = response.context["stats"]
        assert stats["open"] == 2
        assert stats["in_progress"] == 1
        assert stats["resolved"] == 1


@pytest.mark.django_db
class TestRequestDetailClose:
    """Tests for close button on request_detail."""

    def test_pastor_sees_can_close(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        hr = HelpRequestFactory(status=HelpRequestStatus.IN_PROGRESS)
        response = client.get(
            reverse("frontend:help_requests:request_detail", kwargs={"pk": hr.pk})
        )
        assert response.status_code == 200
        assert response.context["can_close"] is True

    def test_member_cannot_close_new(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        hr = HelpRequestFactory(member=member, status=HelpRequestStatus.NEW)
        response = client.get(
            reverse("frontend:help_requests:request_detail", kwargs={"pk": hr.pk})
        )
        assert response.status_code == 200
        assert response.context["can_close"] is False

    def test_member_can_close_resolved(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        hr = HelpRequestFactory(member=member, status=HelpRequestStatus.RESOLVED)
        response = client.get(
            reverse("frontend:help_requests:request_detail", kwargs={"pk": hr.pk})
        )
        assert response.status_code == 200
        assert response.context["can_close"] is True

    def test_closed_request_no_close_button(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        hr = HelpRequestFactory(status="closed")
        response = client.get(
            reverse("frontend:help_requests:request_detail", kwargs={"pk": hr.pk})
        )
        assert response.status_code == 200
        assert response.context["can_close"] is False


@pytest.mark.django_db
class TestRequestDetailTimeline:
    """Tests for status timeline on request_detail."""

    def test_new_request_has_timeline(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        hr = HelpRequestFactory(status=HelpRequestStatus.NEW)
        response = client.get(
            reverse("frontend:help_requests:request_detail", kwargs={"pk": hr.pk})
        )
        assert response.status_code == 200
        assert "timeline" in response.context
        assert len(response.context["timeline"]) >= 1

    def test_resolved_request_timeline(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        hr = HelpRequestFactory(status=HelpRequestStatus.RESOLVED)
        hr.mark_resolved("Done")
        response = client.get(
            reverse("frontend:help_requests:request_detail", kwargs={"pk": hr.pk})
        )
        assert response.status_code == 200
        timeline = response.context["timeline"]
        assert len(timeline) >= 2


@pytest.mark.django_db
class TestMyRequestsPagination:
    """Tests for pagination in my_requests."""

    def test_pagination(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        HelpRequestFactory.create_batch(25, member=member)
        response = client.get(reverse("frontend:help_requests:my_requests"))
        assert response.status_code == 200
        assert hasattr(response.context["requests"], "paginator")
        assert response.context["requests"].paginator.num_pages == 2

    def test_pagination_page_2(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        HelpRequestFactory.create_batch(25, member=member)
        response = client.get(
            reverse("frontend:help_requests:my_requests") + "?page=2"
        )
        assert response.status_code == 200
        assert len(response.context["requests"].object_list) == 5



@pytest.mark.django_db
class TestCategoryListView:

    def test_pastor_can_view(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestCategoryFactory.create_batch(3)
        response = client.get(reverse("frontend:help_requests:category_list"))
        assert response.status_code == 200
        assert len(response.context["categories"]) == 3

    def test_admin_can_view(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        HelpRequestCategoryFactory()
        response = client.get(reverse("frontend:help_requests:category_list"))
        assert response.status_code == 200

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse("frontend:help_requests:category_list"))
        assert response.status_code == 302

    def test_no_profile_denied(self, client, user_no_profile):
        client.force_login(user_no_profile)
        response = client.get(reverse("frontend:help_requests:category_list"))
        assert response.status_code == 302

    def test_shows_inactive_categories(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestCategoryFactory(is_active=True)
        HelpRequestCategoryFactory(is_active=False)
        response = client.get(reverse("frontend:help_requests:category_list"))
        assert response.status_code == 200
        assert len(response.context["categories"]) == 2

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse("frontend:help_requests:category_list"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestCategoryCreateView:

    def test_get_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(reverse("frontend:help_requests:category_create"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        from apps.help_requests.models import HelpRequestCategory
        data = {
            "name": "Transport",
            "name_fr": "Transport",
            "description": "Help with transportation",
            "icon": "car",
            "order": 5,
            "is_active": True,
        }
        response = client.post(
            reverse("frontend:help_requests:category_create"), data
        )
        assert response.status_code == 302
        assert HelpRequestCategory.objects.filter(name="Transport").exists()

    def test_post_invalid_form(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        data = {"name": ""}
        response = client.post(
            reverse("frontend:help_requests:category_create"), data
        )
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_member_denied(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get(reverse("frontend:help_requests:category_create"))
        assert response.status_code == 302

    def test_unauthenticated_redirects(self, client):
        response = client.get(reverse("frontend:help_requests:category_create"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url



@pytest.mark.django_db
class TestCategoryEditView:

    def test_get_form(self, client, pastor_user, category):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(
            reverse("frontend:help_requests:category_edit", kwargs={"pk": category.pk})
        )
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["category"] == category

    def test_post_valid_form(self, client, pastor_user, category):
        user, _ = pastor_user
        client.force_login(user)
        data = {
            "name": "Updated Name",
            "name_fr": "Nom mis a jour",
            "description": "Updated description",
            "icon": "star",
            "order": 10,
            "is_active": True,
        }
        response = client.post(
            reverse("frontend:help_requests:category_edit", kwargs={"pk": category.pk}),
            data,
        )
        assert response.status_code == 302
        category.refresh_from_db()
        assert category.name == "Updated Name"

    def test_member_denied(self, client, member_user, category):
        user, _ = member_user
        client.force_login(user)
        response = client.get(
            reverse("frontend:help_requests:category_edit", kwargs={"pk": category.pk})
        )
        assert response.status_code == 302

    def test_not_found(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(
            reverse("frontend:help_requests:category_edit", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client, category):
        response = client.get(
            reverse("frontend:help_requests:category_edit", kwargs={"pk": category.pk})
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_can_edit_inactive_category(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        cat = HelpRequestCategoryFactory(is_active=False)
        response = client.get(
            reverse("frontend:help_requests:category_edit", kwargs={"pk": cat.pk})
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestCategoryDeleteView:

    def test_get_confirmation_page(self, client, pastor_user, category):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(
            reverse("frontend:help_requests:category_delete", kwargs={"pk": category.pk})
        )
        assert response.status_code == 200
        assert response.context["category"] == category
        assert "request_count" in response.context

    def test_delete_empty_category(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        cat = HelpRequestCategoryFactory()
        pk = cat.pk
        response = client.post(
            reverse("frontend:help_requests:category_delete", kwargs={"pk": pk})
        )
        assert response.status_code == 302
        from apps.help_requests.models import HelpRequestCategory
        assert not HelpRequestCategory.all_objects.filter(pk=pk).exists()

    def test_deactivate_category_with_requests(self, client, pastor_user, category):
        user, _ = pastor_user
        client.force_login(user)
        HelpRequestFactory(category=category)
        response = client.post(
            reverse("frontend:help_requests:category_delete", kwargs={"pk": category.pk})
        )
        assert response.status_code == 302
        category.refresh_from_db()
        assert category.is_active is False

    def test_member_denied(self, client, member_user, category):
        user, _ = member_user
        client.force_login(user)
        response = client.get(
            reverse("frontend:help_requests:category_delete", kwargs={"pk": category.pk})
        )
        assert response.status_code == 302

    def test_not_found(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(
            reverse("frontend:help_requests:category_delete", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects(self, client, category):
        response = client.get(
            reverse("frontend:help_requests:category_delete", kwargs={"pk": category.pk})
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

