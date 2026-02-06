"""Serializers for payment models."""
from rest_framework import serializers
from .models import StripeCustomer, OnlinePayment, RecurringDonation


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
            'amount_display', 'is_successful', 'created_at',
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


class CreateRecurringSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    frequency = serializers.ChoiceField(choices=['weekly', 'monthly'], default='monthly')
    donation_type = serializers.CharField(default='tithe')
