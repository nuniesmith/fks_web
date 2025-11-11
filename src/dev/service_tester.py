"""
Service tester for all FKS services.
Tests health, endpoints, and functionality of each service.
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)


class ServiceTester:
    """Tests all FKS services for health and functionality"""
    
    def __init__(self, service_registry_path: Optional[str] = None):
        """Initialize service tester with service registry"""
        if service_registry_path is None:
            # Try to find service registry
            # Try multiple possible paths
            current_file = Path(__file__)
            # From repo/web/src/dev/service_tester.py
            # Try: repo/main/config/service_registry.json
            # Try multiple possible paths
            possible_paths = [
                current_file.parent.parent.parent.parent / "main" / "config" / "service_registry.json",
                Path("/home/jordan/Documents/code/fks/repo/main/config/service_registry.json"),
                Path("repo/main/config/service_registry.json"),
                Path(os.getenv("FKS_ROOT", ".")) / "repo" / "main" / "config" / "service_registry.json",
            ]
            
            service_registry_path = None
            for path in possible_paths:
                try:
                    if path.exists():
                        service_registry_path = path
                        break
                except Exception:
                    continue
            
            if service_registry_path is None:
                # Use environment variable or default
                default_path = os.getenv("SERVICE_REGISTRY_PATH")
                if default_path:
                    service_registry_path = Path(default_path)
                else:
                    # Use first path as default (will use fallback registry)
                    service_registry_path = possible_paths[0]
        
        self.service_registry_path = Path(service_registry_path)
        self.services = self._load_service_registry()
        self.timeout = 5.0
        
    def _load_service_registry(self) -> Dict[str, Any]:
        """Load service registry from JSON file"""
        try:
            if self.service_registry_path.exists():
                with open(self.service_registry_path, 'r') as f:
                    data = json.load(f)
                    return data.get('services', {})
            else:
                logger.warning(f"Service registry not found at {self.service_registry_path}")
                return self._get_default_services()
        except Exception as e:
            logger.error(f"Error loading service registry: {e}")
            return self._get_default_services()
    
    def _get_default_services(self) -> Dict[str, Any]:
        """Get default service registry if file not found"""
        return {
            "fks_api": {
                "name": "fks_api",
                "port": 8001,
                "base_url": "http://fks_api:8001",
                "health_url": "http://fks_api:8001/health",
            },
            "fks_app": {
                "name": "fks_app",
                "port": 8002,
                "base_url": "http://fks_app:8002",
                "health_url": "http://fks_app:8002/health",
            },
            "fks_data": {
                "name": "fks_data",
                "port": 8003,
                "base_url": "http://fks_data:8003",
                "health_url": "http://fks_data:8003/health",
            },
            "fks_execution": {
                "name": "fks_execution",
                "port": 8006,
                "base_url": "http://fks_execution:8006",
                "health_url": "http://fks_execution:8006/health",
            },
            "fks_web": {
                "name": "fks_web",
                "port": 8000,
                "base_url": "http://fks_web:8000",
                "health_url": "http://fks_web:8000/health",
            },
            "fks_ai": {
                "name": "fks_ai",
                "port": 8007,
                "base_url": "http://fks_ai:8007",
                "health_url": "http://fks_ai:8007/health",
            },
            "fks_analyze": {
                "name": "fks_analyze",
                "port": 8008,
                "base_url": "http://fks_analyze:8008",
                "health_url": "http://fks_analyze:8008/health",
            },
            "fks_monitor": {
                "name": "fks_monitor",
                "port": 8009,
                "base_url": "http://fks_monitor:8009",
                "health_url": "http://fks_monitor:8009/health",
            },
            "fks_main": {
                "name": "fks_main",
                "port": 8010,
                "base_url": "http://fks_main:8010",
                "health_url": "http://fks_main:8010/health",
            },
            "fks_portfolio": {
                "name": "fks_portfolio",
                "port": 8012,
                "base_url": "http://fks_portfolio:8012",
                "health_url": "http://fks_portfolio:8012/health",
            },
        }
    
    def test_all_services(self) -> Dict[str, Any]:
        """Test all services and return results"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "summary": {
                "total": len(self.services),
                "healthy": 0,
                "unhealthy": 0,
                "unreachable": 0,
            }
        }
        
        for service_name, service_config in self.services.items():
            test_result = self.test_service(service_name)
            results["services"][service_name] = test_result
            
            # Update summary
            status = test_result.get("status", "unreachable")
            if status == "healthy":
                results["summary"]["healthy"] += 1
            elif status == "unhealthy":
                results["summary"]["unhealthy"] += 1
            else:
                results["summary"]["unreachable"] += 1
        
        return results
    
    def test_service(self, service_name: str) -> Dict[str, Any]:
        """Test a single service"""
        service_config = self.services.get(service_name)
        if not service_config:
            return {
                "status": "not_found",
                "error": f"Service '{service_name}' not found in registry",
                "timestamp": datetime.now().isoformat(),
            }
        
        result = {
            "name": service_config.get("name", service_name),
            "port": service_config.get("port"),
            "base_url": service_config.get("base_url"),
            "health_url": service_config.get("health_url"),
            "status": "unknown",
            "tests": {},
            "timestamp": datetime.now().isoformat(),
        }
        
        # Test health endpoint
        health_test = self._test_health(service_config)
        result["tests"]["health"] = health_test
        result["status"] = health_test["status"]
        
        # Test readiness endpoint (if available)
        ready_test = self._test_ready(service_config)
        if ready_test:
            result["tests"]["ready"] = ready_test
        
        # Test service-specific endpoints
        service_specific = self._test_service_specific(service_name, service_config)
        if service_specific:
            result["tests"].update(service_specific)
        
        return result
    
    def _test_health(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test service health endpoint"""
        health_url = service_config.get("health_url")
        if not health_url:
            return {
                "status": "unreachable",
                "error": "No health URL configured",
            }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(health_url)
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "status_code": response.status_code,
                        "data": response.json(),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}",
                    }
        except httpx.TimeoutException:
            return {
                "status": "unreachable",
                "error": "Timeout",
            }
        except httpx.ConnectError:
            return {
                "status": "unreachable",
                "error": "Connection refused",
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
            }
    
    def _test_ready(self, service_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Test service readiness endpoint"""
        base_url = service_config.get("base_url")
        if not base_url:
            return None
        
        ready_url = f"{base_url}/ready"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(ready_url)
                if response.status_code == 200:
                    return {
                        "status": "ready",
                        "status_code": response.status_code,
                        "data": response.json(),
                    }
                else:
                    return {
                        "status": "not_ready",
                        "status_code": response.status_code,
                    }
        except Exception:
            return None
    
    def _test_service_specific(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test service-specific endpoints"""
        tests = {}
        base_url = service_config.get("base_url")
        
        if not base_url:
            return tests
        
        # Test common API endpoints
        test_endpoints = {
            "fks_portfolio": [
                "/api/dashboard/overview",
                "/api/signals/generate?category=swing",
                "/api/portfolio/value",
            ],
            "fks_ai": [
                "/ai/health",
            ],
            "fks_data": [
                "/api/v1/health",
            ],
            "fks_api": [
                "/api/v1/health",
            ],
            "fks_app": [
                "/api/v1/health",
            ],
            "fks_analyze": [
                "/api/v1/health",
            ],
            "fks_execution": [
                "/api/v1/health",
            ],
            "fks_monitor": [
                "/api/v1/health",
            ],
            "fks_main": [
                "/api/v1/health",
            ],
        }
        
        endpoints = test_endpoints.get(service_name, [])
        
        for endpoint in endpoints:
            test_url = f"{base_url}{endpoint}"
            test_name = endpoint.replace("/", "_").replace("?", "_").replace("=", "_")
            
            try:
                with httpx.Client(timeout=self.timeout * 2) as client:
                    response = client.get(test_url)
                    tests[test_name] = {
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "url": test_url,
                    }
            except Exception as e:
                tests[test_name] = {
                    "status": "error",
                    "error": str(e),
                    "url": test_url,
                }
        
        return tests
    
    def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """Get information about a service"""
        service_config = self.services.get(service_name)
        if not service_config:
            return {}
        
        return {
            "name": service_config.get("name"),
            "port": service_config.get("port"),
            "base_url": service_config.get("base_url"),
            "health_url": service_config.get("health_url"),
            "dependencies": service_config.get("dependencies", []),
        }

