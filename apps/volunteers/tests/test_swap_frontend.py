"""Tests for swap request frontend views: list, create, detail."""
import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles, ScheduleStatus
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.volunteers.models import SwapRequest
from apps.volunteers.tests.factories import (
    VolunteerScheduleFactory, SwapRequestFactory, VolunteerPositionFactory,
)

pytestmark = pytest.mark.django_db


class TestSwapRequestListView:
    """Tests for swap_request_list view."""

    def test_requires_login(self):
        client = Client()
        response = client.get('/volunteers/swap-requests/')
        assert response.status_code == 302

    def test_member_sees_own_requests(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        member = user.member_profile
        schedule = VolunteerScheduleFactory(member=member)
        SwapRequestFactory(requested_by=member, original_schedule=schedule)
        # Other member's request
        SwapRequestFactory()

        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/swap-requests/')
        assert response.status_code == 200

    def test_staff_sees_all_requests(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        SwapRequestFactory()
        SwapRequestFactory()

        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/swap-requests/')
        assert response.status_code == 200

    def test_no_member_profile_redirects(self):
        from apps.members.tests.factories import UserFactory
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/swap-requests/')
        assert response.status_code == 302


class TestSwapRequestCreateView:
    """Tests for swap_request_create view."""

    def test_requires_login(self):
        client = Client()
        response = client.get('/volunteers/swap-requests/create/')
        assert response.status_code == 302

    def test_get_form(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/swap-requests/create/')
        assert response.status_code == 200

    def test_create_swap_request(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        member = user.member_profile
        position = VolunteerPositionFactory()
        schedule = VolunteerScheduleFactory(
            member=member,
            position=position,
            date=timezone.now().date() + timezone.timedelta(days=7),
        )
        target = MemberFactory()

        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/swap-requests/create/', {
            'requesting_schedule': schedule.pk,
            'target_member': target.pk,
            'reason': 'Cannot make it',
        })
        assert response.status_code == 302
        assert SwapRequest.objects.filter(requested_by=member).exists()


class TestSwapRequestDetailView:
    """Tests for swap_request_detail view."""

    def test_owner_can_view(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        member = user.member_profile
        schedule = VolunteerScheduleFactory(member=member)
        swap = SwapRequestFactory(requested_by=member, original_schedule=schedule)

        client = Client()
        client.force_login(user)
        response = client.get(f'/volunteers/swap-requests/{swap.pk}/')
        assert response.status_code == 200

    def test_staff_can_approve(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        swap = SwapRequestFactory(status='pending')

        client = Client()
        client.force_login(user)
        response = client.post(f'/volunteers/swap-requests/{swap.pk}/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        swap.refresh_from_db()
        assert swap.status == 'approved'

    def test_staff_can_decline(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        swap = SwapRequestFactory(status='pending')

        client = Client()
        client.force_login(user)
        response = client.post(f'/volunteers/swap-requests/{swap.pk}/', {
            'action': 'decline',
        })
        assert response.status_code == 302
        swap.refresh_from_db()
        assert swap.status == 'declined'

    def test_non_involved_member_denied(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        swap = SwapRequestFactory()

        client = Client()
        client.force_login(user)
        response = client.get(f'/volunteers/swap-requests/{swap.pk}/')
        assert response.status_code == 302  # Redirect access denied
