#!/usr/bin/env python
"""
Test sync for all 16 Airtable tables
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime, date

def test_all_16_tables():
    """Test sync for all 16 tables"""
    print("🧪 Testing all 16 table syncs...")
    timestamp = datetime.now().strftime('%H%M%S')
    
    # 1. Branch ✅ (Working)
    try:
        branch = Branch.objects.create(
            name=f"Test Branch {timestamp}",
            address="123 Test St",
            phone="123-456-7890",
            email=f"test{timestamp}@branch.com"
        )
        print("✅ 1. Branch created")
    except Exception as e:
        print(f"❌ 1. Branch failed: {e}")
        return
    
    # 2. Product ✅ (Working)
    try:
        product = Product.objects.create(
            name=f"Test Product {timestamp}",
            sku=f"TEST-{timestamp}",
            unit_price=Decimal('10.00'),
            cost_price=Decimal('5.00'),
            category="Test Category"
        )
        print("✅ 2. Product created")
    except Exception as e:
        print(f"❌ 2. Product failed: {e}")
        return
    
    # 3. Stock
    try:
        stock = Stock.objects.create(
            branch=branch,
            product=product,
            quantity=100,
            min_quantity=10
        )
        print("✅ 3. Stock created")
    except Exception as e:
        print(f"❌ 3. Stock failed: {e}")
    
    # 4. Sale
    try:
        sale = Sale.objects.create(
            sale_number=f"SALE-{timestamp}",
            branch=branch,
            customer_name="Test Customer",
            customer_phone="123-456-7890",
            total_amount=Decimal('100.00'),
            payment_method="Cash"
        )
        print("✅ 4. Sale created")
    except Exception as e:
        print(f"❌ 4. Sale failed: {e}")
    
    # 5. Order
    try:
        order = Order.objects.create(
            order_number=f"ORDER-{timestamp}",
            branch=branch,
            supplier="Test Supplier",
            status="PENDING",
            total_amount=Decimal('200.00')
        )
        print("✅ 5. Order created")
    except Exception as e:
        print(f"❌ 5. Order failed: {e}")
    
    # 6. Vehicle
    try:
        vehicle = Vehicle.objects.create(
            registration_number=f"TEST-{timestamp}",
            branch=branch,
            vehicle_type="CAR",
            make="Toyota",
            model="Camry",
            year=2020,
            current_mileage=50000
        )
        print("✅ 6. Vehicle created")
    except Exception as e:
        print(f"❌ 6. Vehicle failed: {e}")
    
    # 7. Employee ✅ (Working)
    try:
        employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            email=f"test{timestamp}@employee.com",
            phone="123-456-7890",
            position="Tester"
        )
        print("✅ 7. Employee created")
    except Exception as e:
        print(f"❌ 7. Employee failed: {e}")
        return
    
    # 8. Trip
    try:
        trip = Trip.objects.create(
            trip_number=f"TRIP-{timestamp}",
            vehicle=vehicle,
            driver=employee,
            origin="Test Origin",
            destination="Test Destination",
            distance=Decimal('100.0'),
            revenue=Decimal('500.00'),
            fuel_cost=Decimal('50.00'),
            scheduled_date=datetime.now()
        )
        print("✅ 8. Trip created")
    except Exception as e:
        print(f"❌ 8. Trip failed: {e}")
    
    # 9. Logistics
    try:
        logistics = Logistics.objects.create(
            tracking_number=f"LOG-{timestamp}",
            sale=sale,
            from_branch=branch,
            to_address="123 Customer St",
            customer_name="Test Customer",
            customer_phone="123-456-7890",
            vehicle=vehicle,
            driver=employee,
            delivery_cost=Decimal('25.00')
        )
        print("✅ 9. Logistics created")
    except Exception as e:
        print(f"❌ 9. Logistics failed: {e}")
    
    # 10. Expense
    try:
        expense = Expense.objects.create(
            expense_number=f"EXP-{timestamp}",
            branch=branch,
            expense_type="OPERATIONAL",
            description="Test expense",
            amount=Decimal('75.00'),
            expense_date=date.today()
        )
        print("✅ 10. Expense created")
    except Exception as e:
        print(f"❌ 10. Expense failed: {e}")
    
    # 11. Stock Movement
    try:
        stock_movement = StockMovement.objects.create(
            stock=stock,
            movement_type="IN",
            quantity=50,
            status="APPROVED",
            notes="Test stock movement"
        )
        print("✅ 11. Stock Movement created")
    except Exception as e:
        print(f"❌ 11. Stock Movement failed: {e}")
    
    # 12. Broken Product
    try:
        broken_product = BrokenProduct.objects.create(
            stock=stock,
            quantity=5,
            damage_type="BROKEN",
            unit_cost=Decimal('5.00'),
            description="Test broken product",
            reported_by=employee
        )
        print("✅ 12. Broken Product created")
    except Exception as e:
        print(f"❌ 12. Broken Product failed: {e}")
    
    # 13. Vehicle Maintenance
    try:
        maintenance = VehicleMaintenance.objects.create(
            maintenance_number=f"MAINT-{timestamp}",
            vehicle=vehicle,
            maintenance_type="ROUTINE",
            description="Test maintenance",
            service_provider="Test Garage",
            service_date=date.today(),
            parts_cost=Decimal('100.00'),
            labor_cost=Decimal('50.00'),
            mileage_at_service=50000
        )
        print("✅ 13. Vehicle Maintenance created")
    except Exception as e:
        print(f"❌ 13. Vehicle Maintenance failed: {e}")
    
    # 14. Fuel Consumption
    try:
        fuel = FuelConsumption.objects.create(
            vehicle=vehicle,
            liters=Decimal('40.0'),
            cost_per_liter=Decimal('1.50'),
            mileage_at_fill=50100,
            fuel_station="Test Station",
            date=date.today(),
            created_by=employee
        )
        print("✅ 14. Fuel Consumption created")
    except Exception as e:
        print(f"❌ 14. Fuel Consumption failed: {e}")
    
    # 15. User Profile
    try:
        user = User.objects.create_user(
            username=f"testuser{timestamp}",
            email=f"testuser{timestamp}@test.com",
            first_name="Test",
            last_name="User"
        )
        user_profile = UserProfile.objects.create(
            user=user,
            role="SALES",
            branch=branch,
            phone="123-456-7890"
        )
        print("✅ 15. User Profile created")
    except Exception as e:
        print(f"❌ 15. User Profile failed: {e}")
    
    # 16. User (Django User)
    try:
        user2 = User.objects.create_user(
            username=f"testuser2{timestamp}",
            email=f"testuser2{timestamp}@test.com",
            first_name="Test2",
            last_name="User2"
        )
        print("✅ 16. User created")
    except Exception as e:
        print(f"❌ 16. User failed: {e}")
    
    print("\n🎉 All 16 table tests completed!")
    print("Check your Airtable to see which records were synced successfully.")
    print("\n📊 Test Summary:")
    print("1. ✅ Branches (Working)")
    print("2. ✅ Products (Working)")
    print("3. 🔄 Stock")
    print("4. 🔄 Sales")
    print("5. 🔄 Orders")
    print("6. 🔄 Vehicles")
    print("7. ✅ Employees (Working)")
    print("8. 🔄 Trips")
    print("9. 🔄 Logistics")
    print("10. 🔄 Expenses")
    print("11. 🔄 Stock Movements")
    print("12. 🔄 Broken Products")
    print("13. 🔄 Vehicle Maintenance")
    print("14. 🔄 Fuel Consumption")
    print("15. 🔄 User Profiles")
    print("16. 🔄 Users")

if __name__ == "__main__":
    test_all_16_tables()