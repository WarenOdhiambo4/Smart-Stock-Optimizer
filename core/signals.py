"""
Django signals for auto-sync to Airtable
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Branch, Employee, Product, Order, Sale, Expense
from .airtable_service import airtable_service

@receiver(post_save, sender=Branch)
def sync_branch_to_airtable(sender, instance, created, **kwargs):
    if created and not getattr(instance, 'airtable_id', None):
        try:
            data = {
                'Name': instance.name,
                'Address': instance.address,
                'Phone': instance.phone,
                'Email': instance.email,
                'Active': instance.is_active,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            result = airtable_service.create_record('Branches', data)
            Branch.objects.filter(id=instance.id).update(airtable_id=result['id'])
            print(f"✓ Branch {instance.name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing branch to Airtable: {e}")

@receiver(post_save, sender=Product)
def sync_product_to_airtable(sender, instance, created, **kwargs):
    if created and not getattr(instance, 'airtable_id', None):
        try:
            data = {
                'Name': instance.name,
                'SKU': instance.sku,
                'Price': float(instance.unit_price),
                'Cost Price': float(instance.cost_price),
                'Category': instance.category,
                'Description': instance.description,
                'Active': instance.is_active,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            result = airtable_service.create_record('Products', data)
            Product.objects.filter(id=instance.id).update(airtable_id=result['id'])
            print(f"✓ Product {instance.name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing product to Airtable: {e}")

@receiver(post_save, sender=Sale)
def sync_sale_to_airtable(sender, instance, created, **kwargs):
    if created:
        try:
            data = {
                'Sale Number': instance.sale_number,
                'Customer Name': instance.customer_name,
                'Customer Phone': instance.customer_phone,
                'Total Amount': float(instance.total_amount),
                'Payment Method': instance.payment_method,
                'Notes': instance.notes,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Sales', data)
        except Exception as e:
            print(f"Error syncing sale to Airtable: {e}")

@receiver(post_save, sender=Order)
def sync_order_to_airtable(sender, instance, created, **kwargs):
    if created:
        try:
            data = {
                'Order Number': instance.order_number,
                'Supplier': instance.supplier,
                'Status': instance.status,
                'Total Amount': float(instance.total_amount),
                'Notes': instance.notes,
                'Created': instance.created_at.date().isoformat() if instance.created_at else None,
            }
            airtable_service.create_record('Orders', data)
        except Exception as e:
            print(f"Error syncing order to Airtable: {e}")