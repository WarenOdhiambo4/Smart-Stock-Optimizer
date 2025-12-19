from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyairtable import Api
from core.models import *
from decimal import Decimal
import os

@csrf_exempt
def manual_sync(request):
    """Manual sync button for testing"""
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        base = api.base(os.getenv('AIRTABLE_BASE_ID'))
        
        # Clear ALL Django data
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Stock.objects.all().delete()
        Product.objects.all().delete()
        Employee.objects.all().delete()
        Branch.objects.all().delete()
        
        counts = {}
        
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
            counts['branches'] = len(branches)
        except Exception as e:
            counts['branches_error'] = str(e)
        
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
            counts['products'] = len(products)
        except Exception as e:
            counts['products_error'] = str(e)
        
        # Sales
        try:
            table = base.table('Sales')
            sales = table.all()
            for record in sales:
                fields = record['fields']
                branch = Branch.objects.first()
                if branch:
                    Sale.objects.create(
                        sale_number=fields.get('Sale Number', f"SAL-{record['id'][:8]}"),
                        branch=branch,
                        customer_name=fields.get('Customer', ''),
                        total_amount=Decimal(str(fields.get('Total', 0))),
                    )
            counts['sales'] = len(sales)
        except Exception as e:
            counts['sales_error'] = str(e)
        
        # Orders
        try:
            table = base.table('Orders')
            orders = table.all()
            for record in orders:
                fields = record['fields']
                branch = Branch.objects.first()
                if branch:
                    Order.objects.create(
                        order_number=fields.get('Order Number', f"ORD-{record['id'][:8]}"),
                        branch=branch,
                        supplier=fields.get('Supplier', ''),
                        status=fields.get('Status', 'PENDING'),
                    )
            counts['orders'] = len(orders)
        except Exception as e:
            counts['orders_error'] = str(e)
        
        # Create stock for all products at all branches
        for branch in Branch.objects.all():
            for product in Product.objects.all():
                Stock.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={'quantity': 0, 'min_quantity': 5}
                )
        
        counts['success'] = True
        counts['message'] = 'Full sync completed'
        return JsonResponse(counts)
        
    except Exception as e:
        return JsonResponse({'error': str(e)})