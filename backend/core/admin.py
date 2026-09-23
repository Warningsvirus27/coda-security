"""
SecureCoda — Core Admin Configuration
"""
from django.contrib import admin
from .models import CodaDocument, Alert, ScanRun, AuditLog, ScanConfig


@admin.register(CodaDocument)
class CodaDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'doc_id', 'is_published', 'sharing_mode', 'updated_at', 'last_scanned']
    list_filter = ['is_published', 'sharing_mode', 'is_active']
    search_fields = ['name', 'doc_id', 'owner_email']
    readonly_fields = ['id', 'synced_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'severity', 'status', 'detected_at']
    list_filter = ['category', 'severity', 'status']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'fingerprint', 'detected_at']


@admin.register(ScanRun)
class ScanRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'started_at', 'completed_at', 'docs_scanned', 'alerts_created']
    list_filter = ['status', 'trigger']
    readonly_fields = ['id', 'started_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'alert', 'performed_by', 'success', 'performed_at']
    list_filter = ['action_type', 'success']
    readonly_fields = ['id', 'performed_at']


@admin.register(ScanConfig)
class ScanConfigAdmin(admin.ModelAdmin):
    list_display = ['scan_interval_minutes', 'unused_threshold_days', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
