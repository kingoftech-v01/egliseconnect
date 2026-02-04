"""
Members serializers - DRF serializers for member API.

Serializers:
- MemberSerializer: Full member serializer
- MemberListSerializer: Lightweight serializer for lists
- MemberCreateSerializer: For member creation
- MemberProfileSerializer: For profile updates
- BirthdaySerializer: For birthday lists
- FamilySerializer: Family serializer
- GroupSerializer: Group serializer
- GroupMembershipSerializer: Group membership serializer
- DirectoryPrivacySerializer: Privacy settings serializer
"""
from rest_framework import serializers

from .models import Member, Family, Group, GroupMembership, DirectoryPrivacy


# =============================================================================
# MEMBER SERIALIZERS
# =============================================================================

class MemberListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for member lists.

    Used for list views and search results.
    """

    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Member
        fields = [
            'id',
            'member_number',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'role',
            'role_display',
            'photo',
            'age',
            'is_active',
        ]


class MemberSerializer(serializers.ModelSerializer):
    """
    Full member serializer.

    Used for detail views. Includes all fields and related data.
    """

    full_name = serializers.CharField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    family_status_display = serializers.CharField(source='get_family_status_display', read_only=True)
    province_display = serializers.CharField(source='get_province_display', read_only=True)
    family_name = serializers.CharField(source='family.name', read_only=True, allow_null=True)
    groups = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id',
            'member_number',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'phone_secondary',
            'birth_date',
            'address',
            'city',
            'province',
            'province_display',
            'postal_code',
            'full_address',
            'photo',
            'role',
            'role_display',
            'family_status',
            'family_status_display',
            'family',
            'family_name',
            'joined_date',
            'baptism_date',
            'age',
            'groups',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['member_number', 'created_at', 'updated_at']

    def get_groups(self, obj):
        """Get list of groups the member belongs to."""
        memberships = obj.group_memberships.filter(is_active=True).select_related('group')
        return [
            {
                'id': m.group.id,
                'name': m.group.name,
                'role': m.role,
            }
            for m in memberships
        ]


class MemberCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for member creation.

    Handles validation and auto-generation of member number.
    """

    class Meta:
        model = Member
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'phone_secondary',
            'birth_date',
            'address',
            'city',
            'province',
            'postal_code',
            'photo',
            'family_status',
            'family',
        ]

    def create(self, validated_data):
        """Create member with auto-generated number."""
        member = Member.objects.create(**validated_data)
        # Create default privacy settings
        DirectoryPrivacy.objects.create(member=member)
        return member


class MemberProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for member profile updates.

    Members can only update their own non-sensitive fields.
    """

    class Meta:
        model = Member
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'phone_secondary',
            'birth_date',
            'address',
            'city',
            'province',
            'postal_code',
            'photo',
            'family_status',
        ]


class MemberAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for admin member management.

    Includes all fields including role and notes.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            'id',
            'member_number',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'phone_secondary',
            'birth_date',
            'address',
            'city',
            'province',
            'postal_code',
            'photo',
            'role',
            'family_status',
            'family',
            'joined_date',
            'baptism_date',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['member_number', 'created_at', 'updated_at']


class BirthdaySerializer(serializers.ModelSerializer):
    """
    Serializer for birthday lists.

    Lightweight serializer focused on birthday information.
    """

    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    birth_day = serializers.SerializerMethodField()
    birth_month = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id',
            'member_number',
            'full_name',
            'birth_date',
            'birth_day',
            'birth_month',
            'age',
            'photo',
            'phone',
            'email',
        ]

    def get_birth_day(self, obj):
        """Get day of birth."""
        return obj.birth_date.day if obj.birth_date else None

    def get_birth_month(self, obj):
        """Get month of birth."""
        return obj.birth_date.month if obj.birth_date else None


class DirectoryMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for directory listing.

    Respects privacy settings.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            'id',
            'member_number',
            'full_name',
            'email',
            'phone',
            'photo',
        ]

    def to_representation(self, instance):
        """Apply privacy settings to output."""
        data = super().to_representation(instance)

        # Check if privacy settings exist
        if hasattr(instance, 'privacy_settings'):
            privacy = instance.privacy_settings

            if not privacy.show_email:
                data['email'] = None

            if not privacy.show_phone:
                data['phone'] = None

            if not privacy.show_photo:
                data['photo'] = None

        return data


# =============================================================================
# FAMILY SERIALIZERS
# =============================================================================

class FamilySerializer(serializers.ModelSerializer):
    """
    Full family serializer.
    """

    member_count = serializers.IntegerField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    members = MemberListSerializer(many=True, read_only=True)

    class Meta:
        model = Family
        fields = [
            'id',
            'name',
            'address',
            'city',
            'province',
            'postal_code',
            'full_address',
            'notes',
            'member_count',
            'members',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class FamilyListSerializer(serializers.ModelSerializer):
    """
    Lightweight family serializer for lists.
    """

    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Family
        fields = [
            'id',
            'name',
            'city',
            'member_count',
        ]


# =============================================================================
# GROUP SERIALIZERS
# =============================================================================

class GroupSerializer(serializers.ModelSerializer):
    """
    Full group serializer.
    """

    member_count = serializers.IntegerField(read_only=True)
    group_type_display = serializers.CharField(source='get_group_type_display', read_only=True)
    leader_name = serializers.CharField(source='leader.full_name', read_only=True, allow_null=True)

    class Meta:
        model = Group
        fields = [
            'id',
            'name',
            'group_type',
            'group_type_display',
            'description',
            'leader',
            'leader_name',
            'meeting_day',
            'meeting_time',
            'meeting_location',
            'email',
            'member_count',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class GroupListSerializer(serializers.ModelSerializer):
    """
    Lightweight group serializer for lists.
    """

    member_count = serializers.IntegerField(read_only=True)
    group_type_display = serializers.CharField(source='get_group_type_display', read_only=True)

    class Meta:
        model = Group
        fields = [
            'id',
            'name',
            'group_type',
            'group_type_display',
            'member_count',
        ]


class GroupMembershipSerializer(serializers.ModelSerializer):
    """
    Group membership serializer.
    """

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = GroupMembership
        fields = [
            'id',
            'member',
            'member_name',
            'group',
            'group_name',
            'role',
            'role_display',
            'joined_date',
            'notes',
            'is_active',
        ]


# =============================================================================
# PRIVACY SERIALIZERS
# =============================================================================

class DirectoryPrivacySerializer(serializers.ModelSerializer):
    """
    Privacy settings serializer.
    """

    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = DirectoryPrivacy
        fields = [
            'id',
            'visibility',
            'visibility_display',
            'show_email',
            'show_phone',
            'show_address',
            'show_birth_date',
            'show_photo',
        ]
