"""Tests for core template tags (custom_tags.py)."""
import pytest
from apps.core.templatetags.custom_tags import getdata


class TestGetData:
    """Tests for the getdata template filter."""

    def test_valid_url_with_matching_key(self):
        """Resolving a valid URL should look up the function name in the data dict."""
        # /offline/ resolves to the 'offline' view function
        result = getdata({'offline': 'test_value'}, '/offline/')
        assert result == 'test_value'

    def test_valid_url_with_no_matching_key(self):
        """Resolving a valid URL whose function name is not in the dict returns None."""
        result = getdata({}, '/offline/')
        assert result is None

    def test_invalid_url_triggers_resolver404(self):
        """A URL that does not resolve should trigger Resolver404 and return None."""
        result = getdata({'key': 'value'}, '/this-url-does-not-exist-at-all/')
        assert result is None

    def test_invalid_url_with_empty_data(self):
        """Invalid URL with empty data returns None."""
        result = getdata({}, '/nonexistent-path-12345/')
        assert result is None

    def test_data_dict_with_function_name(self):
        """The filter should use the resolved function's __name__ as the lookup key."""
        # /sw.js resolves to the 'service_worker' view
        data = {'service_worker': 'sw_data'}
        result = getdata(data, '/sw.js')
        assert result == 'sw_data'
