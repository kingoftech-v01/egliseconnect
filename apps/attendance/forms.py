"""Forms for attendance app."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.core.constants import AttendanceSessionType, VisitorSource
from .models import (
    AttendanceSession, ChildCheckIn, KioskConfig,
    NFCTag, GeoFence, VisitorInfo,
)


class AttendanceSessionForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing attendance sessions."""

    class Meta:
        model = AttendanceSession
        fields = [
            'name', 'session_type', 'date', 'start_time',
            'end_time', 'duration_minutes', 'event',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class SessionFilterForm(W3CRMFormMixin, forms.Form):
    """Filter form for session list (session_type + date range)."""
    session_type = forms.ChoiceField(
        choices=[('', _('Tous les types'))] + list(AttendanceSessionType.CHOICES),
        required=False,
        label=_('Type de session'),
    )
    date_from = forms.DateField(
        required=False,
        label=_('Date de début'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label=_('Date de fin'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


class ChildCheckInForm(W3CRMFormMixin, forms.Form):
    """Form for checking in a child."""
    child_id = forms.UUIDField(widget=forms.HiddenInput())
    session_id = forms.UUIDField(widget=forms.HiddenInput())


class ChildCheckOutForm(W3CRMFormMixin, forms.Form):
    """Form for checking out a child using security code."""
    security_code = forms.CharField(
        max_length=6,
        min_length=6,
        label=_('Code de sécurité'),
        widget=forms.TextInput(attrs={
            'placeholder': '000000',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        }),
    )


class KioskConfigForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing kiosk configuration."""

    class Meta:
        model = KioskConfig
        fields = ['name', 'location', 'admin_pin', 'auto_timeout_seconds', 'session']
        widgets = {
            'admin_pin': forms.PasswordInput(render_value=True, attrs={
                'placeholder': _('PIN numérique'),
            }),
        }


class KioskPinForm(W3CRMFormMixin, forms.Form):
    """Form for kiosk admin PIN verification."""
    admin_pin = forms.CharField(
        max_length=10,
        label=_("PIN d'administration"),
        widget=forms.PasswordInput(attrs={
            'placeholder': _('Entrer le PIN'),
            'inputmode': 'numeric',
            'autocomplete': 'off',
        }),
    )


class NFCTagForm(W3CRMFormMixin, forms.ModelForm):
    """Form for registering/editing NFC tags."""

    class Meta:
        model = NFCTag
        fields = ['member', 'tag_id']


class GeoFenceForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing geo-fences."""

    class Meta:
        model = GeoFence
        fields = ['name', 'latitude', 'longitude', 'radius_meters']
        widgets = {
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }


class VisitorInfoForm(W3CRMFormMixin, forms.ModelForm):
    """Form for capturing visitor information."""

    class Meta:
        model = VisitorInfo
        fields = ['name', 'email', 'phone', 'source', 'session', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class MemberSearchForm(W3CRMFormMixin, forms.Form):
    """Form for searching members by name (scanner/kiosk)."""
    query = forms.CharField(
        max_length=200,
        label=_('Rechercher un membre'),
        widget=forms.TextInput(attrs={
            'placeholder': _('Nom ou prénom...'),
            'autocomplete': 'off',
        }),
    )
