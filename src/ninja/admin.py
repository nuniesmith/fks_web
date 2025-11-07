"""
Django admin configuration for NT8 account management.

Provides admin interface for:
- Managing NT8 accounts
- Viewing signal logs
- Monitoring connection health
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import NT8Account, SignalLog


@admin.register(NT8Account)
class NT8AccountAdmin(admin.ModelAdmin):
    """Admin interface for NT8 accounts."""

    list_display = [
        'account_display',
        'user',
        'firm_name',
        'socket_port',
        'active_status',
        'signals_today',
        'daily_pnl_display',
        'last_signal_display',
    ]

    list_filter = [
        'active',
        'firm_name',
        'created_at',
    ]

    search_fields = [
        'account_number',
        'user__username',
        'firm_name',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'last_signal_time',
        'signals_today',
    ]

    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'firm_name', 'account_number')
        }),
        ('Connection Settings', {
            'fields': ('socket_port', 'active')
        }),
        ('Trading Status', {
            'fields': ('open_positions_count', 'daily_pnl', 'last_signal_time')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def account_display(self, obj):
        """Display account number with last 4 digits."""
        last_four = obj.account_number[-4:] if len(obj.account_number) >= 4 else obj.account_number
        return f"****{last_four}"
    account_display.short_description = 'Account'

    def active_status(self, obj):
        """Display active status with color coding."""
        if obj.active:
            return format_html('<span style="color: green;">● Active</span>')
        return format_html('<span style="color: red;">○ Inactive</span>')
    active_status.short_description = 'Status'

    def signals_today(self, obj):
        """Count of signals sent today."""
        return obj.get_signals_today_count()
    signals_today.short_description = 'Signals Today'

    def daily_pnl_display(self, obj):
        """Display P&L with color coding."""
        pnl_value = float(obj.daily_pnl)
        if obj.daily_pnl > 0:
            return format_html(
                '<span style="color: green;">${}</span>',
                f"{pnl_value:.2f}"
            )
        elif obj.daily_pnl < 0:
            return format_html(
                '<span style="color: red;">${}</span>',
                f"{pnl_value:.2f}"
            )
        return f"${pnl_value:.2f}"
    daily_pnl_display.short_description = 'Daily P&L'

    def last_signal_display(self, obj):
        """Display last signal time in relative format."""
        if not obj.last_signal_time:
            return '-'
        return obj.last_signal_time.strftime('%H:%M:%S')
    last_signal_display.short_description = 'Last Signal'


@admin.register(SignalLog)
class SignalLogAdmin(admin.ModelAdmin):
    """Admin interface for signal logs."""

    list_display = [
        'timestamp_display',
        'account_link',
        'action_display',
        'instrument',
        'price',
        'success_status',
        'latency_display',
    ]

    list_filter = [
        'success',
        'timestamp',
        'account__firm_name',
    ]

    search_fields = [
        'account__account_number',
        'signal_data',
    ]

    readonly_fields = [
        'account',
        'signal_data',
        'timestamp',
        'success',
        'error_message',
        'latency_ms',
    ]

    fieldsets = (
        ('Signal Details', {
            'fields': ('account', 'signal_data', 'timestamp')
        }),
        ('Delivery Status', {
            'fields': ('success', 'error_message', 'latency_ms')
        }),
    )

    def has_add_permission(self, request):
        """Disable manual signal log creation."""
        return False

    def timestamp_display(self, obj):
        """Display timestamp in readable format."""
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_display.short_description = 'Time'

    def account_link(self, obj):
        """Display account with link to detail page."""
        return format_html(
            '<a href="/admin/ninja/nt8account/{}/change/">{}</a>',
            obj.account.id,
            obj.account
        )
    account_link.short_description = 'Account'

    def action_display(self, obj):
        """Display action with color coding."""
        action = obj.action
        if action in ['BUY', 'LONG']:
            return format_html('<span style="color: green;">▲ {}</span>', action)
        elif action in ['SELL', 'SHORT']:
            return format_html('<span style="color: red;">▼ {}</span>', action)
        return action
    action_display.short_description = 'Action'

    def success_status(self, obj):
        """Display success status with icon."""
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    success_status.short_description = 'Status'

    def latency_display(self, obj):
        """Display latency with color coding."""
        if obj.latency_ms is None:
            return '-'

        if obj.latency_ms < 100:
            color = 'green'
        elif obj.latency_ms < 500:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {};">{} ms</span>',
            color,
            obj.latency_ms
        )
    latency_display.short_description = 'Latency'
