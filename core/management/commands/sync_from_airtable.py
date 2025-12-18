"""
Sync data FROM Airtable TO Django
"""
from django.core.management.base import BaseCommand
from core.airtable_service import airtable_service
from core.models import Branch, Product, Sale, Order
from decimal import Decimal
from datetime import datetime

class Command(BaseCommand):
    help = 'Sync data from Airtable to Django'

    def handle(self, *args, **options):
        self.sync_branches()
        self.sync_products()
        self.sync_sales()
        self.sync_orders()
        
    def sync_branches(self):
        try:
            records = airtable_service.get_records('Branches')
            for record in records:
                fields = record['fields']
                Branch.objects.update_or_create(
                    airtable_id=record['id'],
                    defaults={
                        'name': fields.get('Name', ''),
                        'address': fields.get('Address', ''),
                        'phone': fields.get('Phone', ''),
                        'email': fields.get('Email', ''),
                        'is_active': fields.get('Active', True),
                    }
                )
            self.stdout.write(f"✓ Synced {len(records)} branches from Airtable")
        except Exception as e:
            self.stdout.write(f"✗ Error syncing branches: {e}")
    
    def sync_products(self):
        try:
            records = airtable_service.get_records('Products')
            for record in records:
                fields = record['fields']
                Product.objects.update_or_create(
                    airtable_id=record['id'],
                    defaults={
                        'name': fields.get('Name', ''),
                        'sku': fields.get('SKU', ''),
                        'unit_price': Decimal(str(fields.get('Price', 0))),
                        'cost_price': Decimal(str(fields.get('Cost Price', 0))),
                        'category': fields.get('Category', ''),
                        'description': fields.get('Description', ''),
                        'is_active': fields.get('Active', True),
                    }
                )
            self.stdout.write(f"✓ Synced {len(records)} products from Airtable")
        except Exception as e:
            self.stdout.write(f"✗ Error syncing products: {e}")
    
    def sync_sales(self):
        try:
            records = airtable_service.get_records('Sales')
            for record in records:
                fields = record['fields']
                Sale.objects.update_or_create(
                    airtable_id=record['id'],
                    defaults={
                        'sale_number': fields.get('Sale Number', ''),
                        'customer_name': fields.get('Customer Name', ''),
                        'customer_phone': fields.get('Customer Phone', ''),
                        'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                        'payment_method': fields.get('Payment Method', 'Cash'),
                        'notes': fields.get('Notes', ''),
                    }
                )
            self.stdout.write(f"✓ Synced {len(records)} sales from Airtable")
        except Exception as e:
            self.stdout.write(f"✗ Error syncing sales: {e}")
    
    def sync_orders(self):
        try:
            records = airtable_service.get_records('Orders')
            for record in records:
                fields = record['fields']
                Order.objects.update_or_create(
                    airtable_id=record['id'],
                    defaults={
                        'order_number': fields.get('Order Number', ''),
                        'supplier': fields.get('Supplier', ''),
                        'status': fields.get('Status', 'PENDING'),
                        'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                        'notes': fields.get('Notes', ''),
                    }
                )
            self.stdout.write(f"✓ Synced {len(records)} orders from Airtable")
        except Exception as e:
            self.stdout.write(f"✗ Error syncing orders: {e}")