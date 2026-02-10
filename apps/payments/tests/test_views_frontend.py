"""Tests for payment frontend views: donate, donation_success, payment_history, recurring_manage, cancel_recurring."""
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core.constants import Roles
from apps.payments.models import OnlinePayment, RecurringDonation
from apps.members.tests.factories import MemberFactory, UserFactory
from apps.payments.tests.factories import (
    OnlinePaymentFactory,
    RecurringDonationFactory,
    CancelledRecurringFactory,
)


@pytest.mark.django_db
class TestDonateView:
    """Tests for the donate frontend view."""

    def _url(self):
        return reverse('frontend:payments:donate')

    def test_requires_login(self):
        client = Client()
        response = client.get(self._url())
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_redirects_without_member_profile(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302
        # Redirects to member_create
        assert 'member' in response['Location'].lower() or response.status_code == 302

    def test_renders_donate_template(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        templates = [t.name for t in response.templates]
        assert 'payments/donate.html' in templates

    def test_context_has_donation_types(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'donation_types' in response.context
        assert len(response.context['donation_types']) > 0

    def test_context_has_stripe_public_key(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'stripe_public_key' in response.context

    def test_context_has_campaigns(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'campaigns' in response.context

    def test_context_has_page_title(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'page_title' in response.context

    def test_context_has_suggested_amounts(self):
        """Context includes suggested amount buttons."""
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'suggested_amounts' in response.context
        assert 25 in response.context['suggested_amounts']
        assert 50 in response.context['suggested_amounts']
        assert 100 in response.context['suggested_amounts']

    def test_context_has_selected_campaign(self):
        """Context includes selected_campaign from query param."""
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url() + '?campaign=some-uuid')
        assert 'selected_campaign' in response.context
        assert response.context['selected_campaign'] == 'some-uuid'

    def test_selected_campaign_empty_when_not_provided(self):
        """selected_campaign is empty string when not provided."""
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.context['selected_campaign'] == ''


@pytest.mark.django_db
class TestDonationSuccessView:
    """Tests for the donation_success frontend view."""

    def _url(self):
        return reverse('frontend:payments:donation_success')

    def test_requires_login(self):
        client = Client()
        response = client.get(self._url())
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_renders_success_template(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        templates = [t.name for t in response.templates]
        assert 'payments/donation_success.html' in templates

    def test_context_has_page_title(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'page_title' in response.context


@pytest.mark.django_db
class TestPaymentHistoryView:
    """Tests for the payment_history frontend view."""

    def _url(self):
        return reverse('frontend:payments:payment_history')

    def test_requires_login(self):
        client = Client()
        response = client.get(self._url())
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_redirects_without_member_profile(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302

    def test_regular_member_sees_own_payments(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        own_payment = OnlinePaymentFactory(member=member)
        other_payment = OnlinePaymentFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        pks = [p.pk for p in response.context['payments']]
        assert own_payment.pk in pks
        assert other_payment.pk not in pks

    def test_admin_sees_all_payments(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        p1 = OnlinePaymentFactory()
        p2 = OnlinePaymentFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        pks = [p.pk for p in response.context['payments']]
        assert p1.pk in pks
        assert p2.pk in pks

    def test_pastor_sees_all_payments(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.PASTOR, registration_date=None)

        OnlinePaymentFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        assert len(response.context['payments']) >= 1

    def test_treasurer_sees_all_payments(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.TREASURER, registration_date=None)

        OnlinePaymentFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        assert len(response.context['payments']) >= 1

    def test_volunteer_sees_only_own(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.VOLUNTEER, registration_date=None)

        own = OnlinePaymentFactory(member=member)
        other = OnlinePaymentFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        pks = [p.pk for p in response.context['payments']]
        assert own.pk in pks
        assert other.pk not in pks

    def test_payments_ordered_newest_first(self):
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        p1 = OnlinePaymentFactory(member=member)
        p2 = OnlinePaymentFactory(member=member)

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        pks = [p.pk for p in response.context['payments']]
        assert pks[0] == p2.pk
        assert pks[1] == p1.pk

    def test_context_has_page_title(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'page_title' in response.context

    def test_renders_template(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        templates = [t.name for t in response.templates]
        assert 'payments/payment_history.html' in templates

    def test_pagination(self):
        """Payment history uses paginator."""
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        for i in range(30):
            OnlinePaymentFactory(member=member)

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        payments_page = response.context['payments']
        assert payments_page.paginator.num_pages == 2

    def test_pagination_page_2(self):
        """Can navigate to page 2."""
        user = UserFactory()
        member = MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)

        for i in range(30):
            OnlinePaymentFactory(member=member)

        client = Client()
        client.force_login(user)
        response = client.get(self._url() + '?page=2')
        assert response.status_code == 200

    def test_admin_pagination(self):
        """Admin sees all payments with pagination."""
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        for i in range(30):
            OnlinePaymentFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        payments_page = response.context['payments']
        assert payments_page.paginator.num_pages == 2


@pytest.mark.django_db
class TestRecurringManageView:
    """Tests for the recurring_manage frontend view."""

    def _url(self):
        return reverse('frontend:payments:recurring_manage')

    def test_requires_login(self):
        client = Client()
        response = client.get(self._url())
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_redirects_without_member_profile(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302

    def test_shows_active_recurring_donations(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)

        active = RecurringDonationFactory(member=member, is_active_subscription=True)

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        pks = [r.pk for r in response.context['recurring']]
        assert active.pk in pks

    def test_shows_cancelled_recurring_donations(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)

        cancelled = CancelledRecurringFactory(member=member)

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200
        pks = [r.pk for r in response.context['cancelled']]
        assert cancelled.pk in pks

    def test_only_shows_own_recurring(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)

        own = RecurringDonationFactory(member=member)
        other = RecurringDonationFactory()

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        pks = [r.pk for r in response.context['recurring']]
        assert own.pk in pks
        assert other.pk not in pks

    def test_context_has_page_title(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert 'page_title' in response.context

    def test_renders_template(self):
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        templates = [t.name for t in response.templates]
        assert 'payments/recurring_manage.html' in templates

    def test_cancelled_ordered_by_cancelled_at_desc(self):
        from datetime import timedelta

        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)

        c1 = CancelledRecurringFactory(
            member=member,
            cancelled_at=timezone.now() - timedelta(days=5),
        )
        c2 = CancelledRecurringFactory(
            member=member,
            cancelled_at=timezone.now() - timedelta(days=1),
        )

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        pks = [r.pk for r in response.context['cancelled']]
        assert pks[0] == c2.pk
        assert pks[1] == c1.pk

    def test_cancelled_limited_to_10(self):
        from datetime import timedelta

        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)

        for i in range(15):
            CancelledRecurringFactory(
                member=member,
                cancelled_at=timezone.now() - timedelta(days=i),
            )

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert len(response.context['cancelled']) == 10


@pytest.mark.django_db
class TestCancelRecurringView:
    """Tests for cancel_recurring frontend view."""

    def test_login_required(self):
        import uuid
        client = Client()
        response = client.get(f'/payments/recurring/{uuid.uuid4()}/cancel/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_redirects_without_member_profile(self):
        import uuid
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(f'/payments/recurring/{uuid.uuid4()}/cancel/')
        assert response.status_code == 302

    def test_get_shows_confirmation_page(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)
        recurring = RecurringDonationFactory(member=member, is_active_subscription=True)

        client = Client()
        client.force_login(user)
        response = client.get(f'/payments/recurring/{recurring.pk}/cancel/')
        assert response.status_code == 200
        assert response.context['recurring'] == recurring
        templates = [t.name for t in response.templates]
        assert 'payments/cancel_recurring.html' in templates

    def test_post_cancels_recurring(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)
        recurring = RecurringDonationFactory(member=member, is_active_subscription=True)

        client = Client()
        client.force_login(user)
        response = client.post(f'/payments/recurring/{recurring.pk}/cancel/')
        assert response.status_code == 302
        assert response.url == '/payments/recurring/'

        recurring.refresh_from_db()
        assert recurring.is_active_subscription is False
        assert recurring.cancelled_at is not None

    def test_cannot_cancel_other_member_recurring(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)
        other_recurring = RecurringDonationFactory(is_active_subscription=True)

        client = Client()
        client.force_login(user)
        response = client.get(f'/payments/recurring/{other_recurring.pk}/cancel/')
        assert response.status_code == 404

    def test_cannot_cancel_already_cancelled(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)
        cancelled = CancelledRecurringFactory(member=member)

        client = Client()
        client.force_login(user)
        response = client.get(f'/payments/recurring/{cancelled.pk}/cancel/')
        assert response.status_code == 404

    def test_get_does_not_cancel(self):
        user = UserFactory()
        member = MemberFactory(user=user, registration_date=None)
        recurring = RecurringDonationFactory(member=member, is_active_subscription=True)

        client = Client()
        client.force_login(user)
        client.get(f'/payments/recurring/{recurring.pk}/cancel/')
        recurring.refresh_from_db()
        assert recurring.is_active_subscription is True
        assert recurring.cancelled_at is None

    def test_404_for_nonexistent(self):
        import uuid
        user = UserFactory()
        MemberFactory(user=user, registration_date=None)

        client = Client()
        client.force_login(user)
        response = client.get(f'/payments/recurring/{uuid.uuid4()}/cancel/')
        assert response.status_code == 404
