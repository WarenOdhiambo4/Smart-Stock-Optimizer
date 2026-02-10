from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .logistics_analytics import LogisticsAnalytics, KPISecretDashboard
from .models import Vehicle, Branch
from .views import role_required
from datetime import datetime
import json

@login_required
@role_required('ADMIN', 'LOGISTICS')
def logistics_dashboard(request):
    """Main logistics dashboard view"""
    from .models import Vehicle
    vehicles = Vehicle.objects.all()
    return render(request, 'core/logistics_dashboard.html', {'vehicles': vehicles})

@login_required
@role_required('ADMIN', 'LOGISTICS')
def logistics_analysis_api(request):
    """API endpoint for logistics analysis data"""
    try:
        vehicle_id = request.GET.get('vehicle')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        print(f"API called with: vehicle={vehicle_id}, date_from={date_from}, date_to={date_to}")
        
        analytics = LogisticsAnalytics()
        
        # Get summary data
        summary = analytics.get_monthly_summary(vehicle_id, date_from, date_to)
        print(f"Summary data: {summary}")
        
        # Get trip analysis
        trips = analytics.get_live_trip_analysis(vehicle_id, date_from, date_to)
        print(f"Found {len(trips)} trips")
        
        # Get driver KPI
        drivers = analytics.get_driver_kpi_analysis(vehicle_id, date_from, date_to)
        print(f"Found {len(drivers)} drivers")
        
        return JsonResponse({
            'status': 'success',
            'trips': trips,
            'drivers': drivers,
            'summary': summary
        })
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
@role_required('ADMIN')
def kpi_secret_dashboard(request):
    """Secret KPI dashboard view"""
    # Skip admin check for now to debug the issue
    # if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
    #     return render(request, 'core/access_denied.html')
    
    return render(request, 'core/kpi_secret_dashboard.html')

@login_required
@role_required('ADMIN')
def kpi_dashboard_api(request):
    """API endpoint for KPI secret dashboard data"""
    from django.db import connection
    
    try:
        # Ensure database connection is active
        connection.ensure_connection()
        
        # Skip admin check for now to debug the issue
        # if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        #     return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get date filters from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Convert to datetime if provided
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                start_date = None
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                end_date = None
        
        kpi_dashboard = KPISecretDashboard()
        
        # Get all branches with fresh connection
        branches = list(Branch.objects.all())
        dashboard_data = []
        
        for branch in branches:
            try:
                # Ensure connection for each branch
                connection.ensure_connection()
                
                branch_performance = kpi_dashboard.analyze_branch_performance(
                    branch.id,
                    start_date=start_date,
                    end_date=end_date
                )
                dashboard_data.append(branch_performance)
            except Exception as branch_error:
                print(f"Branch {branch.name} error: {branch_error}")
                # Add default data for failed branches
                dashboard_data.append({
                    'branch_name': branch.name,
                    'profit_margin': 0,
                    'stock_discrepancy_impact': 2.0,
                    'base_kpi': 0,
                    'adjusted_kpi': 0,
                    'roi': 0,
                    'rot_data': [],
                    'total_revenue': 0,
                    'gross_profit': 0
                })
        
        # Sort by adjusted KPI
        dashboard_data.sort(key=lambda x: x['adjusted_kpi'], reverse=True)
        
        # Calculate summary with safe division
        total_branches = len(dashboard_data)
        if total_branches > 0:
            avg_profit_margin = sum(b['profit_margin'] for b in dashboard_data) / total_branches
            avg_adjusted_kpi = sum(b['adjusted_kpi'] for b in dashboard_data) / total_branches
            high_performing_branches = len([b for b in dashboard_data if b['adjusted_kpi'] >= 70])
        else:
            avg_profit_margin = 0
            avg_adjusted_kpi = 0
            high_performing_branches = 0
        
        summary = {
            'total_branches': total_branches,
            'avg_profit_margin': round(avg_profit_margin, 2),
            'avg_adjusted_kpi': round(avg_adjusted_kpi, 2),
            'high_performing_branches': high_performing_branches
        }
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'branch_performances': dashboard_data,
                'summary': summary
            }
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"KPI Dashboard API Error: {error_details}")
        return JsonResponse({
            'status': 'error',
            'error': f'Server error: {str(e)}'
        }, status=500)

