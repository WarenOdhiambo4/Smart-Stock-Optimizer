"""
Django signals for auto-sync to Airtable
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Branch, Employee, Product, Order, Sale, Expense
from .airtable_service import airtable_service

# @receiver(post_save, sender=Branch)
# def sync_branch_to_airtable(sender, instance, created, **kwargs):
#     # Disabled - airtable_id field missing
#     pass

# @receiver(post_save, sender=Product)
# def sync_product_to_airtable(sender, instance, created, **kwargs):
#     # Disabled - airtable_id field missing
#     pass

# @receiver(post_save, sender=Sale)
# def sync_sale_to_airtable(sender, instance, created, **kwargs):
#     # Disabled - sync issues
#     pass

# @receiver(post_save, sender=Order)
# def sync_order_to_airtable(sender, instance, created, **kwargs):
#     # Disabled - sync issues
#     pass