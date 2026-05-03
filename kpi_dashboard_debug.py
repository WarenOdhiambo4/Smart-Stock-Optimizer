
# KPI Dashboard Debug Script
# Tests the KPI dashboard functionality to identify and fix issues
# 

import os
import django
import sys

# Setup Django
sys.path.append('/home/waren/Desktop/blogchain_project/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.logistics_analytics import KPISecretDashboard
from core.models import Branch, Sale, SaleItem
import json

def test_kpi_dashboard():
    """Test KPI dashboard functionality"""
    print(" Testing KPI Dashboard Functionality")
    print("=" * 50)
    
    try:
        # Initialize KPI dashboard
        kpi_dashboard = KPISecretDashboard()
        print("KPI Dashboard initialized successfully")
        
        # Get all branches
        branches = Branch.objects.all()
        print(f"📊 Found {branches.count()} branches")
        
        if branches.count() == 0:
            print(" No branches found. Creating test branch...")
            branch = Branch.objects.create(
                name="Test Branch",
                address="Test Address",
                phone="+254700000000",
                email="test@kabisa.com"
            )
            print(f" Created test branch: {branch.name}")
        
        # Test each branch
        for branch in branches:
            print(f"\n Testing branch: {branch.name}")
            
            try:
                performance = kpi_dashboard.analyze_branch_performance(branch.id)
                print(f"   Branch analysis successful")
                print(f"   Revenue: KES {performance['total_revenue']:,.2f}")
                print(f"   Profit: KES {performance['gross_profit']:,.2f}")
                print(f"  Profit Margin: {performance['profit_margin']:.2f}%")
                print(f"   KPI: {performance['adjusted_kpi']:.2f}%")
                
            except Exception as branch_error:
                print(f"   Branch analysis failed: {branch_error}")
        
        # Test full dashboard data
        print(f"\n Testing full dashboard data...")
        try:
            dashboard_data = kpi_dashboard.get_secret_dashboard_data()
            print(f" Dashboard data retrieved successfully")
            print(f" Summary:")
            print(f"  - Total Branches: {dashboard_data['summary']['total_branches']}")
            print(f"  - Avg Profit Margin: {dashboard_data['summary']['avg_profit_margin']:.2f}%")
            print(f"  - Avg Adjusted KPI: {dashboard_data['summary']['avg_adjusted_kpi']:.2f}%")
            print(f"  - High Performers: {dashboard_data['summary']['high_performing_branches']}")
            
            # Test JSON serialization
            json_data = json.dumps(dashboard_data, indent=2)
            print(f" JSON serialization successful ({len(json_data)} characters)")
            
        except Exception as dashboard_error:
            print(f" Dashboard data failed: {dashboard_error}")
            import traceback
            traceback.print_exc()
        
        print(f"\n KPI Dashboard test completed!")
        
    except Exception as e:
        print(f" KPI Dashboard test failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_response():
    """Test API response format"""
    print(f"\nTesting API Response Format")
    print("=" * 30)
    
    try:
        kpi_dashboard = KPISecretDashboard()
        dashboard_data = kpi_dashboard.get_secret_dashboard_data()
        
        # Simulate API response
        api_response = {
            'status': 'success',
            'data': dashboard_data
        }
        
        # Test JSON serialization
        json_response = json.dumps(api_response, indent=2)
        print(f" API response JSON valid ({len(json_response)} characters)")
        
        # Parse back to verify
        parsed = json.loads(json_response)
        print(f" JSON parsing successful")
        print(f" Response status: {parsed['status']}")
        print(f"Branches in response: {len(parsed['data']['branch_performances'])}")
        
    except Exception as e:
        print(f"API response test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kpi_dashboard()
    test_api_response()
