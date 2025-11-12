"""
Django models for portfolio optimization templates and data.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class AccountType(models.TextChoices):
    """Account type choices"""
    PROP_FIRM = 'prop_firm', 'Prop Firm'
    PERSONAL_TRADING = 'personal_trading', 'Personal Trading'
    RETIREMENT = 'retirement', 'Retirement (RRSP/TFSA)'
    TAXABLE = 'taxable', 'Taxable Investment'


class PortfolioAccount(models.Model):
    """Store account inventory data"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_accounts',
        help_text='Owner of this account'
    )
    
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        help_text='Type of account'
    )
    
    # Account details
    account_name = models.CharField(
        max_length=200,
        help_text='Account name or identifier'
    )
    
    firm_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Firm or broker name (for prop firm/trading accounts)'
    )
    
    account_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Account number'
    )
    
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Current account balance'
    )
    
    currency = models.CharField(
        max_length=10,
        default='USD',
        help_text='Account currency'
    )
    
    # Prop firm specific
    drawdown_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum drawdown limit (for prop firm accounts)'
    )
    
    instruments_allowed = models.TextField(
        blank=True,
        help_text='Comma-separated list of allowed instruments'
    )
    
    restrictions = models.TextField(
        blank=True,
        help_text='Account restrictions or rules'
    )
    
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['account_type', 'account_name']
        verbose_name = 'Portfolio Account'
        verbose_name_plural = 'Portfolio Accounts'
    
    def __str__(self):
        return f"{self.account_name} ({self.get_account_type_display()})"


class RiskProfile(models.Model):
    """Store risk assessment data"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='risk_profile',
        help_text='User risk profile'
    )
    
    # Trading accounts risk
    trading_max_drawdown = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text='Maximum acceptable drawdown for trading accounts (%)'
    )
    
    trading_risk_per_trade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text='Maximum risk per trade (%)'
    )
    
    trading_time_horizon = models.CharField(
        max_length=50,
        default='1-3 days',
        help_text='Trading time horizon'
    )
    
    # Long-term accounts risk
    longterm_time_horizon = models.CharField(
        max_length=50,
        default='5-10 years',
        help_text='Long-term investment time horizon'
    )
    
    longterm_max_decline = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        help_text='Maximum acceptable portfolio decline (%)'
    )
    
    longterm_primary_goal = models.CharField(
        max_length=50,
        default='balanced_growth',
        help_text='Primary investment goal'
    )
    
    # ESG preferences
    esg_priority = models.CharField(
        max_length=50,
        default='all_important',
        help_text='ESG priority (environmental, social, governance, all)'
    )
    
    exclude_fossil_fuels = models.BooleanField(
        default=True,
        help_text='Exclude fossil fuel investments'
    )
    
    exclude_tobacco = models.BooleanField(
        default=True,
        help_text='Exclude tobacco investments'
    )
    
    esg_allocation_target = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('25.00'),
        help_text='Target ESG allocation (%)'
    )
    
    # Vanguard risk assessment
    vanguard_risk_score = models.IntegerField(
        null=True,
        blank=True,
        help_text='Vanguard risk tolerance score (0-100)'
    )
    
    vanguard_risk_category = models.CharField(
        max_length=50,
        blank=True,
        help_text='Vanguard risk category'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Risk Profile'
        verbose_name_plural = 'Risk Profiles'
    
    def __str__(self):
        return f"Risk Profile for {self.user.username}"


class PortfolioAudit(models.Model):
    """Store portfolio audit data"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_audits',
        help_text='Owner of this audit'
    )
    
    audit_date = models.DateField(
        help_text='Date of audit'
    )
    
    total_portfolio_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Total portfolio value'
    )
    
    # Current allocations (JSON stored as text for flexibility)
    current_allocations = models.JSONField(
        default=dict,
        help_text='Current asset class allocations'
    )
    
    # Performance metrics
    total_return_twr = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Total Return (TWR) %'
    )
    
    irr = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Internal Rate of Return (IRR) %'
    )
    
    sharpe_ratio = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Sharpe Ratio'
    )
    
    sortino_ratio = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Sortino Ratio'
    )
    
    beta = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Beta (market correlation)'
    )
    
    # Notes and findings
    key_strengths = models.TextField(
        blank=True,
        help_text='Key portfolio strengths'
    )
    
    key_weaknesses = models.TextField(
        blank=True,
        help_text='Key portfolio weaknesses'
    )
    
    priority_actions = models.TextField(
        blank=True,
        help_text='Priority actions identified'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-audit_date']
        verbose_name = 'Portfolio Audit'
        verbose_name_plural = 'Portfolio Audits'
    
    def __str__(self):
        return f"Portfolio Audit - {self.audit_date} ({self.user.username})"

