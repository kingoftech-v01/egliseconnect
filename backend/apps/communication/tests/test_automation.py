"""Tests for automation models, service, and views."""
import pytest
from datetime import timedelta

from django.utils import timezone

from apps.core.constants import (
    AutomationTrigger, AutomationStatus, AutomationStepChannel,
)
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.communication.models import (
    Automation, AutomationStep, AutomationEnrollment, Notification,
    SMSMessage,
)
from apps.communication.services_automation import AutomationService
from apps.communication.tests.factories import (
    AutomationFactory, AutomationStepFactory, AutomationEnrollmentFactory,
)

pytestmark = pytest.mark.django_db


# ─── Model Tests ─────────────────────────────────────────────────────────────────


class TestAutomationModel:
    def test_str(self):
        auto = AutomationFactory(name='Welcome Series')
        assert 'Welcome Series' in str(auto)

    def test_default_active(self):
        auto = AutomationFactory()
        assert auto.is_active is True

    def test_trigger_type(self):
        auto = AutomationFactory(trigger_type=AutomationTrigger.BIRTHDAY)
        assert auto.trigger_type == AutomationTrigger.BIRTHDAY


class TestAutomationStepModel:
    def test_str(self):
        auto = AutomationFactory(name='Test Auto')
        step = AutomationStepFactory(automation=auto, order=0)
        assert 'Test Auto' in str(step)

    def test_ordering(self):
        auto = AutomationFactory()
        s2 = AutomationStepFactory(automation=auto, order=2)
        s0 = AutomationStepFactory(automation=auto, order=0)
        s1 = AutomationStepFactory(automation=auto, order=1)
        steps = list(auto.steps.order_by('order'))
        assert steps[0].order == 0
        assert steps[1].order == 1
        assert steps[2].order == 2


class TestAutomationEnrollmentModel:
    def test_str(self):
        enrollment = AutomationEnrollmentFactory()
        assert str(enrollment.member) in str(enrollment)

    def test_default_active(self):
        enrollment = AutomationEnrollmentFactory()
        assert enrollment.status == AutomationStatus.ACTIVE

    def test_unique_together(self):
        auto = AutomationFactory()
        member = MemberFactory()
        AutomationEnrollmentFactory(automation=auto, member=member)
        with pytest.raises(Exception):
            AutomationEnrollmentFactory(automation=auto, member=member)


# ─── Service Tests ───────────────────────────────────────────────────────────────


