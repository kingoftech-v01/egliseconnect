"""Tests for onboarding checklist: models, views, scheduling blocking."""
import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles, ScheduleStatus, BackgroundCheckStatus
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.volunteers.models import (
    VolunteerSchedule, ChecklistProgress, PositionChecklist,
)
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory, VolunteerScheduleFactory,
    PositionChecklistFactory, ChecklistProgressFactory,
    VolunteerBackgroundCheckFactory,
)

pytestmark = pytest.mark.django_db


class TestPositionChecklistModel:
    """Tests for PositionChecklist model."""

    def test_str_contains_position_and_title(self):
        item = PositionChecklistFactory(title='Safety Training')
        result = str(item)
        assert 'Safety Training' in result
        assert item.position.name in result

    def test_ordering_by_order(self):
        pos = VolunteerPositionFactory()
        item2 = PositionChecklistFactory(position=pos, order=2, title='Second')
        item1 = PositionChecklistFactory(position=pos, order=1, title='First')
        items = list(PositionChecklist.objects.filter(position=pos))
        assert items[0].title == 'First'
        assert items[1].title == 'Second'


class TestChecklistProgressModel:
    """Tests for ChecklistProgress model."""

    def test_str_contains_status(self):
        progress = ChecklistProgressFactory(completed_at=timezone.now())
        result = str(progress)
        assert 'Complete' in result

    def test_str_in_progress(self):
        progress = ChecklistProgressFactory(completed_at=None)
        result = str(progress)
        assert 'En cours' in result

    def test_is_completed(self):
        progress = ChecklistProgressFactory(completed_at=timezone.now())
        assert progress.is_completed is True

    def test_is_not_completed(self):
        progress = ChecklistProgressFactory(completed_at=None)
        assert progress.is_completed is False

    def test_unique_member_checklist_item(self):
        member = MemberFactory()
        item = PositionChecklistFactory()
        ChecklistProgressFactory(member=member, checklist_item=item)
        with pytest.raises(Exception):
            ChecklistProgressFactory(member=member, checklist_item=item)


class TestChecklistManageView:
    """Tests for checklist_manage view."""

    def test_requires_staff(self):
        user = MemberWithUserFactory(role=Roles.MEMBER).user
        pos = VolunteerPositionFactory()
        client = Client()
        client.force_login(user)
        response = client.get(f'/volunteers/positions/{pos.pk}/checklist/')
        assert response.status_code == 302

    def test_staff_can_view(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        pos = VolunteerPositionFactory()
        client = Client()
        client.force_login(user)
        response = client.get(f'/volunteers/positions/{pos.pk}/checklist/')
        assert response.status_code == 200

    def test_add_checklist_item(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        pos = VolunteerPositionFactory()
        client = Client()
        client.force_login(user)
        response = client.post(f'/volunteers/positions/{pos.pk}/checklist/', {
            'position': pos.pk,
            'title': 'Background Check',
            'description': 'Complete background check',
            'order': 1,
            'is_required': True,
        })
        assert response.status_code == 302
        assert PositionChecklist.objects.filter(position=pos).exists()


class TestOnboardingChecklistView:
    """Tests for onboarding_checklist view."""

    def test_view_checklist(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        pos = VolunteerPositionFactory()
        PositionChecklistFactory(position=pos, title='Item 1')
        client = Client()
        client.force_login(user)
        response = client.get(f'/volunteers/onboarding/{pos.pk}/')
        assert response.status_code == 200

    def test_complete_item(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        member = user.member_profile
        pos = VolunteerPositionFactory()
        item = PositionChecklistFactory(position=pos)
        client = Client()
        client.force_login(user)
        response = client.post(f'/volunteers/onboarding/{pos.pk}/', {
            'item_id': item.pk,
        })
        assert response.status_code == 302
        assert ChecklistProgress.objects.filter(
            member=member, checklist_item=item, completed_at__isnull=False
        ).exists()


class TestChecklistBlocksScheduling:
    """Tests for checklist completion blocking schedule creation."""

    def test_schedule_blocked_if_checklist_incomplete(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        PositionChecklistFactory(position=pos, is_required=True)

        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/schedule/create/', {
            'member': member.pk,
            'position': pos.pk,
            'date': (timezone.now().date() + timezone.timedelta(days=7)).isoformat(),
            'status': ScheduleStatus.SCHEDULED,
            'notes': '',
        })
        # Should stay on form with error
        assert response.status_code == 200
        assert not VolunteerSchedule.objects.filter(member=member).exists()

    def test_schedule_allowed_if_checklist_complete(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        item = PositionChecklistFactory(position=pos, is_required=True)
        ChecklistProgressFactory(
            member=member, checklist_item=item, completed_at=timezone.now()
        )

        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/schedule/create/', {
            'member': member.pk,
            'position': pos.pk,
            'date': (timezone.now().date() + timezone.timedelta(days=7)).isoformat(),
            'status': ScheduleStatus.SCHEDULED,
            'notes': '',
        })
        assert response.status_code == 302
        assert VolunteerSchedule.objects.filter(member=member).exists()

    def test_schedule_allowed_if_no_checklist(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        member = MemberFactory()
        pos = VolunteerPositionFactory()

        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/schedule/create/', {
            'member': member.pk,
            'position': pos.pk,
            'date': (timezone.now().date() + timezone.timedelta(days=7)).isoformat(),
            'status': ScheduleStatus.SCHEDULED,
            'notes': '',
        })
        assert response.status_code == 302
        assert VolunteerSchedule.objects.filter(member=member).exists()

    def test_schedule_blocked_if_bg_check_expired(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        VolunteerBackgroundCheckFactory(
            member=member,
            status=BackgroundCheckStatus.EXPIRED,
            expiry_date=timezone.now().date() - timezone.timedelta(days=1),
        )

        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/schedule/create/', {
            'member': member.pk,
            'position': pos.pk,
            'date': (timezone.now().date() + timezone.timedelta(days=7)).isoformat(),
            'status': ScheduleStatus.SCHEDULED,
            'notes': '',
        })
        # Should show error about expired background check
        assert not VolunteerSchedule.objects.filter(member=member, position=pos).exists()
