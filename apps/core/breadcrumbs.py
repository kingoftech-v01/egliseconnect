"""Breadcrumb helper for function-based views."""


def make_breadcrumbs(*crumbs):
    """
    Build breadcrumb list for template rendering.

    Args:
        *crumbs: tuples of (label, url) or (label, None) for current page

    Returns:
        list of dicts with 'label' and 'url' keys

    Usage:
        context['breadcrumbs'] = make_breadcrumbs(
            ('Accueil', '/'),
            ('Membres', '/members/'),
            ('Détails', None),
        )
    """
    return [{'label': label, 'url': url} for label, url in crumbs]
