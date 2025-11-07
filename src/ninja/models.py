"""
Django models for NinjaTrader 8 account management and signal logging.

Models:
- NT8Account: Tracks prop firm accounts, connection status, and risk limits
- SignalLog: Audit trail of all signals sent to NT8 accounts
"""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class NT8Account(models.Model):
    """
    Track NinjaTrader 8 prop firm accounts and connection states.

    Each account represents a unique NT8 instance listening on a specific port.
    Supports multiple prop firm accounts per user for signal routing.
    """

    FIRM_CHOICES = [
        ('apex', 'Apex Trader Funding'),
        ('takeprofit', 'Take Profit Trader'),
        ('onestep', 'OneStep Funding'),
        ('topstep', 'TopStep Trader'),
        ('hyrotrader', 'HyroTrader (Crypto)'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nt8_accounts',
        help_text='Owner of this NT8 account'
    )

    firm_name = models.CharField(
        max_length=50,
        choices=FIRM_CHOICES,
        help_text='Prop firm or broker name'
    )

    account_number = models.CharField(
        max_length=100,
        help_text='Account number or identifier'
    )

    socket_port = models.IntegerField(
        unique=True,
        help_text='Unique TCP port for this account (e.g., 8080, 8081)'
    )

    active = models.BooleanField(
        default=True,
        help_text='Whether this account should receive signals'
    )

    last_signal_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of last signal sent to this account'
    )

    open_positions_count = models.IntegerField(
        default=0,
        help_text='Current number of open positions'
    )

    daily_pnl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Today\'s profit/loss in USD'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'firm_name', 'account_number')
        ordering = ['-active', 'firm_name', 'account_number']
        verbose_name = 'NT8 Account'
        verbose_name_plural = 'NT8 Accounts'

    def __str__(self):
        return f"{self.firm_name} - {self.account_number[-4:]} (Port: {self.socket_port})"

    @property
    def masked_account(self):
        """Return masked account number for privacy (e.g., ****5678)."""
        if len(self.account_number) >= 4:
            return f"****{self.account_number[-4:]}"
        return self.account_number

    def get_signals_today_count(self) -> int:
        """Count signals sent today."""
        from datetime import datetime
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.signals.filter(timestamp__gte=today_start).count()


class SignalLog(models.Model):
    """
    Log all signals sent to NT8 accounts.

    Provides complete audit trail for:
    - Debugging signal transmission issues
    - Performance analysis
    - Compliance tracking
    - Trade reconstruction
    """

    account = models.ForeignKey(
        NT8Account,
        on_delete=models.CASCADE,
        related_name='signals',
        help_text='NT8 account that received this signal'
    )

    signal_data = models.JSONField(
        help_text='Complete signal payload (action, instrument, price, TP, SL)'
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When signal was sent'
    )

    success = models.BooleanField(
        default=False,
        help_text='Whether signal was successfully delivered'
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        help_text='Error details if delivery failed'
    )

    latency_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text='Signal delivery latency in milliseconds'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Signal Log'
        verbose_name_plural = 'Signal Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['account', '-timestamp']),
            models.Index(fields=['success', '-timestamp']),
        ]

    def __str__(self):
        status = '✓' if self.success else '✗'
        action = self.signal_data.get('action', 'UNKNOWN')
        price = self.signal_data.get('price', 0)
        return f"{status} {action} @ {price} - {self.timestamp:%H:%M:%S}"

    @property
    def instrument(self) -> str:
        """Extract instrument from signal data."""
        return self.signal_data.get('instrument', 'N/A')

    @property
    def action(self) -> str:
        """Extract action from signal data."""
        return self.signal_data.get('action', 'N/A').upper()

    @property
    def price(self) -> float:
        """Extract price from signal data."""
        return self.signal_data.get('price', 0.0)
