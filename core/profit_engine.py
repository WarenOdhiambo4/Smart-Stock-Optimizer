"""
Advanced Profit Calculation Engine
Implements proper profit calculation based on:
1. Average selling price per product per month
2. Weighted average purchase price
3. Stock turnover analysis
4. Broken products tracking
5. Expense allocation
"""

import pandas as pd
from django.db.models import Sum, Avg, Count, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from calendar import monthrange

from .models import (
    Sale, SaleItem, Stock, Product, Branch, Expense, 
    BrokenProduct, MonthlyProfitAnalysis, StockBatch
)


class ProfitCalculationEngine:
    """
    Enterprise-grade profit calculation engine
    Calculates true profitability considering all factors
    """
    
    def __init__(self, branch=None, month=None):
        self.branch = branch
        self.month = month or timezone.now().date().replace(day=1)
        self.month_end = self._get_month_end(self.month)
    
    def _get_month_end(self, month_start):
        """Get last day of the month"""
        year = month_start.year
        month = month_start.month
        last_day = monthrange(year, month)[1]
        return month_start.replace(day=last_day)
    
    def calculate_monthly_profit_analysis(self):
        """
        Calculate comprehensive monthly profit analysis
        Returns profit data per product per branch
        """
        # Get all products that had activity this month
        products_with_sales = Product.objects.filter(
            stocks__items__sale__created_at__date__range=[self.month, self.month_end]
        ).distinct()
        
        if self.branch:
            products_with_sales = products_with_sales.filter(stocks__branch=self.branch)
        
        results = []
        
        for product in products_with_sales:
            branches = [self.branch] if self.branch else Branch.objects.filter(
                stocks__product=product,
                stocks__items__sale__created_at__date__range=[self.month, self.month_end]
            ).distinct()
            
            for branch in branches:
                analysis = self._calculate_product_branch_profit(product, branch)
                if analysis:
                    results.append(analysis)
        
        return results
    
    def _calculate_product_branch_profit(self, product, branch):
        """Calculate profit for specific product at specific branch"""
        try:
            stock = Stock.objects.get(product=product, branch=branch)
        except Stock.DoesNotExist:
            return None
        
        # Get or create monthly analysis record
        analysis, created = MonthlyProfitAnalysis.objects.get_or_create(
            branch=branch,
            product=product,
            month=self.month,
            defaults={
                'opening_stock': stock.quantity,  # Current stock as opening
                'closing_stock': stock.quantity
            }
        )
        
        # Calculate sales data for this month
        sales_data = self._get_monthly_sales_data(stock)
        
        # Calculate purchase data
        purchase_data = self._get_monthly_purchase_data(stock)
        
        # Calculate broken products
        broken_data = self._get_monthly_broken_data(stock)
        
        # Calculate allocated expenses
        allocated_expenses = self._calculate_allocated_expenses(stock, sales_data['total_revenue'])
        
        # Update analysis record
        analysis.total_quantity_sold = sales_data['quantity_sold']
        analysis.total_revenue = sales_data['total_revenue']
        analysis.average_selling_price = sales_data['avg_selling_price']
        
        analysis.weighted_avg_purchase_price = purchase_data['avg_purchase_price']
        analysis.total_purchase_cost = purchase_data['total_cost']
        
        analysis.broken_quantity = broken_data['quantity']
        analysis.broken_cost = broken_data['cost']
        
        analysis.allocated_expenses = allocated_expenses
        analysis.closing_stock = stock.quantity
        
        # Calculate profit metrics
        analysis.calculate_profit()
        
        return {
            'product': product,
            'branch': branch,
            'analysis': analysis,
            'is_profitable': analysis.net_profit > 0,
            'is_loss_making': analysis.net_profit < 0,
            'turnover_healthy': analysis.stock_turnover_ratio > 1.0
        }
    
    def _get_monthly_sales_data(self, stock):
        """Get sales data for the month"""
        sale_items = SaleItem.objects.filter(
            stock=stock,
            sale__created_at__date__range=[self.month, self.month_end]
        )
        
        if not sale_items.exists():
            return {
                'quantity_sold': 0,
                'total_revenue': Decimal('0.00'),
                'avg_selling_price': Decimal('0.00')
            }
        
        # Calculate average selling price (different prices throughout month)
        total_quantity = sale_items.aggregate(total=Sum('quantity'))['total'] or 0
        total_revenue = sale_items.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or Decimal('0.00')
        
        avg_selling_price = total_revenue / total_quantity if total_quantity > 0 else Decimal('0.00')
        
        return {
            'quantity_sold': total_quantity,
            'total_revenue': total_revenue,
            'avg_selling_price': avg_selling_price
        }
    
    def _get_monthly_purchase_data(self, stock):
        """Get purchase cost data using weighted average"""
        # Use current weighted average purchase price
        avg_purchase_price = stock.weighted_avg_purchase_price
        
        # Calculate total cost for items sold this month
        quantity_sold = SaleItem.objects.filter(
            stock=stock,
            sale__created_at__date__range=[self.month, self.month_end]
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        total_cost = quantity_sold * avg_purchase_price
        
        return {
            'avg_purchase_price': avg_purchase_price,
            'total_cost': total_cost
        }
    
    def _get_monthly_broken_data(self, stock):
        """Get broken products data for the month"""
        broken_items = BrokenProduct.objects.filter(
            stock=stock,
            reported_date__date__range=[self.month, self.month_end]
        )
        
        total_quantity = broken_items.aggregate(total=Sum('quantity'))['total'] or 0
        total_cost = broken_items.aggregate(total=Sum('total_loss'))['total'] or Decimal('0.00')
        
        return {
            'quantity': total_quantity,
            'cost': total_cost
        }
    
    def _calculate_allocated_expenses(self, stock, revenue):
        """
        Allocate branch expenses to this product based on revenue contribution
        """
        # Get total branch revenue for the month
        total_branch_revenue = Sale.objects.filter(
            branch=stock.branch,
            created_at__date__range=[self.month, self.month_end]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        if total_branch_revenue == 0:
            return Decimal('0.00')
        
        # Get total branch expenses for the month
        total_branch_expenses = Expense.objects.filter(
            branch=stock.branch,
            expense_date__range=[self.month, self.month_end],
            expense_type__in=['OPERATIONAL', 'UTILITIES', 'RENT', 'SALARY']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Allocate expenses proportionally based on revenue contribution
        revenue_percentage = revenue / total_branch_revenue if total_branch_revenue > 0 else Decimal('0.00')
        allocated_expenses = total_branch_expenses * revenue_percentage
        
        return allocated_expenses
    
    def get_loss_making_products(self):
        """Identify products that are making losses"""
        loss_making = MonthlyProfitAnalysis.objects.filter(
            month=self.month,
            net_profit__lt=0
        )
        
        if self.branch:
            loss_making = loss_making.filter(branch=self.branch)
        
        return loss_making.select_related('product', 'branch').order_by('net_profit')
    
    def get_most_profitable_products(self, limit=10):
        """Get most profitable products"""
        profitable = MonthlyProfitAnalysis.objects.filter(
            month=self.month,
            net_profit__gt=0
        )
        
        if self.branch:
            profitable = profitable.filter(branch=self.branch)
        
        return profitable.select_related('product', 'branch').order_by('-net_profit')[:limit]
    
    def get_slow_moving_stock(self):
        """Identify slow-moving stock (low turnover ratio)"""
        slow_moving = MonthlyProfitAnalysis.objects.filter(
            month=self.month,
            stock_turnover_ratio__lt=1.0,
            stock_turnover_ratio__gt=0
        )
        
        if self.branch:
            slow_moving = slow_moving.filter(branch=self.branch)
        
        return slow_moving.select_related('product', 'branch').order_by('stock_turnover_ratio')
    
    def generate_profit_summary(self):
        """Generate comprehensive profit summary"""
        analyses = MonthlyProfitAnalysis.objects.filter(month=self.month)
        
        if self.branch:
            analyses = analyses.filter(branch=self.branch)
        
        if not analyses.exists():
            return {
                'message': 'No profit data available for this period'
            }
        
        # Aggregate metrics
        total_revenue = analyses.aggregate(total=Sum('total_revenue'))['total'] or Decimal('0.00')
        total_gross_profit = analyses.aggregate(total=Sum('gross_profit'))['total'] or Decimal('0.00')
        total_net_profit = analyses.aggregate(total=Sum('net_profit'))['total'] or Decimal('0.00')
        total_losses = analyses.aggregate(total=Sum('broken_cost'))['total'] or Decimal('0.00')
        
        # Count products
        profitable_products = analyses.filter(net_profit__gt=0).count()
        loss_making_products = analyses.filter(net_profit__lt=0).count()
        total_products = analyses.count()
        
        # Calculate margins
        gross_margin = (total_gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
        net_margin = (total_net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
        
        # Average turnover
        avg_turnover = analyses.aggregate(avg=Avg('stock_turnover_ratio'))['avg'] or Decimal('0.00')
        
        return {
            'period': f"{self.month.strftime('%B %Y')}",
            'branch': self.branch.name if self.branch else 'All Branches',
            'financial_metrics': {
                'total_revenue': float(total_revenue),
                'total_gross_profit': float(total_gross_profit),
                'total_net_profit': float(total_net_profit),
                'total_losses': float(total_losses),
                'gross_margin': float(gross_margin),
                'net_margin': float(net_margin)
            },
            'product_metrics': {
                'total_products': total_products,
                'profitable_products': profitable_products,
                'loss_making_products': loss_making_products,
                'profitability_rate': (profitable_products / total_products * 100) if total_products > 0 else 0
            },
            'operational_metrics': {
                'average_stock_turnover': float(avg_turnover),
                'turnover_health': 'Good' if avg_turnover > 2 else 'Moderate' if avg_turnover > 1 else 'Poor'
            }
        }
    
    def update_stock_purchase_price(self, stock, quantity, unit_price, order=None):
        """Update stock with new purchase - maintains weighted average price"""
        # Create batch record
        batch_number = f"BATCH-{order.order_number if order else timezone.now().strftime('%Y%m%d%H%M%S')}"
        StockBatch.objects.create(
            stock=stock,
            batch_number=batch_number,
            quantity=quantity,
            unit_purchase_price=unit_price,
            order=order
        )
        
        # Update weighted average purchase price
        stock.update_purchase_price(quantity, unit_price)
        
        return stock


def generate_monthly_profit_reports():
    """
    Management command function to generate monthly profit reports
    Should be run at the end of each month
    """
    current_month = timezone.now().date().replace(day=1)
    
    # Generate reports for all branches
    branches = Branch.objects.filter(is_active=True)
    
    for branch in branches:
        engine = ProfitCalculationEngine(branch=branch, month=current_month)
        engine.calculate_monthly_profit_analysis()
    
    print(f"Monthly profit analysis completed for {current_month.strftime('%B %Y')}")


def identify_problem_products(branch=None, months_back=3):
    """
    Identify products that have been consistently loss-making
    """
    end_month = timezone.now().date().replace(day=1)
    start_month = end_month - timedelta(days=months_back * 30)
    start_month = start_month.replace(day=1)
    
    # Get products that have been loss-making for multiple months
    problem_products = MonthlyProfitAnalysis.objects.filter(
        month__gte=start_month,
        month__lte=end_month,
        net_profit__lt=0
    )
    
    if branch:
        problem_products = problem_products.filter(branch=branch)
    
    # Group by product and count loss-making months
    product_losses = {}
    for analysis in problem_products:
        key = f"{analysis.product.id}_{analysis.branch.id}"
        if key not in product_losses:
            product_losses[key] = {
                'product': analysis.product,
                'branch': analysis.branch,
                'loss_months': 0,
                'total_loss': Decimal('0.00')
            }
        product_losses[key]['loss_months'] += 1
        product_losses[key]['total_loss'] += analysis.net_profit
    
    # Filter products with consistent losses
    consistent_losers = [
        data for data in product_losses.values() 
        if data['loss_months'] >= months_back - 1  # Allow 1 month margin
    ]
    
    return sorted(consistent_losers, key=lambda x: x['total_loss'])