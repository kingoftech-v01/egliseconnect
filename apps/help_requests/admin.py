"""Help Requests admin."""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import (
    HelpRequest, HelpRequestCategory, HelpRequestComment,
    PastoralCare, PrayerRequest, CareTeam, CareTeamMember,
    BenevolenceRequest, BenevolenceFund,
    MealTrain, MealSignup,
    CrisisProtocol, CrisisResource,
)


@admin.register(HelpRequestCategory)
class HelpRequestCategoryAdmin(BaseModelAdmin):
    list_display = ['name', 'name_fr', 'icon', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'name_fr']
    ordering = ['order', 'name']


class HelpRequestCommentInline(admin.TabularInline):
    model = HelpRequestComment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(HelpRequest)
class HelpRequestAdmin(BaseModelAdmin):
    list_display = [
        'request_number', 'title', 'member', 'category',
        'urgency', 'status', 'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'urgency', 'category', 'is_confidential', 'created_at']
    search_fields = ['request_number', 'title', 'description', 'member__first_name', 'member__last_name']
    readonly_fields = ['request_number', 'created_at', 'updated_at', 'resolved_at']
    raw_id_fields = ['member', 'assigned_to']
    inlines = [HelpRequestCommentInline]

    fieldsets = (
        (None, {
            'fields': ('request_number', 'member', 'category', 'title', 'description')
        }),
        ('Status', {
            'fields': ('status', 'urgency', 'assigned_to', 'is_confidential')
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HelpRequestComment)
class HelpRequestCommentAdmin(BaseModelAdmin):
    list_display = ['help_request', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['content', 'help_request__request_number']
    raw_id_fields = ['help_request', 'author']


# ─── Pastoral Care Admin ─────────────────────────────────────────────────────


@admin.register(PastoralCare)
class PastoralCareAdmin(BaseModelAdmin):
    list_display = ['care_type', 'member', 'assigned_to', 'date', 'status', 'follow_up_date']
    list_filter = ['care_type', 'status', 'created_at']
    search_fields = ['member__first_name', 'member__last_name', 'notes']
    raw_id_fields = ['member', 'assigned_to', 'created_by']
    date_hierarchy = 'date'


# ─── Prayer Request Admin ────────────────────────────────────────────────────


@admin.register(PrayerRequest)
class PrayerRequestAdmin(BaseModelAdmin):
    list_display = ['title', 'member', 'is_anonymous', 'is_public', 'status', 'is_approved', 'created_at']
    list_filter = ['status', 'is_anonymous', 'is_public', 'is_approved', 'created_at']
    search_fields = ['title', 'description']
    raw_id_fields = ['member']

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'member')
        }),
        ('Visibility', {
            'fields': ('is_anonymous', 'is_public', 'is_approved')
        }),
        ('Status', {
            'fields': ('status', 'answered_at', 'testimony')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ─── Care Team Admin ─────────────────────────────────────────────────────────


class CareTeamMemberInline(admin.TabularInline):
    model = CareTeamMember
    extra = 0
    raw_id_fields = ['member']


@admin.register(CareTeam)
class CareTeamAdmin(BaseModelAdmin):
    list_display = ['name', 'leader', 'created_at']
    search_fields = ['name']
    raw_id_fields = ['leader']
    inlines = [CareTeamMemberInline]


@admin.register(CareTeamMember)
class CareTeamMemberAdmin(BaseModelAdmin):
    list_display = ['team', 'member', 'joined_at']
    list_filter = ['team']
    raw_id_fields = ['team', 'member']


# ─── Benevolence Admin ───────────────────────────────────────────────────────


@admin.register(BenevolenceFund)
class BenevolenceFundAdmin(BaseModelAdmin):
    list_display = ['name', 'total_balance', 'is_active']
    search_fields = ['name']


@admin.register(BenevolenceRequest)
class BenevolenceRequestAdmin(BaseModelAdmin):
    list_display = [
        'member', 'fund', 'amount_requested', 'amount_granted',
        'status', 'approved_by', 'disbursed_at', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['member__first_name', 'member__last_name', 'reason']
    raw_id_fields = ['member', 'fund', 'approved_by']


# ─── Meal Train Admin ────────────────────────────────────────────────────────


class MealSignupInline(admin.TabularInline):
    model = MealSignup
    extra = 0
    raw_id_fields = ['volunteer']


@admin.register(MealTrain)
class MealTrainAdmin(BaseModelAdmin):
    list_display = ['recipient', 'reason', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['recipient__first_name', 'recipient__last_name', 'reason']
    raw_id_fields = ['recipient']
    inlines = [MealSignupInline]


@admin.register(MealSignup)
class MealSignupAdmin(BaseModelAdmin):
    list_display = ['meal_train', 'volunteer', 'date', 'confirmed']
    list_filter = ['confirmed', 'date']
    raw_id_fields = ['meal_train', 'volunteer']


# ─── Crisis Admin ────────────────────────────────────────────────────────────


@admin.register(CrisisProtocol)
class CrisisProtocolAdmin(BaseModelAdmin):
    list_display = ['title', 'protocol_type', 'is_active']
    list_filter = ['protocol_type', 'is_active']
    search_fields = ['title']


@admin.register(CrisisResource)
class CrisisResourceAdmin(BaseModelAdmin):
    list_display = ['title', 'category', 'url', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description']
