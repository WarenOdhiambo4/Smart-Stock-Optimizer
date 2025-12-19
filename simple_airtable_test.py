from pyairtable import Api
import os

# Load environment
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

print(f"API Key: {api_key[:10]}...")
print(f"Base ID: {base_id}")

api = Api(api_key)
base = api.base(base_id)

# Test each table
tables = ['Branches', 'Products', 'Sales', 'Orders']

for table_name in tables:
    try:
        table = base.table(table_name)
        records = table.all()
        print(f"{table_name}: {len(records)} records")
        if records:
            print(f"Sample fields: {list(records[0]['fields'].keys())}")
    except Exception as e:
        print(f"{table_name} error: {e}")
    print("-" * 50)