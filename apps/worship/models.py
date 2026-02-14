"""Worship service planning models."""
from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.constants import (
    WorshipServiceStatus, ServiceSectionType, AssignmentStatus,
    SermonStatus, SongKey, SongRequestStatus, LiveStreamPlatform,
    RehearsalAttendeeStatus,
)


class WorshipService(BaseModel):
    """A planned worship service (culte)."""

    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(verbose_name=_('Heure de debut'))
    end_time = models.TimeField(
        blank=True, null=True, verbose_name=_('Heure de fin')
    )
    duration_minutes = models.PositiveIntegerField(
        default=120, verbose_name=_('Duree (minutes)')
    )

    status = models.CharField(
        max_length=20,
        choices=WorshipServiceStatus.CHOICES,
        default=WorshipServiceStatus.DRAFT,
        verbose_name=_('Statut'),
    )

    theme = models.CharField(
        max_length=300, blank=True, verbose_name=_('Theme')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    created_by = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_services',
        verbose_name=_('Cree par'),
    )

    validation_deadline = models.DateField(
        blank=True, null=True,
        verbose_name=_('Date limite de validation'),
        help_text=_('14 jours avant le culte par defaut'),
    )

    event = models.ForeignKey(
        'events.Event',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='worship_services',
        verbose_name=_('Evenement associe'),
    )

    class Meta:
        verbose_name = _('Culte')
        verbose_name_plural = _('Cultes')
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'Culte du {self.date:%d/%m/%Y} \u00e0 {self.start_time:%H:%M}'

    def save(self, *args, **kwargs):
        if not self.validation_deadline:
            self.validation_deadline = self.date - timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def confirmation_rate(self):
        """Percentage of assignments that are confirmed."""
        total = ServiceAssignment.objects.filter(
            section__service=self
        ).count()
        if total == 0:
            return 0
        confirmed = ServiceAssignment.objects.filter(
            section__service=self,
            status=AssignmentStatus.CONFIRMED,
        ).count()
        return int((confirmed / total) * 100)

    @property
    def total_assignments(self):
        return ServiceAssignment.objects.filter(section__service=self).count()

    @property
    def confirmed_assignments(self):
        return ServiceAssignment.objects.filter(
            section__service=self, status=AssignmentStatus.CONFIRMED
        ).count()

    @property
    def planning_checklist(self):
        """Return a dict of planning readiness checks."""
        sections = self.sections.all()
        total_sections = sections.count()
        sections_with_assignments = 0
        for s in sections:
            if s.assignments.exists():
                sections_with_assignments += 1
        total_assign = self.total_assignments
        confirmed = self.confirmed_assignments
        return {
            'has_sections': total_sections > 0,
            'all_sections_filled': total_sections > 0 and sections_with_assignments == total_sections,
            'all_assigned': total_assign > 0,
            'all_confirmed': total_assign > 0 and confirmed == total_assign,
            'ready': (
                total_sections > 0
                and sections_with_assignments == total_sections
                and total_assign > 0
                and confirmed == total_assign
            ),
        }


class ServiceSection(BaseModel):
    """A section/segment within a worship service."""

    service = models.ForeignKey(
        WorshipService,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('Culte'),
    )

    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    order = models.PositiveIntegerField(verbose_name=_('Ordre'))
    duration_minutes = models.PositiveIntegerField(
        default=15, verbose_name=_('Duree (minutes)')
    )

    section_type = models.CharField(
        max_length=30,
        choices=ServiceSectionType.CHOICES,
        default=ServiceSectionType.OTHER,
        verbose_name=_('Type de section'),
    )

    department = models.ForeignKey(
        'members.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='service_sections',
        verbose_name=_('Departement responsable'),
    )

    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Section de culte')
        verbose_name_plural = _('Sections de culte')
        ordering = ['service', 'order']
        unique_together = ['service', 'order']

    def __str__(self):
        return f'{self.order}. {self.name}'


class ServiceAssignment(BaseModel):
    """Assignment of a member to a section of a worship service."""

    section = models.ForeignKey(
        ServiceSection,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Section'),
    )

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='service_assignments',
        verbose_name=_('Membre'),
    )

    task_type = models.ForeignKey(
        'members.DepartmentTaskType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='service_assignments',
        verbose_name=_('Type de tache'),
    )

    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.CHOICES,
        default=AssignmentStatus.ASSIGNED,
        verbose_name=_('Statut'),
    )

    responded_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Repondu le')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    reminder_5days_sent = models.BooleanField(default=False)
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Assignation')
        verbose_name_plural = _('Assignations')
        unique_together = ['section', 'member']

    def __str__(self):
        return f'{self.member.full_name} \u2192 {self.section.name}'


class EligibleMemberList(BaseModel):
    """Defines which members are eligible for a specific section type."""

    section_type = models.CharField(
        max_length=30,
        choices=ServiceSectionType.CHOICES,
        unique=True,
        verbose_name=_('Type de section'),
    )

    members = models.ManyToManyField(
        'members.Member',
        blank=True,
        related_name='eligible_for_sections',
        verbose_name=_('Membres eligibles'),
    )

    department = models.ForeignKey(
        'members.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='eligible_lists',
        verbose_name=_('Departement'),
    )

    class Meta:
        verbose_name = _("Liste d'eligibilite")
        verbose_name_plural = _("Listes d'eligibilite")

    def __str__(self):
        return f'Eligibles: {self.get_section_type_display()}'


