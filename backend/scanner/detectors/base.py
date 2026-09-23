"""
SecureCoda — Base Detector Interface

Abstract base class that all detectors must implement.
Provides a consistent interface for the scanning engine.
"""
import hashlib
from abc import ABC, abstractmethod
from typing import Optional
from core.models import CodaDocument, Alert


class BaseDetector(ABC):
    """
    Abstract base class for security detectors.

    Each detector scans documents for a specific type of security issue
    and returns a list of Alert objects to be persisted.
    """

    # Subclasses must define these
    name: str = ''
    category: str = ''
    description: str = ''

    @abstractmethod
    def detect(self, documents: list, coda_client) -> list[dict]:
        """
        Run detection logic against a set of documents.

        Args:
            documents: List of CodaDocument model instances
            coda_client: Initialized CodaClient instance

        Returns:
            List of alert dicts ready to be created, each with keys:
            - document: CodaDocument instance
            - category: str
            - severity: str
            - title: str
            - description: str
            - metadata: dict
            - fingerprint: str (unique dedup key)
        """
        pass

    @staticmethod
    def generate_fingerprint(*parts) -> str:
        """
        Generate a unique fingerprint hash for deduplication.
        Combines multiple parts into a single SHA-256 hash.
        """
        combined = '|'.join(str(p) for p in parts)
        return hashlib.sha256(combined.encode()).hexdigest()

    def create_alert_dict(
        self,
        document: CodaDocument,
        severity: str,
        title: str,
        description: str,
        metadata: dict,
        fingerprint_parts: list,
    ) -> dict:
        """
        Helper to create a standardized alert dictionary.
        """
        return {
            'document': document,
            'category': self.category,
            'severity': severity,
            'title': title,
            'description': description,
            'metadata': metadata,
            'fingerprint': self.generate_fingerprint(
                document.doc_id, self.category, *fingerprint_parts
            ),
        }
