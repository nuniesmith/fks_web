"""
App configuration for data_collection app.
"""

from django.apps import AppConfig


class DataCollectionConfig(AppConfig):
    """Configuration for data collection app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "data_collection"
    verbose_name = "Data Collection"

