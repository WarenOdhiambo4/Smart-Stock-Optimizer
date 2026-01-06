#!/usr/bin/env python3
"""
Comprehensive Receipt Management System
Handles all receipt generation with enhanced functionality
"""

import os
import django
import sys

# Setup Django
sys.path.append('/home/waren/Desktop/blogchain_project/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import *
from core.receipt_generator import ReceiptGenerator
from decimal import Decimal
from datetime import date, datetime

class ReceiptManager:
    def __init__(self):
        self.generator = ReceiptGenerator()
        print("🧾 KabisaKabisa Receipt Management System")
        print("=" * 60)
    
    def print_trip_receipts(self):
        """Print trip receipts - both general and per vehicle"""
        print("\n🚛 TRIP RECEIPTS")
        print("-" * 30)
        
        while True:
            print("\n1. General Trip Report (All Trips)")
            print("2. Vehicle-Specific Trip Report")
            print("3. Individual Trip Receipt")
            print("4. Back to Main Menu")
            
            choice = input("\nSelect option (1-4): ")
            
            if choice == '1':
                receipt = self.generator.generate_trip_receipt()
                self._display_receipt(receipt, "General Trip Report")
            
            elif choice == '2':
                vehicles = Vehicle.objects.all()
                if not vehicles:
                    print("❌ No vehicles found.")
                    continue
                
                print("\nAvailable vehicles:")
                for i, vehicle in enumerate(vehicles, 1):
                    print(f"{i}. {vehicle.registration_number} - {vehicle.make} {vehicle.model}")
                
                try:
                    vehicle_choice = int(input("Select vehicle (number): ")) - 1
                    vehicle = vehicles[vehicle_choice]
                    receipt = self.generator.generate_trip_receipt(vehicle=vehicle)
                    self._display_receipt(receipt, f"Trip Report - {vehicle.registration_number}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '3':
                trips = Trip.objects.all()[:10]
                if not trips:
                    print("❌ No trips found.")
                    continue
                
                print("\nRecent trips:")
                for i, trip in enumerate(trips, 1):
                    print(f"{i}. {trip.trip_number} - {trip.origin} to {trip.destination}")
                
                try:
                    trip_choice = int(input("Select trip (number): ")) - 1
                    trip = trips[trip_choice]
                    receipt = self.generator.generate_trip_receipt(trip=trip)
                    self._display_receipt(receipt, f"Trip Receipt - {trip.trip_number}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice.")
    
    def print_maintenance_receipts(self):
        """Print maintenance receipts - both general and per vehicle"""
        print("\n🔧 MAINTENANCE RECEIPTS")
        print("-" * 30)
        
        while True:
            print("\n1. General Maintenance Report (All Maintenance)")
            print("2. Vehicle-Specific Maintenance Report")
            print("3. Individual Maintenance Receipt")
            print("4. Back to Main Menu")
            
            choice = input("\nSelect option (1-4): ")
            
            if choice == '1':
                receipt = self.generator.generate_maintenance_receipt()
                self._display_receipt(receipt, "General Maintenance Report")
            
            elif choice == '2':
                vehicles = Vehicle.objects.all()
                if not vehicles:
                    print("❌ No vehicles found.")
                    continue
                
                print("\nAvailable vehicles:")
                for i, vehicle in enumerate(vehicles, 1):
                    print(f"{i}. {vehicle.registration_number} - {vehicle.make} {vehicle.model}")
                
                try:
                    vehicle_choice = int(input("Select vehicle (number): ")) - 1
                    vehicle = vehicles[vehicle_choice]
                    receipt = self.generator.generate_maintenance_receipt(vehicle=vehicle)
                    self._display_receipt(receipt, f"Maintenance Report - {vehicle.registration_number}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '3':
                maintenances = VehicleMaintenance.objects.all()[:10]
                if not maintenances:
                    print("❌ No maintenance records found.")
                    continue
                
                print("\nRecent maintenance records:")
                for i, maintenance in enumerate(maintenances, 1):
                    print(f"{i}. {maintenance.maintenance_number} - {maintenance.vehicle.registration_number}")
                
                try:
                    maintenance_choice = int(input("Select maintenance (number): ")) - 1
                    maintenance = maintenances[maintenance_choice]
                    receipt = self.generator.generate_maintenance_receipt(maintenance=maintenance)
                    self._display_receipt(receipt, f"Maintenance Receipt - {maintenance.maintenance_number}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice.")
    
    def print_stock_receipts(self):
        """Print stock receipts - both general and per branch"""
        print("\n📦 STOCK RECEIPTS")
        print("-" * 30)
        
        while True:
            print("\n1. General Stock Report (All Branches)")
            print("2. Branch-Specific Stock Report")
            print("3. Individual Stock Item Report")
            print("4. Back to Main Menu")
            
            choice = input("\nSelect option (1-4): ")
            
            if choice == '1':
                receipt = self.generator.generate_stock_receipt()
                self._display_receipt(receipt, "General Stock Report")
            
            elif choice == '2':
                branches = Branch.objects.all()
                if not branches:
                    print("❌ No branches found.")
                    continue
                
                print("\nAvailable branches:")
                for i, branch in enumerate(branches, 1):
                    print(f"{i}. {branch.name}")
                
                try:
                    branch_choice = int(input("Select branch (number): ")) - 1
                    branch = branches[branch_choice]
                    receipt = self.generator.generate_stock_receipt(branch=branch)
                    self._display_receipt(receipt, f"Stock Report - {branch.name}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '3':
                stocks = Stock.objects.all()[:20]
                if not stocks:
                    print("❌ No stock items found.")
                    continue
                
                print("\nStock items:")
                for i, stock in enumerate(stocks, 1):
                    print(f"{i}. {stock.product.name} @ {stock.branch.name} - Qty: {stock.quantity}")
                
                try:
                    stock_choice = int(input("Select stock item (number): ")) - 1
                    stock = stocks[stock_choice]
                    receipt = self.generator.generate_stock_receipt(stock=stock)
                    self._display_receipt(receipt, f"Stock Report - {stock.product.name}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice.")
    
    def print_expense_receipts(self):
        """Print expense receipts - both general and per department"""
        print("\n💰 EXPENSE RECEIPTS")
        print("-" * 30)
        
        while True:
            print("\n1. General Expense Report (All Departments)")
            print("2. Department-Specific Expense Report")
            print("3. Individual Expense Receipt")
            print("4. Back to Main Menu")
            
            choice = input("\nSelect option (1-4): ")
            
            if choice == '1':
                receipt = self.generator.generate_expense_receipt()
                self._display_receipt(receipt, "General Expense Report")
            
            elif choice == '2':
                departments = Branch.objects.all()
                if not departments:
                    print("❌ No departments found.")
                    continue
                
                print("\nAvailable departments:")
                for i, dept in enumerate(departments, 1):
                    print(f"{i}. {dept.name}")
                
                try:
                    dept_choice = int(input("Select department (number): ")) - 1
                    department = departments[dept_choice].name
                    receipt = self.generator.generate_expense_receipt(department=department)
                    self._display_receipt(receipt, f"Expense Report - {department}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '3':
                expenses = Expense.objects.all()[:10]
                if not expenses:
                    print("❌ No expenses found.")
                    continue
                
                print("\nRecent expenses:")
                for i, expense in enumerate(expenses, 1):
                    print(f"{i}. {expense.expense_number} - {expense.description[:50]}")
                
                try:
                    expense_choice = int(input("Select expense (number): ")) - 1
                    expense = expenses[expense_choice]
                    receipt = self.generator.generate_expense_receipt(expense=expense)
                    self._display_receipt(receipt, f"Expense Receipt - {expense.expense_number}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice.")
    
    def print_notes_receipts(self):
        """Print notes receipts"""
        print("\n📝 NOTES RECEIPTS")
        print("-" * 30)
        
        while True:
            print("\n1. All Business Notes Report")
            print("2. Individual Note Receipt")
            print("3. Back to Main Menu")
            
            choice = input("\nSelect option (1-3): ")
            
            if choice == '1':
                receipt = self.generator.generate_notes_receipt()
                self._display_receipt(receipt, "Business Notes Report")
            
            elif choice == '2':
                notes = BusinessNote.objects.all()[:10]
                if not notes:
                    print("❌ No notes found.")
                    continue
                
                print("\nBusiness notes:")
                for i, note in enumerate(notes, 1):
                    content_preview = note.content[:50] + "..." if len(note.content) > 50 else note.content
                    print(f"{i}. Page {note.page_number} - {content_preview}")
                
                try:
                    note_choice = int(input("Select note (number): ")) - 1
                    note = notes[note_choice]
                    receipt = self.generator.generate_notes_receipt(note=note)
                    self._display_receipt(receipt, f"Note Receipt - Page {note.page_number}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == '3':
                break
            else:
                print("❌ Invalid choice.")
    
    def print_sales_receipts_with_expenses(self):
        """Print sales receipts with related expenses"""
        print("\n🛒 SALES RECEIPTS WITH EXPENSES")
        print("-" * 40)
        
        sales = Sale.objects.all()[:10]
        if not sales:
            print("❌ No sales found.")
            return
        
        print("\nRecent sales:")
        for i, sale in enumerate(sales, 1):
            expense_count = sale.expenses.count()
            print(f"{i}. {sale.sale_number} - {sale.customer_name or 'Walk-in'} - Expenses: {expense_count}")
        
        try:
            sale_choice = int(input("Select sale (number): ")) - 1
            sale = sales[sale_choice]
            receipt = self.generator.generate_sale_receipt(sale)
            self._display_receipt(receipt, f"Sales Receipt with Expenses - {sale.sale_number}")
        except (ValueError, IndexError):
            print("❌ Invalid selection.")
    
    def _display_receipt(self, receipt_html, title):
        """Display receipt information"""
        print(f"\n✅ {title} generated successfully!")
        print("📄 Receipt contains:")
        
        # Extract key information from HTML (basic parsing)
        if "KabisaKabisa" in receipt_html:
            print("   ✓ Company information updated")
        if "+254762548428" in receipt_html:
            print("   ✓ Phone number updated")
        if "Waren Odhiambo" in receipt_html:
            print("   ✓ Auditor information included")
        
        # Count items in receipt
        item_count = receipt_html.count('<tr>') - 2  # Subtract header and total rows
        if item_count > 0:
            print(f"   ✓ {item_count} items listed")
        
        print(f"   ✓ Receipt ready for printing/PDF export")
        
        save_choice = input("\nSave receipt to file? (y/n): ")
        if save_choice.lower() == 'y':
            filename = f"receipt_{title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w') as f:
                f.write(receipt_html)
            print(f"✅ Receipt saved as {filename}")
    
    def run(self):
        """Main interface loop"""
        while True:
            print("\n" + "=" * 60)
            print("KABISAKABISA RECEIPT MANAGEMENT SYSTEM")
            print("=" * 60)
            print("1. Trip Receipts (General & Per Vehicle)")
            print("2. Maintenance Receipts (General & Per Vehicle)")
            print("3. Stock Receipts (General & Per Branch)")
            print("4. Expense Receipts (General & Per Department)")
            print("5. Notes Receipts")
            print("6. Sales Receipts with Expenses")
            print("7. Exit")
            
            try:
                choice = input("\nSelect option (1-7): ")
                
                if choice == '1':
                    self.print_trip_receipts()
                elif choice == '2':
                    self.print_maintenance_receipts()
                elif choice == '3':
                    self.print_stock_receipts()
                elif choice == '4':
                    self.print_expense_receipts()
                elif choice == '5':
                    self.print_notes_receipts()
                elif choice == '6':
                    self.print_sales_receipts_with_expenses()
                elif choice == '7':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-7.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    manager = ReceiptManager()
    manager.run()