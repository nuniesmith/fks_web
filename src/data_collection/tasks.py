"""
Celery tasks for scheduled data collection using multi-provider manager.

These tasks use the MultiProviderManager from fks_data to fetch market data
with automatic failover and verification, and persist it to the database.
"""
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import DataCollectionLog, MarketDataPoint, MarketOverview

logger = logging.getLogger(__name__)

# Add fks_data to path if needed
try:
    # Try to import from installed package
    from fks_data.adapters.multi_provider_manager import MultiProviderManager
except ImportError:
    # Fallback: add repo/data/src to path
    data_path = os.path.join(os.path.dirname(__file__), "../../../data/src")
    if os.path.exists(data_path) and data_path not in sys.path:
        sys.path.insert(0, data_path)
    try:
        from adapters.multi_provider_manager import MultiProviderManager
    except ImportError:
        logger.error("Could not import MultiProviderManager. Data collection tasks will not work.")
        MultiProviderManager = None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def collect_crypto_data(
    self,
    symbols: List[str],
    granularity: str = "1m",
    hours_back: int = 24,
    providers: Optional[List[str]] = None,
    save_to_db: bool = True,
) -> Dict[str, Any]:
    """
    Collect cryptocurrency data for specified symbols and optionally save to database.
    
    Args:
        symbols: List of crypto symbols (e.g., ["BTC", "ETH"])
        granularity: Data granularity ("1m", "5m", "1h", "1d")
        hours_back: How many hours of historical data to fetch
        providers: Optional list of providers in priority order
        save_to_db: Whether to save collected data to database
    
    Returns:
        Dictionary with results for each symbol
    """
    if MultiProviderManager is None:
        logger.error("MultiProviderManager not available")
        return {"error": "MultiProviderManager not available", "symbols": symbols}
    
    task_start_time = time.time()
    collection_log = None
    results = {}
    end_time = timezone.now().timestamp()
    start_time = end_time - (hours_back * 3600)
    
    # Default providers for crypto
    if providers is None:
        providers = ["binance", "cmc", "coingecko", "polygon"]
    
    # Create collection log
    if save_to_db:
        collection_log = DataCollectionLog.objects.create(
            task_name="collect_crypto_data",
            task_id=self.request.id,
            symbols=symbols,
            providers_used=providers,
            status="success",  # Will update if errors occur
        )
    
    try:
        manager = MultiProviderManager(
            providers=providers,
            verify_data=True,
            verification_threshold=0.01,
            cooldown_seconds=30.0,
        )
        
        total_data_points = 0
        successful_symbols = 0
        failed_symbols = 0
        
        for symbol in symbols:
            try:
                logger.info(f"Collecting {granularity} data for {symbol} (last {hours_back} hours)")
                
                data = manager.get_data(
                    asset=symbol,
                    granularity=granularity,
                    start_date=start_time,
                    end_date=end_time,
                )
                
                data_list = data.get("data", [])
                provider_name = data.get("provider", "unknown")
                data_points = len(data_list)
                total_data_points += data_points
                
                # Save to database
                if save_to_db and data_points > 0:
                    saved_count = _save_market_data_points(
                        data_list=data_list,
                        symbol=symbol,
                        asset_type="crypto",
                        granularity=granularity,
                        provider=provider_name,
                        raw_data=data,
                    )
                    logger.info(f"✓ Saved {saved_count} data points for {symbol} to database")
                
                results[symbol] = {
                    "status": "success",
                    "provider": provider_name,
                    "data_points": data_points,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "end_time": datetime.fromtimestamp(end_time).isoformat(),
                }
                successful_symbols += 1
                
                logger.info(f"✓ Collected {data_points} data points for {symbol} from {provider_name}")
                
            except Exception as e:
                logger.error(f"Failed to collect data for {symbol}: {e}", exc_info=True)
                results[symbol] = {
                    "status": "error",
                    "error": str(e),
                }
                failed_symbols += 1
        
        # Log provider status
        provider_status = manager.get_provider_status()
        logger.info(f"Provider status: {provider_status}")
        
        # Update collection log
        if collection_log:
            duration = time.time() - task_start_time
            collection_log.status = "partial" if failed_symbols > 0 else "success"
            collection_log.data_points_collected = total_data_points
            collection_log.symbols_successful = successful_symbols
            collection_log.symbols_failed = failed_symbols
            collection_log.duration_seconds = duration
            collection_log.completed_at = timezone.now()
            if failed_symbols > 0:
                collection_log.error_message = f"{failed_symbols} symbols failed"
            collection_log.save()
        
        return {
            "status": "completed",
            "results": results,
            "provider_status": provider_status,
            "data_points_collected": total_data_points,
            "timestamp": timezone.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Data collection task failed: {e}", exc_info=True)
        if collection_log:
            collection_log.status = "error"
            collection_log.error_message = str(e)
            collection_log.duration_seconds = time.time() - task_start_time
            collection_log.completed_at = timezone.now()
            collection_log.save()
        # Retry the task
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def collect_stock_data(
    self,
    symbols: List[str],
    granularity: str = "1d",
    days_back: int = 30,
    providers: Optional[List[str]] = None,
    save_to_db: bool = True,
) -> Dict[str, Any]:
    """
    Collect stock/ETF data for specified symbols and optionally save to database.
    
    Args:
        symbols: List of stock symbols (e.g., ["AAPL", "SPY"])
        granularity: Data granularity ("1m", "5m", "1h", "1d")
        days_back: How many days of historical data to fetch
        providers: Optional list of providers in priority order
        save_to_db: Whether to save collected data to database
    
    Returns:
        Dictionary with results for each symbol
    """
    if MultiProviderManager is None:
        logger.error("MultiProviderManager not available")
        return {"error": "MultiProviderManager not available", "symbols": symbols}
    
    task_start_time = time.time()
    collection_log = None
    results = {}
    end_time = timezone.now().timestamp()
    start_time = end_time - (days_back * 86400)
    
    # Default providers for stocks/ETFs
    if providers is None:
        providers = ["polygon", "alpha_vantage", "eodhd"]
    
    # Create collection log
    if save_to_db:
        collection_log = DataCollectionLog.objects.create(
            task_name="collect_stock_data",
            task_id=self.request.id,
            symbols=symbols,
            providers_used=providers,
            status="success",
        )
    
    try:
        manager = MultiProviderManager(
            providers=providers,
            verify_data=True,
            verification_threshold=0.01,
            cooldown_seconds=30.0,
        )
        
        total_data_points = 0
        successful_symbols = 0
        failed_symbols = 0
        
        for symbol in symbols:
            try:
                logger.info(f"Collecting {granularity} data for {symbol} (last {days_back} days)")
                
                data = manager.get_data(
                    asset=symbol,
                    granularity=granularity,
                    start_date=start_time,
                    end_date=end_time,
                )
                
                data_list = data.get("data", [])
                provider_name = data.get("provider", "unknown")
                data_points = len(data_list)
                total_data_points += data_points
                
                # Save to database
                if save_to_db and data_points > 0:
                    # Determine asset type
                    asset_type = "etf" if symbol.upper() in ["SPY", "QQQ", "DIA", "IWM"] else "stock"
                    saved_count = _save_market_data_points(
                        data_list=data_list,
                        symbol=symbol,
                        asset_type=asset_type,
                        granularity=granularity,
                        provider=provider_name,
                        raw_data=data,
                    )
                    logger.info(f"✓ Saved {saved_count} data points for {symbol} to database")
                
                results[symbol] = {
                    "status": "success",
                    "provider": provider_name,
                    "data_points": data_points,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "end_time": datetime.fromtimestamp(end_time).isoformat(),
                }
                successful_symbols += 1
                
                logger.info(f"✓ Collected {data_points} data points for {symbol} from {provider_name}")
                
            except Exception as e:
                logger.error(f"Failed to collect data for {symbol}: {e}", exc_info=True)
                results[symbol] = {
                    "status": "error",
                    "error": str(e),
                }
                failed_symbols += 1
        
        # Update collection log
        if collection_log:
            duration = time.time() - task_start_time
            collection_log.status = "partial" if failed_symbols > 0 else "success"
            collection_log.data_points_collected = total_data_points
            collection_log.symbols_successful = successful_symbols
            collection_log.symbols_failed = failed_symbols
            collection_log.duration_seconds = duration
            collection_log.completed_at = timezone.now()
            if failed_symbols > 0:
                collection_log.error_message = f"{failed_symbols} symbols failed"
            collection_log.save()
        
        return {
            "status": "completed",
            "results": results,
            "data_points_collected": total_data_points,
            "timestamp": timezone.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Stock data collection task failed: {e}", exc_info=True)
        if collection_log:
            collection_log.status = "error"
            collection_log.error_message = str(e)
            collection_log.duration_seconds = time.time() - task_start_time
            collection_log.completed_at = timezone.now()
            collection_log.save()
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def collect_market_overview(self, save_to_db: bool = True) -> Dict[str, Any]:
    """
    Collect market overview data (top cryptos, market caps, etc.) and save to database.
    
    Uses CoinMarketCap or CoinGecko for listings.
    
    Returns:
        Dictionary with market overview data
    """
    if MultiProviderManager is None:
        logger.error("MultiProviderManager not available")
        return {"error": "MultiProviderManager not available"}
    
    try:
        # Fetch top 100 cryptos
        logger.info("Collecting market overview (top 100 cryptos)")
        
        # For CMC, use listings endpoint
        try:
            from fks_data.adapters import get_adapter
            
            cmc = get_adapter("cmc")
            data = cmc.fetch(
                endpoint="listings_latest",
                limit=100,
                convert="USD",
            )
            
            listings = data.get("data", [])
            total_market_cap = sum(float(item.get("market_cap", 0)) for item in listings)
            total_volume = sum(float(item.get("volume_24h", 0)) for item in listings)
            
            # Save to database
            if save_to_db:
                MarketOverview.objects.create(
                    timestamp=timezone.now(),
                    provider="cmc",
                    total_market_cap=Decimal(str(total_market_cap)),
                    total_volume_24h=Decimal(str(total_volume)),
                    active_cryptocurrencies=len(listings),
                    listings_count=len(listings),
                    raw_data=data,
                )
                logger.info(f"✓ Saved market overview to database")
            
            return {
                "status": "success",
                "provider": "cmc",
                "listings_count": len(listings),
                "total_market_cap": total_market_cap,
                "total_volume_24h": total_volume,
                "timestamp": timezone.now().isoformat(),
            }
            
        except Exception as e:
            logger.warning(f"CMC failed, trying CoinGecko: {e}")
            # Fallback to CoinGecko
            coingecko = get_adapter("coingecko")
            # CoinGecko doesn't have a direct listings endpoint in the adapter
            # Would need to implement or use a different approach
            raise
        
    except Exception as e:
        logger.error(f"Market overview collection failed: {e}", exc_info=True)
        raise self.retry(exc=e)


def _save_market_data_points(
    data_list: List[Dict[str, Any]],
    symbol: str,
    asset_type: str,
    granularity: str,
    provider: str,
    raw_data: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Save market data points to database in bulk.
    
    Args:
        data_list: List of data point dictionaries
        symbol: Asset symbol
        asset_type: Type of asset (crypto, stock, etc.)
        granularity: Data granularity
        provider: Data provider name
        raw_data: Optional raw data for debugging
    
    Returns:
        Number of data points saved
    """
    saved_count = 0
    
    with transaction.atomic():
        for item in data_list:
            try:
                # Parse timestamp
                ts = item.get("ts", 0)
                if isinstance(ts, (int, float)):
                    timestamp = timezone.make_aware(datetime.fromtimestamp(ts))
                else:
                    continue  # Skip invalid timestamps
                
                # Create or update data point
                MarketDataPoint.objects.update_or_create(
                    symbol=symbol,
                    timestamp=timestamp,
                    granularity=granularity,
                    provider=provider,
                    defaults={
                        "asset_type": asset_type,
                        "open": Decimal(str(item.get("open", 0))),
                        "high": Decimal(str(item.get("high", 0))),
                        "low": Decimal(str(item.get("low", 0))),
                        "close": Decimal(str(item.get("close", 0))),
                        "volume": Decimal(str(item.get("volume", 0))),
                        "adjusted_close": Decimal(str(item.get("adjusted_close", item.get("close", 0)))) if item.get("adjusted_close") else None,
                        "market_cap": Decimal(str(item.get("market_cap", 0))) if item.get("market_cap") else None,
                        "raw_data": item if raw_data else None,
                    },
                )
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save data point for {symbol}: {e}")
                continue
    
    return saved_count


@shared_task(bind=True, max_retries=2)
def update_enabled_assets_data(self) -> Dict[str, Any]:
    """
    Update data for all enabled assets.
    
    Reads enabled assets from database or config and collects data for each.
    This is a high-level task that orchestrates multiple collection tasks.
    
    Returns:
        Dictionary with summary of updates
    """
    # TODO: Read enabled assets from database
    # For now, use default list
    default_crypto = ["BTC", "ETH", "BNB", "SOL"]
    default_stocks = ["AAPL", "MSFT", "GOOGL", "SPY"]
    
    results = {
        "crypto": {},
        "stocks": {},
        "timestamp": timezone.now().isoformat(),
    }
    
    # Collect crypto data
    try:
        crypto_result = collect_crypto_data.delay(
            symbols=default_crypto,
            granularity="1h",
            hours_back=24,
        )
        results["crypto"]["task_id"] = crypto_result.id
        results["crypto"]["status"] = "queued"
    except Exception as e:
        logger.error(f"Failed to queue crypto data collection: {e}")
        results["crypto"]["status"] = "error"
        results["crypto"]["error"] = str(e)
    
    # Collect stock data
    try:
        stock_result = collect_stock_data.delay(
            symbols=default_stocks,
            granularity="1d",
            days_back=7,
        )
        results["stocks"]["task_id"] = stock_result.id
        results["stocks"]["status"] = "queued"
    except Exception as e:
        logger.error(f"Failed to queue stock data collection: {e}")
        results["stocks"]["status"] = "error"
        results["stocks"]["error"] = str(e)
    
    return results