class TestAutomationService:
    def test_trigger_enrolls_member(self):
        auto = AutomationFactory(trigger_type=AutomationTrigger.MEMBER_CREATED)
        AutomationStepFactory(automation=auto, order=0, delay_days=0)
        member = MemberFactory()

        service = AutomationService()
        enrollments = service.trigger(AutomationTrigger.MEMBER_CREATED, member)

        assert len(enrollments) == 1
        assert enrollments[0].member == member
        assert enrollments[0].automation == auto

    def test_trigger_skips_already_enrolled(self):
        auto = AutomationFactory(trigger_type=AutomationTrigger.MEMBER_CREATED)
        AutomationStepFactory(automation=auto, order=0)
        member = MemberFactory()
        AutomationEnrollmentFactory(automation=auto, member=member)

        service = AutomationService()
        enrollments = service.trigger(AutomationTrigger.MEMBER_CREATED, member)
        assert len(enrollments) == 0

    def test_trigger_skips_inactive_automations(self):
        AutomationFactory(
            trigger_type=AutomationTrigger.BIRTHDAY,
            is_active=False,
        )
        member = MemberFactory()

        service = AutomationService()
        enrollments = service.trigger(AutomationTrigger.BIRTHDAY, member)
        assert len(enrollments) == 0

    def test_advance_step_email(self):
        auto = AutomationFactory()
        AutomationStepFactory(automation=auto, order=0, channel=AutomationStepChannel.EMAIL)
        AutomationStepFactory(automation=auto, order=1, channel=AutomationStepChannel.EMAIL)
        enrollment = AutomationEnrollmentFactory(automation=auto, current_step=0)

        service = AutomationService()
        result = service.advance_step(enrollment)

        assert result is True
        enrollment.refresh_from_db()
        assert enrollment.current_step == 1

    def test_advance_step_in_app_creates_notification(self):
        auto = AutomationFactory()
        AutomationStepFactory(
            automation=auto, order=0,
            channel=AutomationStepChannel.IN_APP,
            subject='Test Notification',
            body='Test body',
        )
        member = MemberFactory()
        enrollment = AutomationEnrollmentFactory(
            automation=auto, member=member, current_step=0,
        )

        service = AutomationService()
        service.advance_step(enrollment)

        assert Notification.objects.filter(member=member, title='Test Notification').exists()

    def test_advance_step_sms_creates_sms(self):
        auto = AutomationFactory()
        AutomationStepFactory(
            automation=auto, order=0,
            channel=AutomationStepChannel.SMS,
            body='SMS body text',
        )
        member = MemberFactory(phone='+15551234567')
        enrollment = AutomationEnrollmentFactory(
            automation=auto, member=member, current_step=0,
        )

        service = AutomationService()
        service.advance_step(enrollment)

        assert SMSMessage.objects.filter(recipient_member=member).exists()

    def test_advance_last_step_completes(self):
        auto = AutomationFactory()
        AutomationStepFactory(automation=auto, order=0)
        enrollment = AutomationEnrollmentFactory(automation=auto, current_step=0)

        service = AutomationService()
        result = service.advance_step(enrollment)

        assert result is True
        enrollment.refresh_from_db()
        assert enrollment.status == AutomationStatus.COMPLETED
        assert enrollment.completed_at is not None

    def test_complete(self):
        enrollment = AutomationEnrollmentFactory()
        service = AutomationService()
        service.complete(enrollment)
        enrollment.refresh_from_db()
        assert enrollment.status == AutomationStatus.COMPLETED

    def test_cancel(self):
        enrollment = AutomationEnrollmentFactory()
        service = AutomationService()
        service.cancel(enrollment)
        enrollment.refresh_from_db()
        assert enrollment.status == AutomationStatus.CANCELLED

    def test_process_pending_steps(self):
        auto = AutomationFactory()
        AutomationStepFactory(automation=auto, order=0, delay_days=0)
        enrollment = AutomationEnrollmentFactory(
            automation=auto,
            current_step=0,
            next_step_at=timezone.now() - timedelta(hours=1),
        )

        service = AutomationService()
        count = service.process_pending_steps()
        assert count >= 1

    def test_advance_step_already_completed(self):
        enrollment = AutomationEnrollmentFactory(status=AutomationStatus.COMPLETED)
        service = AutomationService()
        result = service.advance_step(enrollment)
        assert result is False


# ─── Frontend View Tests ─────────────────────────────────────────────────────────


class TestAutomationFrontendViews:
    def test_automation_list_staff_only(self, client):
        """Non-staff redirected."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/automations/')
        assert resp.status_code == 302

    def test_automation_list_accessible(self, client):
        """Staff can access automation list."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/automations/')
        assert resp.status_code == 200

    def test_automation_create_get(self, client):
        """Staff can access create form."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/automations/create/')
        assert resp.status_code == 200

    def test_automation_create_post(self, client):
        """Staff can create an automation."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.post('/communication/automations/create/', {
            'name': 'Test Automation',
            'trigger_type': AutomationTrigger.MEMBER_CREATED,
            'is_active': True,
        })
        assert resp.status_code == 302
        assert Automation.objects.filter(name='Test Automation').exists()

    def test_automation_detail(self, client):
        """Staff can view automation detail."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        auto = AutomationFactory()
        resp = client.get(f'/communication/automations/{auto.pk}/')
        assert resp.status_code == 200

    def test_automation_step_add(self, client):
        """Staff can add a step to an automation."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)
        auto = AutomationFactory()
        resp = client.post(f'/communication/automations/{auto.pk}/steps/add/', {
            'order': 0,
            'delay_days': 1,
            'subject': 'Welcome',
            'body': 'Welcome body',
            'channel': AutomationStepChannel.EMAIL,
        })
        assert resp.status_code == 302
        assert auto.steps.count() == 1
