"""Portfolio app configuration"""
from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    """Portfolio app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portfolio'
    verbose_name = 'Portfolio Management'

