"""Context processors for branding and global template variables."""
from django.utils.translation import get_language


def branding(request):
    """Add church branding settings to all templates."""
    from apps.core.models_extended import ChurchBranding

    try:
        brand = ChurchBranding.get_current()
    except Exception:
        brand = None

    return {
        'church_branding': brand,
    }


def language_context(request):
    """Add current language to template context for language switcher."""
    return {
        'current_language': get_language() or 'fr',
    }
