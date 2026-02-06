"""Communication API Views."""
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsMember, IsPastorOrAdmin
from apps.core.constants import NewsletterStatus

from .models import Newsletter, Notification, NotificationPreference
from .serializers import NewsletterSerializer, NewsletterListSerializer, NotificationSerializer, NotificationPreferenceSerializer


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
            return Response({'error': 'Déjà envoyée'}, status=status.HTTP_400_BAD_REQUEST)

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

        return Response({'message': 'Planifiée'})


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
        return Response({'message': 'Marquées comme lues'})

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
