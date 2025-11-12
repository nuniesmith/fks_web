"""Portfolio URL patterns"""
from django.urls import path
from . import views
from . import optimization_views
from . import health_views

app_name = "portfolio"

urlpatterns = [
    # Main portfolio views
    path("", views.PortfolioDashboardView.as_view(), name="dashboard"),
    path("signals/", views.PortfolioSignalsView.as_view(), name="signals"),
    path("signals/approve/<str:signal_id>/", views.approve_signal, name="approve_signal"),
    path("signals/reject/<str:signal_id>/", views.reject_signal, name="reject_signal"),
    path("performance/", views.PortfolioPerformanceView.as_view(), name="performance"),
    path("api/<path:endpoint>", views.portfolio_api_data, name="api_proxy"),
    
    # Portfolio Optimization Phase 1
    path("optimization/", optimization_views.OptimizationDashboardView.as_view(), name="optimization_dashboard"),
    path("optimization/accounts/", optimization_views.AccountInventoryView.as_view(), name="account_inventory"),
    path("optimization/accounts/add/", optimization_views.AccountCreateView.as_view(), name="account_create"),
    path("optimization/accounts/<int:pk>/edit/", optimization_views.AccountUpdateView.as_view(), name="account_update"),
    path("optimization/accounts/<int:pk>/delete/", optimization_views.AccountDeleteView.as_view(), name="account_delete"),
    path("optimization/risk/", optimization_views.RiskAssessmentView.as_view(), name="risk_assessment"),
    path("optimization/audits/", optimization_views.PortfolioAuditListView.as_view(), name="audit_list"),
    path("optimization/audits/add/", optimization_views.PortfolioAuditCreateView.as_view(), name="audit_create"),
    path("optimization/audits/<int:pk>/edit/", optimization_views.PortfolioAuditUpdateView.as_view(), name="audit_update"),
    
    # Services Health Check
    path("services/health/", health_views.ServicesHealthView.as_view(), name="services_health"),
    path("services/health/api/", health_views.health_check_api, name="health_check_api"),
]

