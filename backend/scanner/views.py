import logging
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.activity_logger import ActivityLogger
from core.models import ScanRun
from core.serializers import ScanRunSerializer

logger = logging.getLogger('scanner')


class ScanViewSet(viewsets.ViewSet):
    """
    Class-based ViewSet for triggering security scans and querying scan status.
    """
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """Manually triggers a full security scan."""
        from core.models import ScanConfig
        config = ScanConfig.get_config()
        if not config.coda_api_token:
            return Response(
                {
                    'error': 'Cannot run scan: No Coda API key configured. Please add your API key in Settings first.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user.is_authenticated else None
        user_name = user.username if user else 'anonymous'

        from scanner.tasks import run_full_scan
        try:
            task = run_full_scan.delay(trigger='manual')
            task_id = str(task.id)
        except Exception as e:
            logger.warning("Celery async dispatch failed (%s), running synchronously.", e)
            # Synchronous fallback if Celery worker is offline during local test
            task_id = "local-sync"
            run_full_scan(trigger='manual')

        ActivityLogger.log(
            request=request,
            action='SCAN_TRIGGERED',
            description=f"Security scan initiated by {user_name}",
            details={'task_id': task_id, 'trigger': 'manual'},
            user=user,
        )

        return Response(
            {'status': 'scan_started', 'task_id': task_id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Returns the history of past scans."""
        runs = ScanRun.objects.all()[:50]
        serializer = ScanRunSerializer(runs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Returns the latest scan execution status."""
        latest = ScanRun.objects.first()
        if not latest:
            return Response({'status': 'no_scans', 'message': 'No scans have been executed yet'})
        serializer = ScanRunSerializer(latest)
        return Response(serializer.data)
