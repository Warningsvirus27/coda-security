"""
SecureCoda — Core Serializers
"""
from rest_framework import serializers
from .models import CodaDocument, Alert, ScanRun, AuditLog


class CodaDocumentSerializer(serializers.ModelSerializer):
    alert_count = serializers.SerializerMethodField()
    open_alert_count = serializers.SerializerMethodField()
    days_since_update = serializers.ReadOnlyField()

    class Meta:
        model = CodaDocument
        fields = [
            'id', 'doc_id', 'name', 'owner_email', 'folder_id',
            'created_at', 'updated_at', 'is_published', 'sharing_mode',
            'browser_link', 'last_scanned', 'is_active', 'synced_at',
            'alert_count', 'open_alert_count', 'days_since_update',
        ]

    def get_alert_count(self, obj):
        return obj.alerts.count()

    def get_open_alert_count(self, obj):
        return obj.alerts.filter(status='open').count()


class CodaDocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    open_alert_count = serializers.SerializerMethodField()
    days_since_update = serializers.ReadOnlyField()

    class Meta:
        model = CodaDocument
        fields = [
            'id', 'doc_id', 'name', 'is_published', 'sharing_mode',
            'updated_at', 'last_scanned', 'open_alert_count', 'days_since_update',
        ]

    def get_open_alert_count(self, obj):
        return obj.alerts.filter(status='open').count()


class ScanRunSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = ScanRun
        fields = [
            'id', 'started_at', 'completed_at', 'status',
            'docs_scanned', 'alerts_created', 'alerts_resolved',
            'errors', 'trigger', 'duration_seconds',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    alert_title = serializers.CharField(source='alert.title', read_only=True)
    document_name = serializers.CharField(source='alert.document.name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'alert', 'alert_title', 'document_name',
            'action_type', 'performed_at', 'performed_by',
            'details', 'success', 'error_message',
        ]
