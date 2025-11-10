"""Portfolio views for fks_web"""
import os
import requests
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Portfolio service URL
PORTFOLIO_SERVICE_URL = os.getenv(
    "PORTFOLIO_SERVICE_URL",
    "http://fks_portfolio:8012"
)


class PortfolioDashboardView(LoginRequiredMixin, TemplateView):
    """Portfolio dashboard view"""
    template_name = "portfolio/dashboard.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch portfolio overview
        try:
            overview_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/overview",
                timeout=10
            )
            if overview_response.status_code == 200:
                context["overview"] = overview_response.json()
            else:
                context["overview"] = {
                    "assets": {"enabled_count": 0, "tracked": 0, "prices": {}},
                    "signals": {"total": 0, "buy": 0, "sell": 0, "avg_confidence": 0.0},
                    "status": "error"
                }
                logger.error(f"Failed to fetch overview: {overview_response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching overview: {e}")
            context["overview"] = {
                "assets": {"enabled_count": 0, "tracked": 0, "prices": {}},
                "signals": {"total": 0, "buy": 0, "sell": 0, "avg_confidence": 0.0},
                "status": "error"
            }
        
        # Fetch performance metrics
        try:
            performance_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/performance",
                params={"days": 30},
                timeout=10
            )
            if performance_response.status_code == 200:
                context["performance"] = performance_response.json()
            else:
                context["performance"] = {"error": "Failed to fetch performance"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching performance: {e}")
            context["performance"] = {"error": "Service unavailable"}
        
        # Fetch signal summary
        try:
            signals_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/signals/summary",
                timeout=10
            )
            if signals_response.status_code == 200:
                signals_data = signals_response.json()
                context["signals"] = signals_data
                # Ensure totals exist
                if "totals" not in signals_data:
                    context["signals"]["totals"] = {
                        "count": 0,
                        "buy": 0,
                        "sell": 0,
                        "avg_confidence": 0.0
                    }
                if "by_category" not in signals_data:
                    context["signals"]["by_category"] = {}
            else:
                context["signals"] = {
                    "totals": {"count": 0, "buy": 0, "sell": 0, "avg_confidence": 0.0},
                    "by_category": {}
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching signals: {e}")
            context["signals"] = {
                "totals": {"count": 0, "buy": 0, "sell": 0, "avg_confidence": 0.0},
                "by_category": {}
            }
        
        # Fetch allocation chart data
        try:
            allocation_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/charts/allocation",
                timeout=10
            )
            if allocation_response.status_code == 200:
                allocation_data = allocation_response.json()
                context["allocation_data"] = json.dumps(allocation_data.get("data", []))
            else:
                context["allocation_data"] = "[]"
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching allocation: {e}")
            context["allocation_data"] = "[]"
        
        return context


class PortfolioSignalsView(LoginRequiredMixin, TemplateView):
    """Portfolio signals view"""
    template_name = "portfolio/signals.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get category from query params
            category = self.request.GET.get("category", "swing")
            
            # Fetch signals
            signals_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/signals/generate",
                params={"category": category},
                timeout=30
            )
            if signals_response.status_code == 200:
                signals_data = signals_response.json()
                context["signals"] = signals_data.get("signals", [])
                context["category"] = category
            else:
                context["signals"] = []
                context["error"] = "Failed to fetch signals"
            
            # Fetch signal summary
            summary_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/signals/summary",
                params={"category": category} if category else {},
                timeout=10
            )
            if summary_response.status_code == 200:
                context["summary"] = summary_response.json()
            else:
                context["summary"] = {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching signals: {e}")
            context["error"] = f"Error connecting to portfolio service: {str(e)}"
            context["signals"] = []
            context["summary"] = {}
        
        return context


class PortfolioPerformanceView(LoginRequiredMixin, TemplateView):
    """Portfolio performance view"""
    template_name = "portfolio/performance.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get days from query params
            days = int(self.request.GET.get("days", 30))
            
            # Fetch performance metrics
            performance_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/performance",
                params={"days": days},
                timeout=10
            )
            if performance_response.status_code == 200:
                performance_data = performance_response.json()
                context["performance"] = performance_data
                
                # Prepare chart data
                chart_data = []
                for symbol, data in performance_data.get("assets", {}).items():
                    chart_data.append({
                        "symbol": symbol,
                        "return_pct": data.get("return_pct", 0),
                        "volatility": data.get("volatility", 0)
                    })
                context["chart_data"] = json.dumps(chart_data)
            else:
                context["performance"] = {"error": "Failed to fetch performance"}
                context["chart_data"] = "[]"
            
            # Fetch performance comparison chart
            comparison_response = requests.get(
                f"{PORTFOLIO_SERVICE_URL}/api/dashboard/charts/performance",
                params={"days": days},
                timeout=10
            )
            if comparison_response.status_code == 200:
                context["comparison_data"] = json.dumps(comparison_response.json())
            else:
                context["comparison_data"] = "{}"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching performance: {e}")
            context["error"] = f"Error connecting to portfolio service: {str(e)}"
            context["performance"] = {"error": "Service unavailable"}
            context["chart_data"] = "[]"
            context["comparison_data"] = "{}"
        
        return context


@login_required
def portfolio_api_data(request, endpoint):
    """API proxy for portfolio service"""
    try:
        # Get query parameters
        params = dict(request.GET)
        
        # Fetch data from portfolio service
        response = requests.get(
            f"{PORTFOLIO_SERVICE_URL}/api/{endpoint}",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse(
                {"error": f"Portfolio service returned {response.status_code}"},
                status=response.status_code
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying portfolio API: {e}")
        return JsonResponse(
            {"error": f"Error connecting to portfolio service: {str(e)}"},
            status=503
        )

