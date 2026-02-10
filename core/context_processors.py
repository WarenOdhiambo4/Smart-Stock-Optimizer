from django.db.utils import OperationalError, ProgrammingError


CONTENT_DEFAULTS = {
    'site_name': 'Paroha SCM',
    'page_title_default': 'Kabisa ERP',
    'nav.dashboard': 'Dashboard',
    'nav.organization': 'Organization',
    'nav.branches': 'Branches',
    'nav.employees': 'Employees',
    'nav.notebook': 'Notebook',
    'nav.inventory': 'Inventory',
    'nav.products': 'Products',
    'nav.stock': 'Stock',
    'nav.stock_movements': 'Stock Movements',
    'nav.transfer_stock': 'Transfer Stock',
    'nav.physical_count': 'Physical Stock Count',
    'nav.broken_products': 'Broken Products',
    'nav.operations': 'Operations',
    'nav.orders': 'Orders',
    'nav.sales': 'Sales',
    'nav.expenses': 'Operational Expenses',
    'nav.logistics': 'Logistics',
    'nav.deliveries': 'Deliveries',
    'nav.logistics_analytics': 'Performance Analytics',
    'nav.vehicles': 'Vehicles',
    'nav.trips': 'Trips',
    'nav.maintenance': 'Maintenance',
    'nav.finance': 'Finance',
    'nav.general_ledger': 'General Ledger',
    'nav.chart_of_accounts': 'Chart of Accounts',
    'nav.income_register': 'Income Register',
    'nav.expense_register': 'Expense Register',
    'nav.loans_register': 'Loans Register',
    'nav.payroll_ledger': 'Payroll Ledger',
    'nav.allowances_register': 'Allowances Register',
    'nav.live_analysis': 'Live Analysis',
    'nav.admin': 'Admin',
    'nav.users': 'Users',
    'nav.kpi_secret': 'KPI Secret',
    'nav.content_management': 'Content Management',
    'nav.settings': 'Settings',
    'nav.logout': 'Logout',
    'login.page_title': 'Login',
    'login.title': 'Sign In',
    'login.subtitle': 'Welcome back',
    'login.username_label': 'Username',
    'login.password_label': 'Password',
    'login.username_placeholder': 'Enter username',
    'login.password_placeholder': 'Enter password',
    'login.button': 'Sign In',
    'login.verification_label': 'Verification Code',
    'login.verification_placeholder': 'Enter 6-digit code',
    'login.verification_help': 'Check your email for the verification code. Code expires in 5 minutes.',
    'login.verify_button': 'Verify & Login',
    'login.back_button': 'Back to Login',
    'login.footer': '© 2026 Paroha Hardware. All rights reserved.',
}


def system_content(request):
    content = dict(CONTENT_DEFAULTS)
    try:
        from .models import SystemContent
        for row in SystemContent.objects.filter(is_active=True):
            content[row.key] = row.value
    except (OperationalError, ProgrammingError, Exception):
        pass
    return {'content': content}
