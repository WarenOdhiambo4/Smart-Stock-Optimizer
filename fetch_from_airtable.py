#!/usr/bin/env python
"""
Fetch data FROM Airtable and sync to Django
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from core.airtable_service import airtable_service
from decimal import Decimal
from datetime import datetime

def fetch_branches():
    """Fetch branches from Airtable"""
    print("🏢 Fetching Branches from Airtable...")
    
    try:
        records = airtable_service.get_records('Branches')
        
        for record in records:
            fields = record['fields']
            
            branch, created = Branch.objects.update_or_create(
                name=fields.get('Name', ''),
                defaults={
                    'address': fields.get('Address', ''),
                    'phone': fields.get('Phone', ''),
                    'email': fields.get('Email', ''),
                    'is_active': fields.get('Active', True),
                }
            )
            
            # Prevent circular sync
            branch._skip_sync = True
            
            if created:
                print(f"  ✅ Created branch: {branch.name}")
            else:
                print(f"  🔄 Updated branch: {branch.name}")
                
    except Exception as e:
        print(f"  ❌ Error fetching branches: {e}")

def fetch_products():
    """Fetch products from Airtable"""
    print("📦 Fetching Products from Airtable...")
    
    try:
        records = airtable_service.get_records('Products')
        
        for record in records:
            fields = record['fields']
            
            product, created = Product.objects.update_or_create(
                sku=fields.get('SKU', ''),
                defaults={
                    'name': fields.get('Name', ''),
                    'unit_price': Decimal(str(fields.get('Price', 0))),
                    'cost_price': Decimal(str(fields.get('Cost Price', 0))),
                    'category': fields.get('Category', ''),
                    'description': fields.get('Description', ''),
                    'is_active': fields.get('Active', True),
                }
            )
            
            # Prevent circular sync
            product._skip_sync = True
            
            if created:
                print(f"  ✅ Created product: {product.sku}")
            else:
                print(f"  🔄 Updated product: {product.sku}")
                
    except Exception as e:
        print(f"  ❌ Error fetching products: {e}")

def fetch_sales():
    """Fetch sales from Airtable"""
    print("💰 Fetching Sales from Airtable...")
    
    try:
        records = airtable_service.get_records('Sales')
        
        for record in records:
            fields = record['fields']
            
            # Get branch
            branch_names = fields.get('Branch', [])
            branch = None
            if branch_names:
                try:
                    branch = Branch.objects.get(name=branch_names[0])
                except Branch.DoesNotExist:
                    print(f"  ⚠️  Branch '{branch_names[0]}' not found")
                    continue
            
            sale, created = Sale.objects.update_or_create(
                sale_number=fields.get('Sale Number', ''),
                defaults={
                    'branch': branch,
                    'customer_name': fields.get('Customer Name', ''),
                    'customer_phone': fields.get('Customer Phone', ''),
                    'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                    'payment_method': fields.get('Payment Method', 'Cash'),
                    'notes': fields.get('Notes', ''),
                }
            )
            
            # Prevent circular sync
            sale._skip_sync = True
            
            if created:
                print(f"  ✅ Created sale: {sale.sale_number}")
            else:
                print(f"  🔄 Updated sale: {sale.sale_number}")
                
    except Exception as e:
        print(f"  ❌ Error fetching sales: {e}")

def fetch_orders():
    """Fetch orders from Airtable"""
    print("📋 Fetching Orders from Airtable...")
    
    try:
        records = airtable_service.get_records('Orders')
        
        for record in records:
            fields = record['fields']
            
            # Get branch
            branch_names = fields.get('Branch', [])
            branch = None
            if branch_names:
                try:
                    branch = Branch.objects.get(name=branch_names[0])
                except Branch.DoesNotExist:
                    print(f"  ⚠️  Branch '{branch_names[0]}' not found")
                    continue
            
            order, created = Order.objects.update_or_create(
                order_number=fields.get('Order Number', ''),
                defaults={
                    'branch': branch,
                    'supplier': fields.get('Supplier', ''),
                    'status': fields.get('Status', 'PENDING'),
                    'total_amount': Decimal(str(fields.get('Total Amount', 0))),
                    'notes': fields.get('Notes', ''),
                }
            )
            
            # Prevent circular sync
            order._skip_sync = True
            
            if created:
                print(f"  ✅ Created order: {order.order_number}")
            else:
                print(f"  🔄 Updated order: {order.order_number}")
                
    except Exception as e:
        print(f"  ❌ Error fetching orders: {e}")

def fetch_vehicles():
    """Fetch vehicles from Airtable"""
    print("🚗 Fetching Vehicles from Airtable...")
    
    try:
        records = airtable_service.get_records('Vehicles')
        
        for record in records:
            fields = record['fields']
            
            # Get branch
            branch_names = fields.get('Branch', [])
            branch = None
            if branch_names:
                try:
                    branch = Branch.objects.get(name=branch_names[0])
                except Branch.DoesNotExist:
                    print(f"  ⚠️  Branch '{branch_names[0]}' not found")
                    continue
            
            vehicle, created = Vehicle.objects.update_or_create(
                registration_number=fields.get('Registration Number', ''),
                defaults={
                    'branch': branch,
                    'vehicle_type': fields.get('Type', 'OTHER'),
                    'make': fields.get('Make', ''),
                    'model': fields.get('Model', ''),
                    'year': fields.get('Year', 2020),
                    'status': fields.get('Status', 'ACTIVE'),
                    'current_mileage': fields.get('Current Mileage', 0),
                }
            )
            
            # Prevent circular sync
            vehicle._skip_sync = True
            
            if created:
                print(f"  ✅ Created vehicle: {vehicle.registration_number}")
            else:
                print(f"  🔄 Updated vehicle: {vehicle.registration_number}")
                
    except Exception as e:
        print(f"  ❌ Error fetching vehicles: {e}")

def fetch_trips():
    """Fetch trips from Airtable"""
    print("🛣️ Fetching Trips from Airtable...")
    
    try:
        records = airtable_service.get_records('Trips')
        
        for record in records:
            fields = record['fields']
            
            # Get vehicle
            vehicle_names = fields.get('Vehicle', [])
            vehicle = None
            if vehicle_names:
                try:
                    vehicle = Vehicle.objects.get(registration_number=vehicle_names[0])
                except Vehicle.DoesNotExist:
                    print(f"  ⚠️  Vehicle '{vehicle_names[0]}' not found")
                    continue
            
            # Parse scheduled date
            scheduled_date = None
            if fields.get('Scheduled Date'):
                try:
                    scheduled_date = datetime.fromisoformat(fields['Scheduled Date'].replace('Z', '+00:00'))
                except:
                    scheduled_date = datetime.now()
            
            trip, created = Trip.objects.update_or_create(
                trip_number=fields.get('Trip Number', ''),
                defaults={
                    'vehicle': vehicle,
                    'origin': fields.get('Origin', ''),
                    'destination': fields.get('Destination', ''),
                    'distance': Decimal(str(fields.get('Distance', 0))),
                    'status': fields.get('Status', 'SCHEDULED'),
                    'revenue': Decimal(str(fields.get('Revenue', 0))),
                    'fuel_cost': Decimal(str(fields.get('Fuel Cost', 0))),
                    'customer_name': fields.get('Customer Name', ''),
                    'customer_phone': fields.get('Customer Phone', ''),
                    'scheduled_date': scheduled_date or datetime.now(),
                }
            )
            
            # Prevent circular sync
            trip._skip_sync = True
            
            if created:
                print(f"  ✅ Created trip: {trip.trip_number}")
            else:
                print(f"  🔄 Updated trip: {trip.trip_number}")
                
    except Exception as e:
        print(f"  ❌ Error fetching trips: {e}")

def fetch_expenses():
    """Fetch expenses from Airtable"""
    print("💸 Fetching Expenses from Airtable...")
    
    try:
        records = airtable_service.get_records('Expenses')
        
        for record in records:
            fields = record['fields']
            
            # Get branch
            branch_names = fields.get('Branch', [])
            branch = None
            if branch_names:
                try:
                    branch = Branch.objects.get(name=branch_names[0])
                except Branch.DoesNotExist:
                    print(f"  ⚠️  Branch '{branch_names[0]}' not found")
                    continue
            
            # Parse date
            expense_date = None
            if fields.get('Date'):
                try:
                    expense_date = datetime.fromisoformat(fields['Date']).date()
                except:
                    expense_date = datetime.now().date()
            
            expense, created = Expense.objects.update_or_create(
                expense_number=fields.get('Expense Number', ''),
                defaults={
                    'branch': branch,
                    'expense_type': fields.get('Type', 'OTHER'),
                    'description': fields.get('Description', ''),
                    'amount': Decimal(str(fields.get('Amount', 0))),
                    'expense_date': expense_date or datetime.now().date(),
                    'receipt_number': fields.get('Receipt Number', ''),
                    'notes': fields.get('Notes', ''),
                }
            )
            
            # Prevent circular sync
            expense._skip_sync = True
            
            if created:
                print(f"  ✅ Created expense: {expense.expense_number}")
            else:
                print(f"  🔄 Updated expense: {expense.expense_number}")
                
    except Exception as e:
        print(f"  ❌ Error fetching expenses: {e}")

def fetch_employees():
    """Fetch employees from Airtable"""
    print("👥 Fetching Employees from Airtable...")
    
    try:
        records = airtable_service.get_records('Employees')
        
        for record in records:
            fields = record['fields']
            
            employee, created = Employee.objects.update_or_create(
                email=fields.get('Email', ''),
                defaults={
                    'first_name': fields.get('First Name', ''),
                    'last_name': fields.get('Last Name', ''),
                    'phone': fields.get('Phone', ''),
                    'position': fields.get('Position', ''),
                    'is_active': fields.get('Active', True),
                }
            )
            
            # Prevent circular sync
            employee._skip_sync = True
            
            if created:
                print(f"  ✅ Created employee: {employee.full_name}")
            else:
                print(f"  🔄 Updated employee: {employee.full_name}")
                
    except Exception as e:
        print(f"  ❌ Error fetching employees: {e}")

def main():
    """Run complete fetch from Airtable"""
    print("📥 Starting Complete Fetch from Airtable...")
    print("="*60)
    
    # Core business data first
    fetch_branches()
    print()
    fetch_products()
    print()
    fetch_employees()
    print()
    
    # Transactions
    fetch_sales()
    print()
    fetch_orders()
    print()
    fetch_expenses()
    print()
    
    # Logistics
    fetch_vehicles()
    print()
    fetch_trips()
    print()
    
    print("🎉 Complete fetch from Airtable finished!")
    print("\n📊 Current Django Records:")
    print(f"- Branches: {Branch.objects.count()}")
    print(f"- Products: {Product.objects.count()}")
    print(f"- Sales: {Sale.objects.count()}")
    print(f"- Orders: {Order.objects.count()}")
    print(f"- Vehicles: {Vehicle.objects.count()}")
    print(f"- Trips: {Trip.objects.count()}")
    print(f"- Expenses: {Expense.objects.count()}")
    print(f"- Employees: {Employee.objects.count()}")

if __name__ == "__main__":
    main()