# ─── P1: Sermon/Message Management ──────────────────────────────────────────


class SermonSeries(BaseModel):
    """A series of sermons grouped by theme."""

    title = models.CharField(max_length=300, verbose_name=_('Titre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    start_date = models.DateField(verbose_name=_('Date de debut'))
    end_date = models.DateField(
        blank=True, null=True, verbose_name=_('Date de fin')
    )
    image = models.ImageField(
        upload_to='worship/series/', blank=True, null=True,
        verbose_name=_('Image'),
    )

    class Meta:
        verbose_name = _('Serie de predications')
        verbose_name_plural = _('Series de predications')
        ordering = ['-start_date']

    def __str__(self):
        return self.title


class Sermon(BaseModel):
    """A sermon/message delivered during a worship service."""

    title = models.CharField(max_length=300, verbose_name=_('Titre'))
    speaker = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sermons',
        verbose_name=_('Predicateur'),
    )
    scripture_reference = models.CharField(
        max_length=300, blank=True, verbose_name=_('Reference biblique')
    )
    date = models.DateField(verbose_name=_('Date'))
    series = models.ForeignKey(
        SermonSeries,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sermons',
        verbose_name=_('Serie'),
    )
    audio_url = models.URLField(
        blank=True, verbose_name=_('URL audio')
    )
    video_url = models.URLField(
        blank=True, verbose_name=_('URL video')
    )
    notes = models.TextField(
        blank=True, verbose_name=_('Notes / Plan')
    )
    status = models.CharField(
        max_length=20,
        choices=SermonStatus.CHOICES,
        default=SermonStatus.DRAFT,
        verbose_name=_('Statut'),
    )
    duration_minutes = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Duree (minutes)')
    )
    service = models.ForeignKey(
        WorshipService,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sermons',
        verbose_name=_('Culte associe'),
    )

    class Meta:
        verbose_name = _('Predication')
        verbose_name_plural = _('Predications')
        ordering = ['-date']

    def __str__(self):
        return self.title


# ─── P1: Song/Setlist Management ────────────────────────────────────────────


class Song(BaseModel):
    """A song in the worship song database."""

    title = models.CharField(max_length=300, verbose_name=_('Titre'))
    artist = models.CharField(
        max_length=300, blank=True, verbose_name=_('Artiste')
    )
    song_key = models.CharField(
        max_length=5,
        choices=SongKey.CHOICES,
        blank=True,
        verbose_name=_('Tonalite'),
    )
    bpm = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('BPM')
    )
    lyrics = models.TextField(blank=True, verbose_name=_('Paroles'))
    chord_chart = models.TextField(
        blank=True, verbose_name=_('Grille d\'accords')
    )
    ccli_number = models.CharField(
        max_length=20, blank=True, verbose_name=_('Numero CCLI')
    )
    tags = models.TextField(
        blank=True, verbose_name=_('Tags'),
        help_text=_('Tags separes par des virgules'),
    )
    last_played = models.DateField(
        blank=True, null=True, verbose_name=_('Derniere utilisation')
    )
    play_count = models.PositiveIntegerField(
        default=0, verbose_name=_('Nombre de fois jouee')
    )

    class Meta:
        verbose_name = _('Chant')
        verbose_name_plural = _('Chants')
        ordering = ['title']

    def __str__(self):
        if self.artist:
            return f'{self.title} - {self.artist}'
        return self.title


