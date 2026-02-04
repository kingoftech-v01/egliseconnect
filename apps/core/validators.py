"""
Core validators - Reusable validators for ÉgliseConnect.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_image_file(value):
    """
    Validate uploaded image files for size and content type.

    - Maximum file size: 5 MB
    - Allowed content types: JPEG, PNG, GIF, WebP
    """
    max_size = 5 * 1024 * 1024  # 5 MB

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
    """
    Validate uploaded PDF files for size and content type.

    - Maximum file size: 10 MB
    - Allowed content types: PDF
    """
    max_size = 10 * 1024 * 1024  # 10 MB

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
