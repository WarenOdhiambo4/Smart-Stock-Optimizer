#!/usr/bin/env python3
"""
KPI Dashboard API Test
Tests the API endpoint to ensure it returns valid JSON
"""

import os
import django
import sys
import json

# Setup Django
sys.path.append('/home/waren/Desktop/blogchain_project/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from core.views_logistics import kpi_dashboard_api
from core.models import UserProfile, Branch

def test_kpi_api():
    """Test KPI dashboard API endpoint"""
    print("🌐 Testing KPI Dashboard API")
    print("=" * 30)
    
    try:
        # Create a test request
        factory = RequestFactory()
        request = factory.get('/api/kpi-dashboard/')
        
        # Create or get a test user
        user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'admin@test.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Create or get user profile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'ADMIN'}
        )
        
        request.user = user
        
        # Call the API
        print("📡 Calling KPI dashboard API...")
        response = kpi_dashboard_api(request)
        
        print(f"✅ API response status: {response.status_code}")
        print(f"📄 Content type: {response.get('Content-Type', 'application/json')}")
        
        # Get response content
        content = response.content.decode('utf-8')
        print(f"📊 Response length: {len(content)} characters")
        
        # Try to parse JSON
        try:
            data = json.loads(content)
            print("✅ JSON parsing successful")
            print(f"📊 Response status: {data.get('status', 'unknown')}")
            
            if data.get('status') == 'success':
                branch_count = len(data.get('data', {}).get('branch_performances', []))
                print(f"🏢 Branches in response: {branch_count}")
                
                summary = data.get('data', {}).get('summary', {})
                print(f"📈 Summary:")
                print(f"  - Total Branches: {summary.get('total_branches', 0)}")
                print(f"  - Avg Profit Margin: {summary.get('avg_profit_margin', 0):.2f}%")
                print(f"  - High Performers: {summary.get('high_performing_branches', 0)}")
            else:
                print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
                
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON parsing failed: {json_error}")
            print(f"📄 Raw content (first 500 chars): {content[:500]}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()

def test_branch_data():
    """Test branch data availability"""
    print(f"\n🏢 Testing Branch Data")
    print("=" * 20)
    
    try:
        branches = Branch.objects.all()
        print(f"📊 Found {branches.count()} branches:")
        
        for branch in branches:
            print(f"  - {branch.name} (ID: {branch.id})")
            
        if branches.count() == 0:
            print("⚠️  No branches found - this might cause API issues")
        else:
            print("✅ Branch data available")
            
    except Exception as e:
        print(f"❌ Branch data test failed: {e}")

if __name__ == "__main__":
    test_branch_data()
    test_kpi_api()