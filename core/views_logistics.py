from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .logistics_analytics import LogisticsAnalytics, KPISecretDashboard
from .models import Vehicle, Branch
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
    month = request.GET.get('month')
    year = request.GET.get('year')
    vehicle_id = request.GET.get('vehicle')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    analytics = LogisticsAnalytics()
    
    # Get live trip analysis with filters
    trips = analytics.get_live_trip_analysis(
        month=month, 
        year=year, 
        vehicle_id=vehicle_id,
        date_from=date_from,
        date_to=date_to
    )
    
    # Get driver KPI analysis with filters
    drivers = analytics.get_driver_kpi_analysis(
        month=month, 
        year=year,
        vehicle_id=vehicle_id,
        date_from=date_from,
        date_to=date_to
    )
    
    # Get monthly summary with filters
    summary = analytics.get_monthly_summary(
        month=month, 
        year=year,
        vehicle_id=vehicle_id,
        date_from=date_from,
        date_to=date_to
    )
    
    return JsonResponse({
        'status': 'success',
        'trips': trips,
        'drivers': drivers,
        'summary': summary
    })

@login_required
def kpi_secret_dashboard(request):
    """Secret KPI dashboard view"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return render(request, 'core/access_denied.html')
    
    return render(request, 'core/kpi_secret_dashboard.html')

@login_required
def kpi_dashboard_api(request):
    """API endpoint for KPI secret dashboard data"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    kpi_dashboard = KPISecretDashboard()
    dashboard_data = kpi_dashboard.get_secret_dashboard_data()
    
    return JsonResponse({
        'status': 'success',
        'data': dashboard_data
    })

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