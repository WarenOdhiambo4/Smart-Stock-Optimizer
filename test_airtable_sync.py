#!/usr/bin/env python
"""
Test Airtable sync connection and table access
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.airtable_service import airtable_service

def test_connection():
    """Test Airtable connection and table access"""
    print("🔍 Testing Airtable Connection...")
    print("="*60)
    
    tables = [
        'Branches', 'Products', 'Stock', 'Sales', 'Orders',
        'Vehicles', 'Trips', 'Logistics', 'Expenses',
        'Stock Movements', 'Broken Products', 'Vehicle Maintenance',
        'Fuel Consumption', 'Employees', 'User Profiles', 'Users'
    ]
    
    for table_name in tables:
        try:
            records = airtable_service.get_records(table_name)
            count = len(records)
            print(f"✅ {table_name}: {count} records")
            
            # Show sample fields if records exist
            if count > 0:
                sample_fields = list(records[0]['fields'].keys())
                print(f"   Fields: {', '.join(sample_fields[:5])}...")
                
        except Exception as e:
            print(f"❌ {table_name}: Error - {str(e)[:50]}")
    
    print("\n" + "="*60)
    print("✅ Connection test complete!")

if __name__ == "__main__":
    test_connection()