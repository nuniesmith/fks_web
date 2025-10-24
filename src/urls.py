"""Web UI URL patterns."""

from django.urls import path

from . import views
from .health import HealthAPIView, HealthDashboardView

app_name = "web_app"

urlpatterns = [
    # Main UI Views
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("metrics/", views.MetricsView.as_view(), name="metrics"),
    # Trading Views
    path("signals/", views.SignalsView.as_view(), name="signals"),
    path("signals/approve/<int:signal_id>/", views.approve_signal, name="approve_signal"),
    path("signals/reject/<int:signal_id>/", views.reject_signal, name="reject_signal"),
    path("signals/approve-all/", views.approve_all_signals, name="approve_all_signals"),
    path("signals/reject-all/", views.reject_all_signals, name="reject_all_signals"),
    path("intelligence/", views.IntelligenceView.as_view(), name="intelligence"),
    path("backtest/", views.BacktestView.as_view(), name="backtest"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    # Health monitoring
    path("health/", HealthAPIView.as_view(), name="health_api"),
    path("health/dashboard/", HealthDashboardView.as_view(), name="health_dashboard"),
    # API endpoints (migrated from FastAPI)
    path("api/health", views.api_health_check, name="api_health"),
    path("api/performance", views.api_performance, name="api_performance"),
    path("api/signals", views.api_signals, name="api_signals"),
    path("api/assets", views.api_assets, name="api_assets"),
]
