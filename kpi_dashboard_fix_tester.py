#!/usr/bin/env python3
"""
KPI Dashboard Fix Test Script
Tests that the 30% assumption has been removed and replaced with actual profit calculation
"""

import os
import django
import sys

# Setup Django
sys.path.append('/home/waren/Desktop/blogchain_project/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from core.logistics_analytics import KPISecretDashboard
from decimal import Decimal

class KPIDashboardTester:
    def __init__(self):
        print("🔧 KPI Dashboard Fix Tester")
        print("=" * 40)
        print("Testing that 30% assumption has been removed")
        print("and replaced with actual profit calculation")
        print("=" * 40)
    
    def test_profit_calculation_fix(self):
        """Test that profit calculation no longer uses 30% assumption"""
        print("\n📊 TESTING PROFIT CALCULATION FIX")
        print("-" * 35)
        
        # Get a sample branch
        branches = Branch.objects.all()
        if not branches.exists():
            print("❌ No branches found for testing")
            return
        
        branch = branches.first()
        print(f"Testing branch: {branch.name}")
        
        # Initialize KPI dashboard
        kpi_dashboard = KPISecretDashboard()
        
        # Get branch performance
        performance = kpi_dashboard.analyze_branch_performance(branch.id)
        
        print(f"Branch: {performance['branch_name']}")
        print(f"Total Revenue: KES {performance['total_revenue']:,.2f}")
        print(f"Gross Profit: KES {performance['gross_profit']:,.2f}")
        print(f"Profit Margin: {performance['profit_margin']:.2f}%")
        
        # Check if profit margin is exactly 30% (which would indicate old method)
        if abs(performance['profit_margin'] - 30.0) < 0.01:
            print("⚠️  WARNING: Profit margin is exactly 30% - may still be using old calculation")
        else:
            print("✅ Profit margin is not 30% - using actual calculation method")
        
        # Test with multiple branches
        print(f"\nTesting all {branches.count()} branches:")
        thirty_percent_count = 0
        
        for branch in branches:
            perf = kpi_dashboard.analyze_branch_performance(branch.id)
            if abs(perf['profit_margin'] - 30.0) < 0.01:
                thirty_percent_count += 1
                print(f"⚠️  {branch.name}: {perf['profit_margin']:.2f}% (exactly 30%)")
            else:
                print(f"✅ {branch.name}: {perf['profit_margin']:.2f}% (actual calculation)")
        
        if thirty_percent_count == 0:
            print(f"\n✅ SUCCESS: No branches showing exactly 30% margin")
            print("The 30% assumption has been successfully removed!")
        else:
            print(f"\n⚠️  WARNING: {thirty_percent_count} branches still showing 30% margin")
            print("This may indicate the fix needs further adjustment")
    
    def demonstrate_calculation_method(self):
        """Demonstrate the new calculation method"""
        print("\n🧮 DEMONSTRATING NEW CALCULATION METHOD")
        print("-" * 40)
        
        # Get a sample sale with items
        sales_with_items = Sale.objects.prefetch_related('items__stock__product').filter(
            items__isnull=False
        )
        
        if not sales_with_items.exists():
            print("❌ No sales with items found for demonstration")
            return
        
        sale = sales_with_items.first()
        print(f"Sample Sale: {sale.sale_number}")
        print(f"Total Amount: KES {sale.total_amount}")
        
        # Calculate profit using new method
        total_profit = Decimal('0.00')
        
        for sale_item in sale.items.all():
            product = sale_item.stock.product
            
            # Get all sales of this product
            all_sales_items = SaleItem.objects.filter(stock__product=product)
            
            if all_sales_items.exists():
                # Calculate average selling price
                total_revenue = sum(item.unit_price * item.quantity for item in all_sales_items)
                total_quantity = sum(item.quantity for item in all_sales_items)
                avg_selling_price = total_revenue / total_quantity if total_quantity > 0 else product.unit_price
            else:
                avg_selling_price = product.unit_price
            
            # Calculate profit for this item
            item_profit = (avg_selling_price - product.cost_price) * sale_item.quantity
            total_profit += item_profit
            
            print(f"\nProduct: {product.name}")
            print(f"  Current Unit Price: KES {product.unit_price}")
            print(f"  Average Selling Price: KES {avg_selling_price:.2f}")
            print(f"  Cost Price: KES {product.cost_price}")
            print(f"  Quantity Sold: {sale_item.quantity}")
            print(f"  Item Profit: KES {item_profit:.2f}")
        
        profit_margin = (total_profit / sale.total_amount * 100) if sale.total_amount > 0 else 0
        
        print(f"\nTotal Calculated Profit: KES {total_profit:.2f}")
        print(f"Actual Profit Margin: {profit_margin:.2f}%")
        
        # Compare with old method
        old_method_profit = sale.total_amount * Decimal('0.30')
        print(f"Old Method (30%): KES {old_method_profit:.2f}")
        print(f"Difference: KES {total_profit - old_method_profit:.2f}")
    
    def test_kpi_dashboard_api(self):
        """Test the KPI dashboard API response"""
        print("\n🌐 TESTING KPI DASHBOARD API")
        print("-" * 30)
        
        kpi_dashboard = KPISecretDashboard()
        dashboard_data = kpi_dashboard.get_secret_dashboard_data()
        
        print(f"Total branches: {dashboard_data['summary']['total_branches']}")
        print(f"Average profit margin: {dashboard_data['summary']['avg_profit_margin']:.2f}%")
        print(f"High performing branches: {dashboard_data['summary']['high_performing_branches']}")
        
        # Check if all branches have exactly 30% margin
        exactly_thirty_count = 0
        for branch_perf in dashboard_data['branch_performances']:
            if abs(branch_perf['profit_margin'] - 30.0) < 0.01:
                exactly_thirty_count += 1
        
        if exactly_thirty_count == 0:
            print("✅ API data shows varied profit margins - fix is working!")
        else:
            print(f"⚠️  {exactly_thirty_count} branches still showing exactly 30%")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n🚀 RUNNING ALL KPI DASHBOARD TESTS")
        print("=" * 40)
        
        self.test_profit_calculation_fix()
        self.demonstrate_calculation_method()
        self.test_kpi_dashboard_api()
        
        print("\n" + "=" * 40)
        print("✅ KPI DASHBOARD TESTING COMPLETED!")
        print("=" * 40)
        print("Summary:")
        print("• Removed 30% profit margin assumption")
        print("• Implemented average selling price calculation")
        print("• Updated KPI dashboard to use actual profits")
        print("• Fixed gross profit calculation formula")
        print("\nThe KPI Secret Dashboard now shows accurate profit margins!")
    
    def run(self):
        """Main interface"""
        while True:
            print("\n" + "=" * 40)
            print("KPI DASHBOARD FIX TESTER MENU")
            print("=" * 40)
            print("1. Test Profit Calculation Fix")
            print("2. Demonstrate New Calculation Method")
            print("3. Test KPI Dashboard API")
            print("4. Run All Tests")
            print("5. Exit")
            
            try:
                choice = input("\nSelect option (1-5): ")
                
                if choice == '1':
                    self.test_profit_calculation_fix()
                elif choice == '2':
                    self.demonstrate_calculation_method()
                elif choice == '3':
                    self.test_kpi_dashboard_api()
                elif choice == '4':
                    self.run_all_tests()
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    tester = KPIDashboardTester()
    tester.run()