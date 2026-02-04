"""
Tests for core validators.
"""
import pytest
from unittest.mock import Mock

from django.core.exceptions import ValidationError

from apps.core.validators import validate_image_file, validate_pdf_file


# =============================================================================
# VALIDATE IMAGE FILE TESTS
# =============================================================================

class TestValidateImageFile:
    """Tests for validate_image_file validator."""

    # -------------------------------------------------------------------------
    # Valid files
    # -------------------------------------------------------------------------

    def test_valid_jpeg_file(self):
        """Test that a valid JPEG file passes validation."""
        file = Mock()
        file.size = 1024 * 1024  # 1 MB
        file.content_type = 'image/jpeg'
        # Should not raise
        validate_image_file(file)

    def test_valid_png_file(self):
        """Test that a valid PNG file passes validation."""
        file = Mock()
        file.size = 2 * 1024 * 1024  # 2 MB
        file.content_type = 'image/png'
        validate_image_file(file)

    def test_valid_gif_file(self):
        """Test that a valid GIF file passes validation."""
        file = Mock()
        file.size = 512 * 1024  # 512 KB
        file.content_type = 'image/gif'
        validate_image_file(file)

    def test_valid_webp_file(self):
        """Test that a valid WebP file passes validation."""
        file = Mock()
        file.size = 1024 * 1024  # 1 MB
        file.content_type = 'image/webp'
        validate_image_file(file)

    def test_small_valid_file(self):
        """Test that a very small valid file passes validation."""
        file = Mock()
        file.size = 100  # 100 bytes
        file.content_type = 'image/jpeg'
        validate_image_file(file)

    def test_exact_max_size_passes(self):
        """Test that a file exactly at the 5 MB limit passes validation."""
        file = Mock()
        file.size = 5 * 1024 * 1024  # Exactly 5 MB
        file.content_type = 'image/jpeg'
        validate_image_file(file)

    def test_file_without_content_type_passes(self):
        """Test that a file without content_type attribute passes type check."""
        file = Mock(spec=['size'])
        file.size = 1024 * 1024  # 1 MB
        # No content_type attribute at all; getattr returns None
        validate_image_file(file)

    def test_file_with_none_content_type_passes(self):
        """Test that a file with content_type=None passes type check."""
        file = Mock()
        file.size = 1024 * 1024
        file.content_type = None
        validate_image_file(file)

    # -------------------------------------------------------------------------
    # Oversized files
    # -------------------------------------------------------------------------

    def test_oversized_file_raises_validation_error(self):
        """Test that a file larger than 5 MB raises ValidationError."""
        file = Mock()
        file.size = 6 * 1024 * 1024  # 6 MB
        file.content_type = 'image/jpeg'

        with pytest.raises(ValidationError) as exc_info:
            validate_image_file(file)

        assert 'size' in exc_info.value.params

    def test_one_byte_over_max_size_raises(self):
        """Test that a file one byte over 5 MB raises ValidationError."""
        file = Mock()
        file.size = 5 * 1024 * 1024 + 1
        file.content_type = 'image/jpeg'

        with pytest.raises(ValidationError):
            validate_image_file(file)

    def test_oversized_file_error_includes_actual_size(self):
        """Test that the error message includes the actual file size."""
        file = Mock()
        file.size = 10 * 1024 * 1024  # 10 MB
        file.content_type = 'image/jpeg'

        with pytest.raises(ValidationError) as exc_info:
            validate_image_file(file)

        # The params should contain the size in MB
        assert exc_info.value.params['size'] == pytest.approx(10.0, rel=0.01)

    # -------------------------------------------------------------------------
    # Invalid content types
    # -------------------------------------------------------------------------

    def test_pdf_content_type_raises_validation_error(self):
        """Test that application/pdf content type raises ValidationError."""
        file = Mock()
        file.size = 1024 * 1024
        file.content_type = 'application/pdf'

        with pytest.raises(ValidationError) as exc_info:
            validate_image_file(file)

        assert 'type' in exc_info.value.params

    def test_text_content_type_raises_validation_error(self):
        """Test that text/plain content type raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'text/plain'

        with pytest.raises(ValidationError):
            validate_image_file(file)

    def test_svg_content_type_raises_validation_error(self):
        """Test that image/svg+xml content type raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'image/svg+xml'

        with pytest.raises(ValidationError):
            validate_image_file(file)

    def test_html_content_type_raises_validation_error(self):
        """Test that text/html content type raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'text/html'

        with pytest.raises(ValidationError):
            validate_image_file(file)

    def test_invalid_content_type_error_includes_type(self):
        """Test that error message includes the rejected content type."""
        file = Mock()
        file.size = 1024
        file.content_type = 'application/octet-stream'

        with pytest.raises(ValidationError) as exc_info:
            validate_image_file(file)

        assert exc_info.value.params['type'] == 'application/octet-stream'

    # -------------------------------------------------------------------------
    # Combined: size checked before content type
    # -------------------------------------------------------------------------

    def test_oversized_invalid_type_raises_size_error_first(self):
        """Test that oversized file with bad type raises size error first."""
        file = Mock()
        file.size = 6 * 1024 * 1024  # 6 MB, over limit
        file.content_type = 'text/plain'  # Also invalid type

        with pytest.raises(ValidationError) as exc_info:
            validate_image_file(file)

        # Size is checked first, so the error should be about size
        assert 'size' in exc_info.value.params


# =============================================================================
# VALIDATE PDF FILE TESTS
# =============================================================================

class TestValidatePdfFile:
    """Tests for validate_pdf_file validator."""

    # -------------------------------------------------------------------------
    # Valid files
    # -------------------------------------------------------------------------

    def test_valid_pdf_file(self):
        """Test that a valid PDF file passes validation."""
        file = Mock()
        file.size = 1024 * 1024  # 1 MB
        file.content_type = 'application/pdf'
        validate_pdf_file(file)

    def test_small_valid_pdf_file(self):
        """Test that a very small valid PDF passes validation."""
        file = Mock()
        file.size = 100  # 100 bytes
        file.content_type = 'application/pdf'
        validate_pdf_file(file)

    def test_exact_max_size_passes(self):
        """Test that a file exactly at the 10 MB limit passes validation."""
        file = Mock()
        file.size = 10 * 1024 * 1024  # Exactly 10 MB
        file.content_type = 'application/pdf'
        validate_pdf_file(file)

    def test_file_without_content_type_passes(self):
        """Test that a file without content_type attribute passes type check."""
        file = Mock(spec=['size'])
        file.size = 1024 * 1024
        validate_pdf_file(file)

    def test_file_with_none_content_type_passes(self):
        """Test that a file with content_type=None passes type check."""
        file = Mock()
        file.size = 1024 * 1024
        file.content_type = None
        validate_pdf_file(file)

    # -------------------------------------------------------------------------
    # Oversized files
    # -------------------------------------------------------------------------

    def test_oversized_pdf_raises_validation_error(self):
        """Test that a PDF larger than 10 MB raises ValidationError."""
        file = Mock()
        file.size = 11 * 1024 * 1024  # 11 MB
        file.content_type = 'application/pdf'

        with pytest.raises(ValidationError) as exc_info:
            validate_pdf_file(file)

        assert 'size' in exc_info.value.params

    def test_one_byte_over_max_size_raises(self):
        """Test that a file one byte over 10 MB raises ValidationError."""
        file = Mock()
        file.size = 10 * 1024 * 1024 + 1
        file.content_type = 'application/pdf'

        with pytest.raises(ValidationError):
            validate_pdf_file(file)

    def test_oversized_file_error_includes_actual_size(self):
        """Test that the error message includes the actual file size."""
        file = Mock()
        file.size = 15 * 1024 * 1024  # 15 MB
        file.content_type = 'application/pdf'

        with pytest.raises(ValidationError) as exc_info:
            validate_pdf_file(file)

        assert exc_info.value.params['size'] == pytest.approx(15.0, rel=0.01)

    # -------------------------------------------------------------------------
    # Invalid content types
    # -------------------------------------------------------------------------

    def test_image_jpeg_type_raises_validation_error(self):
        """Test that image/jpeg content type raises ValidationError."""
        file = Mock()
        file.size = 1024 * 1024
        file.content_type = 'image/jpeg'

        with pytest.raises(ValidationError):
            validate_pdf_file(file)

    def test_text_plain_type_raises_validation_error(self):
        """Test that text/plain content type raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'text/plain'

        with pytest.raises(ValidationError):
            validate_pdf_file(file)

    def test_word_document_type_raises_validation_error(self):
        """Test that application/msword content type raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'application/msword'

        with pytest.raises(ValidationError):
            validate_pdf_file(file)

    def test_octet_stream_type_raises_validation_error(self):
        """Test that application/octet-stream raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'application/octet-stream'

        with pytest.raises(ValidationError):
            validate_pdf_file(file)

    def test_image_png_type_raises_validation_error(self):
        """Test that image/png content type raises ValidationError."""
        file = Mock()
        file.size = 1024
        file.content_type = 'image/png'

        with pytest.raises(ValidationError):
            validate_pdf_file(file)

    # -------------------------------------------------------------------------
    # Combined: size checked before content type
    # -------------------------------------------------------------------------

    def test_oversized_invalid_type_raises_size_error_first(self):
        """Test that oversized file with bad type raises size error first."""
        file = Mock()
        file.size = 11 * 1024 * 1024  # Over 10 MB limit
        file.content_type = 'image/jpeg'  # Also invalid type

        with pytest.raises(ValidationError) as exc_info:
            validate_pdf_file(file)

        # Size is checked first
        assert 'size' in exc_info.value.params
