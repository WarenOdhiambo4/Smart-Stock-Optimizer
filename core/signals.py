"""
Django signals for auto-sync to Airtable
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Branch, Employee, Product, Order, Sale, Expense, Vehicle, Trip, UserProfile
from .airtable_service import airtable_service

@receiver(post_save, sender=Branch)
def sync_branch_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Branches', formula=f"{{Name}} = '{instance.name}'")
            if existing_records:
                print(f"⚠ Branch {instance.name} already exists in Airtable, skipping sync")
                return
                
            data = {
                'Name': instance.name,
                'Address': instance.address or '',
                'Phone': instance.phone or '',
                'Email': instance.email or '',
                'Active': instance.is_active,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            result = airtable_service.create_record('Branches', data)
            # Store Airtable ID to prevent future duplicates
            if hasattr(instance, 'airtable_id'):
                instance.airtable_id = result['id']
                instance.save(update_fields=['airtable_id'])
            print(f"✓ Branch {instance.name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing branch: {e}")

@receiver(post_save, sender=Product)
def sync_product_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Products', formula=f"{{SKU}} = '{instance.sku}'")
            if existing_records:
                print(f"⚠ Product {instance.sku} already exists in Airtable, skipping sync")
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
            print(f"✓ Product {instance.name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing product: {e}")

@receiver(post_save, sender=Sale)
def sync_sale_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Sales', formula=f"{{Sale Number}} = '{instance.sale_number}'")
            if existing_records:
                print(f"⚠ Sale {instance.sale_number} already exists in Airtable, skipping sync")
                return
                
            data = {
                'Sale Number': instance.sale_number,
                'Branch': [instance.branch.name] if instance.branch else [],
                'Customer Name': instance.customer_name or '',
                'Customer Phone': instance.customer_phone or '',
                'Total Amount': float(instance.total_amount),
                'Payment Method': instance.payment_method or 'Cash',
                'Notes': instance.notes or '',
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Sales', data)
            print(f"✓ Sale {instance.sale_number} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing sale: {e}")

@receiver(post_save, sender=Order)
def sync_order_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Orders', formula=f"{{Order Number}} = '{instance.order_number}'")
            if existing_records:
                print(f"⚠ Order {instance.order_number} already exists in Airtable, skipping sync")
                return
                
            data = {
                'Order Number': instance.order_number,
                'Branch': [instance.branch.name] if instance.branch else [],
                'Supplier': instance.supplier or '',
                'Status': instance.status,
                'Total Amount': float(instance.total_amount),
                'Notes': instance.notes or '',
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Orders', data)
            print(f"✓ Order {instance.order_number} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing order: {e}")

@receiver(post_save, sender=Vehicle)
def sync_vehicle_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Vehicles', formula=f"{{Registration Number}} = '{instance.registration_number}'")
            if existing_records:
                print(f"⚠ Vehicle {instance.registration_number} already exists in Airtable, skipping sync")
                return
                
            data = {
                'Registration Number': instance.registration_number,
                'Branch': [instance.branch.name] if instance.branch else [],
                'Type': instance.vehicle_type,
                'Make': instance.make,
                'Model': instance.model,
                'Year': instance.year,
                'Current Mileage': instance.current_mileage,
                'Status': instance.status,
            }
            airtable_service.create_record('Vehicles', data)
            print(f"✓ Vehicle {instance.registration_number} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing vehicle: {e}")

@receiver(post_save, sender=Trip)
def sync_trip_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Trips', formula=f"{{Trip Number}} = '{instance.trip_number}'")
            if existing_records:
                print(f"⚠ Trip {instance.trip_number} already exists in Airtable, skipping sync")
                return
                
            data = {
                'Trip Number': instance.trip_number,
                'Vehicle': [instance.vehicle.registration_number] if instance.vehicle else [],
                'Driver Name': instance.driver.full_name if instance.driver else '',
                'Origin': instance.origin,
                'Destination': instance.destination,
                'Distance': float(instance.distance),
                'Status': instance.status,
                'Revenue': float(instance.revenue),
                'Fuel Cost': float(instance.fuel_cost),
                'Customer Name': instance.customer_name or '',
                'Customer Phone': instance.customer_phone or '',
                'Scheduled Date': instance.scheduled_date.isoformat() if instance.scheduled_date else None,
            }
            airtable_service.create_record('Trips', data)
            print(f"✓ Trip {instance.trip_number} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing trip: {e}")

@receiver(post_save, sender=UserProfile)
def sync_userprofile_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('User Profiles', formula=f"{{Username}} = '{instance.user.username}'")
            if existing_records:
                print(f"⚠ UserProfile {instance.user.username} already exists in Airtable, skipping sync")
                return
                
            data = {
                'Username': instance.user.username,
                'Role': instance.role,
                'Phone': instance.phone or '',
                'Active': instance.user.is_active,
                'Branch': [instance.branch.name] if instance.branch else [],
            }
            airtable_service.create_record('User Profiles', data)
            print(f"✓ UserProfile {instance.user.username} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing userprofile: {e}")

@receiver(post_save, sender=Employee)
def sync_employee_to_airtable(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_sync'):
        try:
            # Check if already exists in Airtable to prevent duplicates
            existing_records = airtable_service.get_records('Employees', formula=f"{{Email}} = '{instance.email}'")
            if existing_records:
                print(f"⚠ Employee {instance.email} already exists in Airtable, skipping sync")
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
            print(f"✓ Employee {instance.first_name} {instance.last_name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing employee: {e}")