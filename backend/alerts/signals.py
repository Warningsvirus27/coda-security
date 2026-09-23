import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Alert, AuditLog

logger = logging.getLogger('alerts.signals')


@receiver(post_save, sender=Alert)
def broadcast_alert_change(sender, instance, created, **kwargs):
    """Pushes alert creations or modifications to the WebSocket channel layer."""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        payload = {
            'event': 'ALERT_CREATED' if created else 'ALERT_UPDATED',
            'alert': {
                'id': str(instance.id),
                'title': instance.title,
                'category': instance.category,
                'severity': instance.severity,
                'status': instance.status,
                'document_name': instance.document.name if instance.document else '',
                'detected_at': instance.detected_at.isoformat() if instance.detected_at else '',
                'resolved_at': instance.resolved_at.isoformat() if instance.resolved_at else None,
            },
        }

        async_to_sync(channel_layer.group_send)(
            'alerts_broadcast',
            {
                'type': 'alert_event',
                'payload': payload,
            },
        )
    except Exception as e:
        logger.debug("Could not broadcast alert signal: %s", e)
