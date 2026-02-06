from django.contrib import admin
from .models import StripeCustomer, OnlinePayment, RecurringDonation


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ['member', 'stripe_customer_id', 'created_at']
    search_fields = ['member__first_name', 'member__last_name', 'stripe_customer_id']
    raw_id_fields = ['member']


@admin.register(OnlinePayment)
class OnlinePaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'currency', 'status', 'donation_type', 'created_at']
    list_filter = ['status', 'donation_type', 'currency']
    search_fields = ['member__first_name', 'member__last_name', 'stripe_payment_intent_id']
    raw_id_fields = ['member', 'donation']
    date_hierarchy = 'created_at'


@admin.register(RecurringDonation)
class RecurringDonationAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'frequency', 'donation_type', 'is_active_subscription', 'created_at']
    list_filter = ['is_active_subscription', 'frequency', 'donation_type']
    search_fields = ['member__first_name', 'member__last_name', 'stripe_subscription_id']
    raw_id_fields = ['member']
