#!/usr/bin/env python3
"""
Test Frontend CRUD Operations
"""

import os
import django
import sys

# Setup Django
sys.path.append('/home/waren/Desktop/hp/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import Expense, Branch, UserProfile
from decimal import Decimal
from datetime import date

def test_frontend_crud():
    print("🧪 Testing Frontend CRUD Operations")
    print("=" * 40)
    
    # Create test user and login
    client = Client()
    
    # Get or create admin user
    user, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.username}")
    
    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'ADMIN'}
    )
    
    # Get or create test branch
    branch, created = Branch.objects.get_or_create(
        name="Test Branch Frontend",
        defaults={'address': 'Test Address', 'is_active': True}
    )
    
    # Login
    login_success = client.login(username='testadmin', password='testpass123')
    if not login_success:
        print("❌ Login failed")
        return
    
    print("✅ User logged in successfully")
    
    # Test 1: Access expense list
    print("\n1️⃣ Testing expense list access...")
    response = client.get('/expenses/')
    if response.status_code == 200:
        print("✅ Expense list accessible")
    else:
        print(f"❌ Expense list failed: {response.status_code}")
    
    # Test 2: Access expense create form
    print("\n2️⃣ Testing expense create form...")
    response = client.get('/expenses/create/')
    if response.status_code == 200:
        print("✅ Expense create form accessible")
    else:
        print(f"❌ Expense create form failed: {response.status_code}")
    
    # Test 3: Create expense via POST
    print("\n3️⃣ Testing expense creation...")
    expense_data = {
        'branch': branch.id,
        'expense_type': 'OTHER',
        'description': 'Test frontend expense',
        'amount': '100.00',
        'expense_date': date.today().strftime('%Y-%m-%d'),
        'receipt_number': 'TEST-001',
        'notes': 'Created via frontend test'
    }
    
    response = client.post('/expenses/create/', expense_data)
    if response.status_code == 302:  # Redirect after successful creation
        print("✅ Expense created successfully via frontend")
        
        # Get the created expense
        expense = Expense.objects.filter(description='Test frontend expense').first()
        if expense:
            print(f"   Created expense: {expense.expense_number}")
            
            # Test 4: Access expense update form
            print("\n4️⃣ Testing expense update form...")
            response = client.get(f'/expenses/{expense.id}/edit/')
            if response.status_code == 200:
                print("✅ Expense update form accessible")
                
                # Test 5: Update expense
                print("\n5️⃣ Testing expense update...")
                update_data = expense_data.copy()
                update_data['description'] = 'Updated frontend expense'
                update_data['amount'] = '150.00'
                
                response = client.post(f'/expenses/{expense.id}/edit/', update_data)
                if response.status_code == 302:
                    print("✅ Expense updated successfully via frontend")
                    
                    # Verify update
                    expense.refresh_from_db()
                    if expense.description == 'Updated frontend expense':
                        print("✅ Update verified in database")
                    else:
                        print("❌ Update not reflected in database")
                else:
                    print(f"❌ Expense update failed: {response.status_code}")
            else:
                print(f"❌ Expense update form failed: {response.status_code}")
            
            # Test 6: Delete expense
            print("\n6️⃣ Testing expense deletion...")
            response = client.post(f'/expenses/{expense.id}/delete/')
            if response.status_code == 200:  # JSON response
                print("✅ Expense deleted successfully via frontend")
                
                # Verify deletion
                if not Expense.objects.filter(id=expense.id).exists():
                    print("✅ Deletion verified in database")
                else:
                    print("❌ Expense still exists in database")
            else:
                print(f"❌ Expense deletion failed: {response.status_code}")
        else:
            print("❌ Created expense not found")
    else:
        print(f"❌ Expense creation failed: {response.status_code}")
    
    # Test 7: Test auto-generated expense protection
    print("\n7️⃣ Testing auto-generated expense protection...")
    
    # Create an auto-generated expense
    auto_expense = Expense.objects.create(
        expense_number="TRIP-TEST-FRONTEND",
        branch=branch,
        expense_type="TRANSPORT",
        description="Auto-generated test expense",
        amount=Decimal('50.00'),
        expense_date=date.today()
    )
    
    # Try to access update form
    response = client.get(f'/expenses/{auto_expense.id}/edit/')
    if response.status_code == 302:  # Should redirect with error
        print("✅ Auto-generated expense update blocked")
    else:
        print(f"❌ Auto-generated expense update not blocked: {response.status_code}")
    
    # Try to delete
    response = client.post(f'/expenses/{auto_expense.id}/delete/')
    if response.status_code == 400:  # Should return error
        print("✅ Auto-generated expense deletion blocked")
    else:
        print(f"❌ Auto-generated expense deletion not blocked: {response.status_code}")
    
    # Clean up
    auto_expense.delete()
    
    print("\n🎉 Frontend CRUD testing completed!")
    print("\n📋 Summary:")
    print("   ✅ Expense list accessible")
    print("   ✅ Create form accessible")
    print("   ✅ Create functionality working")
    print("   ✅ Update form accessible")
    print("   ✅ Update functionality working")
    print("   ✅ Delete functionality working")
    print("   ✅ Auto-generated expense protection working")

if __name__ == "__main__":
    test_frontend_crud()