class Setlist(BaseModel):
    """A setlist of songs for a specific worship service."""

    service = models.OneToOneField(
        WorshipService,
        on_delete=models.CASCADE,
        related_name='setlist',
        verbose_name=_('Culte'),
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Liste de chants')
        verbose_name_plural = _('Listes de chants')

    def __str__(self):
        return f'Setlist - {self.service}'


class SetlistSong(BaseModel):
    """A song in a setlist with ordering and optional transposition."""

    setlist = models.ForeignKey(
        Setlist,
        on_delete=models.CASCADE,
        related_name='songs',
        verbose_name=_('Liste de chants'),
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='setlist_appearances',
        verbose_name=_('Chant'),
    )
    order = models.PositiveIntegerField(verbose_name=_('Ordre'))
    key_override = models.CharField(
        max_length=5, blank=True,
        choices=SongKey.CHOICES,
        verbose_name=_('Tonalite (transposition)'),
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Chant dans la liste')
        verbose_name_plural = _('Chants dans la liste')
        ordering = ['setlist', 'order']
        unique_together = ['setlist', 'order']

    def __str__(self):
        return f'{self.order}. {self.song.title}'


# ─── P2: Volunteer Auto-Scheduling ──────────────────────────────────────────


class VolunteerPreference(BaseModel):
    """Scheduling preferences for a worship volunteer."""

    member = models.OneToOneField(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='worship_preference',
        verbose_name=_('Membre'),
    )
    preferred_positions = models.CharField(
        max_length=500, blank=True,
        verbose_name=_('Positions preferees'),
        help_text=_('Types de section separes par des virgules'),
    )
    blackout_dates = models.JSONField(
        default=list, blank=True,
        verbose_name=_('Dates indisponibles'),
        help_text=_('Liste de dates au format YYYY-MM-DD'),
    )
    max_services_per_month = models.PositiveIntegerField(
        default=4,
        verbose_name=_('Maximum de cultes par mois'),
    )

    class Meta:
        verbose_name = _('Preference de volontaire')
        verbose_name_plural = _('Preferences de volontaires')

    def __str__(self):
        return f'Preferences: {self.member.full_name}'


# ─── P3: Live Streaming Integration ─────────────────────────────────────────


class LiveStream(BaseModel):
    """Live stream information for a worship service."""

    service = models.ForeignKey(
        WorshipService,
        on_delete=models.CASCADE,
        related_name='livestreams',
        verbose_name=_('Culte'),
    )
    platform = models.CharField(
        max_length=20,
        choices=LiveStreamPlatform.CHOICES,
        default=LiveStreamPlatform.YOUTUBE,
        verbose_name=_('Plateforme'),
    )
    stream_url = models.URLField(verbose_name=_('URL du flux'))
    start_time = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Debut du flux')
    )
    end_time = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Fin du flux')
    )
    viewer_count = models.PositiveIntegerField(
        default=0, verbose_name=_('Nombre de spectateurs')
    )
    recording_url = models.URLField(
        blank=True, verbose_name=_('URL de l\'enregistrement')
    )

    class Meta:
        verbose_name = _('Diffusion en direct')
        verbose_name_plural = _('Diffusions en direct')
        ordering = ['-start_time']

    def __str__(self):
        return f'{self.get_platform_display()} - {self.service}'


# ─── P3: Rehearsal Scheduling ────────────────────────────────────────────────


class Rehearsal(BaseModel):
    """A worship team rehearsal session."""

    service = models.ForeignKey(
        WorshipService,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='rehearsals',
        verbose_name=_('Culte associe'),
    )
    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(verbose_name=_('Heure de debut'))
    end_time = models.TimeField(
        blank=True, null=True, verbose_name=_('Heure de fin')
    )
    location = models.CharField(
        max_length=300, blank=True, verbose_name=_('Lieu')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta:
        verbose_name = _('Repetition')
        verbose_name_plural = _('Repetitions')
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'Repetition du {self.date:%d/%m/%Y}'


class RehearsalAttendee(BaseModel):
    """RSVP record for a rehearsal attendee."""

    rehearsal = models.ForeignKey(
        Rehearsal,
        on_delete=models.CASCADE,
        related_name='attendees',
        verbose_name=_('Repetition'),
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='rehearsal_attendances',
        verbose_name=_('Membre'),
    )
    status = models.CharField(
        max_length=20,
        choices=RehearsalAttendeeStatus.CHOICES,
        default=RehearsalAttendeeStatus.INVITED,
        verbose_name=_('Statut'),
    )

    class Meta:
        verbose_name = _('Participant a la repetition')
        verbose_name_plural = _('Participants aux repetitions')
        unique_together = ['rehearsal', 'member']

    def __str__(self):
        return f'{self.member.full_name} - {self.rehearsal}'


# ─── P3: Congregation Song Requests ─────────────────────────────────────────


class SongRequest(BaseModel):
    """A song request from a congregation member."""

    requested_by = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='song_requests',
        verbose_name=_('Demande par'),
    )
    song_title = models.CharField(
        max_length=300, verbose_name=_('Titre du chant')
    )
    artist = models.CharField(
        max_length=300, blank=True, verbose_name=_('Artiste')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    votes = models.PositiveIntegerField(
        default=0, verbose_name=_('Votes')
    )
    status = models.CharField(
        max_length=20,
        choices=SongRequestStatus.CHOICES,
        default=SongRequestStatus.PENDING,
        verbose_name=_('Statut'),
    )
    scheduled_date = models.DateField(
        blank=True, null=True,
        verbose_name=_('Date planifiee'),
    )

    class Meta:
        verbose_name = _('Demande de chant')
        verbose_name_plural = _('Demandes de chants')
        ordering = ['-votes', '-created_at']

    def __str__(self):
        return f'{self.song_title} (par {self.requested_by.full_name})'


class SongRequestVote(BaseModel):
    """Tracks which members have voted for a song request."""

    song_request = models.ForeignKey(
        SongRequest,
        on_delete=models.CASCADE,
        related_name='vote_records',
        verbose_name=_('Demande de chant'),
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='song_request_votes',
        verbose_name=_('Membre'),
    )

    class Meta:
        verbose_name = _('Vote de demande de chant')
        verbose_name_plural = _('Votes de demandes de chants')
        unique_together = ['song_request', 'member']

    def __str__(self):
        return f'{self.member.full_name} -> {self.song_request.song_title}'
