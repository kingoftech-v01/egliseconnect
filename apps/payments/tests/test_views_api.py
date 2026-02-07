"""Tests for payment API views: OnlinePaymentViewSet, RecurringDonationViewSet, StripeWebhookView."""
import json
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import Client, override_settings
from rest_framework.test import APIClient

from apps.core.constants import Roles
from apps.payments.models import OnlinePayment, RecurringDonation, PaymentStatus
from apps.members.tests.factories import MemberFactory, UserFactory
from apps.payments.tests.factories import (
    OnlinePaymentFactory,
    SucceededPaymentFactory,
    FailedPaymentFactory,
    RecurringDonationFactory,
)


@pytest.mark.django_db
class TestOnlinePaymentViewSetList:
    """Tests for OnlinePaymentViewSet list endpoint."""

    def _api_url(self):
        return '/api/v1/payments/payments/'

    def test_unauthenticated_returns_403(self):
        client = APIClient()
        response = client.get(self._api_url())
        assert response.status_code == 403

    def test_regular_member_sees_own_payments(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        own_payment = OnlinePaymentFactory(member=member)
        other_payment = OnlinePaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        ids = [str(p['id']) for p in response.data['results']]
        assert str(own_payment.pk) in ids
        assert str(other_payment.pk) not in ids

    def test_admin_sees_all_payments(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        p1 = OnlinePaymentFactory()
        p2 = OnlinePaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        ids = [str(p['id']) for p in response.data['results']]
        assert str(p1.pk) in ids
        assert str(p2.pk) in ids

    def test_pastor_sees_all_payments(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.PASTOR, registration_date=None)

        OnlinePaymentFactory()
        OnlinePaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        assert len(response.data['results']) == 2

    def test_treasurer_sees_all_payments(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.TREASURER, registration_date=None)

        OnlinePaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_user_without_member_sees_none(self):
        user = UserFactory()

        OnlinePaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        assert len(response.data['results']) == 0

    def test_soft_deleted_payments_excluded(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        payment = OnlinePaymentFactory()
        payment.is_active = False
        payment.save()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestOnlinePaymentCreateIntent:
    """Tests for OnlinePaymentViewSet create_intent action."""

    def _api_url(self):
        return '/api/v1/payments/payments/create_intent/'

    def test_creates_intent_successfully(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(), {
                'amount': '50.00',
                'donation_type': 'offering',
            })

        assert response.status_code == 200
        assert 'payment_id' in response.data
        assert 'client_secret' in response.data
        assert 'stripe_public_key' in response.data

    def test_creates_intent_with_campaign(self):
        from apps.donations.models import DonationCampaign
        from django.utils import timezone

        user = UserFactory()
        MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)
        campaign = DonationCampaign.objects.create(
            name='Building Fund',
            goal_amount=Decimal('10000.00'),
            start_date=timezone.now().date(),
        )

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(), {
                'amount': '100.00',
                'donation_type': 'campaign',
                'campaign_id': str(campaign.pk),
            })

        assert response.status_code == 200
        payment = OnlinePayment.objects.get(pk=response.data['payment_id'])
        assert payment.campaign == campaign

    def test_invalid_amount_rejected(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self._api_url(), {
            'amount': '0.00',
            'donation_type': 'offering',
        })
        assert response.status_code == 400

    def test_missing_amount_rejected(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self._api_url(), {
            'donation_type': 'offering',
        })
        assert response.status_code == 400

    def test_unauthenticated_returns_403(self):
        client = APIClient()
        response = client.post(self._api_url(), {
            'amount': '50.00',
            'donation_type': 'offering',
        })
        assert response.status_code == 403

    def test_nonexistent_campaign_ignored(self):
        import uuid
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(), {
                'amount': '50.00',
                'donation_type': 'offering',
                'campaign_id': str(uuid.uuid4()),
            })

        assert response.status_code == 200
        payment = OnlinePayment.objects.get(pk=response.data['payment_id'])
        assert payment.campaign is None


