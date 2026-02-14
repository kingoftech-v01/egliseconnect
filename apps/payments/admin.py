from django.contrib import admin
from .models import (
    StripeCustomer,
    OnlinePayment,
    RecurringDonation,
    GivingStatement,
    GivingGoal,
    SMSDonation,
    PaymentPlan,
    EmployerMatch,
    GivingCampaign,
    KioskSession,
)


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ['member', 'stripe_customer_id', 'created_at']
    search_fields = ['member__first_name', 'member__last_name', 'stripe_customer_id']
    raw_id_fields = ['member']


@admin.register(OnlinePayment)
class OnlinePaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'currency', 'status', 'donation_type', 'payment_method_type', 'created_at']
    list_filter = ['status', 'donation_type', 'currency', 'payment_method_type']
    search_fields = ['member__first_name', 'member__last_name', 'stripe_payment_intent_id']
    raw_id_fields = ['member', 'donation']
    date_hierarchy = 'created_at'


@admin.register(RecurringDonation)
class RecurringDonationAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'frequency', 'donation_type', 'is_active_subscription', 'created_at']
    list_filter = ['is_active_subscription', 'frequency', 'donation_type']
    search_fields = ['member__first_name', 'member__last_name', 'stripe_subscription_id']
    raw_id_fields = ['member']


@admin.register(GivingStatement)
class GivingStatementAdmin(admin.ModelAdmin):
    list_display = ['member', 'statement_type', 'period_start', 'period_end', 'total_amount', 'sent_at', 'generated_at']
    list_filter = ['statement_type', 'sent_at']
    search_fields = ['member__first_name', 'member__last_name']
    raw_id_fields = ['member']
    date_hierarchy = 'generated_at'
    readonly_fields = ['generated_at']


@admin.register(GivingGoal)
class GivingGoalAdmin(admin.ModelAdmin):
    list_display = ['member', 'year', 'target_amount', 'is_active', 'created_at']
    list_filter = ['year', 'is_active']
    search_fields = ['member__first_name', 'member__last_name']
    raw_id_fields = ['member']


@admin.register(SMSDonation)
class SMSDonationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'amount', 'member', 'processed', 'is_recurring', 'created_at']
    list_filter = ['processed', 'is_recurring']
    search_fields = ['phone_number', 'member__first_name', 'member__last_name']
    raw_id_fields = ['member']
    date_hierarchy = 'created_at'


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['member', 'total_amount', 'installment_amount', 'frequency', 'remaining_amount', 'status', 'created_at']
    list_filter = ['status', 'frequency']
    search_fields = ['member__first_name', 'member__last_name']
    raw_id_fields = ['member']
    date_hierarchy = 'created_at'


@admin.register(EmployerMatch)
class EmployerMatchAdmin(admin.ModelAdmin):
    list_display = ['member', 'employer_name', 'match_ratio', 'annual_cap', 'match_amount_received', 'created_at']
    search_fields = ['member__first_name', 'member__last_name', 'employer_name']
    raw_id_fields = ['member']


@admin.register(GivingCampaign)
class GivingCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'goal_amount', 'current_amount', 'start_date', 'end_date', 'is_year_end', 'is_active']
    list_filter = ['is_year_end', 'is_active']
    search_fields = ['name']
    date_hierarchy = 'start_date'


@admin.register(KioskSession)
class KioskSessionAdmin(admin.ModelAdmin):
    list_display = ['session_date', 'location', 'total_transactions', 'total_amount', 'reconciled', 'created_at']
    list_filter = ['reconciled']
    date_hierarchy = 'session_date'
