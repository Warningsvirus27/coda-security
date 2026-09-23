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
        from core.models import ScanConfig
        config = ScanConfig.get_config()
        if not config.coda_api_token:
            return Response(
                {
                    'error': 'Cannot sync Coda documents: No Coda API key configured. Please add your API key in Settings first.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from scanner.tasks import sync_documents
        try:
            task = sync_documents.delay()
            task_id = str(task.id)
        except Exception:
            task_id = "local-sync"
            sync_documents()

        logger.info("Manual document sync triggered, task_id=%s", task_id)
        return Response(
            {'status': 'sync_started', 'message': 'Document sync initiated with Coda API.', 'task_id': task_id},
            status=status.HTTP_202_ACCEPTED,
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing the remediation audit trail.
    Strictly scoped to the logged-in user.
    """
    serializer_class = AuditLogSerializer
    filterset_fields = ['action_type', 'success']
    ordering_fields = ['performed_at']

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if user.is_authenticated:
            return AuditLog.objects.select_related('alert', 'alert__document').filter(
                Q(user=user) | Q(performed_by=user.username)
            ).order_by('-performed_at')
        return AuditLog.objects.none()
