"""
Admin interfaces for data collection models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import DataCollectionLog, MarketDataPoint, MarketOverview


@admin.register(MarketDataPoint)
class MarketDataPointAdmin(admin.ModelAdmin):
    """Admin interface for market data points."""
    
    list_display = [
        "symbol",
        "asset_type",
        "timestamp",
        "granularity",
        "close",
        "volume",
        "provider",
        "price_change_display",
        "created_at",
    ]
    list_filter = [
        "asset_type",
        "granularity",
        "provider",
        "timestamp",
        "created_at",
    ]
    search_fields = ["symbol", "provider"]
    readonly_fields = ["created_at", "updated_at", "price_change", "price_change_percent"]
    
    fieldsets = (
        ("Asset Information", {
            "fields": ("symbol", "asset_type", "granularity")
        }),
        ("Time", {
            "fields": ("timestamp",)
        }),
        ("OHLCV Data", {
            "fields": ("open", "high", "low", "close", "volume")
        }),
        ("Additional Data", {
            "fields": ("adjusted_close", "market_cap"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("provider", "raw_data"),
            "classes": ("collapse",)
        }),
        ("Computed Fields", {
            "fields": ("price_change", "price_change_percent"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def price_change_display(self, obj):
        """Display price change with color coding."""
        change = obj.price_change_percent
        if change > 0:
            return format_html('<span style="color: green;">+{:.2f}%</span>', change)
        elif change < 0:
            return format_html('<span style="color: red;">{:.2f}%</span>', change)
        return format_html('<span>{:.2f}%</span>', change)
    price_change_display.short_description = "Change %"
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related()


@admin.register(MarketOverview)
class MarketOverviewAdmin(admin.ModelAdmin):
    """Admin interface for market overview data."""
    
    list_display = [
        "timestamp",
        "provider",
        "total_market_cap",
        "total_volume_24h",
        "active_cryptocurrencies",
        "listings_count",
        "created_at",
    ]
    list_filter = [
        "provider",
        "timestamp",
        "created_at",
    ]
    search_fields = ["provider"]
    readonly_fields = ["created_at"]
    
    fieldsets = (
        ("Overview", {
            "fields": ("timestamp", "provider", "listings_count")
        }),
        ("Market Statistics", {
            "fields": ("total_market_cap", "total_volume_24h", "active_cryptocurrencies")
        }),
        ("Raw Data", {
            "fields": ("raw_data",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )


@admin.register(DataCollectionLog)
class DataCollectionLogAdmin(admin.ModelAdmin):
    """Admin interface for data collection logs."""
    
    list_display = [
        "task_name",
        "status_display",
        "symbols_count",
        "data_points_collected",
        "duration_display",
        "started_at",
    ]
    list_filter = [
        "status",
        "task_name",
        "started_at",
    ]
    search_fields = ["task_name", "task_id", "error_message"]
    readonly_fields = [
        "started_at",
        "completed_at",
        "duration_seconds",
        "symbols",
        "providers_used",
    ]
    
    fieldsets = (
        ("Task Information", {
            "fields": ("task_name", "task_id", "status")
        }),
        ("Operation Details", {
            "fields": ("symbols", "provider", "providers_used")
        }),
        ("Results", {
            "fields": (
                "data_points_collected",
                "symbols_successful",
                "symbols_failed",
            )
        }),
        ("Performance", {
            "fields": ("duration_seconds", "started_at", "completed_at")
        }),
        ("Errors", {
            "fields": ("error_message", "error_details"),
            "classes": ("collapse",)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            "success": "green",
            "error": "red",
            "partial": "orange",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Status"
    
    def symbols_count(self, obj):
        """Display number of symbols."""
        return len(obj.symbols) if obj.symbols else 0
    symbols_count.short_description = "Symbols"
    
    def duration_display(self, obj):
        """Display duration in human-readable format."""
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.2f}s"
            else:
                return f"{obj.duration_seconds / 60:.2f}m"
        return "-"
    duration_display.short_description = "Duration"

