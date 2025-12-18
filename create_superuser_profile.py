#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/waren/Desktop/hp/Kabisa_enterprise_erp')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Branch

def create_superuser_profile():
    # Get the superuser
    try:
        superuser = User.objects.get(username='WarenOdhiambo')
        print(f"Found superuser: {superuser.username}")
        
        # Check if profile already exists
        if hasattr(superuser, 'profile'):
            print("Profile already exists!")
            print(f"Role: {superuser.profile.role}")
            print(f"Branch: {superuser.profile.branch}")
            return
        
        # Create profile for superuser
        profile = UserProfile.objects.create(
            user=superuser,
            role='ADMIN',  # Give admin role
            branch=None,   # Admin can access all branches
            phone=''
        )
        
        print(f"Created profile for {superuser.username}")
        print(f"Role: {profile.role}")
        print("Profile created successfully!")
        
    except User.DoesNotExist:
        print("Superuser 'WarenOdhiambo' not found!")
        print("Available users:")
        for user in User.objects.all():
            print(f"  - {user.username}")

if __name__ == '__main__':
    create_superuser_profile()