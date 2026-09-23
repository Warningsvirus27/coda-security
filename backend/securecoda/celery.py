"""
SecureCoda — Celery Application Configuration

Initializes the Celery app and configures periodic task scheduling
via Celery Beat for automated security scans.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securecoda.settings')

app = Celery('securecoda')

# Load config from Django settings, using the CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# --------------------------------------------------------------------------
# Celery Beat Schedule — default periodic tasks
# The scan interval is also configurable at runtime via the ScanConfig model.
# --------------------------------------------------------------------------
app.conf.beat_schedule = {
    'run-full-security-scan': {
        'task': 'scanner.tasks.run_full_scan',
        'schedule': 3600.0,  # Default: every 60 minutes (in seconds)
    },
}
