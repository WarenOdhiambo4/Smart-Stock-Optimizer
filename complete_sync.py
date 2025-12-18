#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from core.airtable_service import airtable_service

def sync_all_to_airtable():
    """Sync all existing Django data to Airtable"""
    
    # 1. Sync Branches
    for branch in Branch.objects.all():
        try:
            data = {
                'Name': branch.name,
                'Address': branch.address,
                'Phone': branch.phone,
                'Email': branch.email,
                'Active': branch.is_active,
                'Created': branch.created_at.date().isoformat() if branch.created_at else None,
            }
            if not hasattr(branch, 'airtable_id') or not branch.airtable_id:
                result = airtable_service.create_record('Branches', data)
                branch.airtable_id = result['id']
                branch.save()
                print(f"✓ Branch {branch.name} synced")
        except Exception as e:
            print(f"✗ Branch {branch.name} failed: {e}")
    
    # 2. Sync Employees
    for employee in Employee.objects.all():
        try:
            data = {
                'First Name': employee.first_name,
                'Last Name': employee.last_name,
                'Email': employee.email,
                'Phone': employee.phone,
                'Position': employee.position,
                'Active': employee.is_active,
                'Created': employee.created_at.date().isoformat() if employee.created_at else None,
            }
            result = airtable_service.create_record('Employees', data)
            print(f"✓ Employee {employee.full_name} synced")
        except Exception as e:
            print(f"✗ Employee {employee.full_name} failed: {e}")
    
    # 3. Sync Products
    for product in Product.objects.all():
        try:
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
            print(f"✓ Product {product.name} synced")
        except Exception as e:
            print(f"✗ Product {product.name} failed: {e}")
    
    # 4. Sync Orders
    for order in Order.objects.all():
        try:
            data = {
                'Order Number': order.order_number,
                'Supplier': order.supplier,
                'Status': order.status,
                'Total Amount': float(order.total_amount),
                'Notes': order.notes,
                'Created': order.created_at.date().isoformat() if order.created_at else None,
            }
            result = airtable_service.create_record('Orders', data)
            print(f"✓ Order {order.order_number} synced")
        except Exception as e:
            print(f"✗ Order {order.order_number} failed: {e}")
    
    # 5. Sync Sales
    for sale in Sale.objects.all():
        try:
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
            print(f"✓ Sale {sale.sale_number} synced")
        except Exception as e:
            print(f"✗ Sale {sale.sale_number} failed: {e}")
    
    print("\n🎉 Sync completed! Check your Airtable base.")

if __name__ == "__main__":
    sync_all_to_airtable()