"""Worship admin configuration with enhanced list views and inlines."""
from django.contrib import admin
from .models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
    Sermon, SermonSeries, Song, Setlist, SetlistSong,
    VolunteerPreference, LiveStream, Rehearsal, RehearsalAttendee,
    SongRequest, SongRequestVote,
)


class ServiceSectionInline(admin.TabularInline):
    """Inline for sections within a service."""
    model = ServiceSection
    extra = 0
    fields = ['order', 'name', 'section_type', 'duration_minutes', 'department', 'notes']
    ordering = ['order']


class ServiceAssignmentInline(admin.TabularInline):
    """Inline for assignments within a section."""
    model = ServiceAssignment
    extra = 0
    fields = ['member', 'task_type', 'status', 'responded_at', 'notes']
    readonly_fields = ['responded_at']
    autocomplete_fields = ['member']


class SetlistSongInline(admin.TabularInline):
    """Inline for songs in a setlist."""
    model = SetlistSong
    extra = 0
    fields = ['order', 'song', 'key_override', 'notes']
    ordering = ['order']


class RehearsalAttendeeInline(admin.TabularInline):
    """Inline for rehearsal attendees."""
    model = RehearsalAttendee
    extra = 0
    fields = ['member', 'status']
    autocomplete_fields = ['member']


class SermonInline(admin.TabularInline):
    """Inline for sermons in a series."""
    model = Sermon
    extra = 0
    fields = ['title', 'speaker', 'date', 'status']
    readonly_fields = ['date']


@admin.register(WorshipService)
class WorshipServiceAdmin(admin.ModelAdmin):
    """Admin for WorshipService with rich list display and filters."""
    list_display = [
        'date', 'start_time', 'theme', 'status',
        'total_assignments', 'confirmation_rate_display', 'created_by',
    ]
    list_filter = ['status', 'date']
    search_fields = ['theme', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ServiceSectionInline]
    ordering = ['-date', '-start_time']

    def confirmation_rate_display(self, obj):
        return f'{obj.confirmation_rate}%'
    confirmation_rate_display.short_description = 'Taux confirm.'

    def total_assignments(self, obj):
        return obj.total_assignments
    total_assignments.short_description = 'Assignations'


@admin.register(ServiceSection)
class ServiceSectionAdmin(admin.ModelAdmin):
    """Admin for ServiceSection with filters and inlines."""
    list_display = ['name', 'service', 'order', 'section_type', 'duration_minutes', 'department']
    list_filter = ['section_type', 'service__date']
    search_fields = ['name', 'notes', 'service__theme']
    ordering = ['service', 'order']
    inlines = [ServiceAssignmentInline]


@admin.register(ServiceAssignment)
class ServiceAssignmentAdmin(admin.ModelAdmin):
    """Admin for ServiceAssignment with filters and search."""
    list_display = ['member', 'section', 'status', 'task_type', 'responded_at']
    list_filter = ['status', 'section__service__date']
    search_fields = [
        'member__first_name', 'member__last_name',
        'section__name', 'notes',
    ]
    readonly_fields = ['responded_at', 'created_at', 'updated_at']
    autocomplete_fields = ['member']


@admin.register(EligibleMemberList)
class EligibleMemberListAdmin(admin.ModelAdmin):
    """Admin for EligibleMemberList with filters."""
    list_display = ['section_type', 'department', 'member_count']
    list_filter = ['section_type']
    filter_horizontal = ['members']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Membres'


# ─── Sermon Admin ────────────────────────────────────────────────────────────


@admin.register(SermonSeries)
class SermonSeriesAdmin(admin.ModelAdmin):
    """Admin for SermonSeries."""
    list_display = ['title', 'start_date', 'end_date', 'sermon_count']
    list_filter = ['start_date']
    search_fields = ['title', 'description']
    inlines = [SermonInline]

    def sermon_count(self, obj):
        return obj.sermons.count()
    sermon_count.short_description = 'Predications'


@admin.register(Sermon)
class SermonAdmin(admin.ModelAdmin):
    """Admin for Sermon."""
    list_display = ['title', 'speaker', 'date', 'status', 'series', 'duration_minutes']
    list_filter = ['status', 'date', 'series']
    search_fields = ['title', 'scripture_reference', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['speaker']


# ─── Song Admin ──────────────────────────────────────────────────────────────


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    """Admin for Song."""
    list_display = ['title', 'artist', 'song_key', 'bpm', 'play_count', 'last_played', 'ccli_number']
    list_filter = ['song_key']
    search_fields = ['title', 'artist', 'ccli_number', 'tags']
    readonly_fields = ['play_count', 'last_played', 'created_at', 'updated_at']


@admin.register(Setlist)
class SetlistAdmin(admin.ModelAdmin):
    """Admin for Setlist."""
    list_display = ['service', 'song_count']
    search_fields = ['service__theme']
    inlines = [SetlistSongInline]

    def song_count(self, obj):
        return obj.songs.count()
    song_count.short_description = 'Chants'


@admin.register(SetlistSong)
class SetlistSongAdmin(admin.ModelAdmin):
    """Admin for SetlistSong."""
    list_display = ['song', 'setlist', 'order', 'key_override']
    list_filter = ['setlist__service__date']


# ─── Volunteer Preference Admin ──────────────────────────────────────────────


@admin.register(VolunteerPreference)
class VolunteerPreferenceAdmin(admin.ModelAdmin):
    """Admin for VolunteerPreference."""
    list_display = ['member', 'preferred_positions', 'max_services_per_month']
    search_fields = ['member__first_name', 'member__last_name']
    autocomplete_fields = ['member']


# ─── Live Stream Admin ───────────────────────────────────────────────────────


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    """Admin for LiveStream."""
    list_display = ['service', 'platform', 'stream_url', 'viewer_count']
    list_filter = ['platform']
    search_fields = ['stream_url']


# ─── Rehearsal Admin ─────────────────────────────────────────────────────────


@admin.register(Rehearsal)
class RehearsalAdmin(admin.ModelAdmin):
    """Admin for Rehearsal."""
    list_display = ['date', 'start_time', 'location', 'service', 'attendee_count']
    list_filter = ['date']
    search_fields = ['location', 'notes']
    date_hierarchy = 'date'
    inlines = [RehearsalAttendeeInline]

    def attendee_count(self, obj):
        return obj.attendees.count()
    attendee_count.short_description = 'Participants'


@admin.register(RehearsalAttendee)
class RehearsalAttendeeAdmin(admin.ModelAdmin):
    """Admin for RehearsalAttendee."""
    list_display = ['member', 'rehearsal', 'status']
    list_filter = ['status']
    autocomplete_fields = ['member']


# ─── Song Request Admin ──────────────────────────────────────────────────────


@admin.register(SongRequest)
class SongRequestAdmin(admin.ModelAdmin):
    """Admin for SongRequest."""
    list_display = ['song_title', 'artist', 'requested_by', 'votes', 'status', 'scheduled_date']
    list_filter = ['status']
    search_fields = ['song_title', 'artist']
    readonly_fields = ['votes', 'created_at', 'updated_at']


@admin.register(SongRequestVote)
class SongRequestVoteAdmin(admin.ModelAdmin):
    """Admin for SongRequestVote."""
    list_display = ['song_request', 'member']
    search_fields = ['song_request__song_title', 'member__first_name', 'member__last_name']
