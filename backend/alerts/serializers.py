from rest_framework import serializers
from core.models import Alert, CodaDocument


class AlertDocumentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodaDocument
        fields = ['id', 'doc_id', 'name', 'sharing_mode', 'is_published', 'browser_link']


class AlertSerializer(serializers.ModelSerializer):
    document = AlertDocumentSimpleSerializer(read_only=True)
    document_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Alert
        fields = [
            'id', 'document', 'document_id', 'category', 'severity', 'status',
            'title', 'description', 'metadata', 'fingerprint',
            'detected_at', 'resolved_at', 'resolved_by', 'resolved_by_user',
        ]
        read_only_fields = ['id', 'fingerprint', 'detected_at', 'resolved_at']


class AlertStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Alert.Status.choices)
