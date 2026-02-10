from django.urls import path, include
from . import views
from . import views_logistics
from . import order_management_views
from . import views_finance
from . import views_broken_products
# from . import analytics_views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Branches
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/<int:pk>/', views.branch_detail, name='branch_detail'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),
    
    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Stock
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/add/', views.stock_create, name='stock_create'),
    path('stock/<int:pk>/reduce/', views.stock_reduce, name='stock_reduce'),
    path('stock/<int:pk>/delete/', views.stock_delete, name='stock_delete'),
    path('stock/print/', views.stock_print, name='stock_print'),
    path('stock/movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock/movements/print/', views.stock_movements_print, name='stock_movements_print'),
    path('stock/transfer/', views.stock_transfer, name='stock_transfer'),
    path('stock/transfer/<int:pk>/approve/', views.approve_transfer, name='approve_transfer'),
    
    # Orders - Basic
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/complete/', views.order_complete, name='order_complete'),
    
    # Orders - Enhanced Management
    path('orders/<int:pk>/edit/', order_management_views.order_edit, name='order_edit'),
    path('orders/<int:pk>/partial-complete/', order_management_views.order_partial_complete, name='order_partial_complete'),
    path('orders/<int:pk>/change-branch/', order_management_views.order_change_branch, name='order_change_branch'),
    path('orders/<int:order_pk>/items/<int:item_pk>/complete/', order_management_views.order_item_complete, name='order_item_complete'),
    path('orders/<int:pk>/history/', order_management_views.order_completion_history, name='order_completion_history'),
    path('orders/bulk-operations/', order_management_views.bulk_order_operations, name='bulk_order_operations'),
    
    # Order API
    path('api/order-items/<int:item_pk>/', order_management_views.get_order_item_details, name='get_order_item_details'),
    
    # Sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/create/', views.sale_create, name='sale_create'),
    path('sales/<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/print/', views.expenses_print, name='expenses_print'),
    
    # Logistics
    path('logistics/', views.logistics_list, name='logistics_list'),
    path('logistics/create/', views.logistics_create, name='logistics_create'),
    path('logistics/<int:pk>/edit/', views.logistics_edit, name='logistics_edit'),
    path('logistics/<int:pk>/update/', views.logistics_update_status, name='logistics_update_status'),
    
    # Finance
    path('finance/reports/', views.financial_reports, name='financial_reports'),
    path('finance/ledger/', views_finance.ledger_list, name='ledger_list'),
    path('finance/accounts/', views_finance.chart_of_accounts, name='chart_of_accounts'),
    path('finance/accounts/create/', views_finance.chart_of_accounts_create, name='chart_of_accounts_create'),
    path('finance/accounts/<int:pk>/update/', views_finance.chart_of_accounts_update, name='chart_of_accounts_update'),
    path('finance/income/', views_finance.income_register, name='income_register'),
    path('finance/income/create/', views_finance.income_register_create, name='income_register_create'),
    path('finance/income/<int:pk>/update/', views_finance.income_register_update, name='income_register_update'),
    path('finance/income/<int:pk>/post/', views_finance.income_register_post, name='income_register_post'),
    path('finance/expenses/', views_finance.expense_register, name='expense_register'),
    path('finance/expenses/create/', views_finance.expense_register_create, name='expense_register_create'),
    path('finance/expenses/<int:pk>/update/', views_finance.expense_register_update, name='expense_register_update'),
    path('finance/expenses/<int:pk>/post/', views_finance.expense_register_post, name='expense_register_post'),
    path('finance/loans/', views_finance.loans_register, name='loans_register'),
    path('finance/loans/create/', views_finance.loans_register_create, name='loans_register_create'),
    path('finance/loans/<int:pk>/update/', views_finance.loans_register_update, name='loans_register_update'),
    path('finance/loans/<int:pk>/post/', views_finance.loans_register_post, name='loans_register_post'),
    path('finance/logistics-ledger/', views_finance.logistics_ledger, name='logistics_ledger'),
    path('finance/payroll/', views_finance.payroll_ledger, name='payroll_ledger'),
    path('finance/payroll/create/', views_finance.payroll_ledger_create, name='payroll_ledger_create'),
    path('finance/payroll/<int:pk>/update/', views_finance.payroll_ledger_update, name='payroll_ledger_update'),
    path('finance/payroll/<int:pk>/post/', views_finance.payroll_ledger_post, name='payroll_ledger_post'),
    path('finance/allowances/', views_finance.allowances_register, name='allowances_register'),
    path('finance/allowances/create/', views_finance.allowances_register_create, name='allowances_register_create'),
    path('finance/allowances/<int:pk>/update/', views_finance.allowances_register_update, name='allowances_register_update'),
    path('finance/ledger/<int:pk>/reverse/', views_finance.ledger_reverse, name='ledger_reverse'),
    
    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    
    # Vehicles
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    
    # Trips
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/create/', views.trip_create, name='trip_create'),
    path('trips/<int:pk>/edit/', views.trip_update, name='trip_update'),
    path('trips/<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    path('trips/print/', views.trips_print, name='trips_print'),
    
    # Maintenance
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/create/', views.maintenance_create, name='maintenance_create'),
    path('maintenance/<int:pk>/edit/', views.maintenance_edit, name='maintenance_edit'),
    
    # Broken Products
    path('broken-products/', views_broken_products.broken_products_list, name='broken_products_list'),
    path('broken-products/report/', views_broken_products.report_broken_product, name='report_broken_product'),
    path('broken-products/report/<int:stock_id>/', views_broken_products.report_broken_product, name='report_broken_product_for_stock'),
    
    # Business Notebook
    path('notebook/', views.notebook, name='notebook'),
    path('notes/print/', views.notes_print, name='notes_print'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),

    # Content Management
    path('content-management/', views.content_management, name='content_management'),
    
    # Physical Stock Count
    path('physical-count/', views.physical_count, name='physical_count'),
    path('physical-count/submit/', views.physical_count_submit, name='physical_count_submit'),
    
    # PDF Generation
    path('sales/<int:pk>/print/', views.sale_print, name='sale_print'),
    path('orders/<int:pk>/print/', views.order_print, name='order_print'),
    path('expenses/<int:pk>/print/', views.expense_print, name='expense_print'),
    path('trips/<int:pk>/print/', views.trip_print, name='trip_print'),
    path('logistics/<int:pk>/print/', views.logistics_print, name='logistics_print'),
    path('maintenance/<int:pk>/print/', views.maintenance_print, name='maintenance_print'),
    path('reports/financial/print/', views.financial_report_print, name='financial_report_print'),
    path('reports/branch/<int:branch_id>/monthly/', views.branch_monthly_report, name='branch_monthly_report'),
    path('reports/business/master/', views.business_master_report, name='business_master_report'),
    
    # API
    path('api/branch/<int:branch_id>/stocks/', views.get_branch_stocks, name='get_branch_stocks'),
    
    # Enterprise Price Management
    path('pricing/', include('core.urls_pricing')),
    
    # Logistics Analytics
    path('logistics-performance/', views_logistics.logistics_dashboard, name='logistics_dashboard'),
    path('api/logistics-analysis/', views_logistics.logistics_analysis_api, name='logistics_analysis_api'),
    path('api/trip-distance/', views_logistics.vehicle_trip_distance_api, name='vehicle_trip_distance_api'),
    
    # KPI Secret Dashboard
    path('kpi-secret/', views_logistics.kpi_secret_dashboard, name='kpi_secret_dashboard'),
    path('kpi-secret/print/', views_logistics.kpi_secret_print, name='kpi_secret_print'),
    path('api/kpi-dashboard/', views_logistics.kpi_dashboard_api, name='kpi_dashboard_api'),
    path('api/branch-performance/<int:branch_id>/', views_logistics.branch_performance_detail_api, name='branch_performance_detail_api'),
    
    # Financial Analytics API
    # path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    # path('modern-analytics/', include('core.urls_analytics')),
    # path('api/analytics/dashboard/', analytics_views.financial_dashboard_api, name='financial_dashboard_api'),
    # path('api/analytics/forecast/', analytics_views.sales_forecast_api, name='sales_forecast_api'),
    # path('api/analytics/inventory/', analytics_views.inventory_optimization_api, name='inventory_optimization_api'),
    # path('api/analytics/risk/', analytics_views.risk_assessment_api, name='risk_assessment_api'),
    # path('api/analytics/routes/', analytics_views.route_optimization_api, name='route_optimization_api'),
    # path('api/analytics/profitability/', analytics_views.profitability_analysis_api, name='profitability_analysis_api'),
    # path('api/analytics/metadata/', analytics_views.analytics_metadata, name='analytics_metadata'),
    # path('api/analytics/report/excel/', analytics_views.generate_excel_report, name='generate_excel_report'),
]
