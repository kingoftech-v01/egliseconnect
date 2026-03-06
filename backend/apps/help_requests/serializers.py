"""Help Requests serializers."""
from rest_framework import serializers

from .models import (
    HelpRequest, HelpRequestCategory, HelpRequestComment,
    PastoralCare, PrayerRequest, CareTeam, CareTeamMember,
    BenevolenceRequest, BenevolenceFund,
    MealTrain, MealSignup,
    CrisisProtocol, CrisisResource,
)


class HelpRequestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpRequestCategory
        fields = ['id', 'name', 'name_fr', 'description', 'icon', 'is_active']
        read_only_fields = ['id']


class HelpRequestCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = HelpRequestComment
        fields = [
            'id', 'help_request', 'author', 'author_name',
            'content', 'is_internal', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'created_at']


class HelpRequestSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.full_name',
        read_only=True,
        allow_null=True
    )
    comments = HelpRequestCommentSerializer(many=True, read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = HelpRequest
        fields = [
            'id', 'request_number', 'member', 'member_name',
            'category', 'category_name', 'title', 'description',
            'urgency', 'urgency_display', 'status', 'status_display',
            'assigned_to', 'assigned_to_name', 'is_confidential',
            'resolved_at', 'resolution_notes', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'request_number', 'member', 'resolved_at',
            'created_at', 'updated_at'
        ]


class HelpRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpRequest
        fields = [
            'category', 'title', 'description', 'urgency', 'is_confidential'
        ]

    def create(self, validated_data):
        validated_data['member'] = self.context['request'].user.member_profile
        return super().create(validated_data)


class HelpRequestAssignSerializer(serializers.Serializer):
    assigned_to = serializers.UUIDField()


class HelpRequestResolveSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpRequestComment
        fields = ['content', 'is_internal']


# ─── Pastoral Care Serializers ────────────────────────────────────────────────


class PastoralCareSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.full_name', read_only=True, allow_null=True
    )
    care_type_display = serializers.CharField(source='get_care_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PastoralCare
        fields = [
            'id', 'care_type', 'care_type_display', 'member', 'member_name',
            'assigned_to', 'assigned_to_name', 'date', 'notes',
            'follow_up_date', 'status', 'status_display', 'created_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PastoralCareCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastoralCare
        fields = ['care_type', 'member', 'assigned_to', 'date', 'notes', 'follow_up_date', 'status']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.member_profile
        return super().create(validated_data)


# ─── Prayer Request Serializers ──────────────────────────────────────────────


class PrayerRequestSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PrayerRequest
        fields = [
            'id', 'title', 'description', 'member', 'member_name',
            'is_anonymous', 'is_public', 'status', 'status_display',
            'answered_at', 'testimony', 'is_approved',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'answered_at', 'created_at', 'updated_at']

    def get_member_name(self, obj):
        if obj.is_anonymous:
            return 'Anonyme'
        if obj.member:
            return obj.member.full_name
        return 'Anonyme'


class PrayerRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerRequest
        fields = ['title', 'description', 'is_anonymous', 'is_public']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'member_profile'):
            validated_data['member'] = request.user.member_profile
        return super().create(validated_data)


# ─── Care Team Serializers ───────────────────────────────────────────────────


class CareTeamMemberSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = CareTeamMember
        fields = ['id', 'team', 'member', 'member_name', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class CareTeamSerializer(serializers.ModelSerializer):
    leader_name = serializers.CharField(source='leader.full_name', read_only=True, allow_null=True)
    memberships = CareTeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = CareTeam
        fields = ['id', 'name', 'description', 'leader', 'leader_name', 'memberships', 'created_at']
        read_only_fields = ['id', 'created_at']


# ─── Benevolence Serializers ─────────────────────────────────────────────────


class BenevolenceFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenevolenceFund
        fields = ['id', 'name', 'total_balance', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class BenevolenceRequestSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(
        source='approved_by.full_name', read_only=True, allow_null=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BenevolenceRequest
        fields = [
            'id', 'member', 'member_name', 'fund', 'fund_name',
            'amount_requested', 'reason', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'amount_granted',
            'disbursed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'approved_by', 'disbursed_at', 'created_at', 'updated_at']


# ─── Meal Train Serializers ──────────────────────────────────────────────────


class MealSignupSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(source='volunteer.full_name', read_only=True)

    class Meta:
        model = MealSignup
        fields = ['id', 'meal_train', 'volunteer', 'volunteer_name', 'date', 'confirmed', 'notes']
        read_only_fields = ['id']


class MealTrainSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    signups = MealSignupSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MealTrain
        fields = [
            'id', 'recipient', 'recipient_name', 'reason',
            'start_date', 'end_date', 'dietary_restrictions',
            'status', 'status_display', 'signups',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── Crisis Serializers ──────────────────────────────────────────────────────


class CrisisProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrisisProtocol
        fields = ['id', 'title', 'protocol_type', 'steps_json', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CrisisResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrisisResource
        fields = ['id', 'title', 'description', 'contact_info', 'url', 'category', 'created_at']
        read_only_fields = ['id', 'created_at']
