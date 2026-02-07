"""Tests for volunteers model __str__ methods."""
import pytest
from django.utils import timezone

from apps.volunteers.models import VolunteerPosition, VolunteerSchedule
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory,
    VolunteerScheduleFactory,
)

pytestmark = pytest.mark.django_db


class TestVolunteerPositionStr:
    """Tests for VolunteerPosition.__str__."""

    def test_str_returns_name(self):
        position = VolunteerPositionFactory(name='Pianist')
        assert str(position) == 'Pianist'

    def test_str_with_different_name(self):
        position = VolunteerPositionFactory(name='Sound Technician')
        assert str(position) == 'Sound Technician'


class TestVolunteerScheduleStr:
    """Tests for VolunteerSchedule.__str__."""

    def test_str_returns_member_position_date(self):
        today = timezone.now().date()
        schedule = VolunteerScheduleFactory(date=today)
        expected = f'{schedule.member.full_name} - {schedule.position.name} ({today})'
        assert str(schedule) == expected

    def test_str_format(self):
        schedule = VolunteerScheduleFactory()
        result = str(schedule)
        assert schedule.member.full_name in result
        assert schedule.position.name in result
        assert str(schedule.date) in result
