from rest_framework import serializers
from core.models import AuditLog


class ExecuteActionSerializer(serializers.Serializer):
    alert_id = serializers.UUIDField()
    action_name = serializers.CharField(max_length=100)


class ActionInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    applicable_categories = serializers.ListField(child=serializers.CharField())


class RemediationAuditLogSerializer(serializers.ModelSerializer):
    alert_title = serializers.CharField(source='alert.title', read_only=True)
    alert_category = serializers.CharField(source='alert.category', read_only=True)
    document_name = serializers.CharField(source='alert.document.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'alert', 'alert_title', 'alert_category', 'document_name',
            'user', 'user_name', 'action_type', 'performed_at', 'performed_by',
            'details', 'success', 'error_message',
        ]
