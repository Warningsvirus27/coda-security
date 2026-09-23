"""
SecureCoda — Unused Documents Detector

Flags documents that haven't been accessed or modified within a
configurable timeframe (days, hours, minutes). The threshold is set via
the ScanConfig model and can be changed from the dashboard Settings page.
"""
import logging
from django.utils import timezone
from core.models import ScanConfig
from .base import BaseDetector
from scanner.registry import DetectorRegistry

logger = logging.getLogger('scanner')


@DetectorRegistry.register
class UnusedDocumentsDetector(BaseDetector):
    name = 'unused_docs'
    category = 'unused_doc'
    description = 'Detects documents that have not been modified within the configured threshold'

    def detect(self, documents: list, coda_client) -> list[dict]:
        config = ScanConfig.get_config()
        val = config.unused_threshold_value
        unit = config.unused_threshold_unit
        now = timezone.now()
        alerts = []

        logger.info("Running unused docs detector (threshold=%d %s)", val, unit)

        for doc in documents:
            delta_seconds = (now - doc.updated_at).total_seconds()

            if unit == 'minutes':
                elapsed = int(delta_seconds // 60)
                is_unused = elapsed >= val
                warning = elapsed >= int(val * 0.66)
                unit_label = 'minutes'
            elif unit == 'hours':
                elapsed = int(delta_seconds // 3600)
                is_unused = elapsed >= val
                warning = elapsed >= int(val * 0.66)
                unit_label = 'hours'
            else:
                elapsed = int(delta_seconds // 86400)
                is_unused = elapsed >= val
                warning = elapsed >= int(val * 0.66)
                unit_label = 'days'

            if is_unused:
                alerts.append(self.create_alert_dict(
                    document=doc,
                    severity='medium',
                    title=f'Unused document: "{doc.name}"',
                    description=(
                        f'This document has not been modified in {elapsed} {unit_label} '
                        f'(configured threshold: {val} {unit_label}). Consider archiving or '
                        f'deleting it to reduce security exposure.'
                    ),
                    metadata={
                        'elapsed': elapsed,
                        'unit': unit_label,
                        'threshold_value': val,
                        'last_updated': doc.updated_at.isoformat(),
                    },
                    fingerprint_parts=['unused', unit_label, str(val)],
                ))
            elif warning and val > 1:
                alerts.append(self.create_alert_dict(
                    document=doc,
                    severity='low',
                    title=f'Document approaching inactivity: "{doc.name}"',
                    description=(
                        f'This document has not been modified in {elapsed} {unit_label}. '
                        f'It will reach the inactivity threshold ({val} {unit_label}) soon.'
                    ),
                    metadata={
                        'elapsed': elapsed,
                        'unit': unit_label,
                        'threshold_value': val,
                        'last_updated': doc.updated_at.isoformat(),
                    },
                    fingerprint_parts=['approaching_unused', unit_label, str(val)],
                ))

        logger.info("Unused docs detector found %d alerts", len(alerts))
        return alerts
