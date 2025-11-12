"""
Admin interfaces for authentication models.
"""
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from .api_keys import APIKey
from .models import User

User = get_user_model()


class APIKeyAdminForm(forms.ModelForm):
    """Custom form for APIKey admin with masked key input."""
    
    key_value = forms.CharField(
        label="API Key",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter API key to encrypt"}),
        required=False,
        help_text="Enter the API key value. It will be encrypted before storage."
    )
    
    class Meta:
        model = APIKey
        fields = [
            "name",
            "description",
            "key_value",
            "provider",
            "is_global",
            "assigned_to",
            "is_active",
            "expires_at",
            "created_by",
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing key, don't show the key value (security)
        if self.instance and self.instance.pk:
            self.fields["key_value"].help_text = (
                "Leave blank to keep existing key. Enter new value to update."
            )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Only update key if a new value was provided
        if "key_value" in self.cleaned_data and self.cleaned_data["key_value"]:
            instance.key = self.cleaned_data["key_value"]
        if commit:
            instance.save()
        return instance


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API Key management."""
    
    form = APIKeyAdminForm
    list_display = [
        "name",
        "provider",
        "is_global_display",
        "assigned_to",
        "is_active",
        "status_display",
        "last_used",
        "created_at",
    ]
    list_filter = [
        "provider",
        "is_global",
        "is_active",
        "created_at",
    ]
    search_fields = ["name", "description", "provider"]
    readonly_fields = ["created_at", "updated_at", "last_used"]
    
    fieldsets = (
        ("Key Information", {
            "fields": ("name", "description", "provider")
        }),
        ("Key Value", {
            "fields": ("key_value",),
            "description": "Enter the API key value. It will be encrypted before storage."
        }),
        ("Assignment", {
            "fields": ("is_global", "assigned_to", "created_by")
        }),
        ("Status", {
            "fields": ("is_active", "expires_at", "last_used")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def is_global_display(self, obj):
        """Display global status with icon."""
        if obj.is_global:
            return format_html('<span style="color: green;">✓ Global</span>')
        return format_html('<span style="color: blue;">User-specific</span>')
    is_global_display.short_description = "Scope"
    
    def status_display(self, obj):
        """Display status with color coding."""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        if obj.is_active:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: orange;">Inactive</span>')
    status_display.short_description = "Status"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("assigned_to", "created_by")
    
    def save_model(self, request, obj, form, change):
        """Set created_by if not set."""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model."""
    
    list_display = [
        "username",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_staff", "is_active", "date_joined"]
    search_fields = ["username", "email"]
    readonly_fields = ["date_joined", "last_login"]

