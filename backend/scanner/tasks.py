"""
SecureCoda — Scanner Celery Tasks

Defines the scheduled and manual scan tasks that orchestrate
the detection engine and persist results.
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db import IntegrityError

from core.models import CodaDocument, Alert, ScanRun, ScanConfig
from scanner.coda_client import CodaClient, CodaAPIError
from scanner.registry import DetectorRegistry

# Ensure all detectors are imported and registered
import scanner.detectors.unused_docs      # noqa: F401
import scanner.detectors.public_sharing   # noqa: F401
import scanner.detectors.sensitive_tables  # noqa: F401
import scanner.detectors.sensitive_pages   # noqa: F401

logger = logging.getLogger('scanner')


def _notify_websocket(event_type: str, data: dict):
    """Push an event to the WebSocket alerts_broadcast group."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'alerts_broadcast',
                {
                    'type': 'alert_event',
                    'payload': {
                        'event': event_type,
                        'data': data,
                    },
                }
            )
    except Exception as e:
        logger.debug("Could not send WebSocket notification: %s", str(e))


def ensure_initial_seed_data():
    """Seeds initial sample documents and vulnerabilities for demo/evaluation if DB is empty."""
    if CodaDocument.objects.count() > 0:
        return

    now = timezone.now()
    doc1 = CodaDocument.objects.create(
        doc_id='doc-financial-q3-2024',
        name='Q3 Financial Operations & Vendor Payouts',
        owner_email='finance-lead@company.com',
        created_at=now - timedelta(days=120),
        updated_at=now - timedelta(days=105),
        is_published=False,
        sharing_mode='org',
        browser_link='https://coda.io/d/Q3-Financial_ddoc1',
    )
    doc2 = CodaDocument.objects.create(
        doc_id='doc-customer-support-crm',
        name='Customer Support CRM & Live Escrow Logs',
        owner_email='support-ops@company.com',
        created_at=now - timedelta(days=45),
        updated_at=now - timedelta(days=2),
        is_published=True,
        sharing_mode='public',
        browser_link='https://coda.io/d/Customer-Support_ddoc2',
    )
    doc3 = CodaDocument.objects.create(
        doc_id='doc-developer-onboarding',
        name='DevOps & Cloud Infrastructure Credentials',
        owner_email='devops@company.com',
        created_at=now - timedelta(days=60),
        updated_at=now - timedelta(days=14),
        is_published=False,
        sharing_mode='org',
        browser_link='https://coda.io/d/DevOps-Infra_ddoc3',
    )
    doc4 = CodaDocument.objects.create(
        doc_id='doc-archived-marketing-2023',
        name='Legacy Marketing Campaign Analysis 2023',
        owner_email='marketing@company.com',
        created_at=now - timedelta(days=360),
        updated_at=now - timedelta(days=150),
        is_published=False,
        sharing_mode='private',
        browser_link='https://coda.io/d/Marketing-2023_ddoc4',
    )

    # Initial sample alerts
    Alert.objects.get_or_create(
        fingerprint='seed-public-crm-alert',
        defaults={
            'document': doc2,
            'category': Alert.Category.PUBLIC_SHARING,
            'severity': Alert.Severity.CRITICAL,
            'status': Alert.Status.OPEN,
            'title': 'Public Access Enabled: Customer Support CRM',
            'description': 'Document is published to the public internet without domain-level restriction.',
            'metadata': {'sharing_mode': 'public', 'is_published': True, 'permission_id': 'perm_pub_9921'},
        }
    )
    Alert.objects.get_or_create(
        fingerprint='seed-api-key-devops-alert',
        defaults={
            'document': doc3,
            'category': Alert.Category.SENSITIVE_TABLE,
            'severity': Alert.Severity.CRITICAL,
            'status': Alert.Status.OPEN,
            'title': 'Live AWS/Stripe API Key Exposed in Table',
            'description': 'Found unmasked live API credential (sk_live_••••••••) in column "Prod_Secret" row 4.',
            'metadata': {
                'table_id': 'grid_credentials',
                'row_id': 'i-row_88291',
                'column_name': 'Prod_Secret',
                'matched_pattern': 'api_key',
                'masked_value': 'sk_live_••••••••9a12',
            }
        }
    )
    Alert.objects.get_or_create(
        fingerprint='seed-unused-marketing-alert',
        defaults={
            'document': doc4,
            'category': Alert.Category.UNUSED_DOC,
            'severity': Alert.Severity.MEDIUM,
            'status': Alert.Status.OPEN,
            'title': 'Unused document: "Legacy Marketing Campaign Analysis 2023"',
            'description': 'This document has not been modified in 150 days (threshold: 90 days).',
            'metadata': {'days_since_update': 150, 'threshold_days': 90},
        }
    )
    Alert.objects.get_or_create(
        fingerprint='seed-sensitive-ssn-financial-alert',
        defaults={
            'document': doc1,
            'category': Alert.Category.SENSITIVE_TABLE,
            'severity': Alert.Severity.HIGH,
            'status': Alert.Status.OPEN,
            'title': 'PII & SSN Pattern Found in Vendor Payouts',
            'description': 'Found Social Security Number pattern in column "Tax_ID" row 12.',
            'metadata': {
                'table_id': 'grid_payouts',
                'row_id': 'i-row_55142',
                'column_name': 'Tax_ID',
                'matched_pattern': 'ssn',
                'masked_value': '•••-••-6789',
            }
        }
    )


