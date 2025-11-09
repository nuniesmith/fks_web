"""
Views for API key management in the web interface.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .api_keys import APIKey
from .forms import APIKeyDeleteForm, APIKeyForm


def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class APIKeyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all API keys"""
    
    model = APIKey
    template_name = "authentication/api_keys_list.html"
    context_object_name = "api_keys"
    login_url = "/login/"
    
    def test_func(self):
        return is_staff_or_superuser(self.request.user)
    
    def get_queryset(self):
        """Get API keys user can access"""
        user = self.request.user
        
        if user.is_superuser:
            # Superusers see all keys
            return APIKey.objects.all()
        elif user.is_staff:
            # Staff see global keys and their own
            return APIKey.objects.filter(
                Q(is_global=True) | Q(assigned_to=user) | Q(created_by=user)
            )
        else:
            # Regular users see only their assigned keys
            return APIKey.objects.filter(assigned_to=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create"] = self.request.user.is_staff or self.request.user.is_superuser
        return context


class APIKeyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new API key"""
    
    model = APIKey
    form_class = APIKeyForm
    template_name = "authentication/api_key_form.html"
    login_url = "/login/"
    
    def test_func(self):
        return is_staff_or_superuser(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        return context
    
    def form_valid(self, form):
        """Save with user as creator"""
        form.instance.created_by = self.request.user
        messages.success(self.request, f"API key '{form.instance.name}' created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("authentication:api_keys_list")


class APIKeyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing API key"""
    
    model = APIKey
    form_class = APIKeyForm
    template_name = "authentication/api_key_form.html"
    login_url = "/login/"
    
    def test_func(self):
        user = self.request.user
        if not is_staff_or_superuser(user):
            return False
        
        # Check if user can edit this key
        obj = self.get_object()
        if user.is_superuser:
            return True
        if obj.created_by == user:
            return True
        if user.is_staff and obj.is_global:
            return True
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Edit"
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"API key '{form.instance.name}' updated successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("authentication:api_keys_list")


class APIKeyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an API key"""
    
    model = APIKey
    template_name = "authentication/api_key_confirm_delete.html"
    login_url = "/login/"
    form_class = APIKeyDeleteForm
    
    def test_func(self):
        user = self.request.user
        if not is_staff_or_superuser(user):
            return False
        
        # Check if user can delete this key
        obj = self.get_object()
        if user.is_superuser:
            return True
        if obj.created_by == user:
            return True
        if user.is_staff and obj.is_global:
            return True
        
        return False
    
    def delete(self, request, *args, **kwargs):
        """Delete the key and show success message"""
        obj = self.get_object()
        name = obj.name
        obj.delete()
        messages.success(request, f"API key '{name}' deleted successfully.")
        return redirect("authentication:api_keys_list")


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
def toggle_api_key_status(request, pk):
    """Toggle API key active status"""
    api_key = get_object_or_404(APIKey, pk=pk)
    
    # Check permissions
    user = request.user
    if not (user.is_superuser or (user.is_staff and api_key.is_global) or api_key.created_by == user):
        raise PermissionDenied
    
    api_key.is_active = not api_key.is_active
    api_key.save()
    
    status = "activated" if api_key.is_active else "deactivated"
    messages.success(request, f"API key '{api_key.name}' {status}.")
    
    return JsonResponse({
        "success": True,
        "is_active": api_key.is_active,
        "message": f"API key {status}",
    })


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["GET"])
def api_key_detail(request, pk):
    """Get API key details (without showing the actual key)"""
    api_key = get_object_or_404(APIKey, pk=pk)
    
    # Check permissions
    user = request.user
    if not (user.is_superuser or (user.is_staff and api_key.is_global) or api_key.created_by == user):
        raise PermissionDenied
    
    return JsonResponse({
        "id": api_key.id,
        "name": api_key.name,
        "provider": api_key.provider,
        "description": api_key.description,
        "is_global": api_key.is_global,
        "is_active": api_key.is_active,
        "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "created_at": api_key.created_at.isoformat(),
        "created_by": api_key.created_by.username if api_key.created_by else None,
        # Never return the actual key value
    })

