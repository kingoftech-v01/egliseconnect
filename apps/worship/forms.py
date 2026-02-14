"""Forms for worship service planning."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.core.constants import ServiceSectionType, SermonStatus, SongKey, SongRequestStatus
from apps.members.models import Member, Department, DepartmentTaskType
from .models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
    Sermon, SermonSeries, Song, Setlist, SetlistSong,
    VolunteerPreference, LiveStream, Rehearsal, SongRequest,
)


class WorshipServiceForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing worship services."""

    class Meta:
        model = WorshipService
        fields = ['date', 'start_time', 'end_time', 'duration_minutes',
                  'theme', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceSectionForm(W3CRMFormMixin, forms.ModelForm):
    """Form for adding/editing sections."""

    class Meta:
        model = ServiceSection
        fields = ['name', 'order', 'section_type', 'duration_minutes',
                  'department', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].required = False


class ServiceAssignmentForm(W3CRMFormMixin, forms.Form):
    """Form for assigning a member to a section."""

    member = forms.ModelChoiceField(
        queryset=Member.objects.filter(is_active=True),
        label=_('Membre'),
    )

    task_type = forms.ModelChoiceField(
        queryset=DepartmentTaskType.objects.none(),
        required=False,
        label=_('Type de tache'),
    )

    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label=_('Notes'),
    )

    def __init__(self, *args, section=None, **kwargs):
        super().__init__(*args, **kwargs)
        if section and section.department:
            self.fields['task_type'].queryset = (
                DepartmentTaskType.objects.filter(
                    department=section.department, is_active=True
                )
            )


class EligibleMemberListForm(W3CRMFormMixin, forms.ModelForm):
    """Form for managing which members are eligible for a section type."""

    class Meta:
        model = EligibleMemberList
        fields = ['section_type', 'members', 'department']
        widgets = {
            'members': forms.SelectMultiple(attrs={'size': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].queryset = Member.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].required = False


class ServiceDateRangeFilterForm(W3CRMFormMixin, forms.Form):
    """Filter form for service list date range."""

    date_from = forms.DateField(
        required=False,
        label=_('Du'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label=_('Au'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


# ─── Sermon Forms ────────────────────────────────────────────────────────────


class SermonForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing sermons."""

    class Meta:
        model = Sermon
        fields = [
            'title', 'speaker', 'scripture_reference', 'date', 'series',
            'audio_url', 'video_url', 'notes', 'status', 'duration_minutes',
            'service',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker'].queryset = Member.objects.filter(is_active=True)
        self.fields['speaker'].required = False
        self.fields['series'].required = False
        self.fields['service'].required = False


class SermonSeriesForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing sermon series."""

    class Meta:
        model = SermonSeries
        fields = ['title', 'description', 'start_date', 'end_date', 'image']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SermonFilterForm(W3CRMFormMixin, forms.Form):
    """Filter form for sermon archive."""

    speaker = forms.ModelChoiceField(
        queryset=Member.objects.filter(is_active=True),
        required=False,
        label=_('Predicateur'),
    )
    series = forms.ModelChoiceField(
        queryset=SermonSeries.objects.all(),
        required=False,
        label=_('Serie'),
    )
    date_from = forms.DateField(
        required=False,
        label=_('Du'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label=_('Au'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    q = forms.CharField(
        required=False,
        label=_('Rechercher'),
        widget=forms.TextInput(attrs={'placeholder': 'Titre, reference...'}),
    )


# ─── Song Forms ──────────────────────────────────────────────────────────────


class SongForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing songs."""

    class Meta:
        model = Song
        fields = [
            'title', 'artist', 'song_key', 'bpm', 'lyrics',
            'chord_chart', 'ccli_number', 'tags',
        ]
        widgets = {
            'lyrics': forms.Textarea(attrs={'rows': 10}),
            'chord_chart': forms.Textarea(attrs={
                'rows': 10,
                'style': 'font-family: monospace;',
            }),
            'tags': forms.TextInput(attrs={
                'placeholder': 'louange, francais, rapide',
            }),
        }


class SetlistForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing setlists."""

    class Meta:
        model = Setlist
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class SetlistSongForm(W3CRMFormMixin, forms.ModelForm):
    """Form for adding a song to a setlist."""

    class Meta:
        model = SetlistSong
        fields = ['song', 'order', 'key_override', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['key_override'].required = False


class SongSearchForm(W3CRMFormMixin, forms.Form):
    """Search form for songs."""

    q = forms.CharField(
        required=False,
        label=_('Rechercher'),
        widget=forms.TextInput(attrs={'placeholder': 'Titre, artiste...'}),
    )
    song_key = forms.ChoiceField(
        choices=[('', '---')] + list(SongKey.CHOICES),
        required=False,
        label=_('Tonalite'),
    )


# ─── Volunteer Preference Form ──────────────────────────────────────────────


class VolunteerPreferenceForm(W3CRMFormMixin, forms.ModelForm):
    """Form for editing volunteer scheduling preferences."""

    class Meta:
        model = VolunteerPreference
        fields = ['preferred_positions', 'max_services_per_month']
        widgets = {
            'preferred_positions': forms.TextInput(attrs={
                'placeholder': 'louange, predication, priere',
            }),
        }


# ─── LiveStream Forms ───────────────────────────────────────────────────────


class LiveStreamForm(W3CRMFormMixin, forms.ModelForm):
    """Form for managing live streams."""

    class Meta:
        model = LiveStream
        fields = ['service', 'platform', 'stream_url', 'recording_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recording_url'].required = False


# ─── Rehearsal Forms ─────────────────────────────────────────────────────────


class RehearsalForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing rehearsals."""

    class Meta:
        model = Rehearsal
        fields = ['service', 'date', 'start_time', 'end_time', 'location', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].required = False
        self.fields['end_time'].required = False


# ─── Song Request Forms ──────────────────────────────────────────────────────


class SongRequestForm(W3CRMFormMixin, forms.ModelForm):
    """Form for submitting a song request."""

    class Meta:
        model = SongRequest
        fields = ['song_title', 'artist', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class SongRequestModerationForm(W3CRMFormMixin, forms.Form):
    """Form for moderating a song request."""

    status = forms.ChoiceField(
        choices=SongRequestStatus.CHOICES,
        label=_('Statut'),
    )
    scheduled_date = forms.DateField(
        required=False,
        label=_('Date planifiee'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
