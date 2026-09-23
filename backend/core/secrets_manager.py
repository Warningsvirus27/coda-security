import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Class-based secrets manager supporting dual-source retrieval:
    - AWS Secrets Manager via Boto3 (production / cloud deployment)
    - Local JSON file (development / staging / fallback)
    """

    _instance: Optional["SecretsManager"] = None
    _secrets_cache: Dict[str, Any] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SecretsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, secrets_file_name: str = "secrets.local.json"):
        if getattr(self, "_initialized", False):
            return
        self.secrets_file_name = secrets_file_name
        self._secrets_cache = {}
        self._load_secrets()
        self._initialized = True

    def _get_local_file_path(self) -> Path:
        """Locates the local secrets file across standard root and backend paths."""
        current_dir = Path(__file__).resolve().parent
        potential_paths = [
            current_dir / self.secrets_file_name,
            current_dir.parent / self.secrets_file_name,
            current_dir.parent.parent / self.secrets_file_name,
        ]
        for path in potential_paths:
            if path.is_file():
                return path
        return potential_paths[-1]

    def _load_from_aws(self) -> Dict[str, Any]:
        """Loads secrets from AWS Secrets Manager using Boto3."""
        secret_name = os.getenv("AWS_SECRETS_MANAGER_NAME", "securecoda/secrets")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        try:
            import boto3
            from botocore.exceptions import ClientError

            client = boto3.client(
                service_name="secretsmanager",
                region_name=region_name,
            )
            response = client.get_secret_value(SecretId=secret_name)
            if "SecretString" in response:
                return json.loads(response["SecretString"])
            return {}
        except Exception as e:
            logger.warning("Failed to fetch secrets from AWS Secrets Manager: %s. Falling back to local.", e)
            return {}

    def _load_from_local(self) -> Dict[str, Any]:
        """Loads secrets from local JSON file."""
        file_path = self._get_local_file_path()
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to parse local secrets JSON file at %s: %s", file_path, e)
        return {}

    def _load_secrets(self) -> None:
        """Determines secrets source based on environment configuration."""
        source = os.getenv("SECRETS_SOURCE", "LOCAL").strip().upper()
        secrets = {}
        if source == "AWS":
            secrets = self._load_from_aws()
            if not secrets:
                logger.info("AWS secrets empty or unavailable; checking local file.")
                secrets = self._load_from_local()
        else:
            secrets = self._load_from_local()

        self._secrets_cache = secrets

    def get(self, key: str, default: Any = None) -> Any:
        """Fetches a secret key from environment variable first, then cached secrets, then default."""
        env_val = os.getenv(key)
        if env_val is not None:
            return env_val
        return self._secrets_cache.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Returns all loaded secrets."""
        return dict(self._secrets_cache)

    def reload(self) -> None:
        """Reloads secrets from the configured provider."""
        self._load_secrets()
