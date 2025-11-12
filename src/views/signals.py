"""
Signal Views - Trading day planning interface
Displays signals with lot sizes and entry planning
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import httpx
from loguru import logger
from datetime import datetime
import os

# Signal service URL - use portfolio service for signal API
SIGNAL_SERVICE_URL = os.getenv(
    "FKS_PORTFOLIO_URL",
    "http://fks_portfolio:8012" if os.getenv("KUBERNETES_SERVICE_HOST") else "http://localhost:8012"
)


@require_http_methods(["GET"])
def signals_dashboard(request):
    """
    Main signals dashboard for trading day planning
    """
    date = request.GET.get("date", datetime.now().strftime("%Y%m%d"))
    category = request.GET.get("category")  # Optional filter
    symbol = request.GET.get("symbol")  # Optional filter
    
    try:
        # Fetch signals from portfolio service
        api_url = f"{SIGNAL_SERVICE_URL}/api/signals/from-files"
        params = {"date": date, "include_lot_size": "true"}
        if category:
            params["category"] = category
        if symbol:
            params["symbol"] = symbol
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
        
        context = {
            "date": date,
            "signals": data.get("signals", {}),
            "summary": data.get("summary", {}),
            "performance": data.get("performance", {}),
            "lot_size_enabled": data.get("lot_size_enabled", False),
            "selected_category": category,
            "selected_symbol": symbol
        }
        
        return render(request, "signals/dashboard.html", context)
    
    except httpx.RequestError as e:
        logger.error(f"Error connecting to signal service: {e}")
        context = {
            "error": f"Could not connect to signal service: {str(e)}",
            "date": date,
            "signals": {},
            "summary": {},
            "performance": {}
        }
        return render(request, "signals/error.html", context)
    except Exception as e:
        logger.error(f"Error loading signals dashboard: {e}")
        context = {
            "error": str(e),
            "date": date,
            "signals": {},
            "summary": {},
            "performance": {}
        }
        return render(request, "signals/error.html", context)


@require_http_methods(["GET"])
def signals_api(request):
    """
    API endpoint for signals data (JSON)
    """
    date = request.GET.get("date", datetime.now().strftime("%Y%m%d"))
    category = request.GET.get("category")  # Optional filter
    symbol = request.GET.get("symbol")  # Optional filter
    
    try:
        # Fetch signals from portfolio service
        api_url = f"{SIGNAL_SERVICE_URL}/api/signals/from-files"
        params = {"date": date, "include_lot_size": "true"}
        if category:
            params["category"] = category
        if symbol:
            params["symbol"] = symbol
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(api_url, params=params)
            response.raise_for_status()
            response_data = response.json()
        
        return JsonResponse(response_data)
    
    except httpx.RequestError as e:
        logger.error(f"Error connecting to signal service: {e}")
        return JsonResponse({"error": f"Could not connect to signal service: {str(e)}"}, status=503)
    except Exception as e:
        logger.error(f"Error in signals API: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def signal_detail(request, signal_id):
    """
    Get detailed view of a specific signal
    """
    date = request.GET.get("date", datetime.now().strftime("%Y%m%d"))
    
    try:
        # Fetch signals and find the specific one
        api_url = f"{SIGNAL_SERVICE_URL}/api/signals/from-files"
        params = {"date": date, "include_lot_size": "true"}
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Find the signal by ID across all categories
        signal = None
        for category, signals in data.get("signals", {}).items():
            for s in signals:
                if str(s.get("id", "")) == str(signal_id) or str(s.get("symbol", "")) == str(signal_id):
                    signal = s
                    signal["category"] = category
                    break
            if signal:
                break
        
        if not signal:
            return JsonResponse({"error": "Signal not found"}, status=404)
        
        context = {
            "signal_id": signal_id,
            "date": date,
            "signal": signal
        }
        
        return render(request, "signals/detail.html", context)
    
    except httpx.RequestError as e:
        logger.error(f"Error connecting to signal service: {e}")
        return JsonResponse({"error": f"Could not connect to signal service: {str(e)}"}, status=503)
    except Exception as e:
        logger.error(f"Error loading signal detail: {e}")
        return JsonResponse({"error": str(e)}, status=500)

