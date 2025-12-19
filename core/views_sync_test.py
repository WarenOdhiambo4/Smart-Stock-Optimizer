from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyairtable import Api
from core.models import Branch, Product, Sale, Stock
from decimal import Decimal
import os

@csrf_exempt
def manual_sync(request):
    """Manual sync button for testing"""
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        base = api.base(os.getenv('AIRTABLE_BASE_ID'))
        
        # Clear Django data
        Sale.objects.all().delete()
        Stock.objects.all().delete()
        Product.objects.all().delete()
        Branch.objects.all().delete()
        
        # Sync from Airtable
        branches_count = 0
        products_count = 0
        
        # Branches
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
                )
            branches_count = len(branches)
        except Exception as e:
            return JsonResponse({'error': f'Branch sync failed: {e}'})
        
        # Products
        try:
            table = base.table('Products')
            products = table.all()
            for record in products:
                fields = record['fields']
                Product.objects.create(
                    name=fields.get('Name', ''),
                    sku=fields.get('SKU', f"AUTO-{record['id'][:8]}"),
                    unit_price=Decimal(str(fields.get('Price', 0))),
                    cost_price=Decimal(str(fields.get('Cost', 0))),
                )
            products_count = len(products)
        except Exception as e:
            return JsonResponse({'error': f'Product sync failed: {e}'})
        
        return JsonResponse({
            'success': True,
            'branches': branches_count,
            'products': products_count,
            'message': 'Sync completed successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)})