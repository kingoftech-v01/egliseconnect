"""
Donations serializers - DRF serializers for donation API.

Serializers:
- DonationSerializer: Full donation serializer
- DonationListSerializer: Lightweight for lists
- DonationCreateSerializer: For creating donations
- DonationCampaignSerializer: Campaign serializer
- TaxReceiptSerializer: Tax receipt serializer
"""
from rest_framework import serializers

from .models import Donation, DonationCampaign, TaxReceipt


# =============================================================================
# DONATION SERIALIZERS
# =============================================================================

class DonationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for donation lists.
    """

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    donation_type_display = serializers.CharField(source='get_donation_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)

    class Meta:
        model = Donation
        fields = [
            'id',
            'donation_number',
            'member',
            'member_name',
            'amount',
            'donation_type',
            'donation_type_display',
            'payment_method',
            'payment_method_display',
            'campaign',
            'campaign_name',
            'date',
            'receipt_sent',
        ]


class DonationSerializer(serializers.ModelSerializer):
    """
    Full donation serializer.
    """

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    member_number = serializers.CharField(source='member.member_number', read_only=True)
    donation_type_display = serializers.CharField(source='get_donation_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)
    recorded_by_name = serializers.CharField(source='recorded_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = Donation
        fields = [
            'id',
            'donation_number',
            'member',
            'member_name',
            'member_number',
            'amount',
            'donation_type',
            'donation_type_display',
            'payment_method',
            'payment_method_display',
            'campaign',
            'campaign_name',
            'date',
            'notes',
            'check_number',
            'transaction_id',
            'recorded_by',
            'recorded_by_name',
            'receipt_sent',
            'receipt_sent_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'donation_number',
            'created_at',
            'updated_at',
        ]


class DonationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating online donations.

    Member is set automatically from the request.
    """

    class Meta:
        model = Donation
        fields = [
            'amount',
            'donation_type',
            'campaign',
            'notes',
        ]

    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class PhysicalDonationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for recording physical donations.

    Used by treasurer.
    """

    class Meta:
        model = Donation
        fields = [
            'member',
            'amount',
            'donation_type',
            'payment_method',
            'date',
            'campaign',
            'check_number',
            'notes',
        ]

    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value

    def validate(self, data):
        """Validate check number for check payments."""
        if data.get('payment_method') == 'check' and not data.get('check_number'):
            raise serializers.ValidationError({
                'check_number': "Le numéro de chèque est requis."
            })
        return data


class MemberDonationHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for member's donation history.
    """

    donation_type_display = serializers.CharField(source='get_donation_type_display', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)

    class Meta:
        model = Donation
        fields = [
            'id',
            'donation_number',
            'amount',
            'donation_type',
            'donation_type_display',
            'campaign',
            'campaign_name',
            'date',
        ]


# =============================================================================
# CAMPAIGN SERIALIZERS
# =============================================================================

class DonationCampaignSerializer(serializers.ModelSerializer):
    """
    Full campaign serializer.
    """

    current_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    progress_percentage = serializers.IntegerField(read_only=True)
    is_ongoing = serializers.BooleanField(read_only=True)
    donation_count = serializers.SerializerMethodField()

    class Meta:
        model = DonationCampaign
        fields = [
            'id',
            'name',
            'description',
            'goal_amount',
            'current_amount',
            'progress_percentage',
            'start_date',
            'end_date',
            'image',
            'is_ongoing',
            'donation_count',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_donation_count(self, obj):
        """Get number of donations for this campaign."""
        return obj.donations.filter(is_active=True).count()


class DonationCampaignListSerializer(serializers.ModelSerializer):
    """
    Lightweight campaign serializer for lists.
    """

    current_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    progress_percentage = serializers.IntegerField(read_only=True)
    is_ongoing = serializers.BooleanField(read_only=True)

    class Meta:
        model = DonationCampaign
        fields = [
            'id',
            'name',
            'goal_amount',
            'current_amount',
            'progress_percentage',
            'start_date',
            'end_date',
            'is_ongoing',
        ]


# =============================================================================
# TAX RECEIPT SERIALIZERS
# =============================================================================

class TaxReceiptSerializer(serializers.ModelSerializer):
    """
    Full tax receipt serializer.
    """

    member_full_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = TaxReceipt
        fields = [
            'id',
            'receipt_number',
            'member',
            'member_full_name',
            'year',
            'total_amount',
            'member_name',
            'member_address',
            'generated_at',
            'generated_by',
            'pdf_file',
            'email_sent',
            'email_sent_date',
        ]
        read_only_fields = [
            'receipt_number',
            'generated_at',
            'member_name',
            'member_address',
        ]


class TaxReceiptListSerializer(serializers.ModelSerializer):
    """
    Lightweight tax receipt serializer for lists.
    """

    member_full_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = TaxReceipt
        fields = [
            'id',
            'receipt_number',
            'member',
            'member_full_name',
            'year',
            'total_amount',
            'email_sent',
        ]


# =============================================================================
# SUMMARY SERIALIZERS
# =============================================================================

class DonationSummarySerializer(serializers.Serializer):
    """
    Serializer for donation summaries.
    """

    period = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    donation_count = serializers.IntegerField()
    average_donation = serializers.DecimalField(max_digits=12, decimal_places=2)
    by_type = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    by_method = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))


class MemberDonationSummarySerializer(serializers.Serializer):
    """
    Serializer for member donation summary.
    """

    member_id = serializers.UUIDField()
    member_name = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    donation_count = serializers.IntegerField()
    last_donation_date = serializers.DateField()
