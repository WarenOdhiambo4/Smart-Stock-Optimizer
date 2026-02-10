#!/usr/bin/env python
"""
Test all table syncs by creating sample records
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from decimal import Decimal
from datetime import datetime, date
from django.utils import timezone

def test_all_syncs():
    """Test sync for all tables"""
    print("🧪 Testing all table syncs...")
    
    # 1. Test Branch (working)
    try:
        branch = Branch.objects.create(
            name=f"Test Branch {datetime.now().strftime('%H%M%S')}",
            address="123 Test St",
            phone="123-456-7890",
            email="test@branch.com"
        )
        print("✅ Branch created and should sync")
    except Exception as e:
        print(f"❌ Branch failed: {e}")
    
    # 2. Test Product (working)
    try:
        product = Product.objects.create(
            name=f"Test Product {datetime.now().strftime('%H%M%S')}",
            sku=f"TEST-{datetime.now().strftime('%H%M%S')}",
            unit_price=Decimal('10.00'),
            cost_price=Decimal('5.00'),
            category="Test Category"
        )
        print("✅ Product created and should sync")
    except Exception as e:
        print(f"❌ Product failed: {e}")
    
    # 3. Test Employee (working)
    try:
        employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            email=f"test{datetime.now().strftime('%H%M%S')}@employee.com",
            phone="123-456-7890",
            position="Tester"
        )
        print("✅ Employee created and should sync")
    except Exception as e:
        print(f"❌ Employee failed: {e}")
    
    # 4. Test Sale (should now work)
    try:
        sale = Sale.objects.create(
            sale_number=f"SALE-{datetime.now().strftime('%H%M%S')}",
            branch=branch,
            customer_name="Test Customer",
            customer_phone="123-456-7890",
            total_amount=Decimal('100.00'),
            payment_method="Cash"
        )
        print("✅ Sale created and should sync")
    except Exception as e:
        print(f"❌ Sale failed: {e}")
    
    # 5. Test Order (should now work)
    try:
        order = Order.objects.create(
            order_number=f"ORDER-{datetime.now().strftime('%H%M%S')}",
            branch=branch,
            supplier="Test Supplier",
            status="PENDING",
            total_amount=Decimal('200.00')
        )
        print("✅ Order created and should sync")
    except Exception as e:
        print(f"❌ Order failed: {e}")
    
    # 6. Test Vehicle (should now work)
    try:
        vehicle = Vehicle.objects.create(
            registration_number=f"TEST-{datetime.now().strftime('%H%M%S')}",
            branch=branch,
            vehicle_type="CAR",
            make="Toyota",
            model="Camry",
            year=2020,
            current_mileage=50000
        )
        print("✅ Vehicle created and should sync")
    except Exception as e:
        print(f"❌ Vehicle failed: {e}")
    
    # 7. Test Trip (should now work)
    try:
        trip = Trip.objects.create(
            trip_number=f"TRIP-{datetime.now().strftime('%H%M%S')}",
            vehicle=vehicle,
            driver=employee,
            origin="Test Origin",
            destination="Test Destination",
            distance=Decimal('100.0'),
            revenue=Decimal('500.00'),
            fuel_cost=Decimal('50.00'),
            scheduled_date=timezone.now()
        )
        print("✅ Trip created and should sync")
    except Exception as e:
        print(f"❌ Trip failed: {e}")
    
    # 8. Test Stock (should now work)
    try:
        stock = Stock.objects.create(
            branch=branch,
            product=product,
            quantity=100,
            min_quantity=10
        )
        print("✅ Stock created and should sync")
    except Exception as e:
        print(f"❌ Stock failed: {e}")
    
    # 9. Test Logistics (should now work)
    try:
        logistics = Logistics.objects.create(
            tracking_number=f"LOG-{datetime.now().strftime('%H%M%S')}",
            sale=sale,
            from_branch=branch,
            to_address="123 Customer St",
            customer_name="Test Customer",
            customer_phone="123-456-7890",
            vehicle=vehicle,
            driver=employee,
            delivery_cost=Decimal('25.00')
        )
        print("✅ Logistics created and should sync")
    except Exception as e:
        print(f"❌ Logistics failed: {e}")
    
    # 10. Test Expense (should now work)
    try:
        expense = Expense.objects.create(
            expense_number=f"EXP-{datetime.now().strftime('%H%M%S')}",
            branch=branch,
            expense_type="OPERATIONAL",
            description="Test expense",
            amount=Decimal('75.00'),
            expense_date=date.today()
        )
        print("✅ Expense created and should sync")
    except Exception as e:
        print(f"❌ Expense failed: {e}")
    
    print("\n🎉 All table tests completed!")
    print("Check your Airtable to see which records were synced successfully.")

if __name__ == "__main__":
    test_all_syncs()
