#!/usr/bin/env python
"""
Safe sync script that prevents duplicates
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import Branch, Product, Sale, Order, Employee, Vehicle, Trip
from core.airtable_service import airtable_service

def safe_sync_branches():
    """Safely sync branches without creating duplicates"""
    print("🔄 Syncing Branches...")
    
    for branch in Branch.objects.all():
        try:
            # Check if already exists in Airtable
            existing = airtable_service.get_records('Branches', formula=f"{{Name}} = '{branch.name}'")
            
            if existing:
                print(f"  ⏭️  Branch '{branch.name}' already exists in Airtable")
                # Update airtable_id if missing
                if hasattr(branch, 'airtable_id') and not branch.airtable_id:
                    branch.airtable_id = existing[0]['id']
                    branch.save(update_fields=['airtable_id'])
                continue
            
            # Create new record
            data = {
                'Name': branch.name,
                'Address': branch.address,
                'Phone': branch.phone,
                'Email': branch.email,
                'Active': branch.is_active,
                'Created': branch.created_at.date().isoformat() if branch.created_at else None,
            }
            
            result = airtable_service.create_record('Branches', data)
            
            # Save airtable_id
            if hasattr(branch, 'airtable_id'):
                branch.airtable_id = result['id']
                branch.save(update_fields=['airtable_id'])
            
            print(f"  ✅ Branch '{branch.name}' synced successfully")
            
        except Exception as e:
            print(f"  ❌ Error syncing branch '{branch.name}': {e}")

def safe_sync_products():
    """Safely sync products without creating duplicates"""
    print("🔄 Syncing Products...")
    
    for product in Product.objects.all():
        try:
            # Check if already exists in Airtable
            existing = airtable_service.get_records('Products', formula=f"{{SKU}} = '{product.sku}'")
            
            if existing:
                print(f"  ⏭️  Product '{product.sku}' already exists in Airtable")
                # Update airtable_id if missing
                if hasattr(product, 'airtable_id') and not product.airtable_id:
                    product.airtable_id = existing[0]['id']
                    product.save(update_fields=['airtable_id'])
                continue
            
            # Create new record
            data = {
                'Name': product.name,
                'SKU': product.sku,
                'Price': float(product.unit_price),
                'Cost Price': float(product.cost_price),
                'Category': product.category,
                'Description': product.description,
                'Active': product.is_active,
                'Created': product.created_at.date().isoformat() if product.created_at else None,
            }
            
            result = airtable_service.create_record('Products', data)
            
            # Save airtable_id
            if hasattr(product, 'airtable_id'):
                product.airtable_id = result['id']
                product.save(update_fields=['airtable_id'])
            
            print(f"  ✅ Product '{product.sku}' synced successfully")
            
        except Exception as e:
            print(f"  ❌ Error syncing product '{product.sku}': {e}")

def safe_sync_sales():
    """Safely sync sales without creating duplicates"""
    print("🔄 Syncing Sales...")
    
    for sale in Sale.objects.all():
        try:
            # Check if already exists in Airtable
            existing = airtable_service.get_records('Sales', formula=f"{{Sale Number}} = '{sale.sale_number}'")
            
            if existing:
                print(f"  ⏭️  Sale '{sale.sale_number}' already exists in Airtable")
                # Update airtable_id if missing
                if hasattr(sale, 'airtable_id') and not sale.airtable_id:
                    sale.airtable_id = existing[0]['id']
                    sale.save(update_fields=['airtable_id'])
                continue
            
            # Create new record
            data = {
                'Sale Number': sale.sale_number,
                'Customer Name': sale.customer_name,
                'Customer Phone': sale.customer_phone,
                'Total Amount': float(sale.total_amount),
                'Payment Method': sale.payment_method,
                'Notes': sale.notes,
                'Created': sale.created_at.date().isoformat() if sale.created_at else None,
            }
            
            result = airtable_service.create_record('Sales', data)
            
            # Save airtable_id
            if hasattr(sale, 'airtable_id'):
                sale.airtable_id = result['id']
                sale.save(update_fields=['airtable_id'])
            
            print(f"  ✅ Sale '{sale.sale_number}' synced successfully")
            
        except Exception as e:
            print(f"  ❌ Error syncing sale '{sale.sale_number}': {e}")

def safe_sync_orders():
    """Safely sync orders without creating duplicates"""
    print("🔄 Syncing Orders...")
    
    for order in Order.objects.all():
        try:
            # Check if already exists in Airtable
            existing = airtable_service.get_records('Orders', formula=f"{{Order Number}} = '{order.order_number}'")
            
            if existing:
                print(f"  ⏭️  Order '{order.order_number}' already exists in Airtable")
                # Update airtable_id if missing
                if hasattr(order, 'airtable_id') and not order.airtable_id:
                    order.airtable_id = existing[0]['id']
                    order.save(update_fields=['airtable_id'])
                continue
            
            # Create new record
            data = {
                'Order Number': order.order_number,
                'Supplier': order.supplier,
                'Status': order.status,
                'Total Amount': float(order.total_amount),
                'Notes': order.notes,
                'Created': order.created_at.date().isoformat() if order.created_at else None,
            }
            
            result = airtable_service.create_record('Orders', data)
            
            # Save airtable_id
            if hasattr(order, 'airtable_id'):
                order.airtable_id = result['id']
                order.save(update_fields=['airtable_id'])
            
            print(f"  ✅ Order '{order.order_number}' synced successfully")
            
        except Exception as e:
            print(f"  ❌ Error syncing order '{order.order_number}': {e}")

def main():
    print("🚀 Starting safe sync process...")
    print("This will only create records that don't already exist in Airtable")
    print("="*60)
    
    safe_sync_branches()
    print()
    safe_sync_products()
    print()
    safe_sync_sales()
    print()
    safe_sync_orders()
    
    print("\n🎉 Safe sync completed!")
    print("\n📋 Summary:")
    print("- Existing records were skipped")
    print("- Only new records were created")
    print("- No duplicates were created")

if __name__ == "__main__":
    main()