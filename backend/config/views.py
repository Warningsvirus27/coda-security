import logging
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.activity_logger import ActivityLogger
from core.models import ScanConfig
from scanner.coda_client import CodaClient
from .serializers import ScanConfigSerializer, ValidateTokenSerializer

logger = logging.getLogger('config')


class ConfigViewSet(viewsets.ViewSet):
    """
    Class-based ViewSet for managing system configuration:
    - Coda API authentication key setup & validation
    - Unused document timeframe (days/hours/minutes)
    - Detector activation
    - Slack Integration (Phase 2 - Pending)
    """
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        config = ScanConfig.get_config()
        serializer = ScanConfigSerializer(config)
        return Response(serializer.data)

    def update(self, request):
        config = ScanConfig.get_config()
        serializer = ScanConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        ActivityLogger.log(
            request=request,
            action='CONFIG_UPDATED',
            description='System scan configuration was updated',
            details={
                'unused_threshold': f"{config.unused_threshold_value} {config.unused_threshold_unit}",
                'scan_interval_minutes': config.scan_interval_minutes,
                'has_token': bool(config.coda_api_token),
            },
        )

        # Trigger sync and scan automatically if a valid Coda API token is configured
        if config.coda_api_token:
            from scanner.tasks import sync_documents, run_full_scan
            try:
                sync_documents.delay()
                run_full_scan.delay(trigger='config_update')
            except Exception as e:
                logger.warning("Could not dispatch async Celery scan task (%s), running synchronously.", e)
                try:
                    sync_documents()
                    run_full_scan(trigger='config_update')
                except Exception as inner_e:
                    logger.warning("Synchronous scan error: %s", inner_e)

        return Response(ScanConfigSerializer(config).data)

    @action(detail=False, methods=['post'], url_path='validate-token')
    def validate_token(self, request):
        """Validate Coda API token against /whoami endpoint."""
        serializer = ValidateTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data.get('token')
        if not token:
            config = ScanConfig.get_config()
            token = config.coda_api_token

        if not token:
            return Response(
                {'valid': False, 'message': 'No Coda API token provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = CodaClient(api_token=token)
        whoami = client.whoami()

        if whoami.get('valid'):
            ActivityLogger.log(
                request=request,
                action='TOKEN_VALIDATED',
                description=f"Coda API key validated successfully for {whoami.get('user', {}).get('name', 'user')}",
                details={'user': whoami.get('user')},
            )
            return Response({
                'valid': True,
                'message': 'Coda API token is valid and active.',
                'user': whoami.get('user'),
            })
        else:
            return Response({
                'valid': False,
                'message': whoami.get('error', 'Authentication failed with Coda API.'),
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='slack-status')
    def slack_status(self, request):
        """Check status of Slack integration (Marked as Pending Phase 2)."""
        config = ScanConfig.get_config()
        return Response({
            'status': 'PENDING',
            'phase': 'Phase 2 (Scheduled for upcoming sprint)',
            'configured_channel': config.slack_channel,
            'webhook_configured': bool(config.slack_webhook_url),
            'note': 'Slack API integration is pending. Real-time notifications are currently handled via Django Channels WebSocket and live polling.',
        })
