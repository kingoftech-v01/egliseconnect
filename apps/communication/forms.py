"""Communication forms."""
import bleach
from django import forms
from .models import Newsletter

# Safe HTML subset for newsletter content (used by serializers too)
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div',
    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
    'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody',
    'td', 'th', 'thead', 'tr', 'u', 'ul',
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height', 'style'],
    'td': ['colspan', 'rowspan', 'style'],
    'th': ['colspan', 'rowspan', 'style'],
    'div': ['style', 'class'],
    'span': ['style', 'class'],
    'p': ['style', 'class'],
    'h1': ['style', 'class'],
    'h2': ['style', 'class'],
    'h3': ['style', 'class'],
}


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['subject', 'content', 'content_plain', 'send_to_all', 'target_groups']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'content_plain': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_content(self):
        """Sanitize HTML to prevent XSS."""
        content = self.cleaned_data.get('content', '')
        return bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,
        )
