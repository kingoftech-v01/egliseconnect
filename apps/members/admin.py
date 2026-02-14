"""Member management admin configuration."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.core.admin import SoftDeleteModelAdmin, BaseModelAdmin

from .models import (
    Member, Family, Group, GroupMembership, DirectoryPrivacy,
    Department, DepartmentMembership, DepartmentTaskType,
    DisciplinaryAction, ProfileModificationRequest, MemberRole,
    Child, PastoralCare, BackgroundCheck, ImportHistory,
    MemberMergeLog, CustomField, CustomFieldValue, MemberEngagementScore,
)


class GroupMembershipInline(admin.TabularInline):
    """Inline for managing member's group assignments."""
    model = GroupMembership
    extra = 0
    autocomplete_fields = ['member', 'group']


class DirectoryPrivacyInline(admin.StackedInline):
    """Inline for member privacy settings."""
    model = DirectoryPrivacy
    can_delete = False


class FamilyMemberInline(admin.TabularInline):
    """Inline for viewing family members."""
    model = Member
    extra = 0
    fields = ['member_number', 'first_name', 'last_name', 'role']
    readonly_fields = ['member_number']


class ChildInline(admin.TabularInline):
    """Inline for viewing family children."""
    model = Child
    extra = 0
    fields = ['first_name', 'last_name', 'date_of_birth', 'is_active']


class DepartmentMembershipInline(admin.TabularInline):
    """Inline for department memberships."""
    model = DepartmentMembership
    extra = 0
    autocomplete_fields = ['member']


class CustomFieldValueInline(admin.TabularInline):
    """Inline for custom field values on member."""
    model = CustomFieldValue
    extra = 0


@admin.register(Member)
class MemberAdmin(SoftDeleteModelAdmin):
    """Admin for church members with contact and role management."""

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

    inlines = [DirectoryPrivacyInline, GroupMembershipInline, CustomFieldValueInline]

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('Nom complet')
    full_name.admin_order_field = 'last_name'


@admin.register(Family)
class FamilyAdmin(BaseModelAdmin):
    """Admin for family units."""

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

    inlines = [FamilyMemberInline, ChildInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = _('Membres')


@admin.register(Group)
class GroupAdmin(BaseModelAdmin):
    """Admin for ministry groups and committees."""

    list_display = ['name', 'group_type', 'leader', 'lifecycle_stage', 'member_count', 'is_active']
    list_filter = ['group_type', 'lifecycle_stage', 'is_active']
    search_fields = ['name', 'description', 'leader__first_name', 'leader__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['leader']

    fieldsets = (
        (None, {
            'fields': ('name', 'group_type', 'description', 'leader', 'lifecycle_stage')
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


@admin.register(GroupMembership)
class GroupMembershipAdmin(BaseModelAdmin):
    """Admin for member-group relationships."""

    list_display = ['member', 'group', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'group', 'is_active', 'joined_date']
    search_fields = ['member__first_name', 'member__last_name', 'group__name']
    autocomplete_fields = ['member', 'group']


@admin.register(DirectoryPrivacy)
class DirectoryPrivacyAdmin(BaseModelAdmin):
    """Admin for member directory visibility settings."""

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


@admin.register(Department)
class DepartmentAdmin(BaseModelAdmin):
    """Admin for departments."""

    list_display = ['name', 'leader', 'member_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    autocomplete_fields = ['leader', 'parent_department']
    inlines = [DepartmentMembershipInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = _('Membres')


@admin.register(DepartmentMembership)
class DepartmentMembershipAdmin(BaseModelAdmin):
    """Admin for department memberships."""

    list_display = ['member', 'department', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['member__first_name', 'member__last_name', 'department__name']
    autocomplete_fields = ['member', 'department']


@admin.register(DepartmentTaskType)
class DepartmentTaskTypeAdmin(BaseModelAdmin):
    """Admin for department task types."""

    list_display = ['name', 'department', 'max_assignees', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['name']


@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(BaseModelAdmin):
    """Admin for disciplinary actions."""

    list_display = ['member', 'action_type', 'approval_status', 'start_date', 'end_date', 'is_active']
    list_filter = ['action_type', 'approval_status', 'is_active']
    search_fields = ['member__first_name', 'member__last_name', 'reason']
    autocomplete_fields = ['member', 'created_by', 'approved_by']


@admin.register(ProfileModificationRequest)
class ProfileModificationRequestAdmin(BaseModelAdmin):
    """Admin for modification requests."""

    list_display = ['target_member', 'requested_by', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['target_member__first_name', 'target_member__last_name']


@admin.register(MemberRole)
class MemberRoleAdmin(BaseModelAdmin):
    """Admin for additional member roles."""

    list_display = ['member', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['member__first_name', 'member__last_name']
    autocomplete_fields = ['member']


@admin.register(Child)
class ChildAdmin(BaseModelAdmin):
    """Admin for child/dependent profiles."""

    list_display = ['first_name', 'last_name', 'family', 'date_of_birth', 'is_active']
    list_filter = ['is_active']
    search_fields = ['first_name', 'last_name', 'family__name']


@admin.register(PastoralCare)
class PastoralCareAdmin(BaseModelAdmin):
    """Admin for pastoral care records."""

    list_display = ['member', 'care_type', 'assigned_to', 'date', 'status', 'follow_up_date']
    list_filter = ['care_type', 'status', 'is_active']
    search_fields = ['member__first_name', 'member__last_name', 'notes']
    autocomplete_fields = ['member', 'assigned_to']


@admin.register(BackgroundCheck)
class BackgroundCheckAdmin(BaseModelAdmin):
    """Admin for background check records."""

    list_display = ['member', 'status', 'check_date', 'expiry_date', 'provider']
    list_filter = ['status', 'is_active']
    search_fields = ['member__first_name', 'member__last_name', 'reference_number']
    autocomplete_fields = ['member']


@admin.register(ImportHistory)
class ImportHistoryAdmin(BaseModelAdmin):
    """Admin for import history."""

    list_display = ['filename', 'imported_by', 'total_rows', 'success_count', 'error_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['filename']
    readonly_fields = ['errors_json']


@admin.register(MemberMergeLog)
class MemberMergeLogAdmin(BaseModelAdmin):
    """Admin for merge audit trail."""

    list_display = ['primary_member', 'merged_by', 'created_at']
    search_fields = ['primary_member__first_name', 'primary_member__last_name']
    readonly_fields = ['merged_member_data']


@admin.register(CustomField)
class CustomFieldAdmin(BaseModelAdmin):
    """Admin for custom field definitions."""

    list_display = ['name', 'field_type', 'is_required', 'order', 'is_active']
    list_filter = ['field_type', 'is_required', 'is_active']
    search_fields = ['name']


@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(BaseModelAdmin):
    """Admin for custom field values."""

    list_display = ['member', 'custom_field', 'value']
    search_fields = ['member__first_name', 'member__last_name', 'custom_field__name']
    autocomplete_fields = ['member', 'custom_field']


@admin.register(MemberEngagementScore)
class MemberEngagementScoreAdmin(BaseModelAdmin):
    """Admin for engagement scores."""

    list_display = ['member', 'total_score', 'attendance_score', 'giving_score',
                    'volunteering_score', 'group_score', 'calculated_at']
    list_filter = ['is_active']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['calculated_at']
