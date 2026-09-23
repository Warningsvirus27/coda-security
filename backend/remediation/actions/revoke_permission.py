import logging
from core.models import Alert
from .base import BaseAction, ActionResult

logger = logging.getLogger('remediation.revoke_permission')


class RevokePermissionAction(BaseAction):
    name = "revoke_permission"
    label = "Revoke Public / External Access"
    description = "Removes public or untrusted external access permissions from the document."
    applicable_categories = ["public_sharing"]

    def execute(self, alert: Alert, coda_client, user=None) -> ActionResult:
        doc_id = alert.document.doc_id
        perm_id = (alert.metadata or {}).get('permission_id')

        try:
            if coda_client and getattr(coda_client, 'is_configured', True):
                if perm_id:
                    coda_client.delete_permission(doc_id, perm_id)
            alert.document.sharing_mode = 'private'
            alert.document.is_published = False
            alert.document.save()
            return ActionResult(
                True,
                f"Sharing permission revoked for document '{alert.document.name}'. Sharing mode reset to private.",
                {'doc_id': doc_id, 'permission_id': perm_id},
            )
        except Exception as e:
            logger.error("Failed to revoke permission on doc %s: %s", doc_id, e)
            return ActionResult(False, f"Coda API error: {str(e)}")
