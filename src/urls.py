"""Web UI URL patterns."""

from django.urls import path, include

# Use absolute imports since /app/src is in PYTHONPATH
import views
from health import HealthAPIView, HealthDashboardView
from views.services import (
    ServicesListView,
    ServiceDetailView,
    list_services,
    run_analyze_analysis,
    run_service_test,
)

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
    # Service management
    path("services/", ServicesListView.as_view(), name="services_list"),
    path("services/<str:service_name>/", ServiceDetailView.as_view(), name="service_detail"),
    path("services/<str:service_name>/test/", run_service_test, name="service_test"),
    path("services/analyze/run/", run_analyze_analysis, name="run_analyze"),
    # Health monitoring
    path("ready", views.ready_check, name="ready_check_no_slash"),  # K8s probes (no slash)
    path("ready/", views.ready_check, name="ready_check"),  # K8s probes
    path("health", HealthAPIView.as_view(), name="health_api_no_slash"),  # K8s probes
    path("health/", HealthAPIView.as_view(), name="health_api"),
    path("health/dashboard/", HealthDashboardView.as_view(), name="health_dashboard"),
    # API endpoints (migrated from FastAPI)
    path("api/health", views.api_health_check, name="api_health"),
    path("api/performance", views.api_performance, name="api_performance"),
    path("api/signals", views.api_signals, name="api_signals"),
    path("api/assets", views.api_assets, name="api_assets"),
    # Portfolio app
    path("portfolio/", include("portfolio.urls")),
    # Dev interface
    path("dev/", include("dev.urls")),
]
