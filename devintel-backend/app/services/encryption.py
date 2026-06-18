"""Encryption utilities for securing sensitive data like GitHub tokens."""

from typing import Optional

from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, key: Optional[str] = None):
        """Initialize encryption service with key from settings or provided key."""
        enc_key = key or settings.TOKEN_ENCRYPTION_KEY
        if not enc_key:
            enc_key = Fernet.generate_key().decode()
            logger.warning("Using auto-generated encryption key")
        self.cipher = Fernet(enc_key.encode())
        logger.info("Encryption service initialized")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""

        encrypted = self.cipher.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string to decrypt

        Returns:
            Decrypted plaintext string or None if decryption fails
        """
        if not ciphertext:
            return None

        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a new encryption key.

        Returns:
            Base64-encoded encryption key suitable for Fernet
        """
        return Fernet.generate_key().decode()


# Global encryption service instance (initialized lazily)
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        key = settings.TOKEN_ENCRYPTION_KEY
        if not key:
            # Generate a key for development (WARNING: tokens will be lost on restart)
            logger.warning("TOKEN_ENCRYPTION_KEY not set, using temporary key")
            key = Fernet.generate_key().decode()
        _encryption_service = EncryptionService(key)
    return _encryption_service


# For backwards compatibility - provides lazy initialization
class _LazyEncryptionService:
    def __getattr__(self, name):
        return getattr(get_encryption_service(), name)


encryption_service = _LazyEncryptionService()
