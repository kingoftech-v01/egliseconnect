"""
Members admin - Admin configuration for member management.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.core.admin import SoftDeleteModelAdmin, BaseModelAdmin

from .models import Member, Family, Group, GroupMembership, DirectoryPrivacy


# =============================================================================
# INLINE ADMINS
# =============================================================================

class GroupMembershipInline(admin.TabularInline):
    """Inline admin for group memberships."""
    model = GroupMembership
    extra = 0
    autocomplete_fields = ['member', 'group']


class DirectoryPrivacyInline(admin.StackedInline):
    """Inline admin for privacy settings."""
    model = DirectoryPrivacy
    can_delete = False


class FamilyMemberInline(admin.TabularInline):
    """Inline admin for family members."""
    model = Member
    extra = 0
    fields = ['member_number', 'first_name', 'last_name', 'role']
    readonly_fields = ['member_number']


# =============================================================================
# MEMBER ADMIN
# =============================================================================

@admin.register(Member)
class MemberAdmin(SoftDeleteModelAdmin):
    """Admin for Member model."""

    list_display = [
        'member_number',
        'full_name',
        'email',
        'phone',
        'role',
        'family_status',
        'is_active',
    ]

    list_filter = [
        'role',
        'family_status',
        'province',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'member_number',
        'first_name',
        'last_name',
        'email',
        'phone',
    ]

    readonly_fields = [
        'id',
        'member_number',
        'created_at',
        'updated_at',
        'deleted_at',
    ]

    autocomplete_fields = ['user', 'family']

    fieldsets = (
        (_('Identification'), {
            'fields': ('member_number', 'user', 'photo')
        }),
        (_('Informations personnelles'), {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'phone_secondary',
                'birth_date',
            )
        }),
        (_('Adresse'), {
            'fields': ('address', 'city', 'province', 'postal_code')
        }),
        (_('Église'), {
            'fields': (
                'role',
                'family_status',
                'family',
                'joined_date',
                'baptism_date',
            )
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('is_active', 'deleted_at')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [DirectoryPrivacyInline, GroupMembershipInline]

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('Nom complet')
    full_name.admin_order_field = 'last_name'


# =============================================================================
# FAMILY ADMIN
# =============================================================================

@admin.register(Family)
class FamilyAdmin(BaseModelAdmin):
    """Admin for Family model."""

    list_display = ['name', 'city', 'province', 'member_count', 'is_active']
    list_filter = ['province', 'is_active']
    search_fields = ['name', 'city']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        (_('Adresse'), {
            'fields': ('address', 'city', 'province', 'postal_code')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [FamilyMemberInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = _('Membres')


# =============================================================================
# GROUP ADMIN
# =============================================================================

@admin.register(Group)
class GroupAdmin(BaseModelAdmin):
    """Admin for Group model."""

    list_display = ['name', 'group_type', 'leader', 'member_count', 'is_active']
    list_filter = ['group_type', 'is_active']
    search_fields = ['name', 'description', 'leader__first_name', 'leader__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['leader']

    fieldsets = (
        (None, {
            'fields': ('name', 'group_type', 'description', 'leader')
        }),
        (_('Réunions'), {
            'fields': ('meeting_day', 'meeting_time', 'meeting_location')
        }),
        (_('Contact'), {
            'fields': ('email',)
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [GroupMembershipInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = _('Membres')


# =============================================================================
# GROUP MEMBERSHIP ADMIN
# =============================================================================

@admin.register(GroupMembership)
class GroupMembershipAdmin(BaseModelAdmin):
    """Admin for GroupMembership model."""

    list_display = ['member', 'group', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'group', 'is_active', 'joined_date']
    search_fields = ['member__first_name', 'member__last_name', 'group__name']
    autocomplete_fields = ['member', 'group']


# =============================================================================
# DIRECTORY PRIVACY ADMIN
# =============================================================================

@admin.register(DirectoryPrivacy)
class DirectoryPrivacyAdmin(BaseModelAdmin):
    """Admin for DirectoryPrivacy model."""

    list_display = [
        'member',
        'visibility',
        'show_email',
        'show_phone',
        'show_address',
    ]
    list_filter = ['visibility']
    search_fields = ['member__first_name', 'member__last_name']
    autocomplete_fields = ['member']
