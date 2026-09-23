from typing import Dict, List, Optional
from .base import BaseAction
from .delete_row import DeleteRowAction
from .redact_row import RedactRowAction
from .delete_document import DeleteDocumentAction
from .revoke_permission import RevokePermissionAction


class ActionRegistry:
    _actions: Dict[str, BaseAction] = {}

    @classmethod
    def register(cls, action_class):
        instance = action_class()
        cls._actions[instance.name] = instance
        return action_class

    @classmethod
    def get(cls, name: str) -> Optional[BaseAction]:
        return cls._actions.get(name)

    @classmethod
    def get_for_category(cls, category: str) -> List[BaseAction]:
        return [a for a in cls._actions.values() if category in a.applicable_categories]

    @classmethod
    def all(cls) -> List[BaseAction]:
        return list(cls._actions.values())


# Register default actions
ActionRegistry.register(DeleteRowAction)
ActionRegistry.register(RedactRowAction)
ActionRegistry.register(DeleteDocumentAction)
ActionRegistry.register(RevokePermissionAction)
