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
