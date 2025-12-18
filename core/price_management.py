"""
Enterprise Price Management System
Handles price changes with audit trails, inventory valuation, and background processing
"""
import pandas as pd
import numpy as np
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from celery import shared_task
from .models import Product, Stock, PriceChangeLog
from sklearn.linear_model import LinearRegression


class PriceManager:
    """Enterprise-grade price management with audit trails"""
    
    @staticmethod
    def change_product_price(product_id, new_price, changed_by, reason=""):
        """
        Safely change product price with full audit trail
        """
        with transaction.atomic():
            product = Product.objects.get(id=product_id)
            old_price = product.unit_price
            
            # Update price (history automatically tracked by django-simple-history)
            product.unit_price = Decimal(str(new_price))
            product.save()
            
            # Log the change
            PriceChangeLog.objects.create(
                product=product,
                old_price=old_price,
                new_price=new_price,
                changed_by=changed_by,
                reason=reason,
                change_date=timezone.now()
            )
            
            # Update inventory valuations in background
            update_inventory_valuations.delay(product_id)
            
            return True
    
    @staticmethod
    def bulk_price_update(price_changes, changed_by, reason="Bulk Update"):
        """
        Update multiple product prices efficiently
        price_changes: [{'product_id': 1, 'new_price': 100}, ...]
        """
        # Process in background to avoid timeout
        bulk_update_prices.delay(price_changes, changed_by.id, reason)
        return True
    
    @staticmethod
    def calculate_weighted_average_cost(product_id):
        """
        Calculate WAC using pandas for performance
        """
        stocks = Stock.objects.filter(product_id=product_id).values(
            'quantity', 'weighted_avg_purchase_price'
        )
        
        if not stocks:
            return Decimal('0.00')
        
        df = pd.DataFrame(stocks)
        total_value = (df['quantity'] * df['weighted_avg_purchase_price']).sum()
        total_quantity = df['quantity'].sum()
        
        if total_quantity > 0:
            return Decimal(str(total_value / total_quantity))
        return Decimal('0.00')
    
    @staticmethod
    def analyze_price_elasticity(product_id, days=90):
        """
        Use scikit-learn to analyze price elasticity
        """
        from .models import Sale, SaleItem
        
        # Get sales data
        sales_data = SaleItem.objects.filter(
            stock__product_id=product_id,
            sale__created_at__gte=timezone.now() - timezone.timedelta(days=days)
        ).values('unit_price', 'quantity', 'sale__created_at')
        
        if len(sales_data) < 10:
            return {"error": "Insufficient data for analysis"}
        
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['sale__created_at'])
        
        # Group by price to get demand at each price point
        price_demand = df.groupby('unit_price')['quantity'].sum().reset_index()
        
        if len(price_demand) < 3:
            return {"error": "Need more price variation for analysis"}
        
        # Linear regression: log(quantity) = a + b*log(price)
        X = np.log(price_demand['unit_price'].values).reshape(-1, 1)
        y = np.log(price_demand['quantity'].values)
        
        model = LinearRegression()
        model.fit(X, y)
        
        elasticity = model.coef_[0]  # Price elasticity coefficient
        
        return {
            "elasticity": float(elasticity),
            "interpretation": "elastic" if elasticity < -1 else "inelastic",
            "recommendation": "Lower prices to increase revenue" if elasticity < -1 else "Can increase prices"
        }


@shared_task
def update_inventory_valuations(product_id):
    """
    Background task to update inventory valuations after price change
    """
    try:
        stocks = Stock.objects.filter(product_id=product_id)
        for stock in stocks:
            # Recalculate weighted average cost
            new_wac = PriceManager.calculate_weighted_average_cost(product_id)
            stock.weighted_avg_purchase_price = new_wac
            stock.save()
        return f"Updated {stocks.count()} stock records"
    except Exception as e:
        return f"Error: {str(e)}"


@shared_task
def bulk_update_prices(price_changes, changed_by_id, reason):
    """
    Background task for bulk price updates
    """
    from django.contrib.auth.models import User
    
    try:
        changed_by = User.objects.get(id=changed_by_id)
        updated_count = 0
        
        for change in price_changes:
            try:
                PriceManager.change_product_price(
                    change['product_id'],
                    change['new_price'],
                    changed_by,
                    reason
                )
                updated_count += 1
            except Exception as e:
                print(f"Failed to update product {change['product_id']}: {e}")
        
        return f"Successfully updated {updated_count} products"
    except Exception as e:
        return f"Bulk update failed: {str(e)}"


@shared_task
def optimize_pricing_strategy(product_id):
    """
    Use scipy.optimize to find optimal pricing
    """
    from scipy.optimize import minimize_scalar
    
    def profit_function(price):
        # Simplified profit calculation
        # In reality, you'd use historical data and demand curves
        elasticity_data = PriceManager.analyze_price_elasticity(product_id)
        if "error" in elasticity_data:
            return 0
        
        elasticity = elasticity_data["elasticity"]
        base_demand = 100  # Base demand at current price
        current_price = Product.objects.get(id=product_id).unit_price
        
        # Demand = base_demand * (price/current_price)^elasticity
        demand = base_demand * (price / float(current_price)) ** elasticity
        
        # Profit = (price - cost) * demand
        cost = 50  # Simplified cost
        profit = (price - cost) * demand
        
        return -profit  # Negative because minimize_scalar minimizes
    
    try:
        result = minimize_scalar(profit_function, bounds=(10, 1000), method='bounded')
        optimal_price = result.x
        
        return {
            "optimal_price": round(optimal_price, 2),
            "expected_profit": -result.fun,
            "current_price": float(Product.objects.get(id=product_id).unit_price)
        }
    except Exception as e:
        return {"error": str(e)}