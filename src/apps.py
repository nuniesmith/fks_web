"""Web UI app configuration."""

from django.apps import AppConfig


class WebAppConfig(AppConfig):
    """Web UI with Django templates (replaces React frontend)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "web"  # Fixed: was 'web_app' but directory is 'web'
    verbose_name = "FKS Web Interface"

    def ready(self):
        """Initialize web app on ready."""
        pass  # Register template tags/filters here when needed
