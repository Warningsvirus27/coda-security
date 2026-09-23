import logging
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.activity_logger import ActivityLogger
from core.models import Alert, AuditLog
from scanner.coda_client import CodaClient
from .actions.registry import ActionRegistry
from .serializers import (
    ActionInfoSerializer,
    ExecuteActionSerializer,
    RemediationAuditLogSerializer,
)

logger = logging.getLogger('remediation')


class RemediationViewSet(viewsets.ViewSet):
    """
    Class-based ViewSet for executing remediation actions on alerts
    and discovering available actions.
    """
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def actions(self, request):
        """List all available remediation actions, optionally filtered by category."""
        category = request.query_params.get('category')
        if category:
            actions_list = ActionRegistry.get_for_category(category)
        else:
            actions_list = ActionRegistry.all()

        data = [
            {
                'name': a.name,
                'label': a.label,
                'description': a.description,
                'applicable_categories': a.applicable_categories,
            }
            for a in actions_list
        ]
        return Response(data)

    @action(detail=False, methods=['post'])
    def execute(self, request):
        """Execute a remediation action against a specific alert."""
        serializer = ExecuteActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert_id = serializer.validated_data['alert_id']
        action_name = serializer.validated_data['action_name']

        try:
            alert = Alert.objects.select_related('document').get(id=alert_id)
        except Alert.DoesNotExist:
            return Response({'error': 'Alert not found.'}, status=status.HTTP_404_NOT_FOUND)

        action_handler = ActionRegistry.get(action_name)
        if not action_handler:
            return Response(
                {'error': f"Unknown remediation action '{action_name}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if alert.category not in action_handler.applicable_categories:
            return Response(
                {'error': f"Action '{action_name}' cannot be applied to alert category '{alert.category}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user.is_authenticated else None
        performed_by_name = user.username if user else 'system'

        # Initialize Coda client
        coda_client = CodaClient()

        # Execute remediation action
        result = action_handler.execute(alert, coda_client, user=user)

        # Record in immutable AuditLog
        audit_entry = AuditLog.objects.create(
            alert=alert,
            user=user,
            action_type=action_name,
            performed_by=performed_by_name,
            details=result.details,
            success=result.success,
            error_message='' if result.success else result.message,
        )

        if result.success:
            alert.status = Alert.Status.RESOLVED
            alert.resolved_at = timezone.now()
            alert.resolved_by = f"{action_handler.label} ({performed_by_name})"
            alert.resolved_by_user = user
            alert.save()

            ActivityLogger.log(
                request=request,
                action='REMEDIATION_EXECUTED',
                description=f"Remediation '{action_handler.label}' executed successfully for alert '{alert.title}'",
                details={
                    'alert_id': str(alert.id),
                    'action': action_name,
                    'audit_log_id': str(audit_entry.id),
                },
                user=user,
            )

            return Response({
                'success': True,
                'message': result.message,
                'alert_id': str(alert.id),
                'status': alert.status,
                'resolved_at': alert.resolved_at,
                'resolved_by': alert.resolved_by,
            })
        else:
            ActivityLogger.log(
                request=request,
                action='REMEDIATION_FAILED',
                description=f"Remediation '{action_handler.label}' failed for alert '{alert.title}': {result.message}",
                details={'alert_id': str(alert.id), 'action': action_name, 'error': result.message},
                user=user,
            )
            return Response(
                {'success': False, 'message': result.message},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Class-based ViewSet for viewing the complete remediation audit trail.
    """
    queryset = AuditLog.objects.select_related('alert', 'alert__document', 'user').all()
    serializer_class = RemediationAuditLogSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['action_type', 'success']
    search_fields = ['alert__title', 'performed_by', 'error_message']
    ordering_fields = ['performed_at']
    ordering = ['-performed_at']
