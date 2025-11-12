"""
Django forms for portfolio optimization templates.
"""
from django import forms
from django.contrib.auth import get_user_model
from .models import PortfolioAccount, RiskProfile, PortfolioAudit, AccountType

User = get_user_model()


class AccountForm(forms.ModelForm):
    """Form for creating/editing portfolio accounts - flexible for any account type"""
    
    class Meta:
        model = PortfolioAccount
        fields = [
            'account_type', 'account_name', 'firm_name', 'account_number',
            'current_balance', 'currency', 'drawdown_limit',
            'instruments_allowed', 'restrictions', 'notes', 'active'
        ]
        help_texts = {
            'account_type': 'Select the type of account (prop firm, personal trading, retirement, or taxable)',
            'account_name': 'A descriptive name for this account (e.g., "FTMO Challenge", "Main Trading Account")',
            'firm_name': 'Broker or firm name (optional, but recommended for prop firm and trading accounts)',
            'current_balance': 'Current account balance in the specified currency',
            'drawdown_limit': 'Maximum drawdown limit as percentage (mainly for prop firm accounts)',
            'instruments_allowed': 'Comma-separated list of allowed instruments (e.g., "Futures, Forex, Crypto")',
            'restrictions': 'Any account restrictions or rules (e.g., "Daily loss limit 5%")',
            'notes': 'Any additional notes about this account',
        }
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FTMO Challenge'}),
            'firm_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FTMO'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FTMO-XXXXX'}),
            'current_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'USD'}),
            'drawdown_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '5.00'}),
            'instruments_allowed': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Futures, Forex, Crypto'}),
            'restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Daily loss limit 5%'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'account_type': 'Account Type',
            'account_name': 'Account Name',
            'firm_name': 'Firm/Broker Name',
            'account_number': 'Account Number',
            'current_balance': 'Current Balance',
            'currency': 'Currency',
            'drawdown_limit': 'Drawdown Limit (%)',
            'instruments_allowed': 'Instruments Allowed',
            'restrictions': 'Restrictions',
            'notes': 'Notes',
            'active': 'Active',
        }


class RiskProfileForm(forms.ModelForm):
    """Form for creating/editing risk profile"""
    
    class Meta:
        model = RiskProfile
        fields = [
            'trading_max_drawdown', 'trading_risk_per_trade', 'trading_time_horizon',
            'longterm_time_horizon', 'longterm_max_decline', 'longterm_primary_goal',
            'esg_priority', 'exclude_fossil_fuels', 'exclude_tobacco',
            'esg_allocation_target', 'vanguard_risk_score', 'vanguard_risk_category'
        ]
        widgets = {
            'trading_max_drawdown': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'trading_risk_per_trade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'trading_time_horizon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1-3 days'}),
            'longterm_time_horizon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5-10 years'}),
            'longterm_max_decline': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'longterm_primary_goal': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('capital_preservation', 'Capital Preservation'),
                ('income_generation', 'Income Generation'),
                ('balanced_growth', 'Balanced Growth'),
                ('aggressive_growth', 'Aggressive Growth'),
                ('maximum_returns', 'Maximum Returns'),
            ]),
            'esg_priority': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('environmental', 'Environmental'),
                ('social', 'Social'),
                ('governance', 'Governance'),
                ('all_important', 'All Equally Important'),
            ]),
            'exclude_fossil_fuels': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'exclude_tobacco': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esg_allocation_target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vanguard_risk_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'vanguard_risk_category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Moderate'}),
        }


class PortfolioAuditForm(forms.ModelForm):
    """Form for creating/editing portfolio audit"""
    
    class Meta:
        model = PortfolioAudit
        fields = [
            'audit_date', 'total_portfolio_value',
            'total_return_twr', 'irr', 'sharpe_ratio', 'sortino_ratio', 'beta',
            'key_strengths', 'key_weaknesses', 'priority_actions'
        ]
        widgets = {
            'audit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_portfolio_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_return_twr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '87.87'}),
            'irr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '13.54'}),
            'sharpe_ratio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '0.909'}),
            'sortino_ratio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '1.531'}),
            'beta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '0.848'}),
            'key_strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'key_weaknesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority_actions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