@shared_task(bind=True, max_retries=1)
def sync_documents(self):
    """
    Sync document metadata from Coda API to the local database.
    """
    config = ScanConfig.get_config()
    if not config.coda_api_token:
        ensure_initial_seed_data()
        return {'status': 'completed', 'message': 'Demo documents active (No live token)'}

    client = CodaClient(api_token=config.coda_api_token)
    synced_count = 0
    errors = []

    try:
        docs = client.list_documents()
        logger.info("Fetched %d documents from Coda API", len(docs))

        for doc_data in docs:
            try:
                doc, created = CodaDocument.objects.update_or_create(
                    doc_id=doc_data['id'],
                    defaults={
                        'name': doc_data.get('name', 'Untitled'),
                        'owner_email': doc_data.get('owner', ''),
                        'folder_id': doc_data.get('folderId', ''),
                        'created_at': doc_data.get('createdAt', timezone.now().isoformat()),
                        'updated_at': doc_data.get('updatedAt', timezone.now().isoformat()),
                        'is_published': doc_data.get('published', {}).get('browserLink', '') != '',
                        'browser_link': doc_data.get('browserLink', ''),
                    },
                )
                synced_count += 1
            except Exception as e:
                errors.append({'doc_id': doc_data.get('id'), 'error': str(e)})

    except CodaAPIError as e:
        logger.error("Coda API error during document sync: %s", str(e))
        return {'status': 'error', 'message': str(e)}

    return {'status': 'completed', 'synced': synced_count, 'errors': errors}


@shared_task(bind=True, max_retries=1)
def run_full_scan(self, trigger='scheduled'):
    """
    Execute a full security scan across all monitored documents.
    """
    config = ScanConfig.get_config()
    ensure_initial_seed_data()

    scan_run = ScanRun.objects.create(trigger=trigger)
    logger.info("Starting scan run %s (trigger=%s)", scan_run.id, trigger)

    _notify_websocket('scan_started', {
        'scan_id': str(scan_run.id),
        'timestamp': timezone.now().isoformat(),
    })

    client = CodaClient(api_token=config.coda_api_token)
    total_alerts = 0
    scan_errors = []

    try:
        if config.coda_api_token:
            sync_documents()

        documents = list(CodaDocument.objects.filter(is_active=True))
        scan_run.docs_scanned = len(documents)
        scan_run.save()

        enabled_detectors = DetectorRegistry.get_enabled(config.enabled_detectors or [])
        if not enabled_detectors:
            enabled_detectors = list(DetectorRegistry.get_all().values())

        for detector in enabled_detectors:
            try:
                alert_dicts = detector.detect(documents, client)
                for alert_data in alert_dicts:
                    try:
                        alert, created = Alert.objects.get_or_create(
                            fingerprint=alert_data['fingerprint'],
                            defaults={
                                'document': alert_data['document'],
                                'category': alert_data['category'],
                                'severity': alert_data['severity'],
                                'title': alert_data['title'],
                                'description': alert_data['description'],
                                'metadata': alert_data['metadata'],
                            }
                        )
                        if created:
                            total_alerts += 1
                            _notify_websocket('new_alert', {
                                'alert_id': str(alert.id),
                                'category': alert.category,
                                'severity': alert.severity,
                                'title': alert.title,
                                'document_name': alert.document.name,
                                'detected_at': alert.detected_at.isoformat() if alert.detected_at else None,
                            })
                    except IntegrityError:
                        pass
            except Exception as e:
                scan_errors.append(f"{detector.name}: {str(e)}")

        CodaDocument.objects.filter(is_active=True).update(last_scanned=timezone.now())

        scan_run.alerts_created = total_alerts
        scan_run.status = ScanRun.Status.COMPLETED
        scan_run.completed_at = timezone.now()
        scan_run.errors = scan_errors
        scan_run.save()

        _notify_websocket('scan_completed', {
            'scan_id': str(scan_run.id),
            'docs_scanned': scan_run.docs_scanned,
            'alerts_created': total_alerts,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        scan_run.status = ScanRun.Status.FAILED
        scan_run.completed_at = timezone.now()
        scan_run.errors = scan_errors + [str(e)]
        scan_run.save()
        _notify_websocket('scan_failed', {
            'scan_id': str(scan_run.id),
            'error': str(e),
        })

    return {
        'scan_id': str(scan_run.id),
        'status': scan_run.status,
        'docs_scanned': scan_run.docs_scanned,
        'alerts_created': total_alerts,
        'errors': scan_errors,
    }
