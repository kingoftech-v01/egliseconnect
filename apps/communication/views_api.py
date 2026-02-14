"""Communication API Views."""
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import NewsletterStatus

from .models import (
    Newsletter, Notification, NotificationPreference,
    SMSMessage, SMSTemplate, SMSOptOut, PushSubscription, EmailTemplate,
    Automation, AutomationStep, AutomationEnrollment, ABTest,
    DirectMessage, GroupChat, GroupChatMessage,
)
from .serializers import (
    NewsletterSerializer, NewsletterListSerializer,
    NotificationSerializer, NotificationPreferenceSerializer,
    SMSMessageSerializer, SMSTemplateSerializer, SMSOptOutSerializer,
    PushSubscriptionSerializer, EmailTemplateSerializer,
    AutomationSerializer, AutomationStepSerializer, AutomationEnrollmentSerializer,
    ABTestSerializer,
    DirectMessageSerializer, GroupChatSerializer, GroupChatMessageSerializer,
)


class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['subject']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return NewsletterListSerializer
        return NewsletterSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'member_profile'):
            serializer.save(created_by=self.request.user.member_profile)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Trigger immediate newsletter delivery via Celery."""
        newsletter = self.get_object()
        if newsletter.status == NewsletterStatus.SENT:
            return Response({'error': 'D\u00e9j\u00e0 envoy\u00e9e'}, status=status.HTTP_400_BAD_REQUEST)

        newsletter.status = NewsletterStatus.SENDING
        newsletter.save()

        return Response({'message': 'Envoi en cours'})

    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule newsletter for future delivery."""
        newsletter = self.get_object()
        scheduled_for = request.data.get('scheduled_for')
        if not scheduled_for:
            return Response({'error': 'Date requise'}, status=status.HTTP_400_BAD_REQUEST)

        newsletter.scheduled_for = scheduled_for
        newsletter.status = NewsletterStatus.SCHEDULED
        newsletter.save()

        return Response({'message': 'Planifi\u00e9e'})


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        if hasattr(self.request.user, 'member_profile'):
            return Notification.objects.filter(member=self.request.user.member_profile)
        return Notification.objects.none()

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_read(self, request):
        """Mark specific notifications or all as read."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Profil membre requis'}, status=status.HTTP_404_NOT_FOUND)
        member = request.user.member_profile
        ids = request.data.get('ids', [])
        if ids:
            Notification.objects.filter(id__in=ids, member=member).update(
                is_read=True, read_at=timezone.now()
            )
        else:
            Notification.objects.filter(member=member, is_read=False).update(
                is_read=True, read_at=timezone.now()
            )
        return Response({'message': 'Marqu\u00e9es comme lues'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Return count of unread notifications."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'count': 0})
        count = Notification.objects.filter(member=request.user.member_profile, is_read=False).count()
        return Response({'count': count})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        if hasattr(self.request.user, 'member_profile'):
            return NotificationPreference.objects.filter(member=self.request.user.member_profile)
        return NotificationPreference.objects.none()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's notification preferences."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Profil requis'}, status=status.HTTP_404_NOT_FOUND)

        prefs, created = NotificationPreference.objects.get_or_create(member=request.user.member_profile)

        if request.method == 'GET':
            return Response(NotificationPreferenceSerializer(prefs).data)

        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── SMS API ─────────────────────────────────────────────────────────────────────


class SMSMessageViewSet(viewsets.ModelViewSet):
    queryset = SMSMessage.objects.all()
    serializer_class = SMSMessageSerializer
    permission_classes = [IsPastorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['phone_number', 'body']

    def perform_create(self, serializer):
        sms = serializer.save()
        if hasattr(self.request.user, 'member_profile'):
            sms.sent_by = self.request.user.member_profile
            sms.save(update_fields=['sent_by'])

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send an SMS message via Twilio."""
        sms = self.get_object()
        from .services_sms import TwilioSMSService
        service = TwilioSMSService()
        service.send_sms(sms)
        return Response(SMSMessageSerializer(sms).data)

    @action(detail=True, methods=['post'], url_path='track-delivery')
    def track_delivery(self, request, pk=None):
        """Track delivery status of an SMS."""
        sms = self.get_object()
        from .services_sms import TwilioSMSService
        service = TwilioSMSService()
        service.track_delivery(sms)
        return Response(SMSMessageSerializer(sms).data)


class SMSTemplateViewSet(viewsets.ModelViewSet):
    queryset = SMSTemplate.objects.all()
    serializer_class = SMSTemplateSerializer
    permission_classes = [IsPastorOrAdmin]
    search_fields = ['name', 'body_template']


class SMSOptOutViewSet(viewsets.ModelViewSet):
    queryset = SMSOptOut.objects.all()
    serializer_class = SMSOptOutSerializer
    permission_classes = [IsPastorOrAdmin]


