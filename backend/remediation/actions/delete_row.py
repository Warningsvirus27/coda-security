import logging
from core.models import Alert
from .base import BaseAction, ActionResult

logger = logging.getLogger('remediation.delete_row')


class DeleteRowAction(BaseAction):
    name = "delete_row"
    label = "Delete Vulnerable Row"
    description = "Permanently deletes the table row containing sensitive data from Coda."
    applicable_categories = ["sensitive_table"]

    def execute(self, alert: Alert, coda_client, user=None) -> ActionResult:
        meta = alert.metadata or {}
        table_id = meta.get('table_id')
        row_id = meta.get('row_id')
        doc_id = alert.document.doc_id

        if not table_id or not row_id:
            return ActionResult(False, "Missing table_id or row_id in alert metadata.")

        try:
            if coda_client and getattr(coda_client, 'is_configured', True):
                coda_client.delete_row(doc_id, table_id, row_id)
            return ActionResult(
                True,
                f"Row {row_id} deleted successfully from table {table_id}.",
                {'doc_id': doc_id, 'table_id': table_id, 'row_id': row_id},
            )
        except Exception as e:
            logger.error("Failed to delete row %s: %s", row_id, e)
            return ActionResult(False, f"Coda API error: {str(e)}")
