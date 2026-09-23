"""
SecureCoda — Core Views (Documents & Audit Log)
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import CodaDocument, ScanRun, AuditLog
from .serializers import (
    CodaDocumentSerializer,
    CodaDocumentListSerializer,
    ScanRunSerializer,
    AuditLogSerializer,
)

logger = logging.getLogger('core')


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for browsing monitored Coda documents.
    Supports filtering by sharing_mode, is_published, and is_active.
    """
    queryset = CodaDocument.objects.all()
    filterset_fields = ['sharing_mode', 'is_published', 'is_active']
    search_fields = ['name', 'doc_id', 'owner_email']
    ordering_fields = ['name', 'updated_at', 'created_at', 'last_scanned']

    def get_serializer_class(self):
        if self.action == 'list':
            return CodaDocumentListSerializer
        return CodaDocumentSerializer

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Trigger a manual document sync from Coda API."""
        from scanner.tasks import sync_documents
        task = sync_documents.delay()
        logger.info("Manual document sync triggered, task_id=%s", task.id)
        return Response(
            {'status': 'sync_started', 'task_id': str(task.id)},
            status=status.HTTP_202_ACCEPTED,
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing the remediation audit trail.
    """
    queryset = AuditLog.objects.select_related('alert', 'alert__document').all()
    serializer_class = AuditLogSerializer
    filterset_fields = ['action_type', 'success']
    ordering_fields = ['performed_at']
