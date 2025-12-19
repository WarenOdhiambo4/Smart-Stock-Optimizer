from django.core.management.base import BaseCommand
from pyairtable import Api
from core.models import Branch, Product, Sale, Order
from decimal import Decimal
import os

class Command(BaseCommand):
    help = 'Sync data from Airtable to Django'

    def handle(self, *args, **options):
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        base = api.base(os.getenv('AIRTABLE_BASE_ID'))
        
        # Sync branches
        try:
            table = base.table('Branches')
            branches = table.all()
            for record in branches:
                fields = record['fields']
                Branch.objects.update_or_create(
                    name=fields.get('Name', ''),
                    defaults={
                        'location': fields.get('Address', ''),
                        'manager': 'System',
                        'phone': fields.get('Phone', ''),
                        'email': fields.get('Email', ''),
                    }
                )
            self.stdout.write(f'Synced {len(branches)} branches')
        except Exception as e:
            self.stdout.write(f'Branch sync error: {e}')
        
        # Create sample products if none exist
        if not Product.objects.exists():
            products_data = [
                {'name': 'Sample Product 1', 'category': 'Electronics', 'price': 100, 'cost': 50, 'stock_quantity': 10},
                {'name': 'Sample Product 2', 'category': 'Clothing', 'price': 50, 'cost': 25, 'stock_quantity': 20},
            ]
            for data in products_data:
                Product.objects.create(**data)
            self.stdout.write('Created sample products')
        
        self.stdout.write(self.style.SUCCESS('Sync completed'))