"""Serializers for payment models."""
from rest_framework import serializers
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


class StripeCustomerSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = StripeCustomer
        fields = ['id', 'member', 'member_name', 'stripe_customer_id']


class OnlinePaymentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    amount_display = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()

    class Meta:
        model = OnlinePayment
        fields = [
            'id', 'member', 'member_name', 'stripe_payment_intent_id',
            'amount', 'currency', 'status', 'donation_type',
            'campaign', 'receipt_email', 'stripe_receipt_url',
            'payment_method_type', 'amount_display', 'is_successful', 'created_at',
        ]


class RecurringDonationSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    amount_display = serializers.ReadOnlyField()

    class Meta:
        model = RecurringDonation
        fields = [
            'id', 'member', 'member_name', 'stripe_subscription_id',
            'amount', 'currency', 'frequency', 'donation_type',
            'next_payment_date', 'is_active_subscription',
            'cancelled_at', 'amount_display', 'created_at',
        ]


class CreatePaymentIntentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    donation_type = serializers.CharField(default='offering')
    campaign_id = serializers.UUIDField(required=False, allow_null=True)
    currency = serializers.ChoiceField(choices=['CAD', 'USD', 'EUR'], default='CAD')


class CreateRecurringSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    frequency = serializers.ChoiceField(choices=['weekly', 'monthly'], default='monthly')
    donation_type = serializers.CharField(default='tithe')


class UpdateRecurringSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    frequency = serializers.ChoiceField(choices=['weekly', 'monthly'], default='monthly')


class GivingStatementSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    is_sent = serializers.ReadOnlyField()

    class Meta:
        model = GivingStatement
        fields = [
            'id', 'member', 'member_name', 'period_start', 'period_end',
            'statement_type', 'total_amount', 'generated_at',
            'sent_at', 'is_sent', 'created_at',
        ]


class GivingGoalSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = GivingGoal
        fields = ['id', 'member', 'member_name', 'year', 'target_amount', 'created_at']


class SMSDonationSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = SMSDonation
        fields = [
            'id', 'phone_number', 'amount', 'member', 'member_name',
            'processed', 'stripe_charge_id', 'command_text',
            'is_recurring', 'frequency', 'created_at',
        ]

    def get_member_name(self, obj):
        return obj.member.full_name if obj.member else ''


class PaymentPlanSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    amount_paid = serializers.ReadOnlyField()

    class Meta:
        model = PaymentPlan
        fields = [
            'id', 'member', 'member_name', 'total_amount',
            'installment_amount', 'frequency', 'remaining_amount',
            'start_date', 'status', 'completed_at', 'donation_type',
            'progress_percentage', 'amount_paid', 'created_at',
        ]


class CreatePaymentPlanSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    installment_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    frequency = serializers.CharField(default='monthly')
    start_date = serializers.DateField()
    donation_type = serializers.CharField(default='offering')


class EmployerMatchSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = EmployerMatch
        fields = [
            'id', 'member', 'member_name', 'employer_name',
            'match_ratio', 'annual_cap', 'match_amount_received', 'created_at',
        ]


class GivingCampaignSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = GivingCampaign
        fields = [
            'id', 'name', 'description', 'goal_amount', 'current_amount',
            'start_date', 'end_date', 'is_year_end',
            'progress_percentage', 'is_ongoing', 'days_remaining', 'created_at',
        ]


class KioskSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KioskSession
        fields = [
            'id', 'session_date', 'location', 'total_transactions',
            'total_amount', 'reconciled', 'reconciled_at', 'notes', 'created_at',
        ]


class CryptoChargeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    currency = serializers.CharField(default='CAD')


class SMSWebhookSerializer(serializers.Serializer):
    """Serializer for incoming Twilio SMS webhook."""
    From = serializers.CharField()
    Body = serializers.CharField()
