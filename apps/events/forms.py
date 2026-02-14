"""Event forms — events, RSVP, rooms, bookings, templates, registration,
waitlist, volunteer needs, photos, surveys."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from .models import (
    Event, EventRSVP, Room, RoomBooking, EventTemplate,
    RegistrationForm as RegFormModel, RegistrationEntry,
    EventWaitlist, EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)


# ──────────────────────────────────────────────────────────────────────────────
# Event
# ──────────────────────────────────────────────────────────────────────────────

class EventForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type',
            'start_datetime', 'end_datetime', 'all_day',
            'location', 'location_address', 'is_online', 'online_link',
            'organizer', 'max_attendees', 'requires_rsvp', 'image',
            'is_published', 'is_recurring', 'recurrence_frequency',
            'recurrence_end_date', 'virtual_url', 'virtual_platform',
            'is_hybrid', 'campus', 'kiosk_mode_enabled',
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recurrence_end_date': forms.DateInput(attrs={'type': 'date'}),
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


# ──────────────────────────────────────────────────────────────────────────────
# Room / Booking
# ──────────────────────────────────────────────────────────────────────────────

class RoomForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'location', 'description', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class RoomBookingForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = RoomBooking
        fields = ['room', 'event', 'start_datetime', 'end_datetime', 'notes']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
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


# ──────────────────────────────────────────────────────────────────────────────
# Event Template
# ──────────────────────────────────────────────────────────────────────────────

class EventTemplateForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = [
            'name', 'event_type', 'default_duration',
            'default_description', 'default_capacity',
            'default_location', 'requires_rsvp',
        ]
        widgets = {
            'default_description': forms.Textarea(attrs={'rows': 3}),
        }


class EventFromTemplateForm(W3CRMFormMixin, forms.Form):
    """Form to create an event from a template — user provides date/time."""
    template = forms.ModelChoiceField(
        queryset=EventTemplate.objects.all(),
        label=_('Modèle'),
    )
    start_datetime = forms.DateTimeField(
        label=_('Date et heure de début'),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    title_override = forms.CharField(
        max_length=200, required=False, label=_('Titre (optionnel)'),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────────────

class RegistrationFormForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing a custom registration form definition."""
    class Meta:
        model = RegFormModel
        fields = ['event', 'title']


# ──────────────────────────────────────────────────────────────────────────────
# Volunteer Needs
# ──────────────────────────────────────────────────────────────────────────────

class EventVolunteerNeedForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = EventVolunteerNeed
        fields = ['position_name', 'required_count', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Photo Gallery
# ──────────────────────────────────────────────────────────────────────────────

class EventPhotoForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = EventPhoto
        fields = ['image', 'caption']


# ──────────────────────────────────────────────────────────────────────────────
# Survey
# ──────────────────────────────────────────────────────────────────────────────

class EventSurveyForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = EventSurvey
        fields = ['event', 'title', 'send_after_hours']
