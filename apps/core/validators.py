"""Reusable file validators for uploads."""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_image_file(value):
    """Validate image files (max 5MB, JPEG/PNG/GIF/WebP only)."""
    max_size = 5 * 1024 * 1024

    if value.size > max_size:
        raise ValidationError(
            _('La taille du fichier ne doit pas dépasser 5 Mo. '
              'Taille actuelle: %(size).1f Mo.'),
            params={'size': value.size / (1024 * 1024)},
        )

    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    content_type = getattr(value, 'content_type', None)
    if content_type and content_type not in allowed_types:
        raise ValidationError(
            _('Type de fichier non autorisé: %(type)s. '
              'Types acceptés: JPEG, PNG, GIF, WebP.'),
            params={'type': content_type},
        )


def validate_pdf_file(value):
    """Validate PDF files (max 10MB)."""
    max_size = 10 * 1024 * 1024

    if value.size > max_size:
        raise ValidationError(
            _('La taille du fichier ne doit pas dépasser 10 Mo. '
              'Taille actuelle: %(size).1f Mo.'),
            params={'size': value.size / (1024 * 1024)},
        )

    content_type = getattr(value, 'content_type', None)
    if content_type and content_type != 'application/pdf':
        raise ValidationError(
            _('Seuls les fichiers PDF sont acceptés.'),
        )
