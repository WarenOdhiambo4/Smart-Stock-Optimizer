#!/usr/bin/env python
"""
Complete Airtable sync with correct table IDs and field mappings
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from core.airtable_service import airtable_service
from decimal import Decimal

def sync_branches():
    """Sync all branches to Airtable"""
    print("🏢 Syncing Branches...")
    
    for branch in Branch.objects.all():
        try:
            data = {
                'Name': branch.name,
                'Address': branch.address or '',
                'Phone': branch.phone or '',
                'Email': branch.email or '',
                'Active': branch.is_active,
                'Created': branch.created_at.date().isoformat() if branch.created_at else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Branches', formula=f"{{Name}} = '{branch.name}'")
            if existing:
                print(f"  ⏭️  Branch '{branch.name}' exists")
                continue
                
            result = airtable_service.create_record('Branches', data)
            print(f"  ✅ Branch '{branch.name}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing branch '{branch.name}': {e}")

def sync_products():
    """Sync all products to Airtable"""
    print("📦 Syncing Products...")
    
    for product in Product.objects.all():
        try:
            data = {
                'Name': product.name,
                'SKU': product.sku,
                'Price': float(product.unit_price),
                'Cost Price': float(product.cost_price),
                'Category': product.category or '',
                'Description': product.description or '',
                'Active': product.is_active,
                'Created': product.created_at.date().isoformat() if product.created_at else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Products', formula=f"{{SKU}} = '{product.sku}'")
            if existing:
                print(f"  ⏭️  Product '{product.sku}' exists")
                continue
                
            result = airtable_service.create_record('Products', data)
            print(f"  ✅ Product '{product.sku}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing product '{product.sku}': {e}")

def sync_stock():
    """Sync all stock records to Airtable"""
    print("📊 Syncing Stock...")
    
    for stock in Stock.objects.all():
        try:
            data = {
                'Branch': [stock.branch.name] if stock.branch else [],
                'Product': [stock.product.name] if stock.product else [],
                'Quantity': stock.quantity,
                'Min Quantity': stock.min_quantity,
                'Created': stock.created_at.date().isoformat() if stock.created_at else None,
            }
            
            result = airtable_service.create_record('Stock', data)
            print(f"  ✅ Stock for '{stock.product.name}' at '{stock.branch.name}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing stock: {e}")

def sync_sales():
    """Sync all sales to Airtable"""
    print("💰 Syncing Sales...")
    
    for sale in Sale.objects.all():
        try:
            data = {
                'Sale Number': sale.sale_number,
                'Branch': [sale.branch.name] if sale.branch else [],
                'Customer Name': sale.customer_name or '',
                'Customer Phone': sale.customer_phone or '',
                'Total Amount': float(sale.total_amount),
                'Payment Method': sale.payment_method or 'Cash',
                'Notes': sale.notes or '',
                'Created': sale.created_at.date().isoformat() if sale.created_at else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Sales', formula=f"{{Sale Number}} = '{sale.sale_number}'")
            if existing:
                print(f"  ⏭️  Sale '{sale.sale_number}' exists")
                continue
                
            result = airtable_service.create_record('Sales', data)
            print(f"  ✅ Sale '{sale.sale_number}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing sale '{sale.sale_number}': {e}")

def sync_orders():
    """Sync all orders to Airtable"""
    print("📋 Syncing Orders...")
    
    for order in Order.objects.all():
        try:
            data = {
                'Order Number': order.order_number,
                'Branch': [order.branch.name] if order.branch else [],
                'Supplier': order.supplier or '',
                'Status': order.status,
                'Total Amount': float(order.total_amount),
                'Notes': order.notes or '',
                'Created': order.created_at.date().isoformat() if order.created_at else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Orders', formula=f"{{Order Number}} = '{order.order_number}'")
            if existing:
                print(f"  ⏭️  Order '{order.order_number}' exists")
                continue
                
            result = airtable_service.create_record('Orders', data)
            print(f"  ✅ Order '{order.order_number}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing order '{order.order_number}': {e}")

def sync_vehicles():
    """Sync all vehicles to Airtable"""
    print("🚗 Syncing Vehicles...")
    
    for vehicle in Vehicle.objects.all():
        try:
            data = {
                'Registration Number': vehicle.registration_number,
                'Branch': [vehicle.branch.name] if vehicle.branch else [],
                'Type': vehicle.vehicle_type,
                'Make': vehicle.make,
                'Model': vehicle.model,
                'Year': vehicle.year,
                'Status': vehicle.status,
                'Current Mileage': vehicle.current_mileage,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Vehicles', formula=f"{{Registration Number}} = '{vehicle.registration_number}'")
            if existing:
                print(f"  ⏭️  Vehicle '{vehicle.registration_number}' exists")
                continue
                
            result = airtable_service.create_record('Vehicles', data)
            print(f"  ✅ Vehicle '{vehicle.registration_number}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing vehicle '{vehicle.registration_number}': {e}")

def sync_trips():
    """Sync all trips to Airtable"""
    print("🛣️ Syncing Trips...")
    
    for trip in Trip.objects.all():
        try:
            data = {
                'Trip Number': trip.trip_number,
                'Vehicle': [trip.vehicle.registration_number] if trip.vehicle else [],
                'Driver Name': trip.driver.full_name if trip.driver else '',
                'Origin': trip.origin,
                'Destination': trip.destination,
                'Distance': float(trip.distance),
                'Status': trip.status,
                'Revenue': float(trip.revenue),
                'Fuel Cost': float(trip.fuel_cost),
                'Customer Name': trip.customer_name or '',
                'Customer Phone': trip.customer_phone or '',
                'Scheduled Date': trip.scheduled_date.isoformat() if trip.scheduled_date else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Trips', formula=f"{{Trip Number}} = '{trip.trip_number}'")
            if existing:
                print(f"  ⏭️  Trip '{trip.trip_number}' exists")
                continue
                
            result = airtable_service.create_record('Trips', data)
            print(f"  ✅ Trip '{trip.trip_number}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing trip '{trip.trip_number}': {e}")

def sync_logistics():
    """Sync all logistics records to Airtable"""
    print("📦 Syncing Logistics...")
    
    for logistics in Logistics.objects.all():
        try:
            data = {
                'Tracking Number': logistics.tracking_number,
                'Sale': [logistics.sale.sale_number] if logistics.sale else [],
                'Branch': [logistics.from_branch.name] if logistics.from_branch else [],
                'Customer Name': logistics.customer_name,
                'Customer Phone': logistics.customer_phone,
                'Address': logistics.to_address,
                'Status': logistics.status,
                'Vehicle Number': logistics.vehicle.registration_number if logistics.vehicle else logistics.vehicle_number or '',
                'Driver Name': logistics.driver.full_name if logistics.driver else logistics.driver_name or '',
                'Delivery Cost': float(logistics.delivery_cost),
                'Delivery Date': logistics.delivery_date.isoformat() if logistics.delivery_date else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Logistics', formula=f"{{Tracking Number}} = '{logistics.tracking_number}'")
            if existing:
                print(f"  ⏭️  Logistics '{logistics.tracking_number}' exists")
                continue
                
            result = airtable_service.create_record('Logistics', data)
            print(f"  ✅ Logistics '{logistics.tracking_number}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing logistics '{logistics.tracking_number}': {e}")

def sync_expenses():
    """Sync all expenses to Airtable"""
    print("💸 Syncing Expenses...")
    
    for expense in Expense.objects.all():
        try:
            data = {
                'Expense Number': expense.expense_number,
                'Branch': [expense.branch.name] if expense.branch else [],
                'Type': expense.expense_type,
                'Description': expense.description,
                'Amount': float(expense.amount),
                'Date': expense.expense_date.isoformat() if expense.expense_date else None,
                'Receipt Number': expense.receipt_number or '',
                'Notes': expense.notes or '',
            }
            
            # Check if exists
            existing = airtable_service.get_records('Expenses', formula=f"{{Expense Number}} = '{expense.expense_number}'")
            if existing:
                print(f"  ⏭️  Expense '{expense.expense_number}' exists")
                continue
                
            result = airtable_service.create_record('Expenses', data)
            print(f"  ✅ Expense '{expense.expense_number}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing expense '{expense.expense_number}': {e}")

def sync_employees():
    """Sync all employees to Airtable"""
    print("👥 Syncing Employees...")
    
    for employee in Employee.objects.all():
        try:
            data = {
                'First Name': employee.first_name,
                'Last Name': employee.last_name,
                'Email': employee.email,
                'Phone': employee.phone or '',
                'Position': employee.position or '',
                'Active': employee.is_active,
                'Created': employee.created_at.date().isoformat() if employee.created_at else None,
            }
            
            # Check if exists
            existing = airtable_service.get_records('Employees', formula=f"{{Email}} = '{employee.email}'")
            if existing:
                print(f"  ⏭️  Employee '{employee.email}' exists")
                continue
                
            result = airtable_service.create_record('Employees', data)
            print(f"  ✅ Employee '{employee.full_name}' synced")
            
        except Exception as e:
            print(f"  ❌ Error syncing employee '{employee.full_name}': {e}")

def main():
    """Run complete sync"""
    print("🚀 Starting Complete Airtable Sync...")
    print("="*60)
    
    # Core business data
    sync_branches()
    print()
    sync_products()
    print()
    sync_employees()
    print()
    
    # Inventory
    sync_stock()
    print()
    
    # Transactions
    sync_sales()
    print()
    sync_orders()
    print()
    sync_expenses()
    print()
    
    # Logistics
    sync_vehicles()
    print()
    sync_trips()
    print()
    sync_logistics()
    print()
    
    print("🎉 Complete Airtable sync finished!")
    print("\n📊 Summary:")
    print(f"- Branches: {Branch.objects.count()}")
    print(f"- Products: {Product.objects.count()}")
    print(f"- Stock Records: {Stock.objects.count()}")
    print(f"- Sales: {Sale.objects.count()}")
    print(f"- Orders: {Order.objects.count()}")
    print(f"- Vehicles: {Vehicle.objects.count()}")
    print(f"- Trips: {Trip.objects.count()}")
    print(f"- Logistics: {Logistics.objects.count()}")
    print(f"- Expenses: {Expense.objects.count()}")
    print(f"- Employees: {Employee.objects.count()}")

if __name__ == "__main__":
    main()