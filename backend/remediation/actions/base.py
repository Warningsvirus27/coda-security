from abc import ABC, abstractmethod
from typing import Any, Dict, List
from core.models import Alert


class ActionResult:
    def __init__(self, success: bool, message: str, details: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.details = details or {}


class BaseAction(ABC):
    """
    Abstract base class for all pluggable remediation actions.
    """
    name: str = ""
    label: str = ""
    description: str = ""
    applicable_categories: List[str] = []

    @abstractmethod
    def execute(self, alert: Alert, coda_client, user=None) -> ActionResult:
        """Executes the remediation action against Coda API and updates local state."""
        pass
