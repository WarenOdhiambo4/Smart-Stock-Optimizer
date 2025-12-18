#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import Branch
from core.airtable_service import airtable_service

# Get the branch
branch = Branch.objects.get(name='KISUMU')

# Sync to Airtable manually
data = {
    'Name': branch.name,
    'Address': branch.address,
    'Phone': branch.phone,
    'Email': branch.email,
    'Active': branch.is_active,
    'Created': branch.created_at.date().isoformat() if branch.created_at else None,
}

try:
    result = airtable_service.create_record('Branches', data)
    print(f"Branch synced to Airtable! ID: {result['id']}")
    
    # Save Airtable ID back to Django
    branch.airtable_id = result['id']
    branch.save()
    print("Airtable ID saved to Django")
    
except Exception as e:
    print(f"Error: {e}")