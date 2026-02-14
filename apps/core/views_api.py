"""API views for core app: audit logs, webhooks, branding, search."""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsPastorOrAdmin, IsAdmin
from apps.core.services_search import GlobalSearchService
from apps.core.throttles import SearchRateThrottle, RateLimitHeadersMixin
from .models_extended import AuditLog, WebhookEndpoint, WebhookDelivery, ChurchBranding, Campus
from .serializers_extended import (
    AuditLogSerializer, WebhookEndpointSerializer,
    WebhookDeliverySerializer, ChurchBrandingSerializer,
    CampusSerializer,
)


class AuditLogViewSet(RateLimitHeadersMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing audit logs (admin only)."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = AuditLog.objects.select_related('user').all()
    filterset_fields = ['action', 'model_name']
    search_fields = ['object_repr', 'model_name']
    ordering_fields = ['created_at', 'action']


class WebhookEndpointViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    """API endpoint for managing webhook endpoints (admin only)."""
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = WebhookEndpoint.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """Get delivery history for a webhook endpoint."""
        endpoint = self.get_object()
        deliveries = endpoint.deliveries.all()[:100]
        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)


class ChurchBrandingViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    """API endpoint for managing church branding (admin only)."""
    serializer_class = ChurchBrandingSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = ChurchBranding.objects.all()


class CampusViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    """API endpoint for managing campuses (admin only)."""
    serializer_class = CampusSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Campus.objects.all()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_search(request):
    """API endpoint for global search with autocomplete."""
    query = request.query_params.get('q', '').strip()
    autocomplete = request.query_params.get('autocomplete', 'false') == 'true'

    service = GlobalSearchService(request.user)

    if autocomplete:
        suggestions = service.search_autocomplete(query)
        return Response({'suggestions': suggestions})

    results = service.search(query)
    total_count = service.get_total_count(results)

    # Serialize results
    data = {'total_count': total_count, 'results': {}}
    for category, qs in results.items():
        items = []
        for obj in qs:
            item = {'id': str(obj.pk)}
            if hasattr(obj, 'full_name'):
                item['name'] = obj.full_name
            elif hasattr(obj, 'title'):
                item['name'] = obj.title
            elif hasattr(obj, 'name'):
                item['name'] = obj.name
            else:
                item['name'] = str(obj)
            items.append(item)
        data['results'][category] = items

    return Response(data)
