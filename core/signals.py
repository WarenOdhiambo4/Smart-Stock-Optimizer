"""
Django signals for auto-sync to Airtable
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Branch, Employee, Product, Order, Sale, Expense
from .airtable_service import airtable_service

@receiver(post_save, sender=Branch)
def sync_branch_to_airtable(sender, instance, created, **kwargs):
    if created:
        try:
            from .airtable_service import AirtableService
            service = AirtableService()
            data = {
                'Name': instance.name,
                'Address': instance.address,
                'Phone': instance.phone,
                'Email': instance.email,
                'Active': instance.is_active,
            }
            service.create_record('Branches', data)
            print(f"✓ Branch {instance.name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing branch: {e}")

@receiver(post_save, sender=Product)
def sync_product_to_airtable(sender, instance, created, **kwargs):
    if created:
        try:
            from .airtable_service import AirtableService
            service = AirtableService()
            data = {
                'Name': instance.name,
                'SKU': instance.sku,
                'Price': float(instance.unit_price),
                'Cost': float(instance.cost_price),
                'Category': instance.category,
            }
            service.create_record('Products', data)
            print(f"✓ Product {instance.name} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing product: {e}")

@receiver(post_save, sender=Sale)
def sync_sale_to_airtable(sender, instance, created, **kwargs):
    if created:
        try:
            from .airtable_service import AirtableService
            service = AirtableService()
            data = {
                'Sale Number': instance.sale_number,
                'Customer': instance.customer_name,
                'Phone': instance.customer_phone,
                'Total': float(instance.total_amount),
                'Payment Method': instance.payment_method,
            }
            service.create_record('Sales', data)
            print(f"✓ Sale {instance.sale_number} synced to Airtable")
        except Exception as e:
            print(f"✗ Error syncing sale: {e}")

# @receiver(post_save, sender=Order)
# def sync_order_to_airtable(sender, instance, created, **kwargs):
#     # Disabled - sync issues
#     pass