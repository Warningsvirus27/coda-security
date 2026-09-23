import logging
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.activity_logger import ActivityLogger
from core.models import Alert
from .serializers import AlertSerializer, AlertStatusUpdateSerializer

logger = logging.getLogger('alerts')


class AlertViewSet(viewsets.ModelViewSet):
    """
    Class-based ViewSet for managing security alerts.
    Supports filtering, sorting, status transitions, and aggregate statistics.
    """
    queryset = Alert.objects.select_related('document').all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.AllowAny]  # Allow viewing, auth user details captured when present
    filterset_fields = ['category', 'severity', 'status', 'document__doc_id']
    search_fields = ['title', 'description', 'document__name', 'fingerprint']
    ordering_fields = ['detected_at', 'severity', 'status', 'category', 'title']
    ordering = ['-detected_at']

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        ActivityLogger.log(
            request=request,
            action='ALERT_UPDATED',
            description=f"Alert '{instance.title}' was updated.",
            details={'alert_id': str(instance.id), 'status': instance.status},
        )
        return response

    @action(detail=True, methods=['patch', 'post'], url_path='status')
    def update_status(self, request, pk=None):
        """Update status of an alert (acknowledge, dismiss, resolve)."""
        alert = self.get_object()
        serializer = AlertStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        old_status = alert.status
        alert.status = new_status

        if new_status == Alert.Status.RESOLVED:
            alert.resolved_at = timezone.now()
            user_label = request.user.username if request.user.is_authenticated else 'User'
            alert.resolved_by = f"Manual ({user_label})"
            if request.user.is_authenticated:
                alert.resolved_by_user = request.user
        elif old_status == Alert.Status.RESOLVED and new_status != Alert.Status.RESOLVED:
            alert.resolved_at = None
            alert.resolved_by = ''
            alert.resolved_by_user = None

        alert.save()

        ActivityLogger.log(
            request=request,
            action='ALERT_STATUS_CHANGE',
            description=f"Alert '{alert.title}' status changed from {old_status} to {new_status}",
            details={'alert_id': str(alert.id), 'from_status': old_status, 'to_status': new_status},
        )

        return Response(AlertSerializer(alert).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Returns aggregate vulnerability metrics categorized by type and severity."""
        total_alerts = Alert.objects.count()
        open_alerts = Alert.objects.filter(status=Alert.Status.OPEN).count()
        critical_alerts = Alert.objects.filter(severity=Alert.Severity.CRITICAL, status=Alert.Status.OPEN).count()
        high_alerts = Alert.objects.filter(severity=Alert.Severity.HIGH, status=Alert.Status.OPEN).count()
        medium_alerts = Alert.objects.filter(severity=Alert.Severity.MEDIUM, status=Alert.Status.OPEN).count()
        low_alerts = Alert.objects.filter(severity=Alert.Severity.LOW, status=Alert.Status.OPEN).count()

        by_category = (
            Alert.objects.values('category')
            .annotate(
                total=Count('id'),
                open=Count('id', filter=Q(status=Alert.Status.OPEN)),
                resolved=Count('id', filter=Q(status=Alert.Status.RESOLVED)),
            )
        )

        by_severity = (
            Alert.objects.filter(status=Alert.Status.OPEN)
            .values('severity')
            .annotate(count=Count('id'))
        )

        return Response({
            'total_alerts': total_alerts,
            'open_alerts': open_alerts,
            'critical_alerts': critical_alerts,
            'high_alerts': high_alerts,
            'medium_alerts': medium_alerts,
            'low_alerts': low_alerts,
            'by_category': list(by_category),
            'by_severity': list(by_severity),
        })