@login_required
@role_required('ADMIN')
def kpi_secret_print(request):
    """Generate PDF for KPI Secret Dashboard"""
    from .receipt_generator import ReceiptGenerator
    from .logistics_analytics import KPISecretDashboard
    from datetime import datetime
    
    try:
        # Get date filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Convert to datetime if provided
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                start_date = None
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                end_date = None
        
        # Get KPI data
        from .models import Branch
        kpi_dashboard = KPISecretDashboard()
        branches = Branch.objects.all()
        dashboard_data = []
        
        for branch in branches:
            try:
                branch_performance = kpi_dashboard.analyze_branch_performance(
                    branch.id,
                    start_date=start_date,
                    end_date=end_date
                )
                dashboard_data.append(branch_performance)
            except Exception:
                dashboard_data.append({
                    'branch_name': branch.name,
                    'profit_margin': 0,
                    'stock_discrepancy_impact': 2.0,
                    'base_kpi': 0,
                    'adjusted_kpi': 0,
                    'roi': 0,
                    'total_revenue': 0,
                    'gross_profit': 0
                })
        
        # Sort by adjusted KPI
        dashboard_data.sort(key=lambda x: x['adjusted_kpi'], reverse=True)
        
        # Prepare report data
        report_items = []
        total_revenue = 0
        total_profit = 0
        
        for branch in dashboard_data:
            report_items.append({
                'description': f'{branch["branch_name"]} Branch KPI Analysis',
                'details': f'Revenue: KES {branch["total_revenue"]:,.2f} | Profit Margin: {branch["profit_margin"]:.2f}% | Stock Impact: {branch["stock_discrepancy_impact"]:.2f}%',
                'quantity': 1,
                'unit': 'branch',
                'rate': branch['adjusted_kpi'],
                'total': branch['adjusted_kpi']
            })
            total_revenue += branch['total_revenue']
            total_profit += branch['gross_profit']
        
        # Calculate summary
        avg_kpi = sum(b['adjusted_kpi'] for b in dashboard_data) / len(dashboard_data) if dashboard_data else 0
        high_performers = len([b for b in dashboard_data if b['adjusted_kpi'] >= 70])
        
        period_text = "All Time"
        if start_date and end_date:
            period_text = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
        elif start_date:
            period_text = f"From {start_date.strftime('%d %b %Y')}"
        elif end_date:
            period_text = f"Until {end_date.strftime('%d %b %Y')}"
        
        report_data = {
            'document_type': 'KPI Secret Dashboard Report',
            'document_number': f'KPI-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': request.user.get_full_name() or request.user.username,
            'branch': 'All Branches - CONFIDENTIAL',
            'customer': {
                'name': 'KabisaKabisa Management',
                'address': f'Period: {period_text}'
            },
            'items': report_items,
            'subtotal': total_revenue,
            'discount': total_revenue - total_profit,
            'grand_total': avg_kpi,
            'notes': f'Average KPI: {avg_kpi:.2f}% | High Performers: {high_performers}/{len(dashboard_data)} branches | Total Revenue: KES {total_revenue:,.2f} | Total Profit: KES {total_profit:,.2f}'
        }
        
        generator = ReceiptGenerator()
        format_type = request.GET.get('format', 'pdf')
        return generator.generate_financial_report(report_data, format=format_type)
        
    except Exception as e:
        from django.http import HttpResponse
@login_required
@role_required('ADMIN')
def branch_performance_detail_api(request, branch_id):
    """API endpoint for detailed branch performance"""
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    kpi_dashboard = KPISecretDashboard()
    performance_data = kpi_dashboard.analyze_branch_performance(
        branch_id=branch_id,
        month=int(month) if month else None,
        year=int(year) if year else None
    )
    
    return JsonResponse({
        'status': 'success',
        'data': performance_data
    })

@login_required
@role_required('ADMIN', 'LOGISTICS')
def vehicle_trip_distance_api(request):
    """API endpoint to calculate trip distance"""
    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    
    if not origin or not destination:
        return JsonResponse({'error': 'Origin and destination required'}, status=400)
    
    analytics = LogisticsAnalytics()
    distance = analytics.calculate_trip_distance(origin, destination)
    
    return JsonResponse({
        'status': 'success',
        'distance_km': distance
    })
