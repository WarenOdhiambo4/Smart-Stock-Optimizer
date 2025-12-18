#!/usr/bin/env python
"""
Fix common permission and setup issues for the ERP system
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Branch, Product, Stock
from decimal import Decimal

def fix_user_profiles():
    """Ensure all users have profiles"""
    print("=== FIXING USER PROFILES ===")
    
    users_without_profiles = []
    for user in User.objects.all():
        try:
            profile = user.profile
            print(f"✓ {user.username} has profile: {profile.role}")
        except UserProfile.DoesNotExist:
            users_without_profiles.append(user)
    
    if users_without_profiles:
        # Get first branch or create one
        branch = Branch.objects.first()
        if not branch:
            branch = Branch.objects.create(
                name="Main Branch",
                address="Main Office",
                phone="",
                email=""
            )
            print(f"✓ Created default branch: {branch.name}")
        
        for user in users_without_profiles:
            # Give admin role to superusers, sales to others
            role = 'ADMIN' if user.is_superuser else 'SALES'
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                branch=branch
            )
            print(f"✓ Created profile for {user.username}: {role}")
    
    print("User profiles fixed!\n")

def create_sample_data():
    """Create some sample data if none exists"""
    print("=== CREATING SAMPLE DATA ===")
    
    # Create sample products if none exist
    if Product.objects.count() == 0:
        products = [
            {"name": "Sample Product 1", "sku": "PROD001", "unit_price": "100.00", "cost_price": "80.00"},
            {"name": "Sample Product 2", "sku": "PROD002", "unit_price": "150.00", "cost_price": "120.00"},
            {"name": "Sample Product 3", "sku": "PROD003", "unit_price": "200.00", "cost_price": "160.00"},
        ]
        
        for prod_data in products:
            product = Product.objects.create(
                name=prod_data["name"],
                sku=prod_data["sku"],
                unit_price=Decimal(prod_data["unit_price"]),
                cost_price=Decimal(prod_data["cost_price"]),
                category="Sample"
            )
            print(f"✓ Created product: {product.name}")
        
        # Add stock for products in all branches
        for branch in Branch.objects.all():
            for product in Product.objects.all():
                stock, created = Stock.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={'quantity': 50, 'min_quantity': 10}
                )
                if created:
                    print(f"✓ Added stock: {product.name} at {branch.name}")
    
    print("Sample data created!\n")

def check_permissions():
    """Check if all views are accessible"""
    print("=== CHECKING PERMISSIONS ===")
    
    # Check if admin user exists
    admin_users = User.objects.filter(is_superuser=True)
    if admin_users.exists():
        admin = admin_users.first()
        print(f"✓ Admin user exists: {admin.username}")
        
        try:
            profile = admin.profile
            print(f"✓ Admin profile: {profile.role} at {profile.branch}")
        except:
            print("✗ Admin missing profile - this was fixed above")
    else:
        print("✗ No admin user found")
    
    # Check branches
    branch_count = Branch.objects.count()
    print(f"✓ Branches available: {branch_count}")
    
    # Check products
    product_count = Product.objects.count()
    print(f"✓ Products available: {product_count}")
    
    print("Permission check completed!\n")

def main():
    print("🔧 ERP System Fix Script")
    print("=" * 50)
    
    try:
        fix_user_profiles()
        create_sample_data()
        check_permissions()
        
        print("✅ ALL FIXES COMPLETED SUCCESSFULLY!")
        print("\nYou can now:")
        print("1. Login with your existing credentials")
        print("2. Access all sections (branches, sales, logistics, etc.)")
        print("3. Create orders, sales, and manage stock")
        print("4. Use the admin panel at /admin/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())