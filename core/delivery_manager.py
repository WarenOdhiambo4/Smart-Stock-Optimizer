from decimal import Decimal
from django.db.models import Sum
from .models import Expense


class DeliveryChargesManager:
    """Manage delivery charges as expenses without database schema changes"""
    
    @staticmethod
    def get_delivery_charges(order):
        """Get delivery charges for an order"""
        expense = Expense.objects.filter(
            expense_number=f"DEL-{order.order_number}",
            expense_type='DELIVERY'
        ).first()
        return expense.amount if expense else Decimal('0.00')
    
    @staticmethod
    def set_delivery_charges(order, amount, created_by=None):
        """Set delivery charges for an order"""
        expense = Expense.objects.filter(
            expense_number=f"DEL-{order.order_number}",
            expense_type='DELIVERY'
        ).first()
        
        if amount > 0:
            if expense:
                # Update existing expense
                expense.amount = amount
                expense.notes = f"Updated delivery expense for order to {order.supplier}. Order: {order.order_number}"
                expense.save()
            else:
                # Create new delivery expense
                Expense.objects.create(
                    expense_number=f"DEL-{order.order_number}",
                    branch=order.branch,
                    expense_type='DELIVERY',
                    description=f"Delivery charges for Order #{order.order_number}",
                    amount=amount,
                    expense_date=order.created_at.date(),
                    notes=f"Delivery expense for order to {order.supplier}. Order: {order.order_number}",
                    created_by=created_by
                )
        elif expense:
            # Remove delivery expense if amount is 0
            expense.delete()
    
    @staticmethod
    def get_total_delivery_expenses(start_date=None, end_date=None):
        """Get total delivery expenses for a period"""
        expenses = Expense.objects.filter(expense_type='DELIVERY')
        if start_date:
            expenses = expenses.filter(expense_date__gte=start_date)
        if end_date:
            expenses = expenses.filter(expense_date__lte=end_date)
        return expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')