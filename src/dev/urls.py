"""URL patterns for dev interface"""
from django.urls import path
from . import views

app_name = "dev"

urlpatterns = [
    path("", views.DevDashboardView.as_view(), name="dashboard"),
    path("service/<str:service_name>/", views.ServiceTestView.as_view(), name="service_test"),
    path("api/test/<str:service_name>/", views.run_service_test_api, name="test_service_api"),
    path("api/test-all/", views.test_all_services_api, name="test_all_api"),
    path("api/info/<str:service_name>/", views.service_info_api, name="service_info_api"),
]

