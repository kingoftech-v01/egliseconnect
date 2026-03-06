"""Donation management admin configuration."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.core.admin import SoftDeleteModelAdmin, BaseModelAdmin

from .models import (
    Donation, DonationCampaign, TaxReceipt, FinanceDelegation,
    Pledge, PledgeFulfillment, GivingStatement, GivingGoal,
    DonationImport, DonationImportRow, MatchingCampaign, CryptoDonation,
)


@admin.register(Donation)
class DonationAdmin(SoftDeleteModelAdmin):
    """Admin for donations with payment and receipt tracking."""

    list_display = [
        'donation_number',
        'member',
        'amount',
        'donation_type',
        'payment_method',
        'date',
        'receipt_sent',
    ]

    list_filter = [
        'donation_type',
        'payment_method',
        'date',
        'receipt_sent',
        'campaign',
    ]

    search_fields = [
        'donation_number',
        'member__first_name',
        'member__last_name',
        'member__member_number',
    ]

    readonly_fields = [
        'id',
        'donation_number',
        'created_at',
        'updated_at',
        'deleted_at',
    ]

    autocomplete_fields = ['member', 'campaign', 'recorded_by']

    date_hierarchy = 'date'

    fieldsets = (
        (_('Don'), {
            'fields': (
                'donation_number',
                'member',
                'amount',
                'currency',
                'donation_type',
                'payment_method',
                'date',
            )
        }),
        (_('Campagne'), {
            'fields': ('campaign',),
            'classes': ('collapse',)
        }),
        (_('Détails du paiement'), {
            'fields': ('check_number', 'transaction_id'),
            'classes': ('collapse',)
        }),
        (_('Enregistrement'), {
            'fields': ('recorded_by', 'notes'),
        }),
        (_('Reçu'), {
            'fields': ('receipt_sent', 'receipt_sent_date'),
        }),
        (_('Statut'), {
            'fields': ('is_active', 'deleted_at'),
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DonationCampaign)
class DonationCampaignAdmin(BaseModelAdmin):
    """Admin for fundraising campaigns with goal tracking."""

    list_display = [
        'name',
        'goal_amount',
        'current_amount',
        'progress_percentage',
        'start_date',
        'end_date',
        'is_active',
    ]

    list_filter = ['is_active', 'start_date']

    search_fields = ['name', 'description']

    readonly_fields = [
        'id',
        'current_amount',
        'progress_percentage',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'image')
        }),
        (_('Objectif'), {
            'fields': ('goal_amount', 'current_amount', 'progress_percentage')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def current_amount(self, obj):
        return f'${obj.current_amount}'
    current_amount.short_description = _('Montant actuel')

    def progress_percentage(self, obj):
        return f'{obj.progress_percentage}%'
    progress_percentage.short_description = _('Progression')


@admin.register(TaxReceipt)
class TaxReceiptAdmin(BaseModelAdmin):
    """Admin for annual tax receipts."""

    list_display = [
        'receipt_number',
        'member',
        'year',
        'total_amount',
        'email_sent',
        'generated_at',
    ]

    list_filter = ['year', 'email_sent', 'generated_at']

    search_fields = [
        'receipt_number',
        'member__first_name',
        'member__last_name',
        'member_name',
    ]

    readonly_fields = [
        'id',
        'receipt_number',
        'member_name',
        'member_address',
        'generated_at',
        'created_at',
        'updated_at',
    ]

    autocomplete_fields = ['member', 'generated_by']

    fieldsets = (
        (None, {
            'fields': ('receipt_number', 'member', 'year', 'total_amount')
        }),
        (_('Informations du membre (au moment de la génération)'), {
            'fields': ('member_name', 'member_address'),
            'classes': ('collapse',)
        }),
        (_('Génération'), {
            'fields': ('generated_at', 'generated_by', 'pdf_file')
        }),
        (_('Envoi'), {
            'fields': ('email_sent', 'email_sent_date')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FinanceDelegation)
class FinanceDelegationAdmin(BaseModelAdmin):
    """Admin for finance delegations."""

    list_display = [
        'delegated_to', 'delegated_by', 'granted_at', 'revoked_at', 'is_active',
    ]
    list_filter = ['is_active', 'granted_at']
    search_fields = [
        'delegated_to__first_name', 'delegated_to__last_name',
        'delegated_by__first_name', 'delegated_by__last_name',
    ]
    readonly_fields = ['id', 'granted_at', 'created_at', 'updated_at']


@admin.register(Pledge)
class PledgeAdmin(BaseModelAdmin):
    """Admin for pledges and commitments."""

    list_display = [
        'member', 'amount', 'frequency', 'status',
        'campaign', 'start_date', 'end_date', 'progress_pct',
    ]
    list_filter = ['status', 'frequency', 'campaign']
    search_fields = [
        'member__first_name', 'member__last_name',
        'member__member_number',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['member', 'campaign']

    def progress_pct(self, obj):
        return f'{obj.progress_percentage}%'
    progress_pct.short_description = _('Progression')


@admin.register(PledgeFulfillment)
class PledgeFulfillmentAdmin(BaseModelAdmin):
    """Admin for pledge fulfillments."""

    list_display = ['pledge', 'donation', 'amount', 'date']
    list_filter = ['date']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(GivingStatement)
class GivingStatementAdmin(BaseModelAdmin):
    """Admin for giving statements."""

    list_display = [
        'member', 'year', 'period', 'total_amount',
        'generated_at', 'emailed_at',
    ]
    list_filter = ['year', 'period']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['id', 'generated_at', 'created_at', 'updated_at']
    autocomplete_fields = ['member']


@admin.register(GivingGoal)
class GivingGoalAdmin(BaseModelAdmin):
    """Admin for giving goals."""

    list_display = ['member', 'year', 'target_amount', 'progress_pct']
    list_filter = ['year']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['member']

    def progress_pct(self, obj):
        return f'{obj.progress_percentage}%'
    progress_pct.short_description = _('Progression')


@admin.register(DonationImport)
class DonationImportAdmin(BaseModelAdmin):
    """Admin for donation imports."""

    list_display = [
        'id', 'status', 'total_rows', 'imported_count',
        'skipped_count', 'imported_by', 'created_at',
    ]
    list_filter = ['status', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DonationImportRow)
class DonationImportRowAdmin(BaseModelAdmin):
    """Admin for import rows."""

    list_display = ['donation_import', 'row_number', 'status', 'error_message']
    list_filter = ['status']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(MatchingCampaign)
class MatchingCampaignAdmin(BaseModelAdmin):
    """Admin for matching campaigns."""

    list_display = [
        'matcher_name', 'campaign', 'match_ratio',
        'match_cap', 'matched_total', 'match_progress_pct',
    ]
    search_fields = ['matcher_name', 'campaign__name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def match_progress_pct(self, obj):
        return f'{obj.match_progress_percentage}%'
    match_progress_pct.short_description = _('Progression jumelage')


@admin.register(CryptoDonation)
class CryptoDonationAdmin(BaseModelAdmin):
    """Admin for crypto donations."""

    list_display = [
        'member', 'crypto_type', 'amount_crypto',
        'amount_cad', 'status', 'created_at',
    ]
    list_filter = ['crypto_type', 'status']
    search_fields = ['member__first_name', 'member__last_name', 'coinbase_charge_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
