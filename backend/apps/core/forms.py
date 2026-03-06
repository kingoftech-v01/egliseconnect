"""Forms for core app: branding settings, webhook configuration, etc."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.core.models_extended import ChurchBranding, WebhookEndpoint


class ChurchBrandingForm(W3CRMFormMixin, forms.ModelForm):
    """Form for editing church branding settings."""

    class Meta:
        model = ChurchBranding
        fields = [
            'church_name', 'logo', 'favicon',
            'primary_color', 'secondary_color', 'accent_color',
            'address', 'phone', 'email', 'website',
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class WebhookEndpointForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing webhook endpoints."""

    events = forms.MultipleChoiceField(
        choices=WebhookEndpoint.WEBHOOK_EVENTS,
        widget=forms.CheckboxSelectMultiple,
        label=_('Événements'),
        help_text=_('Sélectionnez les événements qui déclencheront ce webhook'),
    )

    class Meta:
        model = WebhookEndpoint
        fields = ['name', 'url', 'secret', 'events', 'max_retries']
        widgets = {
            'secret': forms.PasswordInput(render_value=True, attrs={
                'placeholder': _('Clé secrète pour la signature HMAC-SHA256'),
            }),
        }

    def clean_events(self):
        """Ensure events is stored as a list."""
        return self.cleaned_data.get('events', [])
