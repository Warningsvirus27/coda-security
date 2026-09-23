"""
SecureCoda — Sensitive Data in Pages Detector

Exports page content (HTML) and scans for sensitive information patterns.
Uses the async Coda export API with polling.
"""
import logging
import re
from .base import BaseDetector
from .patterns import scan_text
from scanner.registry import DetectorRegistry

logger = logging.getLogger('scanner')

# Simple HTML tag stripper for extracting text content
HTML_TAG_RE = re.compile(r'<[^>]+>')


def strip_html(html_content: str) -> str:
    """Remove HTML tags and extract plain text."""
    text = HTML_TAG_RE.sub(' ', html_content)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


@DetectorRegistry.register
class SensitivePagesDetector(BaseDetector):
    name = 'sensitive_pages'
    category = 'sensitive_page'
    description = 'Exports and scans page content for sensitive data patterns'

    def detect(self, documents: list, coda_client) -> list[dict]:
        """
        For each document:
        1. List all pages
        2. Export each page as HTML (async operation)
        3. Strip HTML and scan text content for sensitive patterns
        """
        alerts = []

        for doc in documents:
            try:
                pages = coda_client.list_pages(doc.doc_id)
            except Exception as e:
                logger.warning("Could not list pages for doc %s: %s", doc.doc_id, str(e))
                continue

            for page in pages:
                page_id = page.get('id', '')
                page_name = page.get('name', 'Unknown Page')

                logger.debug("Scanning page '%s' in doc '%s'", page_name, doc.name)

                # Export page content
                try:
                    html_content = coda_client.export_page(doc.doc_id, page_id, 'html')
                except Exception as e:
                    logger.warning(
                        "Could not export page %s ('%s') in doc %s: %s",
                        page_id, page_name, doc.doc_id, str(e)
                    )
                    continue

                if not html_content:
                    continue

                # Strip HTML to get plain text
                plain_text = strip_html(html_content)
                if not plain_text or len(plain_text) < 5:
                    continue

                # Scan for sensitive patterns
                findings = scan_text(plain_text)
                for finding in findings:
                    # Create a redacted context snippet
                    snippet = self._extract_snippet(plain_text, finding['masked_value'])

                    alerts.append(self.create_alert_dict(
                        document=doc,
                        severity=finding['severity'],
                        title=(
                            f'{finding["description"]} in page "{page_name}"'
                        ),
                        description=(
                            f'Sensitive data ({finding["description"]}) found in '
                            f'page "{page_name}" of document "{doc.name}". '
                            f'Matched pattern: {finding["pattern_name"]}. '
                            f'Context: ...{snippet}...'
                        ),
                        metadata={
                            'page_id': page_id,
                            'page_name': page_name,
                            'pattern_name': finding['pattern_name'],
                            'pattern_category': finding['category'],
                            'masked_value': finding['masked_value'],
                            'snippet': snippet,
                            'issue_type': 'sensitive_page_content',
                        },
                        fingerprint_parts=[
                            'page', page_id, finding['pattern_name'],
                            finding['masked_value'],
                        ],
                    ))

        logger.info("Sensitive pages detector found %d alerts", len(alerts))
        return alerts

    @staticmethod
    def _extract_snippet(text: str, masked_value: str, context_chars: int = 50) -> str:
        """
        Extract a short snippet of text around the masked value for context.
        Returns a redacted snippet safe for storage.
        """
        # Search for the start of the masked value (before the ***)
        prefix = masked_value.split('***')[0]
        if not prefix:
            return '[content redacted]'

        idx = text.find(prefix)
        if idx == -1:
            return '[content redacted]'

        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(prefix) + context_chars)
        snippet = text[start:end]

        # Ensure we don't leak the full sensitive value
        return snippet[:100] + '...' if len(snippet) > 100 else snippet
