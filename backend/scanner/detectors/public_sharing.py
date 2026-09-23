"""
SecureCoda — Public Sharing Detector

Detects documents that are publicly accessible or shared with
external domains, potentially exposing sensitive information.
"""
import logging
from core.models import ScanConfig
from .base import BaseDetector
from scanner.registry import DetectorRegistry

logger = logging.getLogger('scanner')


@DetectorRegistry.register
class PublicSharingDetector(BaseDetector):
    name = 'public_sharing'
    category = 'public_sharing'
    description = 'Detects documents with public or external sharing configurations'

    def detect(self, documents: list, coda_client) -> list[dict]:
        """
        For each document:
        1. Check if isPublished is True (publicly accessible via URL)
        2. Query ACL permissions and flag:
           - 'anyone' type permissions (public access)
           - External domain emails (not in internal_domains config)
        """
        config = ScanConfig.get_config()
        internal_domains = [d.lower().strip() for d in (config.internal_domains or [])]
        alerts = []

        logger.info("Running public sharing detector (internal_domains=%s)", internal_domains)

        for doc in documents:
            # Check 1: Published documents
            if doc.is_published:
                alerts.append(self.create_alert_dict(
                    document=doc,
                    severity='critical',
                    title=f'Published document: "{doc.name}"',
                    description=(
                        'This document is published and publicly accessible via URL. '
                        'Anyone with the link can view its contents. '
                        'Consider unpublishing if it contains sensitive information.'
                    ),
                    metadata={
                        'issue_type': 'published',
                        'browser_link': doc.browser_link,
                    },
                    fingerprint_parts=['published'],
                ))

            # Check 2: ACL permissions
            try:
                permissions = coda_client.get_permissions(doc.doc_id)
            except Exception as e:
                logger.warning("Could not fetch permissions for doc %s: %s", doc.doc_id, str(e))
                continue

            for perm in permissions:
                perm_type = perm.get('access', '')
                principal = perm.get('principal', {})
                principal_type = principal.get('type', '')
                principal_email = principal.get('email', '')

                # Anyone / public access
                if principal_type == 'anyone' or principal_type == 'domain':
                    alerts.append(self.create_alert_dict(
                        document=doc,
                        severity='critical',
                        title=f'Public access on: "{doc.name}"',
                        description=(
                            f'This document has a "{principal_type}" permission '
                            f'with "{perm_type}" access. This means it may be accessible '
                            f'to anyone or an entire domain without explicit invitation.'
                        ),
                        metadata={
                            'issue_type': 'public_permission',
                            'permission_id': perm.get('id', ''),
                            'principal_type': principal_type,
                            'access_level': perm_type,
                        },
                        fingerprint_parts=['public_perm', perm.get('id', '')],
                    ))

                # External email sharing
                elif principal_email and internal_domains:
                    email_domain = principal_email.split('@')[-1].lower()
                    if email_domain not in internal_domains:
                        alerts.append(self.create_alert_dict(
                            document=doc,
                            severity='high',
                            title=f'External sharing on: "{doc.name}"',
                            description=(
                                f'This document is shared with an external user '
                                f'({principal_email}) from domain "{email_domain}". '
                                f'Ensure this sharing is intentional and appropriate.'
                            ),
                            metadata={
                                'issue_type': 'external_sharing',
                                'permission_id': perm.get('id', ''),
                                'external_email': principal_email,
                                'external_domain': email_domain,
                                'access_level': perm_type,
                            },
                            fingerprint_parts=['external', principal_email],
                        ))

        logger.info("Public sharing detector found %d alerts", len(alerts))
        return alerts
