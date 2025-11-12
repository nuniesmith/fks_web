"""Web UI admin interfaces."""

from django.contrib import admin

# Import admin from authentication app
from authentication.admin import APIKeyAdmin, UserAdmin  # noqa: F401

# Admin interfaces are registered in authentication.admin
