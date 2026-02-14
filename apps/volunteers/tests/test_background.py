"""Tests for background check: model, views, tasks."""
import pytest
from django.test import Client
from django.utils import timezone
from datetime import timedelta

from apps.core.constants import Roles, BackgroundCheckStatus
from apps.communication.models import Notification
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.volunteers.models import VolunteerBackgroundCheck
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory, VolunteerBackgroundCheckFactory,
)
from apps.volunteers.tasks import check_background_check_expiry

pytestmark = pytest.mark.django_db


class TestVolunteerBackgroundCheckModel:
    """Tests for VolunteerBackgroundCheck model."""

    def test_str_contains_member_and_status(self):
        check = VolunteerBackgroundCheckFactory(status=BackgroundCheckStatus.PENDING)
        result = str(check)
        assert check.member.full_name in result

    def test_is_expired_past_date(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() - timedelta(days=1),
        )
        assert check.is_expired is True

    def test_is_expired_future_date(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() + timedelta(days=30),
        )
        assert check.is_expired is False

    def test_is_expired_no_expiry(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=None,
        )
        assert check.is_expired is False

    def test_is_valid_approved_not_expired(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() + timedelta(days=30),
        )
        assert check.is_valid is True

    def test_is_valid_pending(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.PENDING,
        )
        assert check.is_valid is False

    def test_is_valid_expired(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() - timedelta(days=1),
        )
        assert check.is_valid is False


class TestBackgroundCheckViews:
    """Tests for background check frontend views."""

    def test_list_requires_staff(self):
        user = MemberWithUserFactory(role=Roles.MEMBER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/background-checks/')
        assert response.status_code == 302

    def test_list_accessible_by_staff(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/background-checks/')
        assert response.status_code == 200

    def test_create_form(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/background-checks/create/')
        assert response.status_code == 200

    def test_create_background_check(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        member = MemberFactory()
        position = VolunteerPositionFactory()
        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/background-checks/create/', {
            'member': member.pk,
            'position': position.pk,
            'status': BackgroundCheckStatus.PENDING,
            'check_date': timezone.now().date().isoformat(),
            'expiry_date': (timezone.now().date() + timedelta(days=365)).isoformat(),
            'notes': 'Test check',
        })
        assert response.status_code == 302
        assert VolunteerBackgroundCheck.objects.filter(member=member).exists()

    def test_update_form(self):
        user = MemberWithUserFactory(role=Roles.ADMIN).user
        check = VolunteerBackgroundCheckFactory()
        client = Client()
        client.force_login(user)
        response = client.get(f'/volunteers/background-checks/{check.pk}/edit/')
        assert response.status_code == 200


class TestBackgroundCheckExpiryTask:
    """Tests for check_background_check_expiry task."""

    def test_auto_expire_past_due(self):
        check = VolunteerBackgroundCheckFactory(
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() - timedelta(days=1),
        )
        result = check_background_check_expiry()
        assert result >= 1
        check.refresh_from_db()
        assert check.status == BackgroundCheckStatus.EXPIRED
        assert Notification.objects.filter(member=check.member).exists()

    def test_alert_expiring_soon(self):
        member = MemberFactory()
        VolunteerBackgroundCheckFactory(
            member=member,
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() + timedelta(days=15),
        )
        result = check_background_check_expiry()
        assert result >= 1
        assert Notification.objects.filter(member=member).exists()

    def test_no_alerts_for_far_future(self):
        member = MemberFactory()
        VolunteerBackgroundCheckFactory(
            member=member,
            status=BackgroundCheckStatus.APPROVED,
            expiry_date=timezone.now().date() + timedelta(days=60),
        )
        result = check_background_check_expiry()
        # Only the expiring_soon query should not match
        assert Notification.objects.filter(member=member).count() == 0
