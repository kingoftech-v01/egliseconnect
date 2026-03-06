"""Custom DRF throttle classes for API rate limiting."""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, SimpleRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """Short burst rate limit to prevent rapid-fire requests.

    Default: 30 requests per minute.
    Configure via REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['burst'].
    """
    scope = 'burst'
    rate = '30/minute'


class SustainedRateThrottle(UserRateThrottle):
    """Sustained rate limit to prevent long-term abuse.

    Default: 1000 requests per day.
    Configure via REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['sustained'].
    """
    scope = 'sustained'
    rate = '1000/day'


class AnonBurstRateThrottle(AnonRateThrottle):
    """Burst rate limit for anonymous users.

    Default: 10 requests per minute.
    """
    scope = 'anon_burst'
    rate = '10/minute'


class AnonSustainedRateThrottle(AnonRateThrottle):
    """Sustained rate limit for anonymous users.

    Default: 200 requests per day.
    """
    scope = 'anon_sustained'
    rate = '200/day'


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit for login attempts to prevent brute force.

    Default: 5 attempts per minute.
    """
    scope = 'login'
    rate = '5/minute'


class WebhookRateThrottle(UserRateThrottle):
    """Rate limit for webhook delivery endpoints.

    Default: 60 requests per minute.
    """
    scope = 'webhook'
    rate = '60/minute'


class ExportRateThrottle(UserRateThrottle):
    """Rate limit for export operations (CSV/PDF generation).

    Default: 10 per hour.
    """
    scope = 'export'
    rate = '10/hour'


class SearchRateThrottle(UserRateThrottle):
    """Rate limit for search/autocomplete endpoints.

    Default: 60 per minute.
    """
    scope = 'search'
    rate = '60/minute'


class RateLimitHeadersMixin:
    """Mixin for DRF views to add rate limit headers to responses.

    Add to any APIView to include X-RateLimit headers:
    - X-RateLimit-Limit: Total allowed requests
    - X-RateLimit-Remaining: Remaining requests
    - X-RateLimit-Reset: Seconds until limit resets
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if hasattr(request, '_throttle_durations'):
            for throttle_info in getattr(request, '_throttle_durations', []):
                if isinstance(throttle_info, dict):
                    response['X-RateLimit-Limit'] = throttle_info.get('limit', '')
                    response['X-RateLimit-Remaining'] = throttle_info.get('remaining', '')
                    response['X-RateLimit-Reset'] = throttle_info.get('reset', '')

        # Fallback: inspect throttles directly
        for throttle in self.get_throttles():
            if hasattr(throttle, 'rate') and throttle.rate:
                num_requests, duration = throttle.parse_rate(throttle.rate)
                if num_requests:
                    response['X-RateLimit-Limit'] = str(num_requests)
                    # Get remaining from cache
                    if hasattr(throttle, 'key') and hasattr(throttle, 'cache'):
                        history = throttle.cache.get(throttle.key, [])
                        remaining = max(0, num_requests - len(history))
                        response['X-RateLimit-Remaining'] = str(remaining)
                    break

        return response
