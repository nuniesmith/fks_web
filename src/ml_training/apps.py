"""
Django app configuration for ML Training.
"""

from django.apps import AppConfig


class MLTrainingConfig(AppConfig):
    """Configuration for ML Training app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ml_training"
    verbose_name = "ML Training"

    def ready(self):
        """Import tasks when app is ready."""
        try:
            import ml_training.tasks  # noqa: F401
        except ImportError:
            pass

