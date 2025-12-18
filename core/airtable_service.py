"""
Airtable Service for Django ERP System
"""
import os
from pyairtable import Api
from django.conf import settings

class AirtableService:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.api = Api(self.api_key)
        self.base = self.api.base(self.base_id)
    
    def get_table(self, table_name):
        """Get a specific table from Airtable"""
        return self.base.table(table_name)
    
    def create_record(self, table_name, data):
        """Create a new record in Airtable"""
        table = self.get_table(table_name)
        return table.create(data)
    
    def get_records(self, table_name, **kwargs):
        """Get records from Airtable with optional filters"""
        table = self.get_table(table_name)
        return table.all(**kwargs)
    
    def update_record(self, table_name, record_id, data):
        """Update a record in Airtable"""
        table = self.get_table(table_name)
        return table.update(record_id, data)
    
    def delete_record(self, table_name, record_id):
        """Delete a record from Airtable"""
        table = self.get_table(table_name)
        return table.delete(record_id)

# Global instance
airtable_service = AirtableService()