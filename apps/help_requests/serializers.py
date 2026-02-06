"""Help Requests serializers."""
from rest_framework import serializers
from .models import HelpRequest, HelpRequestCategory, HelpRequestComment


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
