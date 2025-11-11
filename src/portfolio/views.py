"""Portfolio views for fks_web"""
import os
import requests
import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Service URLs
PORTFOLIO_SERVICE_URL = os.getenv(
    "PORTFOLIO_SERVICE_URL",
    "http://fks_portfolio:8012"
)
APP_SERVICE_URL = os.getenv(
    "APP_SERVICE_URL",
    "http://fks_app:8002"
)
EXECUTION_SERVICE_URL = os.getenv(
    "EXECUTION_SERVICE_URL",
    "http://fks_execution:8004"
)


class PortfolioDashboardView(LoginRequiredMixin, TemplateView):
    """Portfolio dashboard view"""
    template_name = "portfolio/dashboard.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add link to services health check
        context['show_health_link'] = True
        
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
    """Portfolio signals view with approval workflow"""
    template_name = "portfolio/signals.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get category from query params
            category = self.request.GET.get("category", "swing")
            use_ai = self.request.GET.get("use_ai", "true").lower() == "true"
            
            # Fetch signals from fks_app (Phase 2.2 pipeline)
            # Try batch generation for common symbols
            symbols = self.request.GET.get("symbols", "BTCUSDT,ETHUSDT,SOLUSDT")
            symbol_list = [s.strip() for s in symbols.split(",")]
            
            signals = []
            for symbol in symbol_list[:5]:  # Limit to 5 symbols for performance
                try:
                    signal_response = requests.get(
                        f"{APP_SERVICE_URL}/api/v1/signals/latest/{symbol}",
                        params={
                            "category": category,
                            "use_ai": use_ai
                        },
                        timeout=10
                    )
                    if signal_response.status_code == 200:
                        signal_data = signal_response.json()
                        # Add status for approval workflow
                        signal_data["status"] = "pending"  # New signals start as pending
                        signal_data["id"] = f"{symbol}_{category}_{int(datetime.now().timestamp())}"
                        signals.append(signal_data)
                except Exception as e:
                    logger.warning(f"Failed to fetch signal for {symbol}: {e}")
                    continue
            
            context["signals"] = signals
            context["category"] = category
            context["use_ai"] = use_ai
            
            # Calculate summary
            if signals:
                buy_count = sum(1 for s in signals if s.get("signal_type") == "BUY")
                sell_count = sum(1 for s in signals if s.get("signal_type") == "SELL")
                avg_confidence = sum(s.get("confidence", 0) for s in signals) / len(signals) * 100
                
                context["summary"] = {
                    "totals": {
                        "count": len(signals),
                        "buy": buy_count,
                        "sell": sell_count,
                        "avg_confidence": avg_confidence
                    }
                }
            else:
                context["summary"] = {
                    "totals": {
                        "count": 0,
                        "buy": 0,
                        "sell": 0,
                        "avg_confidence": 0.0
                    }
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching signals: {e}")
            context["error"] = f"Error connecting to services: {str(e)}"
            context["signals"] = []
            context["summary"] = {"totals": {"count": 0, "buy": 0, "sell": 0, "avg_confidence": 0.0}}
        
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


@login_required
@require_http_methods(["POST"])
def approve_signal(request, signal_id):
    """
    Approve a signal and send to execution service.
    Phase 2.3: Signal approval workflow
    """
    try:
        # Parse signal_id (format: symbol_category_timestamp)
        parts = signal_id.split("_")
        if len(parts) < 2:
            messages.error(request, "Invalid signal ID format")
            return redirect("portfolio:signals")
        
        symbol = parts[0]
        category = parts[1] if len(parts) > 1 else "swing"
        
        # Fetch latest signal data
        signal_response = requests.get(
            f"{APP_SERVICE_URL}/api/v1/signals/latest/{symbol}",
            params={"category": category, "use_ai": "true"},
            timeout=10
        )
        
        if signal_response.status_code != 200:
            messages.error(request, f"Failed to fetch signal data for {symbol}")
            return redirect("portfolio:signals")
        
        signal_data = signal_response.json()
        
        # Prepare order for execution service
        order_data = {
            "symbol": signal_data.get("symbol"),
            "side": signal_data.get("signal_type"),  # BUY or SELL
            "order_type": "MARKET",  # Can be made configurable
            "quantity": signal_data.get("position_size_units", 0),
            "price": signal_data.get("entry_price", 0),
            "stop_loss": signal_data.get("stop_loss"),
            "take_profit": signal_data.get("take_profit"),
            "signal_id": signal_id,
            "category": category,
            "confidence": signal_data.get("confidence", 0),
            "strategy": "fks_app_pipeline"
        }
        
        # Send to execution service
        execution_response = requests.post(
            f"{EXECUTION_SERVICE_URL}/orders",
            json=order_data,
            timeout=30
        )
        
        if execution_response.status_code in [200, 201]:
            execution_result = execution_response.json()
            messages.success(
                request,
                f"Signal approved! Order {execution_result.get('order_id', 'N/A')} submitted for {symbol}"
            )
            logger.info(f"Signal {signal_id} approved and sent to execution")
        else:
            messages.error(
                request,
                f"Failed to execute order: {execution_response.status_code}"
            )
            logger.error(f"Execution service error: {execution_response.text}")
        
    except Exception as e:
        logger.error(f"Error approving signal {signal_id}: {e}")
        messages.error(request, f"Error approving signal: {str(e)}")
    
    return redirect("portfolio:signals")


@login_required
@require_http_methods(["POST"])
def reject_signal(request, signal_id):
    """
    Reject a signal (no execution).
    Phase 2.3: Signal approval workflow
    """
    try:
        parts = signal_id.split("_")
        symbol = parts[0] if parts else "UNKNOWN"
        
        messages.info(request, f"Signal for {symbol} rejected (not executed)")
        logger.info(f"Signal {signal_id} rejected by user")
        
    except Exception as e:
        logger.error(f"Error rejecting signal {signal_id}: {e}")
        messages.error(request, f"Error rejecting signal: {str(e)}")
    
    return redirect("portfolio:signals")

