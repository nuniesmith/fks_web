"""
User models for authentication.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser."""
    
    # Add custom fields here if needed
    api_key = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "auth_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

