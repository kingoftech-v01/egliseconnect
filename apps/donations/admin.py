"""Donation management admin configuration."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.core.admin import SoftDeleteModelAdmin, BaseModelAdmin

from .models import Donation, DonationCampaign, TaxReceipt


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
