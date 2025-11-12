"""
Views for portfolio optimization Phase 1 templates.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from decimal import Decimal

from .models import PortfolioAccount, RiskProfile, PortfolioAudit, AccountType
from .forms import AccountForm, RiskProfileForm, PortfolioAuditForm


class AccountInventoryView(LoginRequiredMixin, TemplateView):
    """Account inventory management view"""
    template_name = 'portfolio/account_inventory.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all accounts grouped by type
        accounts = PortfolioAccount.objects.filter(user=user, active=True)
        
        context['prop_firm_accounts'] = accounts.filter(account_type=AccountType.PROP_FIRM)
        context['personal_trading_accounts'] = accounts.filter(account_type=AccountType.PERSONAL_TRADING)
        context['retirement_accounts'] = accounts.filter(account_type=AccountType.RETIREMENT)
        context['taxable_accounts'] = accounts.filter(account_type=AccountType.TAXABLE)
        
        # Calculate totals
        context['prop_firm_total'] = context['prop_firm_accounts'].aggregate(
            total=Sum('current_balance')
        )['total'] or Decimal('0.00')
        
        context['personal_trading_total'] = context['personal_trading_accounts'].aggregate(
            total=Sum('current_balance')
        )['total'] or Decimal('0.00')
        
        context['retirement_total'] = context['retirement_accounts'].aggregate(
            total=Sum('current_balance')
        )['total'] or Decimal('0.00')
        
        context['taxable_total'] = context['taxable_accounts'].aggregate(
            total=Sum('current_balance')
        )['total'] or Decimal('0.00')
        
        context['grand_total'] = (
            context['prop_firm_total'] +
            context['personal_trading_total'] +
            context['retirement_total'] +
            context['taxable_total']
        )
        
        # Calculate percentages
        if context['grand_total'] > 0:
            context['prop_firm_pct'] = (context['prop_firm_total'] / context['grand_total']) * 100
            context['personal_trading_pct'] = (context['personal_trading_total'] / context['grand_total']) * 100
            context['retirement_pct'] = (context['retirement_total'] / context['grand_total']) * 100
            context['taxable_pct'] = (context['taxable_total'] / context['grand_total']) * 100
        else:
            context['prop_firm_pct'] = 0
            context['personal_trading_pct'] = 0
            context['retirement_pct'] = 0
            context['taxable_pct'] = 0
        
        return context


class AccountCreateView(LoginRequiredMixin, CreateView):
    """Create new account"""
    model = PortfolioAccount
    form_class = AccountForm
    template_name = 'portfolio/account_form.html'
    success_url = reverse_lazy('portfolio:account_inventory')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Account created successfully!')
        return super().form_valid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing account"""
    model = PortfolioAccount
    form_class = AccountForm
    template_name = 'portfolio/account_form.html'
    success_url = reverse_lazy('portfolio:account_inventory')
    
    def get_queryset(self):
        return PortfolioAccount.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Account updated successfully!')
        return super().form_valid(form)


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    """Delete account"""
    model = PortfolioAccount
    template_name = 'portfolio/account_confirm_delete.html'
    success_url = reverse_lazy('portfolio:account_inventory')
    
    def get_queryset(self):
        return PortfolioAccount.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Account deleted successfully!')
        return super().delete(request, *args, **kwargs)


class RiskAssessmentView(LoginRequiredMixin, UpdateView):
    """Risk assessment view"""
    model = RiskProfile
    form_class = RiskProfileForm
    template_name = 'portfolio/risk_assessment.html'
    success_url = reverse_lazy('portfolio:risk_assessment')
    
    def get_object(self, queryset=None):
        obj, created = RiskProfile.objects.get_or_create(user=self.request.user)
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Risk profile updated successfully!')
        return super().form_valid(form)


class PortfolioAuditListView(LoginRequiredMixin, ListView):
    """List portfolio audits"""
    model = PortfolioAudit
    template_name = 'portfolio/audit_list.html'
    context_object_name = 'audits'
    
    def get_queryset(self):
        return PortfolioAudit.objects.filter(user=self.request.user)


class PortfolioAuditCreateView(LoginRequiredMixin, CreateView):
    """Create new portfolio audit"""
    model = PortfolioAudit
    form_class = PortfolioAuditForm
    template_name = 'portfolio/audit_form.html'
    success_url = reverse_lazy('portfolio:audit_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Portfolio audit created successfully!')
        return super().form_valid(form)


class PortfolioAuditUpdateView(LoginRequiredMixin, UpdateView):
    """Update portfolio audit"""
    model = PortfolioAudit
    form_class = PortfolioAuditForm
    template_name = 'portfolio/audit_form.html'
    success_url = reverse_lazy('portfolio:audit_list')
    
    def get_queryset(self):
        return PortfolioAudit.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Portfolio audit updated successfully!')
        return super().form_valid(form)


class OptimizationDashboardView(LoginRequiredMixin, TemplateView):
    """Portfolio optimization Phase 1 dashboard"""
    template_name = 'portfolio/optimization_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get account counts
        accounts = PortfolioAccount.objects.filter(user=user, active=True)
        context['total_accounts'] = accounts.count()
        context['has_accounts'] = context['total_accounts'] > 0
        
        # Check if risk profile exists
        context['has_risk_profile'] = RiskProfile.objects.filter(user=user).exists()
        
        # Get latest audit
        latest_audit = PortfolioAudit.objects.filter(user=user).first()
        context['has_audit'] = latest_audit is not None
        context['latest_audit'] = latest_audit
        
        # Phase 1 completion status
        context['phase1_complete'] = (
            context['has_accounts'] and
            context['has_risk_profile'] and
            context['has_audit']
        )
        
        return context

