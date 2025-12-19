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
        
        # Table ID mappings from your Airtable
        self.table_ids = {
            'Branches': 'tblz1eVffQhuWOj8n',
            'Products': 'tbllUtxUrOVePvbxP', 
            'Stock': 'tblSFKP5yEsFH9nUy',
            'Sales': 'tblML9VAJRlDi0Hhv',
            'Orders': 'tblvZDXpTzhsPjLWZ',
            'Vehicles': 'tblNvLqYFCnZD7BWT',
            'Trips': 'tbl6OMZB4haqf5OpS',
            'Logistics': 'tblihSff5DeIbiQrb',
            'Expenses': 'tblqq5hhLNd4u4eOH',
            'Stock Movements': 'tblWSTuaYzcbkgamV',
            'Broken Products': 'tblTSzL6mQW71adtc',
            'Vehicle Maintenance': 'tbljptogX5wyPOs78',
            'Fuel Consumption': 'tblUkAB4aJf44zRYb',
            'Employees': 'tblYVVaWuX5M3N60r',
            'User Profiles': 'tblZvs1w0AsYj9t7n',
            'Users': 'tblY1f7ZIyRJlW605'
        }
    
    def get_table(self, table_name):
        """Get a specific table from Airtable using table ID"""
        table_id = self.table_ids.get(table_name, table_name)
        return self.base.table(table_id)
    
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
    
    def batch_create(self, table_name, records):
        """Create multiple records in batch"""
        table = self.get_table(table_name)
        return table.batch_create(records)
    
    def batch_update(self, table_name, records):
        """Update multiple records in batch"""
        table = self.get_table(table_name)
        return table.batch_update(records)

# Global instance
airtable_service = AirtableService()