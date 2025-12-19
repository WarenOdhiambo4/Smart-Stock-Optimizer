import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator
from django.views import View
from .webhook_manager import AirtableWebhookManager
from .airtable_service import AirtableService
from .models import Branch, Product, Sale, Order

@csrf_exempt
def webhook_receiver(request):
    """Receive webhook notifications from Airtable"""
    if request.method != 'POST':
        return HttpResponse(status=405)
        
    try:
        data = json.loads(request.body)
        webhook_id = data.get('webhook', {}).get('id')
        
        if webhook_id:
            manager = AirtableWebhookManager()
            payload_data = manager.get_payload(webhook_id)
            sync_airtable_changes(payload_data)
            
        return HttpResponse('OK', status=200)
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=400)

def sync_airtable_changes(payload_data):
    """Sync Airtable changes to Django models"""
    service = AirtableService()
    
    if 'payloads' not in payload_data:
        return
    
    for payload in payload_data['payloads']:
        if 'changedTablesById' not in payload:
            continue
            
        for table_id, changes in payload['changedTablesById'].items():
            # Map table IDs to Django models
            table_mapping = {
                'tblBranches': sync_branches,
                'tblProducts': sync_products,
                'tblSales': sync_sales,
                'tblOrders': sync_orders,
            }
            
            # Find matching sync function
            for table_name, sync_func in table_mapping.items():
                try:
                    # Get table by name since we don't have ID mapping
                    records = service.get_all_records(table_name)
                    sync_func(records)
                except:
                    continue

def sync_branches(records):
    """Sync branch records from Airtable"""
    for record in records:
        fields = record['fields']
        branch, created = Branch.objects.update_or_create(
            name=fields.get('Name', ''),
            defaults={
                'address': fields.get('Address', ''),
                'phone': fields.get('Phone', ''),
                'email': fields.get('Email', ''),
            }
        )
        # Prevent circular sync
        if created:
            branch._skip_sync = True

def sync_products(records):
    """Sync product records from Airtable"""
    for record in records:
        fields = record['fields']
        product, created = Product.objects.update_or_create(
            sku=fields.get('SKU', ''),
            defaults={
                'name': fields.get('Name', ''),
                'category': fields.get('Category', ''),
                'unit_price': fields.get('Price', 0),
                'cost_price': fields.get('Cost Price', 0),
                'description': fields.get('Description', ''),
            }
        )
        # Prevent circular sync
        if created:
            product._skip_sync = True

def sync_sales(records):
    """Sync sale records from Airtable"""
    for record in records:
        fields = record['fields']
        try:
            branch = Branch.objects.get(name=fields.get('Branch', ''))
            
            sale, created = Sale.objects.update_or_create(
                sale_number=fields.get('Sale Number', ''),
                defaults={
                    'branch': branch,
                    'customer_name': fields.get('Customer Name', ''),
                    'customer_phone': fields.get('Customer Phone', ''),
                    'total_amount': fields.get('Total Amount', 0),
                    'payment_method': fields.get('Payment Method', 'Cash'),
                }
            )
            # Prevent circular sync
            if created:
                sale._skip_sync = True
        except Branch.DoesNotExist:
            continue

def sync_orders(records):
    """Sync order records from Airtable"""
    for record in records:
        fields = record['fields']
        try:
            branch = Branch.objects.get(name=fields.get('Branch', ''))
            
            order, created = Order.objects.update_or_create(
                order_number=fields.get('Order Number', ''),
                defaults={
                    'branch': branch,
                    'supplier': fields.get('Supplier', ''),
                    'total_amount': fields.get('Total Amount', 0),
                    'status': fields.get('Status', 'PENDING'),
                }
            )
            # Prevent circular sync
            if created:
                order._skip_sync = True
        except Branch.DoesNotExist:
            continue