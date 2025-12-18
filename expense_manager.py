#!/usr/bin/env python3
"""
Expense Management Interface
Demonstrates update and delete functionality for expenses
"""

import os
import django
import sys

# Setup Django
sys.path.append('/home/waren/Desktop/hp/Kabisa_enterprise_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import Expense, Branch, Employee
from decimal import Decimal
from datetime import date

class ExpenseManager:
    def __init__(self):
        print("🏢 Kabisa Enterprise ERP - Expense Manager")
        print("=" * 50)
    
    def list_expenses(self, limit=10):
        """List recent expenses"""
        expenses = Expense.objects.select_related('branch', 'sale').order_by('-expense_date')[:limit]
        
        if not expenses:
            print("No expenses found.")
            return
        
        print(f"\n📊 Recent Expenses (Last {limit}):")
        print("-" * 80)
        print(f"{'ID':<5} {'Number':<15} {'Type':<12} {'Amount':<10} {'Date':<12} {'Auto':<6}")
        print("-" * 80)
        
        for expense in expenses:
            is_auto = expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-'))
            print(f"{expense.id:<5} {expense.expense_number:<15} {expense.expense_type:<12} "
                  f"${expense.amount:<9} {expense.expense_date} {'Yes' if is_auto else 'No':<6}")
    
    def create_expense(self):
        """Create a new expense"""
        print("\n➕ Create New Expense")
        print("-" * 30)
        
        try:
            # Get branches
            branches = Branch.objects.all()
            if not branches:
                print("❌ No branches found. Please create a branch first.")
                return
            
            print("Available branches:")
            for i, branch in enumerate(branches, 1):
                print(f"{i}. {branch.name}")
            
            branch_choice = int(input("Select branch (number): ")) - 1
            branch = branches[branch_choice]
            
            # Get expense details
            expense_number = input("Expense number: ")
            expense_type = input("Expense type (OPERATIONAL/TRANSPORT/UTILITIES/OTHER): ").upper()
            description = input("Description: ")
            amount = Decimal(input("Amount: "))
            expense_date = input("Date (YYYY-MM-DD) or press Enter for today: ")
            
            if not expense_date:
                expense_date = date.today()
            
            # Create expense
            expense = Expense.objects.create(
                expense_number=expense_number,
                branch=branch,
                expense_type=expense_type,
                description=description,
                amount=amount,
                expense_date=expense_date
            )
            
            print(f"✅ Expense created successfully: {expense.expense_number}")
            
        except Exception as e:
            print(f"❌ Error creating expense: {e}")
    
    def update_expense(self):
        """Update an existing expense"""
        print("\n✏️ Update Expense")
        print("-" * 20)
        
        try:
            expense_id = int(input("Enter expense ID to update: "))
            expense = Expense.objects.get(id=expense_id)
            
            # Check if auto-generated
            if expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
                print("❌ Cannot update auto-generated expenses")
                return
            
            print(f"Current expense: {expense.expense_number}")
            print(f"Current description: {expense.description}")
            print(f"Current amount: ${expense.amount}")
            
            # Get updates
            new_description = input(f"New description (current: {expense.description}): ")
            new_amount = input(f"New amount (current: {expense.amount}): ")
            
            # Apply updates
            if new_description:
                expense.description = new_description
            
            if new_amount:
                expense.amount = Decimal(new_amount)
            
            expense.save()
            print(f"✅ Expense updated successfully: {expense.expense_number}")
            
        except Expense.DoesNotExist:
            print("❌ Expense not found")
        except Exception as e:
            print(f"❌ Error updating expense: {e}")
    
    def delete_expense(self):
        """Delete an expense"""
        print("\n🗑️ Delete Expense")
        print("-" * 18)
        
        try:
            expense_id = int(input("Enter expense ID to delete: "))
            expense = Expense.objects.get(id=expense_id)
            
            # Check if auto-generated
            if expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
                print("❌ Cannot delete auto-generated expenses")
                return
            
            print(f"Expense to delete: {expense.expense_number}")
            print(f"Description: {expense.description}")
            print(f"Amount: ${expense.amount}")
            
            confirm = input("Are you sure you want to delete this expense? (yes/no): ")
            
            if confirm.lower() == 'yes':
                expense_number = expense.expense_number
                expense.delete()
                print(f"✅ Expense deleted successfully: {expense_number}")
            else:
                print("❌ Deletion cancelled")
                
        except Expense.DoesNotExist:
            print("❌ Expense not found")
        except Exception as e:
            print(f"❌ Error deleting expense: {e}")
    
    def expense_summary(self):
        """Show expense summary"""
        print("\n📈 Expense Summary")
        print("-" * 20)
        
        from django.db.models import Sum, Count
        
        # Total expenses
        total = Expense.objects.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id')
        )
        
        print(f"Total Expenses: {total['total_count']}")
        print(f"Total Amount: ${total['total_amount'] or 0}")
        
        # By type
        print("\nBy Type:")
        by_type = Expense.objects.values('expense_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        for item in by_type:
            print(f"  {item['expense_type']}: ${item['total']} ({item['count']} expenses)")
        
        # Auto-generated vs Manual
        auto_count = Expense.objects.filter(
            expense_number__startswith='TRIP-'
        ).count() + Expense.objects.filter(
            expense_number__startswith='MAINT-'
        ).count() + Expense.objects.filter(
            expense_number__startswith='LOSS-'
        ).count()
        
        manual_count = total['total_count'] - auto_count
        
        print(f"\nAuto-generated: {auto_count}")
        print(f"Manual: {manual_count}")
    
    def run(self):
        """Main interface loop"""
        while True:
            print("\n" + "=" * 50)
            print("EXPENSE MANAGEMENT MENU")
            print("=" * 50)
            print("1. List Expenses")
            print("2. Create Expense")
            print("3. Update Expense")
            print("4. Delete Expense")
            print("5. Expense Summary")
            print("6. Exit")
            
            try:
                choice = input("\nSelect option (1-6): ")
                
                if choice == '1':
                    self.list_expenses()
                elif choice == '2':
                    self.create_expense()
                elif choice == '3':
                    self.update_expense()
                elif choice == '4':
                    self.delete_expense()
                elif choice == '5':
                    self.expense_summary()
                elif choice == '6':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    manager = ExpenseManager()
    manager.run()