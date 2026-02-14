"""Automation service for drip campaigns and triggered sequences."""
import logging

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import AutomationStatus, AutomationStepChannel

logger = logging.getLogger(__name__)


class AutomationService:
    """
    Service for managing communication automations (drip campaigns).

    Handles enrolling members, advancing steps, and completing automations.
    """

    def trigger(self, trigger_type, member):
        """
        Enroll a member in all active automations matching the given trigger type.

        Args:
            trigger_type: AutomationTrigger value
            member: Member instance

        Returns:
            List of created AutomationEnrollment instances.
        """
        from .models import Automation, AutomationEnrollment

        automations = Automation.objects.filter(
            trigger_type=trigger_type, is_active=True,
        )

        enrollments = []
        for automation in automations:
            # Skip if already enrolled
            if AutomationEnrollment.objects.filter(
                automation=automation, member=member,
            ).exists():
                continue

            first_step = automation.steps.order_by('order').first()
            next_step_at = None
            if first_step:
                next_step_at = timezone.now() + timezone.timedelta(days=first_step.delay_days)

            enrollment = AutomationEnrollment.objects.create(
                automation=automation,
                member=member,
                current_step=0,
                status=AutomationStatus.ACTIVE,
                next_step_at=next_step_at,
            )
            enrollments.append(enrollment)
            logger.info(
                "Member %s enrolled in automation '%s'",
                member.pk, automation.name,
            )

        return enrollments

    def advance_step(self, enrollment):
        """
        Execute the current step and advance to the next one.

        Args:
            enrollment: AutomationEnrollment instance

        Returns:
            True if advanced, False if automation is complete or invalid.
        """
        from .models import AutomationStep

        if enrollment.status != AutomationStatus.ACTIVE:
            return False

        steps = list(enrollment.automation.steps.order_by('order'))
        if enrollment.current_step >= len(steps):
            self.complete(enrollment)
            return False

        step = steps[enrollment.current_step]
        self._execute_step(step, enrollment.member)

        # Move to next step
        next_index = enrollment.current_step + 1
        if next_index >= len(steps):
            self.complete(enrollment)
            return True

        next_step = steps[next_index]
        enrollment.current_step = next_index
        enrollment.next_step_at = timezone.now() + timezone.timedelta(days=next_step.delay_days)
        enrollment.save(update_fields=['current_step', 'next_step_at', 'updated_at'])

        logger.info(
            "Enrollment %s advanced to step %d",
            enrollment.pk, next_index,
        )
        return True

    def complete(self, enrollment):
        """Mark an enrollment as completed."""
        enrollment.status = AutomationStatus.COMPLETED
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=['status', 'completed_at', 'updated_at'])
        logger.info("Enrollment %s completed.", enrollment.pk)

    def cancel(self, enrollment):
        """Cancel an enrollment."""
        enrollment.status = AutomationStatus.CANCELLED
        enrollment.save(update_fields=['status', 'updated_at'])
        logger.info("Enrollment %s cancelled.", enrollment.pk)

    def process_pending_steps(self):
        """
        Process all enrollments whose next_step_at has passed.
        Intended to be called by a periodic Celery task.

        Returns:
            Number of steps processed.
        """
        from .models import AutomationEnrollment

        now = timezone.now()
        pending = AutomationEnrollment.objects.filter(
            status=AutomationStatus.ACTIVE,
            next_step_at__lte=now,
        ).select_related('automation', 'member')

        count = 0
        for enrollment in pending:
            if self.advance_step(enrollment):
                count += 1

        logger.info("Processed %d pending automation steps.", count)
        return count

    def _execute_step(self, step, member):
        """
        Execute a single automation step by sending through the appropriate channel.
        """
        channel = step.channel

        if channel == AutomationStepChannel.EMAIL:
            self._send_email(step, member)
        elif channel == AutomationStepChannel.SMS:
            self._send_sms(step, member)
        elif channel == AutomationStepChannel.PUSH:
            self._send_push(step, member)
        elif channel == AutomationStepChannel.IN_APP:
            self._send_in_app(step, member)
        else:
            logger.warning("Unknown channel '%s' for step %s", channel, step.pk)

    def _send_email(self, step, member):
        """Send an email for an automation step (stub)."""
        logger.info(
            "[AUTOMATION] Email to %s: %s", member.email, step.subject,
        )

    def _send_sms(self, step, member):
        """Send an SMS for an automation step."""
        from .models import SMSMessage
        from .services_sms import TwilioSMSService

        if not member.phone:
            logger.warning("No phone for member %s, skipping SMS step.", member.pk)
            return

        sms = SMSMessage.objects.create(
            recipient_member=member,
            phone_number=member.phone,
            body=step.body,
        )
        service = TwilioSMSService()
        service.send_sms(sms)

    def _send_push(self, step, member):
        """Send a push notification for an automation step."""
        from .services_push import WebPushService

        service = WebPushService()
        service.send_to_member(member, step.subject, step.body)

    def _send_in_app(self, step, member):
        """Create an in-app notification for an automation step."""
        from .models import Notification
        from apps.core.constants import NotificationType

        Notification.objects.create(
            member=member,
            title=step.subject,
            message=step.body,
            notification_type=NotificationType.GENERAL,
        )
