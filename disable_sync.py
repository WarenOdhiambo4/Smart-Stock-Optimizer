#!/usr/bin/env python
"""
Temporarily disable sync signals to prevent duplicates during cleanup
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from django.db.models.signals import post_save
from core.models import Branch, Product, Sale, Order, Employee, Vehicle, Trip, UserProfile
from core import signals

def disable_sync_signals():
    """Disconnect all sync signals"""
    print("🔇 Disabling sync signals...")
    
    # Disconnect all signals
    post_save.disconnect(signals.sync_branch_to_airtable, sender=Branch)
    post_save.disconnect(signals.sync_product_to_airtable, sender=Product)
    post_save.disconnect(signals.sync_sale_to_airtable, sender=Sale)
    post_save.disconnect(signals.sync_order_to_airtable, sender=Order)
    post_save.disconnect(signals.sync_employee_to_airtable, sender=Employee)
    post_save.disconnect(signals.sync_vehicle_to_airtable, sender=Vehicle)
    post_save.disconnect(signals.sync_trip_to_airtable, sender=Trip)
    post_save.disconnect(signals.sync_userprofile_to_airtable, sender=UserProfile)
    
    print("✅ All sync signals disabled")
    print("You can now safely run cleanup scripts without triggering duplicates")

def enable_sync_signals():
    """Reconnect all sync signals"""
    print("🔊 Enabling sync signals...")
    
    # Reconnect all signals
    post_save.connect(signals.sync_branch_to_airtable, sender=Branch)
    post_save.connect(signals.sync_product_to_airtable, sender=Product)
    post_save.connect(signals.sync_sale_to_airtable, sender=Sale)
    post_save.connect(signals.sync_order_to_airtable, sender=Order)
    post_save.connect(signals.sync_employee_to_airtable, sender=Employee)
    post_save.connect(signals.sync_vehicle_to_airtable, sender=Vehicle)
    post_save.connect(signals.sync_trip_to_airtable, sender=Trip)
    post_save.connect(signals.sync_userprofile_to_airtable, sender=UserProfile)
    
    print("✅ All sync signals enabled")
    print("New records will now automatically sync to Airtable")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'disable':
            disable_sync_signals()
        elif sys.argv[1] == 'enable':
            enable_sync_signals()
        else:
            print("Usage: python disable_sync.py [disable|enable]")
    else:
        print("Usage: python disable_sync.py [disable|enable]")
        print("  disable - Turn off automatic sync signals")
        print("  enable  - Turn on automatic sync signals")