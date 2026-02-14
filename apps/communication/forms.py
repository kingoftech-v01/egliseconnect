"""Communication forms."""
import bleach
from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.mixins import W3CRMFormMixin
from .models import (
    Newsletter, SMSMessage, SMSTemplate, EmailTemplate,
    Automation, AutomationStep, DirectMessage, GroupChat,
)

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


class NewsletterForm(W3CRMFormMixin, forms.ModelForm):
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


class SMSComposeForm(W3CRMFormMixin, forms.ModelForm):
    """Form for composing a single SMS message."""

    class Meta:
        model = SMSMessage
        fields = ['recipient_member', 'phone_number', 'body', 'template']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4, 'maxlength': 1600}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            # Try to get from member
            member = self.cleaned_data.get('recipient_member')
            if member and member.phone:
                return member.phone
            raise forms.ValidationError(_('Un numero de telephone est requis.'))
        return phone


class SMSBulkForm(W3CRMFormMixin, forms.Form):
    """Form for sending bulk SMS to a group."""
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'maxlength': 1600}),
        label=_('Message'),
    )
    template = forms.ModelChoiceField(
        queryset=SMSTemplate.objects.filter(is_active=True),
        required=False,
        label=_('Modele'),
    )
    send_to_all = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Envoyer a tous les membres'),
    )


class SMSTemplateForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing SMS templates."""

    class Meta:
        model = SMSTemplate
        fields = ['name', 'body_template', 'is_active']
        widgets = {
            'body_template': forms.Textarea(attrs={'rows': 4}),
        }


class EmailTemplateForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing email templates."""

    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject_template', 'body_html_template', 'category', 'is_active']
        widgets = {
            'body_html_template': forms.Textarea(attrs={'rows': 10}),
        }

    def clean_body_html_template(self):
        content = self.cleaned_data.get('body_html_template', '')
        return bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,
        )


class AutomationForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing automations."""

    class Meta:
        model = Automation
        fields = ['name', 'description', 'trigger_type', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class AutomationStepForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing automation steps."""

    class Meta:
        model = AutomationStep
        fields = ['order', 'delay_days', 'subject', 'body', 'channel']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class DirectMessageForm(W3CRMFormMixin, forms.ModelForm):
    """Form for sending a direct message."""

    class Meta:
        model = DirectMessage
        fields = ['recipient', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }


class GroupChatForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating a group chat."""

    class Meta:
        model = GroupChat
        fields = ['name', 'members']


class GroupChatMessageForm(W3CRMFormMixin, forms.Form):
    """Form for posting a message to a group chat."""
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Message'),
    )
