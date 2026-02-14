"""Tests for volunteer recognition: milestones, leaderboard, notifications."""
import pytest
from decimal import Decimal
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles, MilestoneType
from apps.communication.models import Notification
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.volunteers.models import MilestoneAchievement, VolunteerHours
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory, VolunteerHoursFactory,
    MilestoneFactory, MilestoneAchievementFactory,
)
from apps.volunteers.services_recognition import RecognitionService

pytestmark = pytest.mark.django_db


class TestMilestoneModel:
    """Tests for Milestone model."""

    def test_str_returns_name_and_threshold(self):
        m = MilestoneFactory(name='100 heures', threshold=100)
        result = str(m)
        assert '100 heures' in result
        assert '100' in result

    def test_unique_type_threshold(self):
        MilestoneFactory(milestone_type=MilestoneType.HOURS, threshold=100)
        with pytest.raises(Exception):
            MilestoneFactory(milestone_type=MilestoneType.HOURS, threshold=100)


class TestMilestoneAchievementModel:
    """Tests for MilestoneAchievement model."""

    def test_str_contains_member_and_milestone(self):
        a = MilestoneAchievementFactory()
        result = str(a)
        assert a.member.full_name in result
        assert a.milestone.name in result

    def test_unique_member_milestone(self):
        member = MemberFactory()
        milestone = MilestoneFactory()
        MilestoneAchievementFactory(member=member, milestone=milestone)
        with pytest.raises(Exception):
            MilestoneAchievementFactory(member=member, milestone=milestone)


class TestCheckMilestones:
    """Tests for RecognitionService.check_milestones."""

    def test_no_milestones_available(self):
        member = MemberFactory()
        result = RecognitionService.check_milestones(member)
        assert result == []

    def test_hours_milestone_achieved(self):
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        MilestoneFactory(milestone_type=MilestoneType.HOURS, threshold=10)
        VolunteerHoursFactory(member=member, position=pos, hours_worked=Decimal('15.00'))
        result = RecognitionService.check_milestones(member)
        assert len(result) == 1
        assert result[0].member == member

    def test_hours_milestone_not_reached(self):
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        MilestoneFactory(milestone_type=MilestoneType.HOURS, threshold=100)
        VolunteerHoursFactory(member=member, position=pos, hours_worked=Decimal('5.00'))
        result = RecognitionService.check_milestones(member)
        assert len(result) == 0

    def test_already_achieved_milestone_skipped(self):
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        milestone = MilestoneFactory(milestone_type=MilestoneType.HOURS, threshold=10)
        VolunteerHoursFactory(member=member, position=pos, hours_worked=Decimal('15.00'))
        MilestoneAchievementFactory(member=member, milestone=milestone)
        result = RecognitionService.check_milestones(member)
        assert len(result) == 0


class TestTriggerNotification:
    """Tests for RecognitionService.trigger_notification."""

    def test_notification_created(self):
        achievement = MilestoneAchievementFactory(notified=False)
        RecognitionService.trigger_notification(achievement)
        assert Notification.objects.filter(member=achievement.member).exists()
        achievement.refresh_from_db()
        assert achievement.notified is True

    def test_notification_not_duplicated(self):
        achievement = MilestoneAchievementFactory(notified=True)
        RecognitionService.trigger_notification(achievement)
        assert Notification.objects.filter(member=achievement.member).count() == 0


class TestLeaderboard:
    """Tests for RecognitionService.get_leaderboard."""

    def test_empty_leaderboard(self):
        result = RecognitionService.get_leaderboard()
        assert result == []

    def test_leaderboard_ordering(self):
        pos = VolunteerPositionFactory()
        m1 = MemberFactory()
        m2 = MemberFactory()
        VolunteerHoursFactory(member=m1, position=pos, hours_worked=Decimal('10.00'))
        VolunteerHoursFactory(member=m2, position=pos, hours_worked=Decimal('20.00'))
        result = RecognitionService.get_leaderboard()
        assert len(result) == 2
        assert result[0]['total_hours'] > result[1]['total_hours']


class TestMilestonesViews:
    """Tests for recognition frontend views."""

    def test_milestones_page(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/milestones/')
        assert response.status_code == 200

    def test_volunteer_of_month(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/volunteer-of-month/')
        assert response.status_code == 200
