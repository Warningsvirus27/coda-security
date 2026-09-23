from rest_framework import serializers
from core.models import ScanConfig


class ScanConfigSerializer(serializers.ModelSerializer):
    # Mask the token when returning
    coda_api_token_masked = serializers.SerializerMethodField()
    is_token_configured = serializers.SerializerMethodField()

    class Meta:
        model = ScanConfig
        fields = [
            'id',
            'coda_api_token',
            'coda_api_token_masked',
            'is_token_configured',
            'scan_interval_minutes',
            'unused_threshold_value',
            'unused_threshold_unit',
            'unused_threshold_days',
            'enabled_detectors',
            'internal_domains',
            'slack_webhook_url',
            'slack_channel',
            'slack_status',
            'slack_notifications_enabled',
            'updated_at',
        ]
        extra_kwargs = {
            'coda_api_token': {'write_only': True, 'required': False},
        }

    def get_coda_api_token_masked(self, obj) -> str:
        if not obj.coda_api_token:
            return ""
        if len(obj.coda_api_token) <= 8:
            return "••••••••"
        return f"{obj.coda_api_token[:4]}••••••••{obj.coda_api_token[-4:]}"

    def get_is_token_configured(self, obj) -> bool:
        return bool(obj.coda_api_token)


class ValidateTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=False, allow_blank=True)
