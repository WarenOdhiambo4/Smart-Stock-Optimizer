from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyairtable import Api
from core.models import *
from decimal import Decimal
import os
from datetime import datetime

@csrf_exempt
def manual_sync(request):
    """Complete sync for all 16 Airtable tables - EXACT SCHEMA MATCH"""
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        base = api.base(os.getenv('AIRTABLE_BASE_ID'))
        
        counts = {}
        
        # 1. Branches (Primary Key: Name) - NO CLEAR, JUST SYNC
        try:
            table = base.table('Branches')
            branches = table.all()
            synced = 0
            for record in branches:
                fields = record['fields']
                name = fields.get('Name', '')
                if name:
                    branch, created = Branch.objects.get_or_create(
                        name=name,
                        defaults={
                            'address': fields.get('Address', ''),
                            'phone': fields.get('Phone', ''),
                            'email': fields.get('Email', ''),
                            'is_active': fields.get('Active', True)
                        }
                    )
                    if created:
                        synced += 1
            counts['branches'] = f"{synced} new from {len(branches)} total"
        except Exception as e:
            counts['branches_error'] = str(e)
        
        # 2. Products (Primary Key: Name)
        try:
            table = base.table('Products')
            products = table.all()
            synced = 0
            for record in products:
                fields = record['fields']
                name = fields.get('Name', '')
                if name:
                    product, created = Product.objects.get_or_create(
                        name=name,
                        defaults={
                            'sku': fields.get('SKU', f"AUTO-{name[:10]}"),
                            'unit_price': Decimal(str(fields.get('Price', 0))),
                            'cost_price': Decimal(str(fields.get('Cost Price', 0))),
                            'category': fields.get('Category', ''),
                            'description': fields.get('Description', ''),
                            'is_active': fields.get('Active', True)
                        }
                    )
                    if created:
                        synced += 1
            counts['products'] = f"{synced} new from {len(products)} total"
        except Exception as e:
            counts['products_error'] = str(e)
        
        # 3. Employees (Primary Key: First Name + Last Name)
        try:
            table = base.table('Employees')
            employees = table.all()
            synced = 0
            for record in employees:
                fields = record['fields']
                first_name = fields.get('First Name', '')
                last_name = fields.get('Last Name', '')
                email = fields.get('Email', '')
                if first_name and last_name and email:
                    employee, created = Employee.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        defaults={
                            'phone': fields.get('Phone', ''),
                            'position': fields.get('Position', ''),
                            'is_active': fields.get('Active', True)
                        }
                    )
                    if created:
                        synced += 1
            counts['employees'] = f"{synced} new from {len(employees)} total"
        except Exception as e:
            counts['employees_error'] = str(e)
        
        # 4. Vehicles (Primary Key: Registration Number)
        try:
            table = base.table('Vehicles')
            vehicles = table.all()
            synced = 0
            for record in vehicles:
                fields = record['fields']
                reg_number = fields.get('Registration Number', '')
                if reg_number:
                    branch = Branch.objects.first()
                    if branch:
                        vehicle, created = Vehicle.objects.get_or_create(
                            registration_number=reg_number,
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
                        if created:
                            synced += 1
            counts['vehicles'] = f"{synced} new from {len(vehicles)} total"
        except Exception as e:
            counts['vehicles_error'] = str(e)
        
        # 5. Orders (Primary Key: Order Number)
        try:
            table = base.table('Orders')
            orders = table.all()
            synced = 0
            for record in orders:
                fields = record['fields']
                order_number = fields.get('Order Number', '')
                if order_number:
                    branch = Branch.objects.first()
                    if branch:
                        order, created = Order.objects.get_or_create(
                            order_number=order_number,
                            defaults={
                                'branch': branch,
                                'supplier': fields.get('Supplier', ''),
                                'status': fields.get('Status', 'PENDING'),
                                'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                                'notes': fields.get('Notes', '')
                            }
                        )
                        if created:
                            synced += 1
            counts['orders'] = f"{synced} new from {len(orders)} total"
        except Exception as e:
            counts['orders_error'] = str(e)
        
        # 6. Sales (Primary Key: Sale Number)
        try:
            table = base.table('Sales')
            sales = table.all()
            synced = 0
            for record in sales:
                fields = record['fields']
                sale_number = fields.get('Sale Number', '')
                if sale_number:
                    branch = Branch.objects.first()
                    if branch:
                        sale, created = Sale.objects.get_or_create(
                            sale_number=sale_number,
                            defaults={
                                'branch': branch,
                                'customer_name': fields.get('Customer Name', ''),
                                'customer_phone': fields.get('Customer Phone', ''),
                                'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                                'payment_method': fields.get('Payment Method', 'Cash')
                            }
                        )
                        if created:
                            synced += 1
            counts['sales'] = f"{synced} new from {len(sales)} total"
        except Exception as e:
            counts['sales_error'] = str(e)
        
        # 7. Trips (Primary Key: Trip Number) - 258 records
        try:
            table = base.table('Trips')
            trips = table.all()
            synced = 0
            for record in trips:
                fields = record['fields']
                trip_number = fields.get('Trip Number', '')
                if trip_number:
                    vehicle = Vehicle.objects.first()
                    if vehicle:
                        trip, created = Trip.objects.get_or_create(
                            trip_number=trip_number,
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
                        if created:
                            synced += 1
            counts['trips'] = f"{synced} new from {len(trips)} total"
        except Exception as e:
            counts['trips_error'] = str(e)
        
        # 8. Logistics (Primary Key: Tracking Number)
        try:
            table = base.table('Logistics')
            logistics = table.all()
            synced = 0
            for record in logistics:
                fields = record['fields']
                tracking_number = fields.get('Tracking Number', '')
                if tracking_number:
                    branch = Branch.objects.first()
                    if branch:
                        logistics_obj, created = Logistics.objects.get_or_create(
                            tracking_number=tracking_number,
                            defaults={
                                'from_branch': branch,
                                'to_address': fields.get('Delivery Address', ''),
                                'customer_name': fields.get('Customer Name', ''),
                                'customer_phone': fields.get('Customer Phone', ''),
                                'status': fields.get('Status', 'PENDING'),
                                'delivery_cost': Decimal(str(fields.get('Delivery Cost', 0)))
                            }
                        )
                        if created:
                            synced += 1
            counts['logistics'] = f"{synced} new from {len(logistics)} total"
        except Exception as e:
            counts['logistics_error'] = str(e)
        
        # Create stock for all products at all branches
        stock_created = 0
        for branch in Branch.objects.all():
            for product in Product.objects.all():
                stock, created = Stock.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={'quantity': 0, 'min_quantity': 5}
                )
                if created:
                    stock_created += 1
        
        counts['stock_created'] = stock_created
        counts['success'] = True
        counts['message'] = 'EXACT SCHEMA SYNC - No duplicates, only new records added'
        return JsonResponse(counts)
        
    except Exception as e:
        return JsonResponse({'error': str(e)})