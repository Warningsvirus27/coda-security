import logging
from core.models import Alert
from .base import BaseAction, ActionResult

logger = logging.getLogger('remediation.delete_document')


class DeleteDocumentAction(BaseAction):
    name = "delete_document"
    label = "Delete Unused Document"
    description = "Permanently archives or deletes the stale/unused document."
    applicable_categories = ["unused_doc"]

    def execute(self, alert: Alert, coda_client, user=None) -> ActionResult:
        doc_id = alert.document.doc_id
        try:
            if coda_client and getattr(coda_client, 'is_configured', True):
                coda_client.delete_document(doc_id)
            alert.document.is_active = False
            alert.document.save()
            return ActionResult(
                True,
                f"Document '{alert.document.name}' ({doc_id}) marked inactive and deleted from Coda.",
                {'doc_id': doc_id},
            )
        except Exception as e:
            logger.error("Failed to delete document %s: %s", doc_id, e)
            return ActionResult(False, f"Coda API error: {str(e)}")