# ─── Push API ────────────────────────────────────────────────────────────────────


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PushSubscriptionSerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        if hasattr(self.request.user, 'member_profile'):
            return PushSubscription.objects.filter(member=self.request.user.member_profile)
        return PushSubscription.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'member_profile'):
            from .services_push import WebPushService
            service = WebPushService()
            service.subscribe(
                member=self.request.user.member_profile,
                endpoint=serializer.validated_data['endpoint'],
                p256dh_key=serializer.validated_data['p256dh_key'],
                auth_key=serializer.validated_data['auth_key'],
            )

    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe from push notifications."""
        endpoint = request.data.get('endpoint')
        if not endpoint or not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Endpoint requis'}, status=status.HTTP_400_BAD_REQUEST)

        from .services_push import WebPushService
        service = WebPushService()
        service.unsubscribe(request.user.member_profile, endpoint)
        return Response({'message': 'D\u00e9sabonn\u00e9'})

    @action(detail=False, methods=['post'], url_path='test-send')
    def test_send(self, request):
        """Send a test push notification (staff only)."""
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'Profil requis'}, status=status.HTTP_404_NOT_FOUND)

        from .services_push import WebPushService
        service = WebPushService()
        count = service.send_to_member(
            request.user.member_profile,
            request.data.get('title', 'Test'),
            request.data.get('body', 'Notification de test'),
        )
        return Response({'sent': count})


# ─── Email Template API ─────────────────────────────────────────────────────────


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsPastorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'subject_template']


# ─── Automation API ──────────────────────────────────────────────────────────────


class AutomationViewSet(viewsets.ModelViewSet):
    queryset = Automation.objects.all()
    serializer_class = AutomationSerializer
    permission_classes = [IsPastorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['trigger_type', 'is_active']
    search_fields = ['name']

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'member_profile'):
            serializer.save(created_by=self.request.user.member_profile)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Manually trigger an automation for a member."""
        automation = self.get_object()
        member_id = request.data.get('member_id')
        if not member_id:
            return Response({'error': 'member_id requis'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.members.models import Member
        from .services_automation import AutomationService

        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Membre introuvable'}, status=status.HTTP_404_NOT_FOUND)

        service = AutomationService()
        enrollments = service.trigger(automation.trigger_type, member)
        return Response({'enrolled': len(enrollments)})


class AutomationStepViewSet(viewsets.ModelViewSet):
    queryset = AutomationStep.objects.all()
    serializer_class = AutomationStepSerializer
    permission_classes = [IsPastorOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['automation']


class AutomationEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = AutomationEnrollment.objects.all()
    serializer_class = AutomationEnrollmentSerializer
    permission_classes = [IsPastorOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['automation', 'status']


# ─── A/B Test API ────────────────────────────────────────────────────────────────


class ABTestViewSet(viewsets.ModelViewSet):
    queryset = ABTest.objects.all()
    serializer_class = ABTestSerializer
    permission_classes = [IsPastorOrAdmin]

    @action(detail=True, methods=['post'], url_path='pick-winner')
    def pick_winner(self, request, pk=None):
        """Determine the winner based on open rates."""
        abtest = self.get_object()
        if abtest.variant_a_opens >= abtest.variant_b_opens:
            abtest.winner = 'A'
        else:
            abtest.winner = 'B'
        abtest.status = 'completed'
        abtest.save(update_fields=['winner', 'status', 'updated_at'])
        return Response(ABTestSerializer(abtest).data)


# ─── Direct Message API ─────────────────────────────────────────────────────────


class DirectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        if hasattr(self.request.user, 'member_profile'):
            member = self.request.user.member_profile
            from django.db.models import Q
            return DirectMessage.objects.filter(
                Q(sender=member) | Q(recipient=member)
            )
        return DirectMessage.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'member_profile'):
            serializer.save(sender=self.request.user.member_profile)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark a message as read."""
        dm = self.get_object()
        if hasattr(request.user, 'member_profile') and dm.recipient == request.user.member_profile:
            dm.read_at = timezone.now()
            dm.save(update_fields=['read_at', 'updated_at'])
        return Response(DirectMessageSerializer(dm).data)


# ─── Group Chat API ──────────────────────────────────────────────────────────────


class GroupChatViewSet(viewsets.ModelViewSet):
    serializer_class = GroupChatSerializer
    permission_classes = [IsMember]

    def get_queryset(self):
        if hasattr(self.request.user, 'member_profile'):
            return GroupChat.objects.filter(members=self.request.user.member_profile)
        return GroupChat.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'member_profile'):
            serializer.save(created_by=self.request.user.member_profile)


class GroupChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = GroupChatMessageSerializer
    permission_classes = [IsMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['chat']

    def get_queryset(self):
        if hasattr(self.request.user, 'member_profile'):
            member = self.request.user.member_profile
            return GroupChatMessage.objects.filter(
                chat__members=member,
            )
        return GroupChatMessage.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'member_profile'):
            serializer.save(sender=self.request.user.member_profile)
