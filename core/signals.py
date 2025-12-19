"""
Complete Django signals for all 16 Airtable tables
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import *
from .airtable_service import airtable_service

# 1. Branches ✅ (Working)
@receiver(post_save, sender=Branch)
def sync_branch_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Branches', formula=f"{{Name}} = '{instance.name}'")
            if existing_records:
                return
            data = {
                'Name': instance.name,
                'Address': instance.address or '',
                'Phone': instance.phone or '',
                'Email': instance.email or '',
                'Active': instance.is_active,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Branches', data)
            print(f"✓ Branch {instance.name} synced")
        except Exception as e:
            print(f"✗ Branch sync error: {e}")

# 2. Products ✅ (Working)
@receiver(post_save, sender=Product)
def sync_product_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Products', formula=f"{{SKU}} = '{instance.sku}'")
            if existing_records:
                return
            data = {
                'Name': instance.name,
                'SKU': instance.sku,
                'Price': float(instance.unit_price),
                'Cost Price': float(instance.cost_price),
                'Category': instance.category or '',
                'Description': instance.description or '',
                'Active': instance.is_active,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Products', data)
            print(f"✓ Product {instance.sku} synced")
        except Exception as e:
            print(f"✗ Product sync error: {e}")

# 3. Stock
@receiver(post_save, sender=Stock)
def sync_stock_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            data = {
                'Quantity': instance.quantity,
                'Min Quantity': instance.min_quantity,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Stock', data)
            print(f"✓ Stock synced")
        except Exception as e:
            print(f"✗ Stock sync error: {e}")

# 4. Sales
@receiver(post_save, sender=Sale)
def sync_sale_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Sales', formula=f"{{Sale Number}} = '{instance.sale_number}'")
            if existing_records:
                return
            data = {
                'Sale Number': instance.sale_number,
                'Customer Name': instance.customer_name or '',
                'Customer Phone': instance.customer_phone or '',
                'Total Amount': float(instance.total_amount),
                'Payment Method': instance.payment_method or 'Cash',
                'Notes': instance.notes or '',
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Sales', data)
            print(f"✓ Sale {instance.sale_number} synced")
        except Exception as e:
            print(f"✗ Sale sync error: {e}")

# 5. Orders
@receiver(post_save, sender=Order)
def sync_order_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Orders', formula=f"{{Order Number}} = '{instance.order_number}'")
            if existing_records:
                return
            data = {
                'Order Number': instance.order_number,
                'Supplier': instance.supplier or '',
                'Status': instance.status,
                'Total Amount': float(instance.total_amount),
                'Notes': instance.notes or '',
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Orders', data)
            print(f"✓ Order {instance.order_number} synced")
        except Exception as e:
            print(f"✗ Order sync error: {e}")

# 6. Vehicles
@receiver(post_save, sender=Vehicle)
def sync_vehicle_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Vehicles', formula=f"{{Registration Number}} = '{instance.registration_number}'")
            if existing_records:
                return
            data = {
                'Registration Number': instance.registration_number,
                'Type': instance.vehicle_type,
                'Make': instance.make,
                'Model': instance.model,
                'Year': instance.year,
                'Current Mileage': instance.current_mileage,
                'Status': instance.status,
            }
            airtable_service.create_record('Vehicles', data)
            print(f"✓ Vehicle {instance.registration_number} synced")
        except Exception as e:
            print(f"✗ Vehicle sync error: {e}")

# 7. Trips
@receiver(post_save, sender=Trip)
def sync_trip_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Trips', formula=f"{{Trip Number}} = '{instance.trip_number}'")
            if existing_records:
                return
            data = {
                'Trip Number': instance.trip_number,
                'Driver Name': instance.driver.full_name if instance.driver else '',
                'Origin': instance.origin,
                'Destination': instance.destination,
                'Distance': float(instance.distance),
                'Status': instance.status,
                'Revenue': float(instance.revenue),
                'Fuel Cost': float(instance.fuel_cost),
                'Customer Name': instance.customer_name or '',
                'Customer Phone': instance.customer_phone or '',
                'Scheduled Date': instance.scheduled_date.date().isoformat() if instance.scheduled_date else None,
            }
            airtable_service.create_record('Trips', data)
            print(f"✓ Trip {instance.trip_number} synced")
        except Exception as e:
            print(f"✗ Trip sync error: {e}")

# 8. Logistics
@receiver(post_save, sender=Logistics)
def sync_logistics_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Logistics', formula=f"{{Tracking Number}} = '{instance.tracking_number}'")
            if existing_records:
                return
            data = {
                'Tracking Number': instance.tracking_number,
                'Customer Name': instance.customer_name,
                'Customer Phone': instance.customer_phone,
                'To Address': instance.to_address,
                'Status': instance.status,
                'Vehicle Number': instance.vehicle.registration_number if instance.vehicle else instance.vehicle_number or '',
                'Driver Name': instance.driver.full_name if instance.driver else instance.driver_name or '',
                'Delivery Cost': float(instance.delivery_cost),
                'Delivery Date': instance.delivery_date.isoformat() if instance.delivery_date else None,
            }
            airtable_service.create_record('Logistics', data)
            print(f"✓ Logistics {instance.tracking_number} synced")
        except Exception as e:
            print(f"✗ Logistics sync error: {e}")

# 9. Expenses
@receiver(post_save, sender=Expense)
def sync_expense_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Expenses', formula=f"{{Expense Number}} = '{instance.expense_number}'")
            if existing_records:
                return
            data = {
                'Expense Number': instance.expense_number,
                'Type': instance.expense_type,
                'Description': instance.description,
                'Amount': float(instance.amount),
                'Date': instance.expense_date.isoformat() if instance.expense_date else None,
                'Receipt Number': instance.receipt_number or '',
                'Notes': instance.notes or '',
            }
            airtable_service.create_record('Expenses', data)
            print(f"✓ Expense {instance.expense_number} synced")
        except Exception as e:
            print(f"✗ Expense sync error: {e}")

# 10. Stock Movements
@receiver(post_save, sender=StockMovement)
def sync_stock_movement_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            data = {
                'Type': instance.movement_type,
                'Quantity': instance.quantity,
                'Status': instance.status,
                'Notes': instance.notes or '',
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Stock Movements', data)
            print(f"✓ Stock Movement synced")
        except Exception as e:
            print(f"✗ Stock Movement sync error: {e}")

# 11. Broken Products
@receiver(post_save, sender=BrokenProduct)
def sync_broken_product_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            data = {
                'Quantity': instance.quantity,
                'Damage Type': instance.damage_type,
                'Unit Cost': float(instance.unit_cost),
                'Total Loss': float(instance.total_loss),
                'Description': instance.description or '',
                'Reported Date': instance.reported_date.date().isoformat() if instance.reported_date else None,
            }
            airtable_service.create_record('Broken Products', data)
            print(f"✓ Broken Product synced")
        except Exception as e:
            print(f"✗ Broken Product sync error: {e}")

# 12. Vehicle Maintenance
@receiver(post_save, sender=VehicleMaintenance)
def sync_vehicle_maintenance_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Vehicle Maintenance', formula=f"{{Maintenance Number}} = '{instance.maintenance_number}'")
            if existing_records:
                return
            data = {
                'Maintenance Number': instance.maintenance_number,
                'Type': instance.maintenance_type,
                'Service Provider': instance.service_provider,
                'Description': instance.description,
                'Parts Cost': float(instance.parts_cost),
                'Labor Cost': float(instance.labor_cost),
                'Total Cost': float(instance.total_cost),
                'Service Date': instance.service_date.isoformat() if instance.service_date else None,
                'Status': instance.status,
            }
            airtable_service.create_record('Vehicle Maintenance', data)
            print(f"✓ Vehicle Maintenance {instance.maintenance_number} synced")
        except Exception as e:
            print(f"✗ Vehicle Maintenance sync error: {e}")

# 13. Fuel Consumption
@receiver(post_save, sender=FuelConsumption)
def sync_fuel_consumption_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            data = {
                'Liters': float(instance.liters),
                'Cost Per Liter': float(instance.cost_per_liter),
                'Total Cost': float(instance.total_cost),
                'Mileage': instance.mileage_at_fill,
                'Fuel Station': instance.fuel_station or '',
                'Date': instance.date.isoformat() if instance.date else None,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Fuel Consumption', data)
            print(f"✓ Fuel Consumption synced")
        except Exception as e:
            print(f"✗ Fuel Consumption sync error: {e}")

# 14. Employees ✅ (Working)
@receiver(post_save, sender=Employee)
def sync_employee_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Employees', formula=f"{{Email}} = '{instance.email}'")
            if existing_records:
                return
            data = {
                'First Name': instance.first_name,
                'Last Name': instance.last_name,
                'Email': instance.email,
                'Phone': instance.phone or '',
                'Position': instance.position or '',
                'Active': instance.is_active,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Employees', data)
            print(f"✓ Employee {instance.full_name} synced")
        except Exception as e:
            print(f"✗ Employee sync error: {e}")

# 15. User Profiles
@receiver(post_save, sender=UserProfile)
def sync_userprofile_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('User Profiles', formula=f"{{Username}} = '{instance.user.username}'")
            if existing_records:
                return
            data = {
                'Username': instance.user.username,
                'Role': instance.role,
                'Phone': instance.phone or '',
                'Active': instance.user.is_active,
            }
            airtable_service.create_record('User Profiles', data)
            print(f"✓ UserProfile {instance.user.username} synced")
        except Exception as e:
            print(f"✗ UserProfile sync error: {e}")

# 16. Users (Django User model)
@receiver(post_save, sender=User)
def sync_user_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            existing_records = airtable_service.get_records('Users', formula=f"{{Email}} = '{instance.email}'")
            if existing_records:
                return
            data = {
                'Email': instance.email,
                'First Name': instance.first_name,
                'Last Name': instance.last_name,
                'Username': instance.username,
                'Active': instance.is_active,
                'Django User ID': instance.id,
            }
            airtable_service.create_record('Users', data)
            print(f"✓ User {instance.username} synced")
        except Exception as e:
            print(f"✗ User sync error: {e}")

# All 16 Airtable tables now have sync signals