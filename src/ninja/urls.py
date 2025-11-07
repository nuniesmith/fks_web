"""
URL routing for NinjaTrader 8 management interface.

Endpoints:
- /ninja/dashboard/ - Main management dashboard
- /ninja/download/ - Download NT8 package
- /ninja/build-status/ - Check DLL/source status (AJAX)
- /ninja/build/ - Manually trigger build
- /ninja/installation/ - Installation guide
"""

from django.urls import path

from . import views

app_name = 'ninja'

urlpatterns = [
    # Main dashboard
    path('dashboard/', views.ninja_dashboard, name='dashboard'),

    # Package management
    path('download/', views.download_nt8_package, name='download_package'),
    path('build-status/', views.build_status, name='build_status'),
    path('build/', views.trigger_build, name='trigger_build'),

    # Documentation
    path('installation/', views.installation_guide, name='installation_guide'),
]
