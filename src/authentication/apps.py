"""
App configuration for authentication app.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration for authentication app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"
    verbose_name = "Authentication"

