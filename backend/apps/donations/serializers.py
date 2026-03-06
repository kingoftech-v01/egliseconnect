"""DRF serializers for donation API."""
from rest_framework import serializers

from .models import (
    Donation, DonationCampaign, TaxReceipt,
    Pledge, PledgeFulfillment, GivingStatement, GivingGoal,
    DonationImport, DonationImportRow, MatchingCampaign, CryptoDonation,
)


class DonationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for donation lists."""

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
    """Full donation serializer with all fields."""

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
    """Serializer for online donations. Member is set from request."""

    class Meta:
        model = Donation
        fields = [
            'amount',
            'donation_type',
            'campaign',
            'notes',
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class PhysicalDonationCreateSerializer(serializers.ModelSerializer):
    """Serializer for treasurer to record physical donations."""

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
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value

    def validate(self, data):
        """Check payments require a check number."""
        if data.get('payment_method') == 'check' and not data.get('check_number'):
            raise serializers.ValidationError({
                'check_number': "Le numéro de chèque est requis."
            })
        return data


class MemberDonationHistorySerializer(serializers.ModelSerializer):
    """Serializer for member's own donation history."""

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


class DonationCampaignSerializer(serializers.ModelSerializer):
    """Full campaign serializer with computed fields."""

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
        return obj.donations.filter(is_active=True).count()


class DonationCampaignListSerializer(serializers.ModelSerializer):
    """Lightweight campaign serializer for lists."""

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


class TaxReceiptSerializer(serializers.ModelSerializer):
    """Full tax receipt serializer."""

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
    """Lightweight tax receipt serializer for lists."""

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


class DonationSummarySerializer(serializers.Serializer):
    """Serializer for donation statistics."""

    period = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    donation_count = serializers.IntegerField()
    average_donation = serializers.DecimalField(max_digits=12, decimal_places=2)
    by_type = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    by_method = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))


class MemberDonationSummarySerializer(serializers.Serializer):
    """Serializer for per-member donation summary."""

    member_id = serializers.UUIDField()
    member_name = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    donation_count = serializers.IntegerField()
    last_donation_date = serializers.DateField()


# ==============================================================================
# Pledge Serializers
# ==============================================================================


class PledgeSerializer(serializers.ModelSerializer):
    """Full pledge serializer."""

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)
    fulfilled_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    progress_percentage = serializers.IntegerField(read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Pledge
        fields = [
            'id', 'member', 'member_name', 'campaign', 'campaign_name',
            'amount', 'frequency', 'frequency_display', 'start_date', 'end_date',
            'status', 'status_display', 'notes',
            'fulfilled_amount', 'progress_percentage', 'remaining_amount',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class PledgeListSerializer(serializers.ModelSerializer):
    """Lightweight pledge list serializer."""

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)
    progress_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pledge
        fields = [
            'id', 'member', 'member_name', 'campaign_name',
            'amount', 'frequency', 'start_date', 'end_date',
            'status', 'progress_percentage',
        ]


class PledgeFulfillmentSerializer(serializers.ModelSerializer):
    """Pledge fulfillment serializer."""

    class Meta:
        model = PledgeFulfillment
        fields = [
            'id', 'pledge', 'donation', 'amount', 'date',
            'created_at',
        ]
        read_only_fields = ['created_at']


# ==============================================================================
# Giving Statement Serializers
# ==============================================================================


class GivingStatementSerializer(serializers.ModelSerializer):
    """Full giving statement serializer."""

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = GivingStatement
        fields = [
            'id', 'member', 'member_name', 'year', 'period', 'period_display',
            'start_date', 'end_date', 'total_amount', 'pdf_file',
            'generated_at', 'emailed_at', 'created_at',
        ]
        read_only_fields = ['generated_at', 'created_at']


class GivingStatementListSerializer(serializers.ModelSerializer):
    """Lightweight statement list serializer."""

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = GivingStatement
        fields = [
            'id', 'member_name', 'year', 'period_display',
            'total_amount', 'generated_at', 'emailed_at',
        ]


# ==============================================================================
# Giving Goal Serializers
# ==============================================================================


class GivingGoalSerializer(serializers.ModelSerializer):
    """Full giving goal serializer."""

    member_name = serializers.CharField(source='member.full_name', read_only=True)
    current_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    progress_percentage = serializers.IntegerField(read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = GivingGoal
        fields = [
            'id', 'member', 'member_name', 'year', 'target_amount', 'notes',
            'current_amount', 'progress_percentage', 'remaining_amount',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# ==============================================================================
# Import Serializers
# ==============================================================================


class DonationImportSerializer(serializers.ModelSerializer):
    """Full import serializer."""

    imported_by_name = serializers.CharField(
        source='imported_by.full_name', read_only=True, allow_null=True
    )

    class Meta:
        model = DonationImport
        fields = [
            'id', 'file', 'status', 'imported_by', 'imported_by_name',
            'error_log', 'total_rows', 'imported_count', 'skipped_count',
            'created_at',
        ]
        read_only_fields = ['status', 'total_rows', 'imported_count', 'skipped_count', 'created_at']


class DonationImportRowSerializer(serializers.ModelSerializer):
    """Import row serializer."""

    class Meta:
        model = DonationImportRow
        fields = [
            'id', 'row_number', 'data_json', 'status', 'error_message',
            'donation',
        ]


# ==============================================================================
# Matching Campaign Serializers
# ==============================================================================


class MatchingCampaignSerializer(serializers.ModelSerializer):
    """Full matching campaign serializer."""

    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    match_progress_percentage = serializers.IntegerField(read_only=True)
    remaining_match = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = MatchingCampaign
        fields = [
            'id', 'campaign', 'campaign_name', 'matcher_name',
            'match_ratio', 'match_cap', 'matched_total',
            'match_progress_percentage', 'remaining_match',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# ==============================================================================
# Crypto Donation Serializers
# ==============================================================================


class CryptoDonationSerializer(serializers.ModelSerializer):
    """Full crypto donation serializer."""

    member_name = serializers.CharField(
        source='member.full_name', read_only=True, allow_null=True
    )
    crypto_type_display = serializers.CharField(
        source='get_crypto_type_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CryptoDonation
        fields = [
            'id', 'member', 'member_name', 'crypto_type', 'crypto_type_display',
            'wallet_address', 'amount_crypto', 'amount_cad',
            'coinbase_charge_id', 'status', 'status_display',
            'donation', 'created_at',
        ]
        read_only_fields = ['created_at']


# ==============================================================================
# Analytics Serializers
# ==============================================================================


class GivingTrendSerializer(serializers.Serializer):
    """Serializer for giving trend data."""

    period = serializers.DateField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()
    avg = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)


class DonorRetentionSerializer(serializers.Serializer):
    """Serializer for donor retention metrics."""

    year = serializers.IntegerField()
    new_donors = serializers.IntegerField()
    returning_donors = serializers.IntegerField()
    lapsed_donors = serializers.IntegerField()
    total_current_donors = serializers.IntegerField()
    retention_rate = serializers.FloatField()


class TopDonorSerializer(serializers.Serializer):
    """Serializer for top donor data."""

    member_id = serializers.CharField()
    member_name = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    donation_count = serializers.IntegerField()
