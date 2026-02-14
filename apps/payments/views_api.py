"""API views for payments."""
import json
import logging

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsPastorOrAdmin, IsFinanceStaff, IsMember
from .models import (
    OnlinePayment,
    RecurringDonation,
    GivingStatement,
    GivingGoal,
    SMSDonation,
    PaymentPlan,
    EmployerMatch,
    GivingCampaign,
    KioskSession,
)
from .serializers import (
    OnlinePaymentSerializer,
    RecurringDonationSerializer,
    CreatePaymentIntentSerializer,
    CreateRecurringSerializer,
    UpdateRecurringSerializer,
    GivingStatementSerializer,
    GivingGoalSerializer,
    SMSDonationSerializer,
    PaymentPlanSerializer,
    CreatePaymentPlanSerializer,
    EmployerMatchSerializer,
    GivingCampaignSerializer,
    KioskSessionSerializer,
    CryptoChargeSerializer,
    SMSWebhookSerializer,
)
from .services import PaymentService, get_stripe

logger = logging.getLogger(__name__)


class OnlinePaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """View payment history."""
    serializer_class = OnlinePaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in ['admin', 'pastor', 'treasurer']:
                return OnlinePayment.objects.filter(is_active=True)
            return OnlinePayment.objects.filter(
                member=user.member_profile, is_active=True
            )
        return OnlinePayment.objects.none()

    @action(detail=False, methods=['post'])
    def create_intent(self, request):
        """Create a new payment intent."""
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = request.user.member_profile
        campaign = None
        campaign_id = serializer.validated_data.get('campaign_id')
        if campaign_id:
            from apps.donations.models import DonationCampaign
            campaign = DonationCampaign.objects.filter(pk=campaign_id).first()

        currency = serializer.validated_data.get('currency', 'CAD')

        payment, client_secret = PaymentService.create_payment_intent(
            member=member,
            amount=serializer.validated_data['amount'],
            donation_type=serializer.validated_data['donation_type'],
            campaign=campaign,
            currency=currency,
        )

        return Response({
            'payment_id': str(payment.pk),
            'client_secret': client_secret,
            'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsPastorOrAdmin])
    def refund(self, request, pk=None):
        """Refund a payment (admin only)."""
        payment = self.get_object()
        try:
            PaymentService.refund_payment(payment)
            return Response({'status': 'refunded'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringDonationViewSet(viewsets.ReadOnlyModelViewSet):
    """Manage recurring donations."""
    serializer_class = RecurringDonationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in ['admin', 'pastor', 'treasurer']:
                return RecurringDonation.objects.filter(is_active=True)
            return RecurringDonation.objects.filter(
                member=user.member_profile, is_active=True
            )
        return RecurringDonation.objects.none()

    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        """Create a new recurring donation."""
        serializer = CreateRecurringSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = request.user.member_profile
        recurring = PaymentService.create_recurring_donation(
            member=member,
            amount=serializer.validated_data['amount'],
            frequency=serializer.validated_data['frequency'],
            donation_type=serializer.validated_data['donation_type'],
        )

        return Response(RecurringDonationSerializer(recurring).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a recurring donation."""
        recurring = self.get_object()
        if recurring.member != request.user.member_profile:
            return Response(
                {'error': 'Vous ne pouvez annuler que vos propres dons.'},
                status=status.HTTP_403_FORBIDDEN
            )
        PaymentService.cancel_recurring_donation(recurring)
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['post'])
    def update_subscription(self, request, pk=None):
        """Update amount/frequency for a recurring donation."""
        recurring = self.get_object()
        if recurring.member != request.user.member_profile:
            return Response(
                {'error': 'Vous ne pouvez modifier que vos propres dons.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UpdateRecurringSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PaymentService.update_recurring_donation(
            recurring,
            new_amount=serializer.validated_data['amount'],
            new_frequency=serializer.validated_data['frequency'],
        )

        return Response(RecurringDonationSerializer(recurring).data)


class GivingStatementViewSet(viewsets.ReadOnlyModelViewSet):
    """View giving statements."""
    serializer_class = GivingStatementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in ['admin', 'pastor', 'treasurer']:
                return GivingStatement.objects.filter(is_active=True)
            return GivingStatement.objects.filter(
                member=user.member_profile, is_active=True
            )
        return GivingStatement.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsFinanceStaff])
    def send_email(self, request, pk=None):
        """Send statement email to member."""
        statement = self.get_object()
        from .tasks import send_statement_email
        send_statement_email.delay(str(statement.pk))
        return Response({'status': 'email_queued'})


class GivingGoalViewSet(viewsets.ModelViewSet):
    """Manage giving goals."""
    serializer_class = GivingGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            return GivingGoal.objects.filter(
                member=user.member_profile, is_active=True
            )
        return GivingGoal.objects.none()

    def perform_create(self, serializer):
        serializer.save(member=self.request.user.member_profile)

    @action(detail=False, methods=['get'])
    def progress(self, request):
        """Get current year giving goal progress."""
        from django.utils import timezone
        member = request.user.member_profile
        current_year = timezone.now().year
        progress = PaymentService.calculate_giving_goal_progress(member, current_year)
        if progress is None:
            return Response({'message': 'No goal set for this year'}, status=status.HTTP_404_NOT_FOUND)
        return Response(progress)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsFinanceStaff])
    def summary(self, request):
        """Finance staff: total pledged vs received."""
        summary = PaymentService.get_giving_goal_summary()
        return Response(summary)


class SMSDonationViewSet(viewsets.ReadOnlyModelViewSet):
    """View SMS donations (admin only)."""
    serializer_class = SMSDonationSerializer
    permission_classes = [IsAuthenticated, IsFinanceStaff]

    def get_queryset(self):
        return SMSDonation.objects.filter(is_active=True)


class PaymentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """View and manage payment plans."""
    serializer_class = PaymentPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in ['admin', 'pastor', 'treasurer']:
                return PaymentPlan.objects.filter(is_active=True)
            return PaymentPlan.objects.filter(
                member=user.member_profile, is_active=True
            )
        return PaymentPlan.objects.none()

    @action(detail=False, methods=['post'])
    def create_plan(self, request):
        """Create a new payment plan."""
        serializer = CreatePaymentPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = request.user.member_profile
        plan = PaymentService.create_payment_plan(
            member=member,
            total_amount=serializer.validated_data['total_amount'],
            installment_amount=serializer.validated_data['installment_amount'],
            frequency=serializer.validated_data['frequency'],
            start_date=serializer.validated_data['start_date'],
            donation_type=serializer.validated_data['donation_type'],
        )

        return Response(PaymentPlanSerializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def complete_early(self, request, pk=None):
        """Complete a payment plan early."""
        plan = self.get_object()
        if plan.member != request.user.member_profile:
            return Response(
                {'error': 'Vous ne pouvez modifier que vos propres plans.'},
                status=status.HTTP_403_FORBIDDEN
            )
        PaymentService.complete_plan_early(plan)
        return Response(PaymentPlanSerializer(plan).data)


class EmployerMatchViewSet(viewsets.ModelViewSet):
    """Manage employer matching."""
    serializer_class = EmployerMatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            if user.member_profile.role in ['admin', 'pastor', 'treasurer']:
                return EmployerMatch.objects.filter(is_active=True)
            return EmployerMatch.objects.filter(
                member=user.member_profile, is_active=True
            )
        return EmployerMatch.objects.none()

    def perform_create(self, serializer):
        serializer.save(member=self.request.user.member_profile)


class GivingCampaignViewSet(viewsets.ReadOnlyModelViewSet):
    """View giving campaigns."""
    serializer_class = GivingCampaignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GivingCampaign.objects.filter(is_active=True)


class KioskSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """View kiosk sessions (admin only)."""
    serializer_class = KioskSessionSerializer
    permission_classes = [IsAuthenticated, IsFinanceStaff]

    def get_queryset(self):
        return KioskSession.objects.filter(is_active=True)

    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Mark kiosk session as reconciled."""
        session = self.get_object()
        PaymentService.reconcile_kiosk_session(session)
        return Response(KioskSessionSerializer(session).data)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Receives Stripe webhook events."""

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

        stripe = get_stripe()

        if stripe and webhook_secret:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except (ValueError, Exception) as e:
                logger.error(f'Stripe webhook error: {e}')
                return HttpResponse(status=400)
        else:
            # Development mode - parse JSON directly
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                return HttpResponse(status=400)

        event_type = event.get('type', '')

        if event_type == 'payment_intent.succeeded':
            data = event.get('data', {}).get('object', {})
            PaymentService.handle_payment_succeeded(
                payment_intent_id=data.get('id', ''),
                receipt_url=data.get('charges', {}).get('data', [{}])[0].get('receipt_url', '') if data.get('charges') else '',
            )

        elif event_type == 'payment_intent.payment_failed':
            data = event.get('data', {}).get('object', {})
            failure = data.get('last_payment_error', {})
            PaymentService.handle_payment_failed(
                payment_intent_id=data.get('id', ''),
                failure_reason=failure.get('message', ''),
            )

        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name='dispatch')
class TwilioSMSWebhookView(View):
    """Receives Twilio SMS webhook for text-to-give."""

    def post(self, request):
        phone_number = request.POST.get('From', '')
        body = request.POST.get('Body', '')

        if not phone_number or not body:
            return HttpResponse(status=400)

        sms_donation, reply_message = PaymentService.process_sms_donation(
            phone_number=phone_number,
            message_text=body,
        )

        # Return TwiML response
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_message}</Message>
</Response>'''
        return HttpResponse(twiml, content_type='text/xml')


class CryptoChargeView(View):
    """Create a Coinbase Commerce charge for crypto donation."""

    def post(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'member_profile'):
            return HttpResponse(status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        amount = data.get('amount')
        currency = data.get('currency', 'CAD')

        if not amount:
            return HttpResponse(status=400)

        member = request.user.member_profile
        charge = PaymentService.create_crypto_charge(member, amount, currency)

        if charge:
            import json as json_module
            return HttpResponse(
                json_module.dumps(charge),
                content_type='application/json',
            )
        return HttpResponse(status=500)
