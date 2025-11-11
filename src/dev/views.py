"""
Dev interface views for testing and monitoring FKS services.
"""
import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .service_tester import ServiceTester

logger = logging.getLogger(__name__)


class DevDashboardView(LoginRequiredMixin, TemplateView):
    """Dev dashboard for testing all FKS services"""
    
    template_name = "dev/dashboard.html"
    login_url = "/login/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize service tester
        tester = ServiceTester()
        
        # Test all services
        test_results = tester.test_all_services()
        
        # Format JSON for display
        import json
        context["test_results_json"] = json.dumps(test_results, indent=2)
        context["services"] = tester.services
        
        # Calculate summary
        context["summary"] = test_results.get("summary", {})
        context["services_data"] = test_results.get("services", {})
        
        return context


class ServiceTestView(LoginRequiredMixin, TemplateView):
    """Individual service test view"""
    
    template_name = "dev/service_test.html"
    login_url = "/login/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_name = kwargs.get("service_name")
        
        # Initialize service tester
        tester = ServiceTester()
        
        # Test specific service
        test_result = tester.test_service(service_name)
        
        # Format JSON for display
        import json
        context["test_result_json"] = json.dumps(test_result, indent=2)
        
        context["service_name"] = service_name
        context["test_result"] = test_result
        context["service_info"] = tester.get_service_info(service_name)
        
        return context


@login_required
@require_http_methods(["POST"])
def run_service_test_api(request, service_name: str):
    """API endpoint to run a service test"""
    try:
        tester = ServiceTester()
        test_result = tester.test_service(service_name)
        return JsonResponse(test_result)
    except Exception as e:
        logger.error(f"Error testing service {service_name}: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def test_all_services_api(request):
    """API endpoint to test all services"""
    try:
        tester = ServiceTester()
        test_results = tester.test_all_services()
        return JsonResponse(test_results)
    except Exception as e:
        logger.error(f"Error testing all services: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def service_info_api(request, service_name: str):
    """API endpoint to get service information"""
    try:
        tester = ServiceTester()
        service_info = tester.get_service_info(service_name)
        if not service_info:
            return JsonResponse({"error": "Service not found"}, status=404)
        return JsonResponse(service_info)
    except Exception as e:
        logger.error(f"Error getting service info for {service_name}: {e}")
        return JsonResponse({"error": str(e)}, status=500)

