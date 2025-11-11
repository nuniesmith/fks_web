"""
URL configuration for authentication app.
"""

from django.urls import path
from . import views
from . import views_api_keys

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    # API Key Management
    path("api-keys/", views_api_keys.APIKeyListView.as_view(), name="api_keys_list"),
    path("api-keys/create/", views_api_keys.APIKeyCreateView.as_view(), name="api_key_create"),
    path("api-keys/<int:pk>/edit/", views_api_keys.APIKeyUpdateView.as_view(), name="api_key_edit"),
    path("api-keys/<int:pk>/delete/", views_api_keys.APIKeyDeleteView.as_view(), name="api_key_delete"),
    path("api-keys/<int:pk>/toggle/", views_api_keys.toggle_api_key_status, name="api_key_toggle"),
    path("api-keys/<int:pk>/detail/", views_api_keys.api_key_detail, name="api_key_detail"),
]

