from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .logistics_analytics import LogisticsAnalytics, KPISecretDashboard
from .models import Vehicle, Branch
from datetime import datetime
import json

@login_required
def logistics_dashboard(request):
    """Main logistics dashboard view"""
    from .models import Vehicle
    vehicles = Vehicle.objects.all()
    return render(request, 'core/logistics_dashboard.html', {'vehicles': vehicles})

@login_required
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
def kpi_secret_dashboard(request):
    """Secret KPI dashboard view"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return render(request, 'core/access_denied.html')
    
    return render(request, 'core/kpi_secret_dashboard.html')

@login_required
def kpi_dashboard_api(request):
    """API endpoint for KPI secret dashboard data"""
    try:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get date filters from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Convert to datetime if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        kpi_dashboard = KPISecretDashboard()
        
        # Get all branches
        branches = Branch.objects.all()
        dashboard_data = []
        
        for branch in branches:
            branch_performance = kpi_dashboard.analyze_branch_performance(
                branch.id,
                start_date=start_date,
                end_date=end_date
            )
            dashboard_data.append(branch_performance)
        
        # Sort by adjusted KPI
        dashboard_data.sort(key=lambda x: x['adjusted_kpi'], reverse=True)
        
        # Calculate summary
        import numpy as np
        summary = {
            'total_branches': len(dashboard_data),
            'avg_profit_margin': float(np.mean([b['profit_margin'] for b in dashboard_data])) if dashboard_data else 0,
            'avg_adjusted_kpi': float(np.mean([b['adjusted_kpi'] for b in dashboard_data])) if dashboard_data else 0,
            'high_performing_branches': len([b for b in dashboard_data if b['adjusted_kpi'] >= 70])
        }
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'branch_performances': dashboard_data,
                'summary': summary
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
def branch_performance_detail_api(request, branch_id):
    """API endpoint for detailed branch performance"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
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