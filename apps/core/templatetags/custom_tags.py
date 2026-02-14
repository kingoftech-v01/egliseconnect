import logging
from django import template
from django.urls import resolve
from django.urls.exceptions import Resolver404

logger = logging.getLogger(__name__)
register = template.Library()


def getdata(json_data, args):
    func_name = ''
    try:
        myfunc, myargs, mykwargs = resolve(args)
        if myfunc:
            func_name = myfunc.__name__
    except Resolver404:
        pass

    return json_data.get(func_name)


register.filter('getdata', getdata)


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class to a form field widget."""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field


# ─── Feature Flag Template Tags ──────────────────────────────────────────────
# django-waffle is installed. These tags provide convenient access in templates.
#
# Usage in templates:
#   {% load custom_tags %}
#   {% feature_flag "new_dashboard" as show_dashboard %}
#   {% if show_dashboard %}...{% endif %}
#
#   Or use waffle's built-in tags:
#   {% load waffle_tags %}
#   {% flag "new_dashboard" %}...{% endflag %}

@register.simple_tag(takes_context=True)
def feature_flag(context, flag_name):
    """Check if a waffle flag is active for the current request.

    Usage:
        {% feature_flag "flag_name" as is_active %}
        {% if is_active %}...{% endif %}
    """
    try:
        import waffle
        request = context.get('request')
        if request:
            return waffle.flag_is_active(request, flag_name)
    except Exception:
        pass
    return False


@register.simple_tag
def feature_switch(switch_name):
    """Check if a waffle switch is active.

    Usage:
        {% feature_switch "switch_name" as is_active %}
        {% if is_active %}...{% endif %}
    """
    try:
        import waffle
        return waffle.switch_is_active(switch_name)
    except Exception:
        return False


@register.simple_tag(takes_context=True)
def feature_sample(context, sample_name):
    """Check if a waffle sample is active.

    Usage:
        {% feature_sample "sample_name" as is_active %}
    """
    try:
        import waffle
        return waffle.sample_is_active(sample_name)
    except Exception:
        return False


# ─── Breadcrumb Helper ───────────────────────────────────────────────────────

@register.inclusion_tag('elements/breadcrumbs.html')
def render_breadcrumbs(breadcrumbs):
    """Render a consistent breadcrumb navigation.

    Usage:
        {% render_breadcrumbs breadcrumbs %}

    Where breadcrumbs is a list of (label, url) tuples.
    Last item's url should be None (current page).
    """
    return {'breadcrumbs': breadcrumbs}
