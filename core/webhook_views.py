import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .webhook_manager import AirtableWebhookManager
from .airtable_service import AirtableService
from .models import Branch, Product, Sale, Order

@csrf_exempt
@require_http_methods(["POST"])
def webhook_receiver(request):
    """Receive webhook notifications from Airtable"""
    try:
        data = json.loads(request.body)
        webhook_id = data.get('webhook', {}).get('id')
        
        if webhook_id:
            # Process the webhook payload
            manager = AirtableWebhookManager()
            payload_data = manager.get_payload(webhook_id)
            
            # Sync changes to Django
            sync_airtable_changes(payload_data)
            
        return HttpResponse(status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

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
        Branch.objects.update_or_create(
            name=fields.get('Name', ''),
            defaults={
                'location': fields.get('Location', ''),
                'manager': fields.get('Manager', ''),
                'phone': fields.get('Phone', ''),
                'email': fields.get('Email', ''),
            }
        )

def sync_products(records):
    """Sync product records from Airtable"""
    for record in records:
        fields = record['fields']
        Product.objects.update_or_create(
            name=fields.get('Name', ''),
            defaults={
                'category': fields.get('Category', ''),
                'price': fields.get('Price', 0),
                'cost': fields.get('Cost', 0),
                'stock_quantity': fields.get('Stock', 0),
                'description': fields.get('Description', ''),
            }
        )

def sync_sales(records):
    """Sync sale records from Airtable"""
    for record in records:
        fields = record['fields']
        try:
            product = Product.objects.get(name=fields.get('Product', ''))
            branch = Branch.objects.get(name=fields.get('Branch', ''))
            
            Sale.objects.update_or_create(
                product=product,
                branch=branch,
                quantity=fields.get('Quantity', 0),
                defaults={
                    'unit_price': fields.get('Unit Price', 0),
                    'total_amount': fields.get('Total', 0),
                }
            )
        except (Product.DoesNotExist, Branch.DoesNotExist):
            continue

def sync_orders(records):
    """Sync order records from Airtable"""
    for record in records:
        fields = record['fields']
        try:
            branch = Branch.objects.get(name=fields.get('Branch', ''))
            
            Order.objects.update_or_create(
                order_number=fields.get('Order Number', ''),
                defaults={
                    'branch': branch,
                    'customer_name': fields.get('Customer', ''),
                    'total_amount': fields.get('Total', 0),
                    'status': fields.get('Status', 'pending'),
                }
            )
        except Branch.DoesNotExist:
            continue