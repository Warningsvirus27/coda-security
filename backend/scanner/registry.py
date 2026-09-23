"""
SecureCoda — Detector Registry

Central registry for all available detectors.
Detectors self-register on import, making it trivial to add new ones.
"""
import logging

logger = logging.getLogger('scanner')


class DetectorRegistry:
    """
    Registry for security detectors.
    Detectors register themselves, and the scanner engine queries this
    registry to get the list of enabled detectors.
    """

    _detectors: dict = {}

    @classmethod
    def register(cls, detector_class):
        """
        Register a detector class. Can be used as a decorator.

        Usage:
            @DetectorRegistry.register
            class MyDetector(BaseDetector):
                ...
        """
        instance = detector_class()
        cls._detectors[instance.name] = instance
        logger.debug("Registered detector: %s", instance.name)
        return detector_class

    @classmethod
    def get_all(cls) -> dict:
        """Return all registered detectors."""
        return cls._detectors.copy()

    @classmethod
    def get_enabled(cls, enabled_names: list) -> list:
        """Return only detectors whose names are in the enabled list."""
        return [
            detector
            for name, detector in cls._detectors.items()
            if name in enabled_names
        ]

    @classmethod
    def get_detector(cls, name: str):
        """Get a specific detector by name."""
        return cls._detectors.get(name)

    @classmethod
    def list_names(cls) -> list[str]:
        """List all registered detector names."""
        return list(cls._detectors.keys())
