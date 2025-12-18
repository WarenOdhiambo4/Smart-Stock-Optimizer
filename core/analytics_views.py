"""
Enterprise Financial Analytics Views
Professional-grade financial analysis endpoints for React frontend
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .financial_analytics import FinancialAnalytics, ReportGenerator
from .models import Branch
from .views import role_required


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def financial_dashboard_api(request):
    """
    Main financial analytics API endpoint
    Returns comprehensive financial metrics for React dashboard
    """
    # Get parameters
    branch_id = request.GET.get('branch')
    days = int(request.GET.get('days', 365))
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Initialize analytics engine
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    analytics = FinancialAnalytics(
        branch=branch,
        date_range=(start_date, end_date)
    )
    
    # Generate all analytics
    try:
        profitability = analytics.calculate_profitability_metrics()
        forecast = analytics.sales_forecasting(periods=30)
        inventory = analytics.inventory_optimization()
        routes = analytics.vehicle_route_optimization()
        risk = analytics.financial_risk_assessment()
        
        response_data = {
            'success': True,
            'data': {
                'profitability': profitability,
                'forecast': forecast,
                'inventory': inventory,
                'routes': routes,
                'risk': risk,
                'metadata': {
                    'branch': branch.name if branch else 'All Branches',
                    'date_range': f"{start_date} to {end_date}",
                    'analysis_date': timezone.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        response_data = {
            'success': False,
            'error': str(e),
            'message': 'Analytics calculation failed. Please check data availability.'
        }
    
    return JsonResponse(response_data)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def sales_forecast_api(request):
    """
    Dedicated sales forecasting endpoint
    Uses Prophet for professional-grade forecasting
    """
    branch_id = request.GET.get('branch')
    periods = int(request.GET.get('periods', 30))
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    analytics = FinancialAnalytics(branch=branch)
    
    try:
        forecast_data = analytics.sales_forecasting(periods=periods)
        
        if forecast_data:
            response = {
                'success': True,
                'forecast': forecast_data,
                'metadata': {
                    'branch': branch.name if branch else 'All Branches',
                    'periods': periods,
                    'model': 'Prophet' if 'confidence_interval' in forecast_data else 'Linear Regression'
                }
            }
        else:
            response = {
                'success': False,
                'message': 'Insufficient data for forecasting. Need at least 10 days of sales data.'
            }
    
    except Exception as e:
        response = {
            'success': False,
            'error': str(e),
            'message': 'Forecasting failed. Please check data quality.'
        }
    
    return JsonResponse(response)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def inventory_optimization_api(request):
    """
    Inventory optimization using operations research
    Economic Order Quantity (EOQ) calculations
    """
    branch_id = request.GET.get('branch')
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    analytics = FinancialAnalytics(branch=branch)
    
    try:
        optimization_data = analytics.inventory_optimization()
        
        response = {
            'success': True,
            'optimization': optimization_data,
            'metadata': {
                'branch': branch.name if branch else 'All Branches',
                'analysis_date': timezone.now().isoformat(),
                'algorithm': 'Economic Order Quantity (EOQ)'
            }
        }
    
    except Exception as e:
        response = {
            'success': False,
            'error': str(e),
            'message': 'Inventory optimization failed.'
        }
    
    return JsonResponse(response)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def risk_assessment_api(request):
    """
    Financial risk assessment using statistical models
    Value at Risk (VaR) and other risk metrics
    """
    branch_id = request.GET.get('branch')
    days = int(request.GET.get('days', 365))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    analytics = FinancialAnalytics(
        branch=branch,
        date_range=(start_date, end_date)
    )
    
    try:
        risk_data = analytics.financial_risk_assessment()
        
        response = {
            'success': True,
            'risk': risk_data,
            'metadata': {
                'branch': branch.name if branch else 'All Branches',
                'date_range': f"{start_date} to {end_date}",
                'model': 'Value at Risk (VaR) with Monte Carlo simulation'
            }
        }
    
    except Exception as e:
        response = {
            'success': False,
            'error': str(e),
            'message': 'Risk assessment failed.'
        }
    
    return JsonResponse(response)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def route_optimization_api(request):
    """
    Vehicle route optimization for logistics
    Linear programming for cost minimization
    """
    try:
        analytics = FinancialAnalytics()
        optimization_data = analytics.vehicle_route_optimization()
        
        response = {
            'success': True,
            'optimization': optimization_data,
            'metadata': {
                'date': timezone.now().date().isoformat(),
                'algorithm': 'Linear Programming (PuLP)'
            }
        }
    
    except Exception as e:
        response = {
            'success': False,
            'error': str(e),
            'message': 'Route optimization failed.'
        }
    
    return JsonResponse(response)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def generate_excel_report(request):
    """
    Generate professional Excel report with charts
    Investment bank quality reporting
    """
    branch_id = request.GET.get('branch')
    days = int(request.GET.get('days', 365))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    analytics = FinancialAnalytics(
        branch=branch,
        date_range=(start_date, end_date)
    )
    
    try:
        # Generate all analytics data
        analytics_data = {
            'profitability': analytics.calculate_profitability_metrics(),
            'forecast': analytics.sales_forecasting(periods=30),
            'inventory': analytics.inventory_optimization(),
            'risk': analytics.financial_risk_assessment()
        }
        
        # Generate Excel file
        filename = f"kabisa_financial_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_data = ReportGenerator.generate_excel_report(analytics_data, filename)
        
        # Return as download
        response = HttpResponse(
            excel_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Report generation failed.'
        })


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def analytics_dashboard(request):
    """
    Render the analytics dashboard template
    """
    branches = Branch.objects.filter(is_active=True)
    
    context = {
        'branches': branches,
        'page_title': 'Financial Analytics Dashboard'
    }
    
    return render(request, 'core/analytics_dashboard.html', context)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def profitability_analysis_api(request):
    """
    Detailed profitability analysis by branch, product, time period
    """
    branch_id = request.GET.get('branch')
    days = int(request.GET.get('days', 365))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    analytics = FinancialAnalytics(
        branch=branch,
        date_range=(start_date, end_date)
    )
    
    try:
        profitability_data = analytics.calculate_profitability_metrics()
        
        # Add additional analysis
        sales_df, expenses_df = analytics.get_financial_dataframe()
        
        additional_metrics = {}
        
        if not sales_df.empty:
            # Branch performance (if analyzing all branches)
            if not branch:
                branch_performance = sales_df.groupby('branch__name')['total_amount'].agg([
                    'sum', 'mean', 'count'
                ]).round(2).to_dict('index')
                additional_metrics['branch_performance'] = branch_performance
            
            # Payment method analysis
            payment_analysis = sales_df.groupby('payment_method')['total_amount'].agg([
                'sum', 'count'
            ]).round(2).to_dict('index')
            additional_metrics['payment_methods'] = payment_analysis
        
        if not expenses_df.empty:
            # Expense category analysis
            expense_analysis = expenses_df.groupby('expense_type')['amount'].agg([
                'sum', 'mean', 'count'
            ]).round(2).to_dict('index')
            additional_metrics['expense_categories'] = expense_analysis
        
        response = {
            'success': True,
            'profitability': profitability_data,
            'detailed_analysis': additional_metrics,
            'metadata': {
                'branch': branch.name if branch else 'All Branches',
                'date_range': f"{start_date} to {end_date}",
                'analysis_type': 'Comprehensive Profitability Analysis'
            }
        }
    
    except Exception as e:
        response = {
            'success': False,
            'error': str(e),
            'message': 'Profitability analysis failed.'
        }
    
    return JsonResponse(response)


# Utility function for React frontend
@require_http_methods(["GET"])
def analytics_metadata(request):
    """
    Provide metadata for analytics frontend
    Available branches, date ranges, etc.
    """
    branches = Branch.objects.filter(is_active=True).values('id', 'name')
    
    metadata = {
        'branches': list(branches),
        'available_periods': [
            {'value': 30, 'label': 'Last 30 Days'},
            {'value': 90, 'label': 'Last 3 Months'},
            {'value': 180, 'label': 'Last 6 Months'},
            {'value': 365, 'label': 'Last Year'},
            {'value': 730, 'label': 'Last 2 Years'}
        ],
        'forecast_periods': [
            {'value': 7, 'label': '1 Week'},
            {'value': 30, 'label': '1 Month'},
            {'value': 90, 'label': '3 Months'},
            {'value': 180, 'label': '6 Months'}
        ],
        'analytics_features': [
            'Profitability Analysis',
            'Sales Forecasting (Prophet)',
            'Inventory Optimization (EOQ)',
            'Route Optimization',
            'Risk Assessment (VaR)',
            'Excel Report Generation'
        ]
    }
    
    return JsonResponse(metadata)