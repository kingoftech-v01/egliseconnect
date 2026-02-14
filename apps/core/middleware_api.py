"""Middleware for API versioning and deprecation headers."""
import re

from django.utils import timezone


class APIDeprecationHeadersMiddleware:
    """
    Adds deprecation headers for API v1 responses.

    When API v2 is available, v1 endpoints get:
    - Deprecation: true
    - Sunset: <date when v1 will be removed>
    - Link: <v2 equivalent URL>
    """

    # Date when v1 will be sunset (set to a future date)
    SUNSET_DATE = '2027-06-01T00:00:00Z'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add headers to API v1 responses
        if request.path.startswith('/api/v1/'):
            response['Deprecation'] = 'false'  # Not yet deprecated
            response['API-Version'] = 'v1'

            # When v2 is fully ready, change to:
            # response['Deprecation'] = 'true'
            # response['Sunset'] = self.SUNSET_DATE
            # v2_path = request.path.replace('/api/v1/', '/api/v2/')
            # response['Link'] = f'<{v2_path}>; rel="successor-version"'

        elif request.path.startswith('/api/v2/'):
            response['API-Version'] = 'v2'

        return response
