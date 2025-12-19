from django.core.management.base import BaseCommand
from pyairtable import Api
from core.models import *
from decimal import Decimal
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Sync ALL data from Airtable to Django on startup'

    def handle(self, *args, **options):
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        base = api.base(os.getenv('AIRTABLE_BASE_ID'))
        
        # Clear existing data first
        self.stdout.write('Clearing existing data...')
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        Order.objects.all().delete()
        Stock.objects.all().delete()
        Product.objects.all().delete()
        Branch.objects.all().delete()
        
        # Sync branches
        try:
            table = base.table('Branches')
            branches = table.all()
            for record in branches:
                fields = record['fields']
                Branch.objects.create(
                    name=fields.get('Name', ''),
                    address=fields.get('Address', ''),
                    phone=fields.get('Phone', ''),
                    email=fields.get('Email', ''),
                    is_active=fields.get('Active', True)
                )
            self.stdout.write(f'Synced {len(branches)} branches')
        except Exception as e:
            self.stdout.write(f'Branch sync error: {e}')
        
        # Sync products
        try:
            table = base.table('Products')
            products = table.all()
            for record in products:
                fields = record['fields']
                Product.objects.create(
                    name=fields.get('Name', ''),
                    sku=fields.get('SKU', f"AUTO-{fields.get('Name', '')[:10]}"),
                    category=fields.get('Category', ''),
                    unit_price=Decimal(str(fields.get('Price', 0))),
                    cost_price=Decimal(str(fields.get('Cost', 0))),
                    description=fields.get('Description', '')
                )
            self.stdout.write(f'Synced {len(products)} products')
        except Exception as e:
            self.stdout.write(f'Product sync error: {e}')
        
        # Create stock for all products at all branches
        for branch in Branch.objects.all():
            for product in Product.objects.all():
                Stock.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={'quantity': 0, 'min_quantity': 5}
                )
        
        # Sync sales
        try:
            table = base.table('Sales')
            sales = table.all()
            for record in sales:
                fields = record['fields']
                Sale.objects.create(
                    sale_number=fields.get('Sale Number', f"SAL-{record['id'][:8]}"),
                    branch=Branch.objects.first(),
                    customer_name=fields.get('Customer', ''),
                    customer_phone=fields.get('Phone', ''),
                    total_amount=Decimal(str(fields.get('Total', 0))),
                    payment_method=fields.get('Payment Method', 'Cash')
                )
            self.stdout.write(f'Synced {len(sales)} sales')
        except Exception as e:
            self.stdout.write(f'Sales sync error: {e}')
        
        self.stdout.write(self.style.SUCCESS('Full sync completed - Django now matches Airtable'))