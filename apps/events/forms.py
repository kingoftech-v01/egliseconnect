"""Event forms."""
from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.mixins import W3CRMFormMixin
from .models import Event, EventRSVP


class EventForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'start_datetime', 'end_datetime', 'all_day', 'location', 'location_address', 'is_online', 'online_link', 'organizer', 'max_attendees', 'requires_rsvp', 'image', 'is_published']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')
        if start and end and end <= start:
            raise forms.ValidationError(
                _('La date de fin doit être après la date de début.')
            )
        return cleaned_data


class RSVPForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = EventRSVP
        fields = ['status', 'guests', 'notes']
