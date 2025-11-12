"""
Service management views for individual FKS services.
Each service gets its own page with health checks, tests, and features.
"""

import json
from typing import Any, Dict

import httpx
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView


# Service registry with endpoints and features
SERVICE_REGISTRY = {
    "fks-api": {
        "name": "FKS API",
        "port": 8001,
        "base_url": "http://fks-api:8001",
        "health_url": "http://fks-api:8001/health",
        "description": "Main API gateway for trading operations",
        "features": ["health_check", "api_test", "endpoints_list"],
    },
    "fks-app": {
        "name": "FKS App",
        "port": 8002,
        "base_url": "http://fks-app:8002",
        "health_url": "http://fks-app:8002/health",
        "description": "Application service for trading logic",
        "features": ["health_check", "api_test"],
    },
    "fks-data": {
        "name": "FKS Data",
        "port": 8003,
        "base_url": "http://fks-data:8003",
        "health_url": "http://fks-data:8003/health",
        "description": "Data ingestion and management service",
        "features": ["health_check", "data_test", "ingestion_status"],
    },
    "fks-ai": {
        "name": "FKS AI",
        "port": 8007,
        "base_url": "http://fks-ai:8007",
        "health_url": "http://fks-ai:8007/health",
        "description": "AI-powered trading intelligence service",
        "features": ["health_check", "ai_test", "model_status"],
    },
    "fks-analyze": {
        "name": "FKS Analyze",
        "port": 8008,
        "base_url": "http://fks-analyze:8008",
        "health_url": "http://fks-analyze:8008/health",
        "description": "Analysis and optimization service for trading strategies",
        "features": ["health_check", "analysis_test", "run_analysis", "optimization"],
    },
    "fks-main": {
        "name": "FKS Main",
        "port": 8010,
        "base_url": "http://fks-main:8010",
        "health_url": "http://fks-main:8010/health",
        "description": "Main orchestration service for Kubernetes control",
        "features": ["health_check", "k8s_test", "service_management"],
    },
    "fks-monitor": {
        "name": "FKS Monitor",
        "port": 8009,
        "base_url": "http://fks-monitor:8009",
        "health_url": "http://fks-monitor:8009/health",
        "description": "Service monitoring and health tracking",
        "features": ["health_check", "monitor_test", "metrics_view"],
    },
}


class ServiceDetailView(LoginRequiredMixin, TemplateView):
    """Individual service detail page with health, tests, and features"""

    template_name = "pages/service_detail.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_name = kwargs.get("service_name", "")

        # Get service config
        service_config = SERVICE_REGISTRY.get(service_name, {})
        if not service_config:
            context["error"] = f"Service '{service_name}' not found"
            return context

        context["service_name"] = service_name
        context["service"] = service_config

        # Fetch service health
        try:
            with httpx.Client(timeout=5.0) as client:
                health_response = client.get(service_config["health_url"])
                if health_response.status_code == 200:
                    context["health_status"] = "healthy"
                    health_json = health_response.json()
                    context["health_data"] = json.dumps(health_json, indent=2)
                else:
                    context["health_status"] = "unhealthy"
                    context["health_data"] = json.dumps({"status_code": health_response.status_code}, indent=2)
        except Exception as e:
            context["health_status"] = "unreachable"
            context["health_error"] = str(e)
            context["health_data"] = None

        # Get service-specific data
        try:
            if service_name == "fks-analyze":
                context["analysis_features"] = self._get_analyze_features()
            elif service_name == "fks-ai":
                context["ai_features"] = self._get_ai_features()
            elif service_name == "fks-data":
                context["data_features"] = self._get_data_features()
        except Exception as e:
            context["feature_error"] = str(e)

        return context

    def _get_analyze_features(self) -> Dict[str, Any]:
        """Get fks-analyze specific features"""
        return {
            "available_analyses": [
                "Strategy Optimization",
                "Performance Analysis",
                "Risk Assessment",
                "Backtest Analysis",
            ],
            "endpoints": [
                "/api/v1/analyze/strategy",
                "/api/v1/analyze/performance",
                "/api/v1/analyze/risk",
                "/api/v1/analyze/backtest",
            ],
        }

    def _get_ai_features(self) -> Dict[str, Any]:
        """Get fks-ai specific features"""
        return {
            "models": ["gemini-pro", "ollama-llama3.2"],
            "rag_enabled": True,
            "google_ai_usage": self._get_google_ai_usage(),
        }

    def _get_data_features(self) -> Dict[str, Any]:
        """Get fks-data specific features"""
        return {
            "data_sources": ["Binance", "Alpha Vantage", "Custom"],
            "ingestion_status": "active",
        }

    def _get_google_ai_usage(self) -> Dict[str, Any]:
        """Get Google AI API usage statistics"""
        try:
            from src.rag.google_ai import GoogleAIRateLimiter

            limiter = GoogleAIRateLimiter()
            return limiter.get_usage_stats()
        except Exception:
            return {"error": "Rate limiter not available"}


@login_required
@require_http_methods(["POST"])
def run_service_test(request, service_name: str):
    """Run a test on a specific service"""
    service_config = SERVICE_REGISTRY.get(service_name)
    if not service_config:
        return JsonResponse({"error": "Service not found"}, status=404)

    test_type = request.POST.get("test_type", "health")

    try:
        with httpx.Client(timeout=10.0) as client:
            if test_type == "health":
                response = client.get(service_config["health_url"])
                return JsonResponse(
                    {
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "data": response.json() if response.status_code == 200 else {},
                    }
                )
            elif test_type == "api" and "api_test" in service_config.get("features", []):
                # Test API endpoint
                test_url = f"{service_config['base_url']}/api/v1/test"
                response = client.get(test_url)
                return JsonResponse(
                    {
                        "status": "success" if response.status_code == 200 else "failed",
                        "data": response.json() if response.status_code == 200 else {},
                    }
                )
            else:
                return JsonResponse({"error": "Test type not supported"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def run_analyze_analysis(request):
    """Run an analysis using fks-analyze service"""
    analysis_type = request.POST.get("analysis_type")
    parameters = json.loads(request.POST.get("parameters", "{}"))

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "http://fks-analyze:8008/api/v1/analyze",
                json={"type": analysis_type, "parameters": parameters},
            )
            return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def list_services(request):
    """List all available services"""
    services = []
    for service_name, config in SERVICE_REGISTRY.items():
        # Quick health check
        try:
            with httpx.Client(timeout=2.0) as client:
                health_response = client.get(config["health_url"])
                status = "healthy" if health_response.status_code == 200 else "unhealthy"
        except Exception:
            status = "unreachable"

        services.append(
            {
                "name": service_name,
                "display_name": config["name"],
                "status": status,
                "description": config["description"],
            }
        )

    return JsonResponse({"services": services})


class ServicesListView(LoginRequiredMixin, TemplateView):
    """List view of all FKS services"""

    template_name = "pages/services_list.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = SERVICE_REGISTRY
        return context

