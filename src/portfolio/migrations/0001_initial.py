# Generated migration file - run: python manage.py makemigrations portfolio

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_type', models.CharField(choices=[('prop_firm', 'Prop Firm'), ('personal_trading', 'Personal Trading'), ('retirement', 'Retirement (RRSP/TFSA)'), ('taxable', 'Taxable Investment')], max_length=20)),
                ('account_name', models.CharField(max_length=200)),
                ('firm_name', models.CharField(blank=True, max_length=200)),
                ('account_number', models.CharField(blank=True, max_length=100)),
                ('current_balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('drawdown_limit', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('instruments_allowed', models.TextField(blank=True)),
                ('restrictions', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_accounts', to='authentication.user')),
            ],
            options={
                'verbose_name': 'Portfolio Account',
                'verbose_name_plural': 'Portfolio Accounts',
                'ordering': ['account_type', 'account_name'],
            },
        ),
        migrations.CreateModel(
            name='RiskProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trading_max_drawdown', models.DecimalField(decimal_places=2, default=Decimal('5.00'), max_digits=5)),
                ('trading_risk_per_trade', models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=5)),
                ('trading_time_horizon', models.CharField(default='1-3 days', max_length=50)),
                ('longterm_time_horizon', models.CharField(default='5-10 years', max_length=50)),
                ('longterm_max_decline', models.DecimalField(decimal_places=2, default=Decimal('20.00'), max_digits=5)),
                ('longterm_primary_goal', models.CharField(default='balanced_growth', max_length=50)),
                ('esg_priority', models.CharField(default='all_important', max_length=50)),
                ('exclude_fossil_fuels', models.BooleanField(default=True)),
                ('exclude_tobacco', models.BooleanField(default=True)),
                ('esg_allocation_target', models.DecimalField(decimal_places=2, default=Decimal('25.00'), max_digits=5)),
                ('vanguard_risk_score', models.IntegerField(blank=True, null=True)),
                ('vanguard_risk_category', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='risk_profile', to='authentication.user')),
            ],
            options={
                'verbose_name': 'Risk Profile',
                'verbose_name_plural': 'Risk Profiles',
            },
        ),
        migrations.CreateModel(
            name='PortfolioAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audit_date', models.DateField()),
                ('total_portfolio_value', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('current_allocations', models.JSONField(default=dict)),
                ('total_return_twr', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('irr', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('sharpe_ratio', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('sortino_ratio', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('beta', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('key_strengths', models.TextField(blank=True)),
                ('key_weaknesses', models.TextField(blank=True)),
                ('priority_actions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_audits', to='authentication.user')),
            ],
            options={
                'verbose_name': 'Portfolio Audit',
                'verbose_name_plural': 'Portfolio Audits',
                'ordering': ['-audit_date'],
            },
        ),
    ]

