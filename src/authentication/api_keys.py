"""
API Key management models with encryption for secure storage.

This module provides models and utilities for managing API keys that can be
assigned to users or used globally for services like Polygon, CoinMarketCap, etc.
"""
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable.
    
    Generates a new key if ENCRYPTION_KEY is not set (for development only).
    In production, ENCRYPTION_KEY must be set.
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Development fallback - generate a key (not secure for production!)
        # In production, this should raise an error
        if os.getenv("DEBUG", "False") == "True":
            import warnings
            warnings.warn(
                "ENCRYPTION_KEY not set. Using generated key (not secure for production!)",
                UserWarning
            )
            return Fernet.generate_key()
        raise ValueError(
            "ENCRYPTION_KEY environment variable must be set in production"
        )
    
    # Ensure key is bytes
    if isinstance(key, str):
        key = key.encode()
    
    return key


class APIKey(models.Model):
    """
    Encrypted API key storage model.
    
    Supports both global keys (for app-wide use) and user-assignable keys.
    """
    
    # Key identification
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique name for this API key (e.g., 'polygon_prod', 'cmc_free_tier')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this API key is used for"
    )
    
    # Encrypted storage
    encrypted_api_key = models.BinaryField(
        help_text="Encrypted API key value"
    )
    
    # Assignment and access control
    is_global = models.BooleanField(
        default=True,
        help_text="If True, key is available globally. If False, assigned to specific users."
    )
    assigned_to = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="api_keys",
        help_text="User this key is assigned to (if not global)"
    )
    
    # Metadata
    provider = models.CharField(
        max_length=100,
        blank=True,
        help_text="API provider name (e.g., 'polygon', 'coinmarketcap', 'binance')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this key is currently active"
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this key was used"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration date for the key"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_api_keys",
        help_text="User who created this key"
    )
    
    class Meta:
        db_table = "api_keys"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["is_active"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.provider or 'unknown'})"
    
    @property
    def key(self) -> str:
        """
        Decrypt and return the API key.
        
        Raises:
            ValueError: If decryption fails
        """
        if not self.encrypted_api_key:
            return ""
        
        try:
            cipher_suite = Fernet(get_encryption_key())
            decrypted = cipher_suite.decrypt(self.encrypted_api_key)
            return decrypted.decode("utf-8")
        except InvalidToken:
            raise ValueError(f"Failed to decrypt API key for {self.name}")
        except Exception as e:
            raise ValueError(f"Error decrypting API key: {e}")
    
    @key.setter
    def key(self, value: str) -> None:
        """
        Encrypt and store the API key.
        
        Args:
            value: Plain text API key to encrypt
        """
        if not value:
            self.encrypted_api_key = b""
            return
        
        try:
            cipher_suite = Fernet(get_encryption_key())
            encrypted = cipher_suite.encrypt(value.encode("utf-8"))
            self.encrypted_api_key = encrypted
        except Exception as e:
            raise ValueError(f"Error encrypting API key: {e}")
    
    def clean(self):
        """Validate model before saving."""
        super().clean()
        
        # Ensure either global or assigned to user
        if not self.is_global and not self.assigned_to:
            raise ValidationError(
                "Non-global keys must be assigned to a user"
            )
        
        # Check expiration
        if self.expires_at and self.expires_at < timezone.now():
            self.is_active = False
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def mark_used(self):
        """Mark this key as used (update last_used timestamp)."""
        self.last_used = timezone.now()
        self.save(update_fields=["last_used"])
    
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()
    
    @classmethod
    def get_key(cls, name: str, user: Optional["User"] = None) -> Optional[str]:
        """
        Get decrypted API key by name.
        
        Args:
            name: Key name
            user: Optional user to check for user-assigned keys
        
        Returns:
            Decrypted key or None if not found
        """
        try:
            # Try global key first
            key_obj = cls.objects.get(name=name, is_global=True, is_active=True)
            if not key_obj.is_expired():
                return key_obj.key
            
            # Try user-assigned key if user provided
            if user:
                key_obj = cls.objects.get(
                    name=name,
                    is_global=False,
                    assigned_to=user,
                    is_active=True
                )
                if not key_obj.is_expired():
                    return key_obj.key
        except cls.DoesNotExist:
            pass
        
        return None
    
    @classmethod
    def get_key_for_provider(cls, provider: str, user: Optional["User"] = None) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (e.g., 'polygon', 'cmc')
            user: Optional user to check for user-assigned keys
        
        Returns:
            Decrypted key or None if not found
        """
        try:
            # Try global key first
            key_obj = cls.objects.filter(
                provider=provider,
                is_global=True,
                is_active=True
            ).first()
            
            if key_obj and not key_obj.is_expired():
                return key_obj.key
            
            # Try user-assigned key if user provided
            if user:
                key_obj = cls.objects.filter(
                    provider=provider,
                    is_global=False,
                    assigned_to=user,
                    is_active=True
                ).first()
                
                if key_obj and not key_obj.is_expired():
                    return key_obj.key
        except Exception:
            pass
        
        return None

