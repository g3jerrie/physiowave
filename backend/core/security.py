"""PhysioWave — PII Encryption Service.

HIPAA Compliance Note: This module provides AES-256 encryption for all
Protected Health Information (PHI/PII) before storage in SQLite.
Uses Fernet (AES-128-CBC with HMAC-SHA256) from the cryptography library.

All PII MUST pass through this service before database writes.
"""

from cryptography.fernet import Fernet, InvalidToken

from backend.core.config import settings
from backend.core.logger import logger

# ─── PII Field Definitions ────────────────────────────────────────────

PII_FIELDS = frozenset({
    "patient_name",
    "date_of_birth",
    "phone_number",
    "email",
    "address",
    "medical_record_number",
    "insurance_id",
    "emergency_contact",
})

REDACTION_PLACEHOLDER = "[REDACTED-PII]"


class EncryptionService:
    """AES-256 encryption for PII fields.

    HIPAA Compliance Note: The encryption key MUST be stored securely
    in the .env file and never committed to version control.
    """

    def __init__(self, key: str | None = None):
        raw_key = key or settings.encryption_key
        if not raw_key:
            logger.warning(
                "No encryption key configured — PII will NOT be encrypted! "
                "Set ENCRYPTION_KEY in .env for HIPAA compliance."
            )
            self._fernet = None
        else:
            self._fernet = Fernet(raw_key.encode())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
        if not self._fernet:
            return plaintext  # No-op if key not configured
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string. Returns plaintext."""
        if not self._fernet:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt PII — invalid key or corrupted data")
            return REDACTION_PLACEHOLDER

    def encrypt_pii_dict(self, data: dict[str, str]) -> dict[str, str]:
        """Encrypt all PII fields in a dictionary."""
        result = {}
        for key, value in data.items():
            if key in PII_FIELDS and value:
                result[key] = self.encrypt(value)
            else:
                result[key] = value
        return result

    def decrypt_pii_dict(self, data: dict[str, str]) -> dict[str, str]:
        """Decrypt all PII fields in a dictionary."""
        result = {}
        for key, value in data.items():
            if key in PII_FIELDS and value:
                result[key] = self.decrypt(value)
            else:
                result[key] = value
        return result

    @property
    def is_configured(self) -> bool:
        return self._fernet is not None


def redact_pii(text: str) -> str:
    """Redact known PII patterns from log output."""
    sanitized = text
    for field in PII_FIELDS:
        # Match "field_name: value" or "field_name=value"
        import re
        pattern = re.compile(rf"({field})\s*[:=]\s*\S+", re.IGNORECASE)
        sanitized = pattern.sub(rf"\1: {REDACTION_PLACEHOLDER}", sanitized)
    return sanitized


# Singleton instance
encryption_service = EncryptionService()
