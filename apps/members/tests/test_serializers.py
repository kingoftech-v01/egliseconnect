"""Tests for members serializers."""
import pytest

from apps.members.serializers import BirthdaySerializer, DirectoryMemberSerializer
from apps.members.models import DirectoryPrivacy

from .factories import MemberFactory


@pytest.mark.django_db
class TestBirthdaySerializerMissedLines:
    """Tests covering missed lines in BirthdaySerializer (lines 199, 202)."""

    def test_birth_day_none_when_no_birth_date(self):
        """get_birth_day returns None when birth_date is None (line 199)."""
        member = MemberFactory(birth_date=None)
        serializer = BirthdaySerializer(member)
        assert serializer.data['birth_day'] is None

    def test_birth_month_none_when_no_birth_date(self):
        """get_birth_month returns None when birth_date is None (line 202)."""
        member = MemberFactory(birth_date=None)
        serializer = BirthdaySerializer(member)
        assert serializer.data['birth_month'] is None

    def test_birth_day_and_month_with_date(self):
        """get_birth_day and get_birth_month return correct values."""
        from datetime import date
        member = MemberFactory(birth_date=date(1990, 6, 15))
        serializer = BirthdaySerializer(member)
        assert serializer.data['birth_day'] == 15
        assert serializer.data['birth_month'] == 6


@pytest.mark.django_db
class TestDirectoryMemberSerializerMissedLines:
    """Tests covering missed lines in DirectoryMemberSerializer (lines 229, 232, 235)."""

    def test_privacy_hides_email(self):
        """Email hidden when show_email is False (line 229)."""
        member = MemberFactory(email='visible@example.com')
        DirectoryPrivacy.objects.filter(member=member).update(show_email=False)
        member.refresh_from_db()
        # Need to select_related for privacy_settings
        from apps.members.models import Member
        member = Member.objects.select_related('privacy_settings').get(pk=member.pk)
        serializer = DirectoryMemberSerializer(member)
        assert serializer.data['email'] is None

    def test_privacy_hides_phone(self):
        """Phone hidden when show_phone is False (line 232)."""
        member = MemberFactory(phone='514-555-0000')
        DirectoryPrivacy.objects.filter(member=member).update(show_phone=False)
        from apps.members.models import Member
        member = Member.objects.select_related('privacy_settings').get(pk=member.pk)
        serializer = DirectoryMemberSerializer(member)
        assert serializer.data['phone'] is None

    def test_privacy_hides_photo(self):
        """Photo hidden when show_photo is False (line 235)."""
        member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=member).update(show_photo=False)
        from apps.members.models import Member
        member = Member.objects.select_related('privacy_settings').get(pk=member.pk)
        serializer = DirectoryMemberSerializer(member)
        assert serializer.data['photo'] is None

    def test_privacy_shows_all_when_enabled(self):
        """All fields visible when privacy allows them."""
        member = MemberFactory(email='show@example.com', phone='514-555-1234')
        DirectoryPrivacy.objects.filter(member=member).update(
            show_email=True, show_phone=True, show_photo=True
        )
        from apps.members.models import Member
        member = Member.objects.select_related('privacy_settings').get(pk=member.pk)
        serializer = DirectoryMemberSerializer(member)
        assert serializer.data['email'] == 'show@example.com'
        assert serializer.data['phone'] == '514-555-1234'
