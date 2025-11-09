"""
Django models for storing collected market data.

These models store OHLCV data and market statistics collected by
the multi-provider data collection system.
"""
from django.db import models
from django.utils import timezone


class MarketDataPoint(models.Model):
    """
    Store individual OHLCV data points for any asset.
    
    Supports both crypto and traditional assets (stocks, ETFs).
    """
    
    ASSET_TYPE_CHOICES = [
        ("crypto", "Cryptocurrency"),
        ("stock", "Stock"),
        ("etf", "ETF"),
        ("forex", "Forex"),
        ("commodity", "Commodity"),
    ]
    
    # Asset identification
    symbol = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Asset symbol (e.g., BTC, AAPL, SPY)"
    )
    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPE_CHOICES,
        default="crypto",
        db_index=True,
        help_text="Type of asset"
    )
    
    # Time and granularity
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Timestamp of this data point"
    )
    granularity = models.CharField(
        max_length=10,
        default="1m",
        db_index=True,
        help_text="Data granularity (1m, 5m, 1h, 1d, etc.)"
    )
    
    # OHLCV data
    open = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Opening price"
    )
    high = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="High price"
    )
    low = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Low price"
    )
    close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Closing price"
    )
    volume = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0,
        help_text="Trading volume"
    )
    
    # Additional fields
    adjusted_close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Adjusted closing price (for stocks with splits/dividends)"
    )
    market_cap = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Market capitalization (for crypto)"
    )
    
    # Metadata
    provider = models.CharField(
        max_length=50,
        help_text="Data provider (binance, polygon, cmc, etc.)"
    )
    raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw data from provider (for debugging)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "market_data_points"
        verbose_name = "Market Data Point"
        verbose_name_plural = "Market Data Points"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["symbol", "timestamp"]),
            models.Index(fields=["symbol", "granularity", "timestamp"]),
            models.Index(fields=["asset_type", "timestamp"]),
            models.Index(fields=["provider", "timestamp"]),
        ]
        # Prevent duplicate data points
        unique_together = [["symbol", "timestamp", "granularity", "provider"]]
    
    def __str__(self):
        return f"{self.symbol} @ {self.timestamp} ({self.granularity}) - {self.provider}"
    
    @property
    def price_change(self) -> float:
        """Calculate price change from open to close."""
        if self.open and self.close:
            return float(self.close - self.open)
        return 0.0
    
    @property
    def price_change_percent(self) -> float:
        """Calculate price change percentage."""
        if self.open and self.open != 0:
            return float((self.close - self.open) / self.open * 100)
        return 0.0


class MarketOverview(models.Model):
    """
    Store market-wide statistics and overview data.
    
    Typically collected hourly or daily from providers like CoinMarketCap.
    """
    
    # Timestamp
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this overview was collected"
    )
    
    # Market statistics
    total_market_cap = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total market capitalization (for crypto)"
    )
    total_volume_24h = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total 24h trading volume"
    )
    active_cryptocurrencies = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of active cryptocurrencies"
    )
    
    # Provider and metadata
    provider = models.CharField(
        max_length=50,
        help_text="Data provider (cmc, coingecko, etc.)"
    )
    listings_count = models.IntegerField(
        default=0,
        help_text="Number of assets in this overview"
    )
    raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw data from provider"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "market_overview"
        verbose_name = "Market Overview"
        verbose_name_plural = "Market Overviews"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["provider", "-timestamp"]),
        ]
    
    def __str__(self):
        return f"Market Overview @ {self.timestamp} ({self.provider})"


class DataCollectionLog(models.Model):
    """
    Log data collection operations for monitoring and debugging.
    """
    
    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
        ("partial", "Partial Success"),
    ]
    
    # Task identification
    task_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the Celery task"
    )
    task_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Celery task ID"
    )
    
    # Operation details
    symbols = models.JSONField(
        default=list,
        help_text="List of symbols processed"
    )
    provider = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Provider used (if single provider)"
    )
    providers_used = models.JSONField(
        default=list,
        help_text="List of providers attempted"
    )
    
    # Results
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True,
        help_text="Overall status of the collection"
    )
    data_points_collected = models.IntegerField(
        default=0,
        help_text="Number of data points successfully collected"
    )
    symbols_successful = models.IntegerField(
        default=0,
        help_text="Number of symbols successfully processed"
    )
    symbols_failed = models.IntegerField(
        default=0,
        help_text="Number of symbols that failed"
    )
    
    # Error information
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if collection failed"
    )
    error_details = models.JSONField(
        null=True,
        blank=True,
        help_text="Detailed error information"
    )
    
    # Performance metrics
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Time taken to complete collection"
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = "data_collection_logs"
        verbose_name = "Data Collection Log"
        verbose_name_plural = "Data Collection Logs"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["-started_at"]),
            models.Index(fields=["task_name", "-started_at"]),
            models.Index(fields=["status", "-started_at"]),
        ]
    
    def __str__(self):
        return f"{self.task_name} @ {self.started_at} - {self.status}"

