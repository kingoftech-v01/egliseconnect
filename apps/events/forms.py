"""Events forms."""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Event, EventRSVP


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'start_datetime', 'end_datetime', 'all_day', 'location', 'location_address', 'is_online', 'online_link', 'organizer', 'max_attendees', 'requires_rsvp', 'image', 'is_published']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class RSVPForm(forms.ModelForm):
    class Meta:
        model = EventRSVP
        fields = ['status', 'guests', 'notes']
