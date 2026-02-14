"""Tests for custom API rate limiting throttle classes."""
import pytest
from unittest.mock import MagicMock

from apps.core.throttles import (
    BurstRateThrottle,
    SustainedRateThrottle,
    AnonBurstRateThrottle,
    AnonSustainedRateThrottle,
    LoginRateThrottle,
    WebhookRateThrottle,
    ExportRateThrottle,
    SearchRateThrottle,
    RateLimitHeadersMixin,
)


class TestBurstRateThrottle:
    def test_scope(self):
        throttle = BurstRateThrottle()
        assert throttle.scope == 'burst'

    def test_rate(self):
        throttle = BurstRateThrottle()
        assert throttle.rate == '30/minute'


class TestSustainedRateThrottle:
    def test_scope(self):
        throttle = SustainedRateThrottle()
        assert throttle.scope == 'sustained'

    def test_rate(self):
        throttle = SustainedRateThrottle()
        assert throttle.rate == '1000/day'


class TestAnonBurstRateThrottle:
    def test_scope(self):
        throttle = AnonBurstRateThrottle()
        assert throttle.scope == 'anon_burst'

    def test_rate(self):
        throttle = AnonBurstRateThrottle()
        assert throttle.rate == '10/minute'


class TestAnonSustainedRateThrottle:
    def test_scope(self):
        throttle = AnonSustainedRateThrottle()
        assert throttle.scope == 'anon_sustained'

    def test_rate(self):
        throttle = AnonSustainedRateThrottle()
        assert throttle.rate == '200/day'


class TestLoginRateThrottle:
    def test_scope(self):
        throttle = LoginRateThrottle()
        assert throttle.scope == 'login'

    def test_rate(self):
        throttle = LoginRateThrottle()
        assert throttle.rate == '5/minute'


class TestWebhookRateThrottle:
    def test_scope(self):
        throttle = WebhookRateThrottle()
        assert throttle.scope == 'webhook'

    def test_rate(self):
        throttle = WebhookRateThrottle()
        assert throttle.rate == '60/minute'


class TestExportRateThrottle:
    def test_scope(self):
        throttle = ExportRateThrottle()
        assert throttle.scope == 'export'

    def test_rate(self):
        throttle = ExportRateThrottle()
        assert throttle.rate == '10/hour'


class TestSearchRateThrottle:
    def test_scope(self):
        throttle = SearchRateThrottle()
        assert throttle.scope == 'search'

    def test_rate(self):
        throttle = SearchRateThrottle()
        assert throttle.rate == '60/minute'


class TestRateLimitHeadersMixin:
    def test_mixin_has_finalize_response(self):
        assert hasattr(RateLimitHeadersMixin, 'finalize_response')

    def test_all_throttle_classes_importable(self):
        """Verify all throttle classes can be imported."""
        throttle_classes = [
            BurstRateThrottle,
            SustainedRateThrottle,
            AnonBurstRateThrottle,
            AnonSustainedRateThrottle,
            LoginRateThrottle,
            WebhookRateThrottle,
            ExportRateThrottle,
            SearchRateThrottle,
        ]
        for cls in throttle_classes:
            instance = cls()
            assert instance.scope is not None
            assert instance.rate is not None

    def test_parse_rate(self):
        """Verify throttles can parse their own rate."""
        throttle = BurstRateThrottle()
        num_requests, duration = throttle.parse_rate(throttle.rate)
        assert num_requests == 30
        assert duration == 60  # minute = 60 seconds

    def test_sustained_parse_rate(self):
        throttle = SustainedRateThrottle()
        num_requests, duration = throttle.parse_rate(throttle.rate)
        assert num_requests == 1000
        assert duration == 86400  # day = 86400 seconds
