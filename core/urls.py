from django.urls import path, include
from . import views
from . import views_logistics
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
    path('stock/movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock/transfer/', views.stock_transfer, name='stock_transfer'),
    path('stock/transfer/<int:pk>/approve/', views.approve_transfer, name='approve_transfer'),
    
    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/complete/', views.order_complete, name='order_complete'),
    
    # Sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/create/', views.sale_create, name='sale_create'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    # Logistics
    path('logistics/', views.logistics_list, name='logistics_list'),
    path('logistics/create/', views.logistics_create, name='logistics_create'),
    path('logistics/<int:pk>/update/', views.logistics_update_status, name='logistics_update_status'),
    
    # Finance
    path('finance/reports/', views.financial_reports, name='financial_reports'),
    
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
    
    # Maintenance
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/create/', views.maintenance_create, name='maintenance_create'),
    
    # Business Notebook
    path('notebook/', views.notebook, name='notebook'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
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
    path('api/kpi-dashboard/', views_logistics.kpi_dashboard_api, name='kpi_dashboard_api'),
    path('api/branch-performance/<int:branch_id>/', views_logistics.branch_performance_detail_api, name='branch_performance_detail_api'),
    
    # Financial Analytics API
    # path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('modern-analytics/', include('core.urls_analytics')),
    # path('api/analytics/dashboard/', analytics_views.financial_dashboard_api, name='financial_dashboard_api'),
    # path('api/analytics/forecast/', analytics_views.sales_forecast_api, name='sales_forecast_api'),
    # path('api/analytics/inventory/', analytics_views.inventory_optimization_api, name='inventory_optimization_api'),
    # path('api/analytics/risk/', analytics_views.risk_assessment_api, name='risk_assessment_api'),
    # path('api/analytics/routes/', analytics_views.route_optimization_api, name='route_optimization_api'),
    # path('api/analytics/profitability/', analytics_views.profitability_analysis_api, name='profitability_analysis_api'),
    # path('api/analytics/metadata/', analytics_views.analytics_metadata, name='analytics_metadata'),
    # path('api/analytics/report/excel/', analytics_views.generate_excel_report, name='generate_excel_report'),
]
