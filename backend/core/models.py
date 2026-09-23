import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class CodaDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doc_id = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=500)
    owner_email = models.EmailField(blank=True, default='')
    folder_id = models.CharField(max_length=255, blank=True, default='')
    icon = models.CharField(max_length=100, blank=True, default='')

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    is_published = models.BooleanField(default=False)
    sharing_mode = models.CharField(
        max_length=50,
        choices=[
            ('private', 'Private'),
            ('org', 'Organization'),
            ('public', 'Public'),
        ],
        default='private',
    )
    browser_link = models.URLField(max_length=1000, blank=True, default='')

    last_scanned = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Coda Document'
        verbose_name_plural = 'Coda Documents'

    def __str__(self):
        return f"{self.name} ({self.doc_id})"

    @property
    def days_since_update(self):
        delta = timezone.now() - self.updated_at
        return delta.days

    @property
    def hours_since_update(self):
        delta = timezone.now() - self.updated_at
        return int(delta.total_seconds() // 3600)

    @property
    def minutes_since_update(self):
        delta = timezone.now() - self.updated_at
        return int(delta.total_seconds() // 60)


class Alert(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'
        INFO = 'info', 'Info'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
        RESOLVED = 'resolved', 'Resolved'
        DISMISSED = 'dismissed', 'Dismissed'

    class Category(models.TextChoices):
        UNUSED_DOC = 'unused_doc', 'Unused Document'
        PUBLIC_SHARING = 'public_sharing', 'Public Sharing'
        SENSITIVE_TABLE = 'sensitive_table', 'Sensitive Data in Table'
        SENSITIVE_PAGE = 'sensitive_page', 'Sensitive Data in Page'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        CodaDocument,
        on_delete=models.CASCADE,
        related_name='alerts',
    )

    category = models.CharField(max_length=50, choices=Category.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    title = models.CharField(max_length=500)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)

    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=255, blank=True, default='')
    resolved_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
    )

    class Meta:
        ordering = ['-detected_at']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        indexes = [
            models.Index(fields=['category', 'severity', 'status']),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title}"


class ScanRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    docs_scanned = models.IntegerField(default=0)
    alerts_created = models.IntegerField(default=0)
    alerts_resolved = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    trigger = models.CharField(
        max_length=20,
        choices=[('scheduled', 'Scheduled'), ('manual', 'Manual')],
        default='scheduled',
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scan_runs',
    )

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Scan Run'
        verbose_name_plural = 'Scan Runs'

    def __str__(self):
        return f"Scan {self.id} ({self.status}) — {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def duration_seconds(self):
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remediation_audit_logs',
    )
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('delete_row', 'Delete Row'),
            ('redact_row', 'Redact Row Values'),
            ('delete_document', 'Delete Document'),
            ('revoke_permission', 'Revoke Permission'),
            ('acknowledge', 'Acknowledge Alert'),
            ('dismiss', 'Dismiss Alert'),
        ],
    )
    performed_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.CharField(max_length=255, default='system')
    details = models.JSONField(default=dict, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-performed_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        status = '✓' if self.success else '✗'
        return f"{status} {self.action_type} on {self.alert_id} at {self.performed_at:%H:%M}"


class UserActivityLog(models.Model):
    """
    Tracks all user activities and user-made changes across the platform.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    username = models.CharField(max_length=150, blank=True, default='anonymous')
    action = models.CharField(max_length=100, db_index=True)
    description = models.CharField(max_length=500)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.CharField(max_length=64, blank=True, default='')
    user_agent = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'

    def __str__(self):
        return f"{self.username} - {self.action} at {self.created_at:%Y-%m-%d %H:%M}"


class ScanConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    coda_api_token = models.CharField(max_length=500, blank=True, default='')
    scan_interval_minutes = models.IntegerField(default=60)

    # Configurable timeframe for unused document detection
    unused_threshold_value = models.IntegerField(default=90)
    unused_threshold_unit = models.CharField(
        max_length=20,
        choices=[
            ('days', 'Days'),
            ('hours', 'Hours'),
            ('minutes', 'Minutes'),
        ],
        default='days',
    )
    unused_threshold_days = models.IntegerField(default=90)

    enabled_detectors = models.JSONField(default=list, blank=True)
    internal_domains = models.JSONField(default=list, blank=True)

    # Slack Integration — Marked as Pending (Phase 2)
    slack_webhook_url = models.CharField(max_length=500, blank=True, default='')
    slack_channel = models.CharField(max_length=100, blank=True, default='#security-alerts')
    slack_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[('pending', 'Pending (Phase 2)'), ('configured', 'Configured'), ('active', 'Active')],
    )
    slack_notifications_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Scan Configuration'
        verbose_name_plural = 'Scan Configurations'

    def __str__(self):
        return f"ScanConfig ({self.unused_threshold_value} {self.unused_threshold_unit})"

    def save(self, *args, **kwargs):
        if not self.pk and ScanConfig.objects.exists():
            existing = ScanConfig.objects.first()
            self.pk = existing.pk

        # Automatically calculate unused_threshold_days for compatibility
        if self.unused_threshold_unit == 'days':
            self.unused_threshold_days = self.unused_threshold_value
        elif self.unused_threshold_unit == 'hours':
            self.unused_threshold_days = max(1, self.unused_threshold_value // 24)
        elif self.unused_threshold_unit == 'minutes':
            self.unused_threshold_days = max(1, self.unused_threshold_value // (24 * 60))

        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(
            defaults={
                'unused_threshold_value': 90,
                'unused_threshold_unit': 'days',
                'unused_threshold_days': 90,
                'enabled_detectors': [
                    'unused_docs',
                    'public_sharing',
                    'sensitive_tables',
                    'sensitive_pages',
                ],
                'internal_domains': [],
                'slack_status': 'pending',
                'slack_notifications_enabled': False,
            }
        )
        return config


class ExportHistory(models.Model):
    """Tracks previously exported reports, formats, and filter options."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='export_histories',
    )
    title = models.CharField(max_length=255, default='Security Exposure Report')
    format = models.CharField(
        max_length=10,
        choices=[('html', 'HTML Report'), ('pdf', 'PDF Report')],
        default='html',
    )
    options = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Export History'
        verbose_name_plural = 'Export Histories'

    def __str__(self):
        return f"{self.title} ({self.format.upper()}) - {self.created_at:%Y-%m-%d %H:%M}"

