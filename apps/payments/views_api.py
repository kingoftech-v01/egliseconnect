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

from apps.core.permissions import IsPastorOrAdmin
from .models import OnlinePayment, RecurringDonation
from .serializers import (
    OnlinePaymentSerializer,
    RecurringDonationSerializer,
    CreatePaymentIntentSerializer,
    CreateRecurringSerializer,
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

        payment, client_secret = PaymentService.create_payment_intent(
            member=member,
            amount=serializer.validated_data['amount'],
            donation_type=serializer.validated_data['donation_type'],
            campaign=campaign,
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