@pytest.mark.django_db
class TestOnlinePaymentRefund:
    """Tests for OnlinePaymentViewSet refund action."""

    def _api_url(self, pk):
        return f'/api/v1/payments/payments/{pk}/refund/'

    def test_admin_can_refund_succeeded_payment(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)
        payment = SucceededPaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(payment.pk))

        assert response.status_code == 200
        assert response.data['status'] == 'refunded'
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.REFUNDED

    def test_pastor_can_refund(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.PASTOR, registration_date=None)
        payment = SucceededPaymentFactory()

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(payment.pk))

        assert response.status_code == 200

    def test_regular_member_cannot_refund(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)
        payment = SucceededPaymentFactory(member=member)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self._api_url(payment.pk))
        assert response.status_code == 403

    def test_refund_pending_returns_400(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self._api_url(payment.pk))
        assert response.status_code == 400
        assert 'error' in response.data

    def test_unauthenticated_returns_403(self):
        payment = SucceededPaymentFactory()
        client = APIClient()
        response = client.post(self._api_url(payment.pk))
        assert response.status_code == 403


@pytest.mark.django_db
class TestRecurringDonationViewSetList:
    """Tests for RecurringDonationViewSet list endpoint."""

    def _api_url(self):
        return '/api/v1/payments/recurring/'

    def test_unauthenticated_returns_403(self):
        client = APIClient()
        response = client.get(self._api_url())
        assert response.status_code == 403

    def test_regular_member_sees_own(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        own = RecurringDonationFactory(member=member)
        other = RecurringDonationFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        ids = [str(r['id']) for r in response.data['results']]
        assert str(own.pk) in ids
        assert str(other.pk) not in ids

    def test_admin_sees_all(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        RecurringDonationFactory()
        RecurringDonationFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        assert len(response.data['results']) == 2

    def test_user_without_member_sees_none(self):
        user = UserFactory()

        RecurringDonationFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(self._api_url())
        assert response.status_code == 200
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestRecurringDonationCreateSubscription:
    """Tests for RecurringDonationViewSet create_subscription action."""

    def _api_url(self):
        return '/api/v1/payments/recurring/create_subscription/'

    def test_creates_subscription_successfully(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(), {
                'amount': '25.00',
                'frequency': 'monthly',
                'donation_type': 'tithe',
            })

        assert response.status_code == 201
        assert RecurringDonation.objects.count() == 1

    def test_creates_weekly_subscription(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(), {
                'amount': '10.00',
                'frequency': 'weekly',
                'donation_type': 'offering',
            })

        assert response.status_code == 201
        recurring = RecurringDonation.objects.first()
        assert recurring.frequency == 'weekly'

    def test_invalid_amount_rejected(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self._api_url(), {
            'amount': '0.00',
            'frequency': 'monthly',
            'donation_type': 'tithe',
        })
        assert response.status_code == 400

    def test_invalid_frequency_rejected(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self._api_url(), {
            'amount': '25.00',
            'frequency': 'yearly',
            'donation_type': 'tithe',
        })
        assert response.status_code == 400

    def test_unauthenticated_returns_403(self):
        client = APIClient()
        response = client.post(self._api_url(), {
            'amount': '25.00',
            'frequency': 'monthly',
        })
        assert response.status_code == 403


@pytest.mark.django_db
class TestRecurringDonationCancel:
    """Tests for RecurringDonationViewSet cancel action."""

    def _api_url(self, pk):
        return f'/api/v1/payments/recurring/{pk}/cancel/'

    def test_member_can_cancel_own_subscription(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)
        recurring = RecurringDonationFactory(
            member=member,
            stripe_subscription_id='sub_dev_test',
        )

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(recurring.pk))

        assert response.status_code == 200
        assert response.data['status'] == 'cancelled'
        recurring.refresh_from_db()
        assert recurring.is_active_subscription is False

    def test_member_cannot_cancel_others_subscription(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        other_member = MemberFactory()
        recurring = RecurringDonationFactory(member=other_member)

        # Admin sees all so the get_queryset returns it,
        # but the cancel check rejects non-owner.
        # Regular member won't even see the object (404).
        # Let's use admin to find the object but test the ownership check:
        admin_user = UserFactory()
        admin_member = MemberFactory(user=admin_user, role=Roles.ADMIN, registration_date=None)

        # Admin user who is not the owner should get 403 from the ownership check
        client = APIClient()
        client.force_authenticate(user=admin_user)

        with patch('apps.payments.services.get_stripe', return_value=None):
            response = client.post(self._api_url(recurring.pk))

        assert response.status_code == 403
        assert 'error' in response.data


@pytest.mark.django_db
class TestStripeWebhookView:
    """Tests for the StripeWebhookView."""

    def _url(self):
        return '/api/v1/payments/webhook/'

    def test_payment_succeeded_webhook(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        payload = json.dumps({
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': payment.stripe_payment_intent_id,
                },
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.SUCCEEDED

    def test_payment_succeeded_with_receipt_url(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        payload = json.dumps({
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': payment.stripe_payment_intent_id,
                    'charges': {
                        'data': [
                            {'receipt_url': 'https://receipt.stripe.com/abc'}
                        ]
                    },
                },
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.stripe_receipt_url == 'https://receipt.stripe.com/abc'

    def test_payment_failed_webhook(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        payload = json.dumps({
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': payment.stripe_payment_intent_id,
                    'last_payment_error': {
                        'message': 'Your card was declined.',
                    },
                },
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.FAILED

    def test_invalid_json_returns_400(self):
        client = APIClient()
        response = client.post(
            self._url(),
            data='not valid json{{{',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_unknown_event_type_returns_200(self):
        payload = json.dumps({
            'type': 'charge.refunded',
            'data': {
                'object': {'id': 'ch_test'},
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )
        assert response.status_code == 200

    def test_succeeded_with_no_charges(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        payload = json.dumps({
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': payment.stripe_payment_intent_id,
                },
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.SUCCEEDED
        assert payment.stripe_receipt_url == ''

    def test_empty_payload_returns_400(self):
        client = APIClient()
        response = client.post(
            self._url(),
            data=b'',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_failed_with_no_error_info(self):
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        payload = json.dumps({
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': payment.stripe_payment_intent_id,
                },
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.FAILED

    def test_nonexistent_payment_intent_handled_gracefully(self):
        payload = json.dumps({
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_nonexistent_abc123',
                },
            },
        })

        client = APIClient()
        response = client.post(
            self._url(),
            data=payload,
            content_type='application/json',
        )
        # Should not crash, returns 200 even if payment not found
        assert response.status_code == 200


@pytest.mark.django_db
class TestStripeWebhookWithStripeConfigured:
    """Tests for StripeWebhookView when Stripe is configured (not dev mode)."""

    def _url(self):
        return '/api/v1/payments/webhook/'

    def test_webhook_invalid_signature_returns_400(self):
        """When Stripe is configured, an invalid signature returns 400."""
        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.side_effect = ValueError('Invalid signature')

        client = Client()
        with patch('apps.payments.views_api.get_stripe', return_value=mock_stripe):
            with patch('apps.payments.views_api.settings') as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = 'whsec_test_secret'
                response = client.post(
                    self._url(),
                    data=b'{}',
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='invalid_sig',
                )
        assert response.status_code == 400

    def test_webhook_generic_exception_returns_400(self):
        """When Stripe construct_event raises a generic Exception, returns 400."""
        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.side_effect = Exception('Webhook error')

        client = Client()
        with patch('apps.payments.views_api.get_stripe', return_value=mock_stripe):
            with patch('apps.payments.views_api.settings') as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = 'whsec_test_secret'
                response = client.post(
                    self._url(),
                    data=b'{}',
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='invalid_sig',
                )
        assert response.status_code == 400

    def test_webhook_valid_stripe_event_succeeds(self):
        """When Stripe verifies the event, it processes normally."""
        payment = OnlinePaymentFactory(status=PaymentStatus.PENDING)

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': payment.stripe_payment_intent_id,
                },
            },
        }

        client = Client()
        with patch('apps.payments.views_api.get_stripe', return_value=mock_stripe):
            with patch('apps.payments.views_api.settings') as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = 'whsec_test_secret'
                response = client.post(
                    self._url(),
                    data=b'{}',
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='valid_sig',
                )
        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.SUCCEEDED
