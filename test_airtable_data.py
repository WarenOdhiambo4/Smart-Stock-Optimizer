import os
import django
import sys

sys.path.append('/home/waren/Desktop/blogchain_project/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.airtable_service import AirtableService

def test_airtable():
    service = AirtableService()
    
    # Test each table
    tables = ['Branches', 'Products', 'Sales', 'Orders']
    
    for table in tables:
        try:
            records = service.get_all_records(table)
            print(f"{table}: {len(records)} records")
            if records:
                print(f"Sample: {records[0]['fields']}")
        except Exception as e:
            print(f"{table} error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_airtable()