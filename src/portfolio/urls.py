"""Portfolio URL patterns"""
from django.urls import path
from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.PortfolioDashboardView.as_view(), name="dashboard"),
    path("signals/", views.PortfolioSignalsView.as_view(), name="signals"),
    path("performance/", views.PortfolioPerformanceView.as_view(), name="performance"),
    path("api/<path:endpoint>", views.portfolio_api_data, name="api_proxy"),
]

