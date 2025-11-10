"""
Views package for the web service.
Exports main views and services views.
"""

# Import main views
from .main import (
    HomeView,
    CustomLoginView,
    CustomLogoutView,
    DashboardView,
    MetricsView,
    SignalsView,
    IntelligenceView,
    BacktestView,
    SettingsView,
    approve_signal,
    reject_signal,
    approve_all_signals,
    reject_all_signals,
    ready_check,
    api_health_check,
    api_performance,
    api_signals,
    api_assets,
)

# Import services views
from . import services

__all__ = [
    "HomeView",
    "CustomLoginView",
    "CustomLogoutView",
    "DashboardView",
    "MetricsView",
    "SignalsView",
    "IntelligenceView",
    "BacktestView",
    "SettingsView",
    "approve_signal",
    "reject_signal",
    "approve_all_signals",
    "reject_all_signals",
    "ready_check",
    "api_health_check",
    "api_performance",
    "api_signals",
    "api_assets",
    "services",
]

