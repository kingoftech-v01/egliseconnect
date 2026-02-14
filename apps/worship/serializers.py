"""Worship service API serializers."""
from rest_framework import serializers
from .models import (
    WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList,
    Sermon, SermonSeries, Song, Setlist, SetlistSong,
    VolunteerPreference, LiveStream, Rehearsal, RehearsalAttendee,
    SongRequest, SongRequestVote,
)


class WorshipServiceSerializer(serializers.ModelSerializer):
    """Serializer for WorshipService model."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    confirmation_rate = serializers.IntegerField(read_only=True)
    total_assignments = serializers.IntegerField(read_only=True)
    confirmed_assignments = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorshipService
        fields = '__all__'


class ServiceSectionSerializer(serializers.ModelSerializer):
    """Serializer for ServiceSection model."""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = ServiceSection
        fields = '__all__'


class ServiceAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ServiceAssignment model."""
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True, default=None)

    class Meta:
        model = ServiceAssignment
        fields = '__all__'


class EligibleMemberListSerializer(serializers.ModelSerializer):
    """Serializer for EligibleMemberList model."""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = EligibleMemberList
        fields = '__all__'

    def get_member_count(self, obj):
        return obj.members.count()


# ─── Sermon Serializers ──────────────────────────────────────────────────────


class SermonSeriesSerializer(serializers.ModelSerializer):
    """Serializer for SermonSeries model."""
    sermon_count = serializers.SerializerMethodField()

    class Meta:
        model = SermonSeries
        fields = '__all__'

    def get_sermon_count(self, obj):
        return obj.sermons.count()


class SermonSerializer(serializers.ModelSerializer):
    """Serializer for Sermon model."""
    speaker_name = serializers.CharField(source='speaker.full_name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    series_title = serializers.CharField(source='series.title', read_only=True, default=None)

    class Meta:
        model = Sermon
        fields = '__all__'


# ─── Song Serializers ────────────────────────────────────────────────────────


class SongSerializer(serializers.ModelSerializer):
    """Serializer for Song model."""
    song_key_display = serializers.CharField(source='get_song_key_display', read_only=True)

    class Meta:
        model = Song
        fields = '__all__'


class SetlistSongSerializer(serializers.ModelSerializer):
    """Serializer for SetlistSong model."""
    song_title = serializers.CharField(source='song.title', read_only=True)
    song_artist = serializers.CharField(source='song.artist', read_only=True)

    class Meta:
        model = SetlistSong
        fields = '__all__'


class SetlistSerializer(serializers.ModelSerializer):
    """Serializer for Setlist model."""
    songs = SetlistSongSerializer(many=True, read_only=True)
    service_date = serializers.DateField(source='service.date', read_only=True)

    class Meta:
        model = Setlist
        fields = '__all__'


# ─── Other Serializers ───────────────────────────────────────────────────────


class VolunteerPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for VolunteerPreference model."""
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = VolunteerPreference
        fields = '__all__'


class LiveStreamSerializer(serializers.ModelSerializer):
    """Serializer for LiveStream model."""
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = LiveStream
        fields = '__all__'


class RehearsalAttendeeSerializer(serializers.ModelSerializer):
    """Serializer for RehearsalAttendee model."""
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RehearsalAttendee
        fields = '__all__'


class RehearsalSerializer(serializers.ModelSerializer):
    """Serializer for Rehearsal model."""
    attendees = RehearsalAttendeeSerializer(many=True, read_only=True)

    class Meta:
        model = Rehearsal
        fields = '__all__'


class SongRequestSerializer(serializers.ModelSerializer):
    """Serializer for SongRequest model."""
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SongRequest
        fields = '__all__'


class CalendarEventSerializer(serializers.Serializer):
    """Serializer for calendar event data (FullCalendar compatible)."""
    id = serializers.UUIDField()
    title = serializers.CharField()
    start = serializers.CharField()
    end = serializers.CharField(required=False)
    url = serializers.CharField()
    color = serializers.CharField(required=False)
