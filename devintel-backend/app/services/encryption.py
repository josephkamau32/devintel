"""Encryption utilities for securing sensitive data like GitHub tokens."""

from typing import Optional

from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key from settings."""
        self.cipher = Fernet(settings.token_encryption_key.encode())
        logger.info("Encryption service initialized with configured key")
    
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


# Global encryption service instance
encryption_service = EncryptionService()
