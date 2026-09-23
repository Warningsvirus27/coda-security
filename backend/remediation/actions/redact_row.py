import logging
from core.models import Alert
from .base import BaseAction, ActionResult

logger = logging.getLogger('remediation.redact_row')


class RedactRowAction(BaseAction):
    name = "redact_row"
    label = "Redact Sensitive Cell"
    description = "Replaces detected sensitive values with [REDACTED] in Coda."
    applicable_categories = ["sensitive_table"]

    def execute(self, alert: Alert, coda_client, user=None) -> ActionResult:
        meta = alert.metadata or {}
        table_id = meta.get('table_id')
        row_id = meta.get('row_id')
        column_name = meta.get('column_name') or meta.get('column_id')
        doc_id = alert.document.doc_id

        if not table_id or not row_id or not column_name:
            return ActionResult(False, "Missing table, row, or column information in alert metadata.")

        try:
            if coda_client and getattr(coda_client, 'is_configured', True):
                coda_client.update_row(doc_id, table_id, row_id, {column_name: "[REDACTED]"})
            return ActionResult(
                True,
                f"Redacted sensitive content in column '{column_name}' for row {row_id}.",
                {'doc_id': doc_id, 'table_id': table_id, 'row_id': row_id, 'column': column_name},
            )
        except Exception as e:
            logger.error("Failed to redact row %s: %s", row_id, e)
            return ActionResult(False, f"Coda API error: {str(e)}")
