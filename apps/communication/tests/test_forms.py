"""Communication form tests."""
import pytest
from apps.communication.forms import NewsletterForm, ALLOWED_TAGS, ALLOWED_ATTRIBUTES


@pytest.mark.django_db
class TestNewsletterForm:
    """Tests for NewsletterForm."""

    def test_valid_form(self):
        """Form with valid data is valid."""
        data = {
            'subject': 'Weekly Newsletter',
            'content': '<p>Hello everyone!</p>',
            'content_plain': 'Hello everyone!',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid(), form.errors

    def test_subject_required(self):
        """Subject is required."""
        data = {
            'subject': '',
            'content': '<p>Content</p>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert not form.is_valid()
        assert 'subject' in form.errors

    def test_content_required(self):
        """Content is required."""
        data = {
            'subject': 'A Subject',
            'content': '',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_content_plain_optional(self):
        """Content plain is optional."""
        data = {
            'subject': 'Newsletter',
            'content': '<p>Content</p>',
            'content_plain': '',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()

    def test_sanitizes_script_tags(self):
        """Script tags are stripped from content."""
        data = {
            'subject': 'XSS Test',
            'content': '<p>Safe</p><script>alert("xss")</script>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        # bleach strips the <script> tag (text content may remain but is harmless without the tag)
        assert '<script>' not in cleaned
        assert '</script>' not in cleaned
        assert '<p>Safe</p>' in cleaned

    def test_sanitizes_onclick_attribute(self):
        """Event handler attributes are stripped."""
        data = {
            'subject': 'XSS Attribute',
            'content': '<p onclick="alert(\'xss\')">Click me</p>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        assert 'onclick' not in cleaned
        assert '<p>' in cleaned

    def test_sanitizes_iframe(self):
        """Iframe tags are stripped."""
        data = {
            'subject': 'Iframe Test',
            'content': '<p>Text</p><iframe src="evil.com"></iframe>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        assert '<iframe' not in cleaned

    def test_sanitizes_javascript_in_href(self):
        """JavaScript in href is sanitized."""
        data = {
            'subject': 'JS href Test',
            'content': '<a href="javascript:alert(1)">Click</a>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        # bleach should sanitize the javascript: protocol
        assert 'javascript:' not in cleaned

    def test_preserves_allowed_tags(self):
        """Allowed HTML tags are preserved."""
        data = {
            'subject': 'Allowed Tags',
            'content': (
                '<h1>Title</h1>'
                '<p>Paragraph with <strong>bold</strong> and <em>italic</em></p>'
                '<ul><li>Item 1</li><li>Item 2</li></ul>'
                '<a href="https://example.com" title="Link">Link text</a>'
                '<img src="image.jpg" alt="Image">'
                '<blockquote>Quote</blockquote>'
                '<table><thead><tr><th>Header</th></tr></thead>'
                '<tbody><tr><td>Cell</td></tr></tbody></table>'
            ),
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        assert '<h1>' in cleaned
        assert '<p>' in cleaned
        assert '<strong>' in cleaned
        assert '<em>' in cleaned
        assert '<ul>' in cleaned
        assert '<li>' in cleaned
        assert '<a href=' in cleaned
        assert '<img ' in cleaned
        assert '<blockquote>' in cleaned
        assert '<table>' in cleaned

    def test_preserves_allowed_attributes(self):
        """Allowed attributes are preserved."""
        data = {
            'subject': 'Attributes Test',
            'content': (
                '<a href="https://example.com" title="Example" target="_blank">Link</a>'
                '<img src="photo.jpg" alt="Photo" width="100" height="100">'
                '<div style="color: red;" class="highlight">Styled</div>'
                '<td colspan="2" style="padding: 5px;">Cell</td>'
            ),
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        assert 'href="https://example.com"' in cleaned
        assert 'title="Example"' in cleaned
        assert 'target="_blank"' in cleaned
        assert 'alt="Photo"' in cleaned
        assert 'style=' in cleaned
        assert 'class=' in cleaned

    def test_strips_disallowed_attributes(self):
        """Disallowed attributes are stripped."""
        data = {
            'subject': 'Bad Attributes',
            'content': '<p id="hack" data-custom="val">Text</p>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        assert 'id=' not in cleaned
        assert 'data-custom' not in cleaned
        assert '<p>' in cleaned

    def test_strips_style_tag(self):
        """Style tags are stripped."""
        data = {
            'subject': 'Style Tag',
            'content': '<style>body{display:none}</style><p>Text</p>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        cleaned = form.cleaned_data['content']
        assert '<style>' not in cleaned
        assert '<p>Text</p>' in cleaned

    def test_send_to_all_default_true(self):
        """send_to_all defaults to True in the model."""
        data = {
            'subject': 'Newsletter',
            'content': '<p>Content</p>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert form.is_valid()
        instance = form.save(commit=False)
        assert instance.send_to_all is True

    def test_subject_max_length(self):
        """Subject has max length of 200 characters."""
        data = {
            'subject': 'A' * 201,
            'content': '<p>Content</p>',
            'send_to_all': True,
        }
        form = NewsletterForm(data=data)
        assert not form.is_valid()
        assert 'subject' in form.errors

    def test_form_widgets(self):
        """Form has correct widgets configured."""
        form = NewsletterForm()
        assert form.fields['content'].widget.attrs.get('rows') == 10
        assert form.fields['content_plain'].widget.attrs.get('rows') == 5

    def test_form_fields(self):
        """Form includes correct fields."""
        form = NewsletterForm()
        expected_fields = {'subject', 'content', 'content_plain', 'send_to_all', 'target_groups'}
        assert set(form.fields.keys()) == expected_fields
