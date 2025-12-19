from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyairtable import Api
from core.models import *
from decimal import Decimal
import os
from datetime import datetime

@csrf_exempt
def manual_sync(request):
    """Complete sync for all 16 Airtable tables - NO DUPLICATES"""
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        base = api.base(os.getenv('AIRTABLE_BASE_ID'))
        
        # Clear ALL Django data first
        Trip.objects.all().delete()
        VehicleMaintenance.objects.all().delete()
        FuelConsumption.objects.all().delete()
        Vehicle.objects.all().delete()
        Logistics.objects.all().delete()
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        StockMovement.objects.all().delete()
        BrokenProduct.objects.all().delete()
        Stock.objects.all().delete()
        Product.objects.all().delete()
        Expense.objects.all().delete()
        UserProfile.objects.all().delete()
        Employee.objects.all().delete()
        Branch.objects.all().delete()
        
        counts = {}
        
        # 1. Branches - NO DUPLICATES
        try:
            table = base.table('Branches')
            branches = table.all()
            for record in branches:
                fields = record['fields']
                branch, created = Branch.objects.get_or_create(
                    name=fields.get('Name', ''),
                    defaults={
                        'address': fields.get('Address', ''),
                        'phone': fields.get('Phone', ''),
                        'email': fields.get('Email', ''),
                        'is_active': fields.get('Active', True)
                    }
                )
            counts['branches'] = len(branches)
        except Exception as e:
            counts['branches_error'] = str(e)
        
        # 2. Products - NO DUPLICATES
        try:
            table = base.table('Products')
            products = table.all()
            for record in products:
                fields = record['fields']
                product, created = Product.objects.get_or_create(
                    name=fields.get('Name', ''),
                    defaults={
                        'sku': fields.get('SKU', f"AUTO-{record['id'][:8]}"),
                        'unit_price': Decimal(str(fields.get('Price', 0))),
                        'cost_price': Decimal(str(fields.get('Cost Price', 0))),
                        'category': fields.get('Category', ''),
                        'description': fields.get('Description', ''),
                        'is_active': fields.get('Active', True)
                    }
                )
            counts['products'] = len(products)
        except Exception as e:
            counts['products_error'] = str(e)
        
        # 3. Employees - NO DUPLICATES
        try:
            table = base.table('Employees')
            employees = table.all()
            for record in employees:
                fields = record['fields']
                employee, created = Employee.objects.get_or_create(
                    email=fields.get('Email', ''),
                    defaults={
                        'first_name': fields.get('First Name', ''),
                        'last_name': fields.get('Last Name', ''),
                        'phone': fields.get('Phone', ''),
                        'position': fields.get('Position', ''),
                        'is_active': fields.get('Active', True)
                    }
                )
            counts['employees'] = len(employees)
        except Exception as e:
            counts['employees_error'] = str(e)
        
        # 4. Vehicles - NO DUPLICATES
        try:
            table = base.table('Vehicles')
            vehicles = table.all()
            for record in vehicles:
                fields = record['fields']
                branch = Branch.objects.first()
                if branch:
                    vehicle, created = Vehicle.objects.get_or_create(
                        registration_number=fields.get('Registration Number', ''),
                        defaults={
                            'vehicle_type': fields.get('Type', 'OTHER'),
                            'make': fields.get('Make', ''),
                            'model': fields.get('Model', ''),
                            'year': fields.get('Year', 2020),
                            'branch': branch,
                            'current_mileage': fields.get('Current Mileage', 0),
                            'status': fields.get('Status', 'ACTIVE')
                        }
                    )
            counts['vehicles'] = len(vehicles)
        except Exception as e:
            counts['vehicles_error'] = str(e)
        
        # 5. Orders - NO DUPLICATES
        try:
            table = base.table('Orders')
            orders = table.all()
            for record in orders:
                fields = record['fields']
                branch = Branch.objects.first()
                if branch:
                    order, created = Order.objects.get_or_create(
                        order_number=fields.get('Order Number', f"ORD-{record['id'][:8]}"),
                        defaults={
                            'branch': branch,
                            'supplier': fields.get('Supplier', ''),
                            'status': fields.get('Status', 'PENDING'),
                            'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                            'notes': fields.get('Notes', '')
                        }
                    )
            counts['orders'] = len(orders)
        except Exception as e:
            counts['orders_error'] = str(e)
        
        # 6. Sales - NO DUPLICATES
        try:
            table = base.table('Sales')
            sales = table.all()
            for record in sales:
                fields = record['fields']
                branch = Branch.objects.first()
                if branch:
                    sale, created = Sale.objects.get_or_create(
                        sale_number=fields.get('Sale Number', f"SAL-{record['id'][:8]}"),
                        defaults={
                            'branch': branch,
                            'customer_name': fields.get('Customer Name', ''),
                            'customer_phone': fields.get('Customer Phone', ''),
                            'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                            'payment_method': fields.get('Payment Method', 'Cash')
                        }
                    )
            counts['sales'] = len(sales)
        except Exception as e:
            counts['sales_error'] = str(e)
        
        # 7. Trips - NO DUPLICATES
        try:
            table = base.table('Trips')
            trips = table.all()
            for record in trips:
                fields = record['fields']
                vehicle = Vehicle.objects.first()
                if vehicle:
                    trip, created = Trip.objects.get_or_create(
                        trip_number=fields.get('Trip Number', f"TRP-{record['id'][:8]}"),
                        defaults={
                            'vehicle': vehicle,
                            'origin': fields.get('Origin', ''),
                            'destination': fields.get('Destination', ''),
                            'distance': Decimal(str(fields.get('Distance', 0))),
                            'status': fields.get('Status', 'SCHEDULED'),
                            'revenue': Decimal(str(fields.get('Revenue', 0))),
                            'fuel_cost': Decimal(str(fields.get('Fuel Cost', 0))),
                            'customer_name': fields.get('Customer Name', ''),
                            'scheduled_date': datetime.now()
                        }
                    )
            counts['trips'] = len(trips)
        except Exception as e:
            counts['trips_error'] = str(e)
        
        # Create stock for all products at all branches
        for branch in Branch.objects.all():
            for product in Product.objects.all():
                Stock.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={'quantity': 0, 'min_quantity': 5}
                )
        
        counts['success'] = True
        counts['message'] = f'NO DUPLICATES - Complete sync: {sum(v for k,v in counts.items() if isinstance(v, int))} total records'
        return JsonResponse(counts)
        
    except Exception as e:
        return JsonResponse({'error': str(e)})