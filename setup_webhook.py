#!/usr/bin/env python
"""
One-time script to register Airtable webhook
Run this once after deployment to enable real-time sync
"""
import os
import django
import sys

# Setup Django
sys.path.append('/home/waren/Desktop/blogchain_project/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.webhook_manager import AirtableWebhookManager

def main():
    manager = AirtableWebhookManager()
    
    # Your deployed webhook URL
    webhook_url = "https://kabisa-enterprise-ltd.onrender.com/webhook/"
    
    print(f"Registering webhook with URL: {webhook_url}")
    
    try:
        result = manager.register_webhook(webhook_url)
        
        if 'id' in result:
            webhook_id = result['id']
            print(f"✅ Webhook registered successfully!")
            print(f"📝 Webhook ID: {webhook_id}")
            print(f"⏰ Expires: {result.get('expirationTime', 'Unknown')}")
            print(f"\n💡 Save this webhook ID to your .env file:")
            print(f"AIRTABLE_WEBHOOK_ID={webhook_id}")
            
        else:
            print(f"❌ Failed to register webhook: {result}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()