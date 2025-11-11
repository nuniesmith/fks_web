"""
Views for FKS microservices health check dashboard.
"""
import os
import requests
import json
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Load service registry
# Try multiple paths for different repo structures
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SERVICE_REGISTRY_PATHS = [
    BASE_DIR / 'main' / 'config' / 'service_registry.json',  # Monorepo structure
    BASE_DIR / 'repo' / 'main' / 'config' / 'service_registry.json',  # Alternative structure
    BASE_DIR / 'config' / 'service_registry.json',  # Standalone
]

SERVICE_REGISTRY = None
for path in SERVICE_REGISTRY_PATHS:
    if path.exists():
        try:
            with open(path, 'r') as f:
                SERVICE_REGISTRY = json.load(f)
            break
        except Exception:
            continue

# Fallback to default service registry
if SERVICE_REGISTRY is None:
    SERVICE_REGISTRY = {
        "version": "1.1",
        "services": {
            "fks_web": {"port": 8000, "health_url": "http://fks_web:8000/health"},
            "fks_api": {"port": 8001, "health_url": "http://fks_api:8001/health"},
            "fks_app": {"port": 8002, "health_url": "http://fks_app:8002/health"},
            "fks_data": {"port": 8003, "health_url": "http://fks_data:8003/health"},
            "fks_execution": {"port": 8004, "health_url": "http://fks_execution:8004/health"},
            "fks_meta": {"port": 8005, "health_url": "http://fks_meta:8005/health"},
            "fks_ai": {"port": 8007, "health_url": "http://fks_ai:8007/health"},
            "fks_analyze": {"port": 8008, "health_url": "http://fks_analyze:8008/health"},
            "fks_auth": {"port": 8009, "health_url": "http://fks_auth:8009/health"},
            "fks_main": {"port": 8010, "health_url": "http://fks_main:8010/health"},
            "fks_training": {"port": 8011, "health_url": "http://fks_training:8011/health"},
            "fks_portfolio": {"port": 8012, "health_url": "http://fks_portfolio:8012/health"},
            "fks_monitor": {"port": 8013, "health_url": "http://fks_monitor:8013/health"},
        }
    }


class ServicesHealthView(LoginRequiredMixin, TemplateView):
    """Health check dashboard for all FKS microservices"""
    template_name = 'portfolio/services_health.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get environment (dev/staging/prod)
        env = os.getenv('ENVIRONMENT', 'development')
        context['environment'] = env
        
        # Check health of all services
        services_status = []
        services = SERVICE_REGISTRY.get('services', {})
        
        for service_name, service_info in services.items():
            port = service_info.get('port', 0)
            health_url = service_info.get('health_url', '')
            
            # Try multiple URLs
            status = {
                'name': service_name,
                'port': port,
                'status': 'unknown',
                'response_time': None,
                'error': None,
                'details': {},
                'url': health_url
            }
            
            # Try localhost first (for dev), then Docker service name
            urls_to_try = []
            if env == 'development':
                urls_to_try.append(f"http://localhost:{port}/health")
            urls_to_try.append(health_url)
            
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=2)
                    status['status'] = 'healthy' if response.status_code == 200 else 'unhealthy'
                    status['response_time'] = response.elapsed.total_seconds()
                    if response.status_code == 200:
                        try:
                            status['details'] = response.json()
                        except:
                            status['details'] = {'message': response.text[:100]}
                    status['url'] = url
                    break  # Success, stop trying
                except requests.exceptions.RequestException as e:
                    status['error'] = str(e)
                    continue
            
            # If all URLs failed, mark as unreachable
            if status['status'] == 'unknown':
                status['status'] = 'unreachable'
            
            services_status.append(status)
        
        # Calculate summary
        healthy_count = sum(1 for s in services_status if s['status'] == 'healthy')
        unhealthy_count = sum(1 for s in services_status if s['status'] == 'unhealthy')
        unreachable_count = sum(1 for s in services_status if s['status'] == 'unreachable')
        
        context['services'] = services_status
        context['summary'] = {
            'total': len(services_status),
            'healthy': healthy_count,
            'unhealthy': unhealthy_count,
            'unreachable': unreachable_count,
            'health_percentage': (healthy_count / len(services_status) * 100) if services_status else 0
        }
        
        return context


@login_required
def health_check_api(request):
    """API endpoint for health check (AJAX)"""
    service_name = request.GET.get('service')
    
    if not service_name:
        return JsonResponse({'error': 'Service name required'}, status=400)
    
    services = SERVICE_REGISTRY.get('services', {})
    service_info = services.get(service_name)
    
    if not service_info:
        return JsonResponse({'error': 'Service not found'}, status=404)
    
    health_url = service_info.get('health_url', '')
    port = service_info.get('port', 0)
    
    # Try localhost first (dev), then service name
    env = os.getenv('ENVIRONMENT', 'development')
    urls_to_try = []
    if env == 'development':
        urls_to_try.append(f"http://localhost:{port}/health")
    urls_to_try.append(health_url)
    
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=2)
            return JsonResponse({
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'details': response.json() if response.status_code == 200 else {},
                'url': url
            })
        except Exception as e:
            continue
    
    return JsonResponse({
        'status': 'unreachable',
        'error': 'Service unreachable',
        'url': health_url
    }, status=503)
