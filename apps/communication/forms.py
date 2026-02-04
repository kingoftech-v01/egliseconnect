"""Communication forms."""
from django import forms
from .models import Newsletter


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['subject', 'content', 'content_plain', 'send_to_all', 'target_groups']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'content_plain': forms.Textarea(attrs={'rows': 5}),
        }
