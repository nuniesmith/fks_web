# Portfolio Optimization Web Interface

**Date**: 2025-01-15  
**Status**: ✅ **Ready to Use**  
**Purpose**: Web-based interface for editing portfolio optimization Phase 1 templates

---

## 🎯 Overview

The web interface allows users to:
- ✅ Add and manage accounts through forms
- ✅ Complete risk assessment questionnaires
- ✅ Create and edit portfolio audits
- ✅ View progress and summaries
- ✅ All data stored in database (editable anytime)

---

## 📋 Features

### 1. Account Inventory Management
- **URL**: `/portfolio/optimization/accounts/`
- **Features**:
  - Add accounts (prop firm, personal trading, retirement, taxable)
  - Edit existing accounts
  - Delete accounts
  - View totals and percentages
  - Grouped by account type

### 2. Risk Assessment
- **URL**: `/portfolio/optimization/risk/`
- **Features**:
  - Trading accounts risk settings
  - Long-term accounts risk settings
  - ESG preferences
  - Vanguard risk assessment results

### 3. Portfolio Audit
- **URL**: `/portfolio/optimization/audits/`
- **Features**:
  - Create new audits
  - Edit existing audits
  - View audit history
  - Performance metrics tracking

### 4. Optimization Dashboard
- **URL**: `/portfolio/optimization/`
- **Features**:
  - Progress overview
  - Phase 1 completion status
  - Quick navigation
  - Summary cards

---

## 🚀 Setup Instructions

### 1. Run Migrations

```bash
cd repo/web
python manage.py makemigrations portfolio
python manage.py migrate portfolio
```

### 2. Access the Interface

1. Start the web service:
   ```bash
   docker-compose up fks_web
   ```

2. Navigate to:
   - Dashboard: `http://localhost:8000/portfolio/optimization/`
   - Accounts: `http://localhost:8000/portfolio/optimization/accounts/`
   - Risk: `http://localhost:8000/portfolio/optimization/risk/`
   - Audits: `http://localhost:8000/portfolio/optimization/audits/`

---

## 📊 Data Models

### PortfolioAccount
- Stores account inventory data
- Supports all account types (prop firm, personal trading, retirement, taxable)
- User-specific (each user has their own accounts)

### RiskProfile
- One per user (OneToOne relationship)
- Stores risk tolerance settings
- ESG preferences
- Vanguard assessment results

### PortfolioAudit
- Multiple audits per user
- Stores performance metrics
- Analysis and findings
- Historical tracking

---

## 🎨 User Experience

### Account Management
1. Click "Add Account" button
2. Fill out form (all fields optional except account name and type)
3. Save - account appears in appropriate section
4. Edit/Delete as needed
5. View totals automatically calculated

### Risk Assessment
1. Navigate to Risk Assessment page
2. Fill out all sections
3. Save - profile created/updated
4. Can edit anytime

### Portfolio Audit
1. Click "New Audit" button
2. Enter audit date and portfolio value
3. Fill in performance metrics (optional)
4. Add analysis notes
5. Save - audit added to history

---

## 🔗 Integration

The web interface integrates with:
- **Django Authentication**: User-specific data
- **Portfolio Service**: Can sync data via API (future enhancement)
- **Database**: All data persisted in PostgreSQL

---

## 📝 Next Steps

1. **Run migrations** to create database tables
2. **Test the interface** by adding sample accounts
3. **Complete Phase 1** using the web forms
4. **Export data** (future: add export functionality)

---

## 🛠️ Technical Details

### Models
- `PortfolioAccount` - Account inventory
- `RiskProfile` - Risk assessment
- `PortfolioAudit` - Portfolio audits

### Views
- `OptimizationDashboardView` - Main dashboard
- `AccountInventoryView` - Account list
- `AccountCreateView` / `AccountUpdateView` / `AccountDeleteView` - Account CRUD
- `RiskAssessmentView` - Risk profile form
- `PortfolioAuditListView` / `PortfolioAuditCreateView` / `PortfolioAuditUpdateView` - Audit CRUD

### Templates
- `optimization_dashboard.html` - Main dashboard
- `account_inventory.html` - Account list
- `account_form.html` - Account add/edit
- `risk_assessment.html` - Risk profile form
- `audit_list.html` - Audit list
- `audit_form.html` - Audit add/edit

---

**Last Updated**: 2025-01-15

