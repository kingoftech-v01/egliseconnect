"""Tests for analytics dashboard and A/B testing views."""
import pytest

from apps.core.constants import NewsletterStatus, ABTestStatus
from apps.members.tests.factories import MemberWithUserFactory
from apps.communication.models import ABTest
from apps.communication.tests.factories import (
    NewsletterFactory, ABTestFactory,
)

pytestmark = pytest.mark.django_db


# ─── A/B Test Model Tests ───────────────────────────────────────────────────────


class TestABTestModel:
    def test_str(self):
        nl = NewsletterFactory(subject='Weekly Update')
        abtest = ABTestFactory(newsletter=nl)
        assert 'Weekly Update' in str(abtest)

    def test_default_status_draft(self):
        abtest = ABTestFactory()
        assert abtest.status == ABTestStatus.DRAFT

    def test_default_test_size(self):
        abtest = ABTestFactory()
        assert abtest.test_size_pct == 20

    def test_winner_initially_blank(self):
        abtest = ABTestFactory()
        assert abtest.winner == ''

    def test_variant_opens_default_zero(self):
        abtest = ABTestFactory()
        assert abtest.variant_a_opens == 0
        assert abtest.variant_b_opens == 0


# ─── Analytics Dashboard View Tests ─────────────────────────────────────────────


class TestAnalyticsDashboard:
    def test_dashboard_staff_only(self, client):
        """Non-staff redirected."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        resp = client.get('/communication/analytics/')
        assert resp.status_code == 302

    def test_dashboard_accessible(self, client):
        """Staff can access analytics dashboard."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/analytics/')
        assert resp.status_code == 200

    def test_dashboard_context(self, client):
        """Dashboard returns expected context keys."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)

        NewsletterFactory(status=NewsletterStatus.SENT, recipients_count=100, opened_count=30)
        NewsletterFactory(status=NewsletterStatus.SENT, recipients_count=50, opened_count=10)

        resp = client.get('/communication/analytics/')
        assert resp.status_code == 200
        ctx = resp.context
        assert 'total_sent' in ctx
        assert 'total_recipients' in ctx
        assert 'total_opens' in ctx
        assert 'avg_open_rate' in ctx
        assert ctx['total_sent'] == 2
        assert ctx['total_recipients'] == 150
        assert ctx['total_opens'] == 40

    def test_dashboard_empty(self, client):
        """Dashboard works with no data."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        resp = client.get('/communication/analytics/')
        assert resp.status_code == 200
        assert resp.context['total_sent'] == 0


# ─── A/B Test View Tests ────────────────────────────────────────────────────────


class TestABTestResultsView:
    def test_abtest_results_staff_only(self, client):
        """Non-staff redirected."""
        user = MemberWithUserFactory().user
        client.force_login(user)
        abtest = ABTestFactory()
        resp = client.get(f'/communication/ab-tests/{abtest.pk}/results/')
        assert resp.status_code == 302

    def test_abtest_results_accessible(self, client):
        """Staff can access A/B test results."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'admin'
        user.member_profile.save()
        client.force_login(user)
        abtest = ABTestFactory(
            variant_a_opens=50,
            variant_b_opens=30,
            variant_a_clicks=20,
            variant_b_clicks=10,
        )
        resp = client.get(f'/communication/ab-tests/{abtest.pk}/results/')
        assert resp.status_code == 200
        assert resp.context['abtest'] == abtest

    def test_abtest_results_context(self, client):
        """Results page includes total metrics."""
        user = MemberWithUserFactory().user
        user.member_profile.role = 'pastor'
        user.member_profile.save()
        client.force_login(user)
        abtest = ABTestFactory(
            variant_a_opens=100, variant_a_clicks=50,
            variant_b_opens=80, variant_b_clicks=40,
        )
        resp = client.get(f'/communication/ab-tests/{abtest.pk}/results/')
        assert resp.context['total_a'] == 150
        assert resp.context['total_b'] == 120
