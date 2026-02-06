"""API views for login audit."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsPastorOrAdmin
from .audit import LoginAudit
from .serializers_audit import LoginAuditSerializer


class LoginAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing login audit logs."""
    serializer_class = LoginAuditSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = LoginAudit.objects.all()
    filterset_fields = ['success', 'method']
    search_fields = ['email_attempted', 'ip_address']
