"""Twilio SMS service for sending and tracking SMS messages."""
import logging

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import SMSStatus

logger = logging.getLogger(__name__)


class TwilioSMSService:
    """
    Service for sending SMS via Twilio.

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER
    in Django settings.  When Twilio credentials are not configured the service
    operates in *stub mode* -- it logs the message and marks it as sent without
    actually calling the Twilio API.
    """

    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        self._client = None

    @property
    def client(self):
        """Lazy-load the Twilio REST client."""
        if self._client is None and self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.warning("twilio package not installed -- running in stub mode.")
        return self._client

    @property
    def is_configured(self):
        return bool(self.account_sid and self.auth_token and self.from_number)

    # ── public API ───────────────────────────────────────────────────────────

    def send_sms(self, sms_message):
        """
        Send a single SMSMessage instance.

        Updates the model in-place with status and twilio_sid.
        Returns the updated SMSMessage.
        """
        from .models import SMSOptOut

        # Check opt-out
        if SMSOptOut.objects.filter(phone_number=sms_message.phone_number).exists():
            sms_message.status = SMSStatus.FAILED
            sms_message.save(update_fields=['status', 'updated_at'])
            logger.info("SMS to %s skipped -- opted out.", sms_message.phone_number)
            return sms_message

        if not self.is_configured or self.client is None:
            # Stub mode
            logger.info(
                "[STUB] SMS to %s: %s",
                sms_message.phone_number,
                sms_message.body[:80],
            )
            sms_message.status = SMSStatus.SENT
            sms_message.sent_at = timezone.now()
            sms_message.twilio_sid = 'STUB_SID'
            sms_message.save(update_fields=['status', 'sent_at', 'twilio_sid', 'updated_at'])
            return sms_message

        try:
            message = self.client.messages.create(
                body=sms_message.body,
                from_=self.from_number,
                to=sms_message.phone_number,
            )
            sms_message.twilio_sid = message.sid
            sms_message.status = SMSStatus.SENT
            sms_message.sent_at = timezone.now()
            sms_message.save(update_fields=['status', 'sent_at', 'twilio_sid', 'updated_at'])
            logger.info("SMS sent to %s (SID: %s)", sms_message.phone_number, message.sid)
        except Exception as exc:
            sms_message.status = SMSStatus.FAILED
            sms_message.save(update_fields=['status', 'updated_at'])
            logger.error("SMS send failed to %s: %s", sms_message.phone_number, exc)

        return sms_message

    def bulk_send(self, sms_messages):
        """Send a list of SMSMessage instances. Returns list of updated instances."""
        results = []
        for msg in sms_messages:
            results.append(self.send_sms(msg))
        return results

    def track_delivery(self, sms_message):
        """
        Query Twilio for the delivery status of a sent message.
        Updates the model status accordingly.
        """
        if not sms_message.twilio_sid:
            return sms_message

        if sms_message.twilio_sid == 'STUB_SID':
            sms_message.status = SMSStatus.DELIVERED
            sms_message.save(update_fields=['status', 'updated_at'])
            return sms_message

        if not self.is_configured or self.client is None:
            return sms_message

        try:
            msg = self.client.messages(sms_message.twilio_sid).fetch()
            status_map = {
                'delivered': SMSStatus.DELIVERED,
                'sent': SMSStatus.SENT,
                'failed': SMSStatus.FAILED,
                'undelivered': SMSStatus.UNDELIVERED,
            }
            sms_message.status = status_map.get(msg.status, SMSStatus.SENT)
            sms_message.save(update_fields=['status', 'updated_at'])
        except Exception as exc:
            logger.error("Delivery tracking failed for SID %s: %s", sms_message.twilio_sid, exc)

        return sms_message

    def render_template(self, template, context=None):
        """
        Render an SMSTemplate body with context variables.

        Args:
            template: SMSTemplate instance
            context: dict of merge fields (e.g. {'member_name': 'Jean'})

        Returns:
            Rendered body string.
        """
        body = template.body_template
        if context:
            for key, value in context.items():
                body = body.replace('{{' + key + '}}', str(value))
        return body
