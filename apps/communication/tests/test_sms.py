"""Tests for SMS models, service, and views."""
import pytest
from unittest.mock import patch, MagicMock

from django.test import RequestFactory
from django.utils import timezone

from apps.core.constants import SMSStatus
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory, PastorFactory
from apps.communication.models import SMSMessage, SMSTemplate, SMSOptOut
from apps.communication.services_sms import TwilioSMSService
from apps.communication.tests.factories import (
    SMSMessageFactory, SMSTemplateFactory, SMSOptOutFactory,
)

pytestmark = pytest.mark.django_db


# ─── Model Tests ─────────────────────────────────────────────────────────────────


class TestSMSMessageModel:
    def test_str(self):
        sms = SMSMessageFactory(phone_number='+15551234567', status=SMSStatus.PENDING)
        assert '+15551234567' in str(sms)

    def test_default_status_is_pending(self):
        sms = SMSMessageFactory()
        assert sms.status == SMSStatus.PENDING

    def test_has_uuid_pk(self):
        sms = SMSMessageFactory()
        assert sms.pk is not None

    def test_recipient_member_optional(self):
        sms = SMSMessageFactory(recipient_member=None)
        assert sms.recipient_member is None

    def test_template_fk(self):
        template = SMSTemplateFactory()
        sms = SMSMessageFactory(template=template)
        assert sms.template == template


class TestSMSTemplateModel:
    def test_str(self):
        tpl = SMSTemplateFactory(name='Bienvenue')
        assert str(tpl) == 'Bienvenue'

    def test_default_active(self):
        tpl = SMSTemplateFactory()
        assert tpl.is_active is True


class TestSMSOptOutModel:
    def test_str(self):
        optout = SMSOptOutFactory(phone_number='+15559999999')
        assert '+15559999999' in str(optout)


# ─── Service Tests ───────────────────────────────────────────────────────────────


class TestTwilioSMSService:
    def test_stub_mode_sends_successfully(self):
        """When Twilio is not configured, service runs in stub mode."""
        sms = SMSMessageFactory()
        service = TwilioSMSService()
        result = service.send_sms(sms)
        assert result.status == SMSStatus.SENT
        assert result.twilio_sid == 'STUB_SID'
        assert result.sent_at is not None

    def test_opt_out_prevents_send(self):
        """SMS to an opted-out number should fail."""
        sms = SMSMessageFactory(phone_number='+15550001234')
        SMSOptOutFactory(phone_number='+15550001234')
        service = TwilioSMSService()
        result = service.send_sms(sms)
        assert result.status == SMSStatus.FAILED

    def test_bulk_send(self):
        """Bulk send returns list of processed messages."""
        msgs = [SMSMessageFactory() for _ in range(3)]
        service = TwilioSMSService()
        results = service.bulk_send(msgs)
        assert len(results) == 3
        assert all(r.status == SMSStatus.SENT for r in results)

    def test_track_delivery_stub(self):
        """Track delivery in stub mode marks as delivered."""
        sms = SMSMessageFactory(twilio_sid='STUB_SID', status=SMSStatus.SENT)
        service = TwilioSMSService()
        result = service.track_delivery(sms)
        assert result.status == SMSStatus.DELIVERED

    def test_track_delivery_no_sid(self):
        """Track delivery with no SID returns unchanged."""
        sms = SMSMessageFactory(twilio_sid='', status=SMSStatus.PENDING)
        service = TwilioSMSService()
        result = service.track_delivery(sms)
        assert result.status == SMSStatus.PENDING

    def test_render_template(self):
        """Template rendering replaces merge fields."""
        tpl = SMSTemplateFactory(body_template='Bonjour {{member_name}}, rappel: {{event_title}}')
        service = TwilioSMSService()
        result = service.render_template(tpl, {
            'member_name': 'Jean',
            'event_title': 'Culte',
        })
        assert 'Jean' in result
        assert 'Culte' in result

    def test_render_template_no_context(self):
        """Template rendering without context returns raw template."""
        tpl = SMSTemplateFactory(body_template='Hello {{member_name}}')
        service = TwilioSMSService()
        result = service.render_template(tpl)
        assert '{{member_name}}' in result

    def test_is_configured_false_by_default(self):
        service = TwilioSMSService()
        assert service.is_configured is False


# ─── Frontend View Tests ─────────────────────────────────────────────────────────


class TestSMSFrontendViews:
    def test_sms_list_staff_only(self, client):
        """Non-staff users are redirected."""
        member = MemberWithUserFactory()
        client.force_login(member.user)
        resp = client.get('/communication/sms/')
        assert resp.status_code == 302

    def test_sms_list_accessible_to_staff(self, client):
        """Staff can access SMS list."""
        pastor = PastorFactory()
        user = MemberWithUserFactory(role=pastor.role).user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/sms/')
        assert resp.status_code == 200

    def test_sms_compose_get(self, client):
        """Staff can access SMS compose form."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/sms/compose/')
        assert resp.status_code == 200

    def test_sms_template_list(self, client):
        """Staff can access SMS template list."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/sms/templates/')
        assert resp.status_code == 200

    def test_sms_template_create_get(self, client):
        """Staff can access SMS template create form."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/sms/templates/create/')
        assert resp.status_code == 200

    def test_sms_template_create_post(self, client):
        """Staff can create an SMS template."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.post('/communication/sms/templates/create/', {
            'name': 'Test Template',
            'body_template': 'Hello {{member_name}}',
            'is_active': True,
        })
        assert resp.status_code == 302
        assert SMSTemplate.objects.filter(name='Test Template').exists()

    def test_sms_template_edit(self, client):
        """Staff can edit an SMS template."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        tpl = SMSTemplateFactory(name='Old Name')
        resp = client.post(f'/communication/sms/templates/{tpl.pk}/edit/', {
            'name': 'New Name',
            'body_template': 'Updated body',
            'is_active': True,
        })
        assert resp.status_code == 302
        tpl.refresh_from_db()
        assert tpl.name == 'New Name'
