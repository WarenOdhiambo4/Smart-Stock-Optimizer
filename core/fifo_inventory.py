from django.db import models
from decimal import Decimal
from collections import deque

class InventoryLayer(models.Model):
    """Track inventory layers for FIFO costing"""
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, related_name='layers')
    quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    source_type = models.CharField(max_length=20, choices=[
        ('ORDER', 'From Order'),
        ('MANUAL', 'Manual Stock Addition'),
        ('TRANSFER', 'Stock Transfer')
    ])
    source_id = models.PositiveIntegerField(null=True, blank=True)  # Order ID or other source
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']  # FIFO ordering
    
    def __str__(self):
        return f"{self.stock.product.name} - {self.remaining_quantity}/{self.quantity} @ {self.unit_cost}"

class FIFOInventoryManager:
    """Manages FIFO inventory costing calculations"""
    
    @staticmethod
    def add_inventory_layer(stock, quantity, unit_cost, source_type, source_id=None):
        """Add new inventory layer when stock is received"""
        return InventoryLayer.objects.create(
            stock=stock,
            quantity=quantity,
            remaining_quantity=quantity,
            unit_cost=unit_cost,
            source_type=source_type,
            source_id=source_id
        )
    
    @staticmethod
    def calculate_fifo_cost(stock, quantity_sold):
        """Calculate FIFO cost for sold quantity"""
        layers = stock.layers.filter(remaining_quantity__gt=0).order_by('created_at')
        
        total_cost = Decimal('0.00')
        remaining_to_sell = quantity_sold
        
        for layer in layers:
            if remaining_to_sell <= 0:
                break
                
            quantity_from_layer = min(layer.remaining_quantity, remaining_to_sell)
            cost_from_layer = quantity_from_layer * layer.unit_cost
            
            total_cost += cost_from_layer
            remaining_to_sell -= quantity_from_layer
            
            # Update layer remaining quantity
            layer.remaining_quantity -= quantity_from_layer
            layer.save()
        
        return total_cost
    
    @staticmethod
    def get_current_average_cost(stock):
        """Get weighted average cost of current inventory"""
        layers = stock.layers.filter(remaining_quantity__gt=0)
        
        total_value = Decimal('0.00')
        total_quantity = 0
        
        for layer in layers:
            total_value += layer.remaining_quantity * layer.unit_cost
            total_quantity += layer.remaining_quantity
        
        if total_quantity > 0:
            return total_value / total_quantity
        return stock.product.cost_price  # Fallback to product cost price
    
    @staticmethod
    def process_order_completion(order_item, completion_branch):
        """Process order completion and add inventory layers"""
        from .models import Stock, Product
        
        # Get or create stock for the product at completion branch
        try:
            product = Product.objects.get(name=order_item.product_name)
        except Product.DoesNotExist:
            # Create product if it doesn't exist
            product = Product.objects.create(
                name=order_item.product_name,
                sku=order_item.product_sku or '',
                unit_price=order_item.unit_price,
                cost_price=order_item.unit_price * Decimal('0.8')  # Assume 80% cost ratio
            )
        
        stock, created = Stock.objects.get_or_create(
            branch=completion_branch,
            product=product,
            defaults={'quantity': 0, 'min_quantity': 10}
        )
        
        # Add inventory layer from order
        FIFOInventoryManager.add_inventory_layer(
            stock=stock,
            quantity=order_item.quantity_remaining,
            unit_cost=order_item.unit_price,  # Use order unit price as cost
            source_type='ORDER',
            source_id=order_item.order.id
        )
        
        # Update stock quantity
        stock.quantity += order_item.quantity_remaining
        stock.save()
    
    @staticmethod
    def process_manual_stock_addition(stock, quantity, unit_cost=None):
        """Process manual stock addition"""
        if unit_cost is None:
            unit_cost = stock.product.cost_price
        
        FIFOInventoryManager.add_inventory_layer(
            stock=stock,
            quantity=quantity,
            unit_cost=unit_cost,
            source_type='MANUAL'
        )
    
    @staticmethod
    def calculate_gross_profit_fifo(branch, date_filter):
        """Calculate gross profit using FIFO costing"""
        from .models import Sale
        
        sales = Sale.objects.filter(branch=branch).filter(date_filter)
        product_stats = {}
        
        # Step 1: Calculate average selling price per product
        for sale in sales:
            for item in sale.items.all():
                product_id = item.stock.product.id
                if product_id not in product_stats:
                    product_stats[product_id] = {
                        'total_revenue': Decimal('0.00'),
                        'total_quantity': 0,
                        'total_fifo_cost': Decimal('0.00'),
                        'stock': item.stock
                    }
                
                # Calculate FIFO cost for this sale item
                fifo_cost = FIFOInventoryManager.calculate_fifo_cost(
                    item.stock, 
                    item.quantity
                )
                
                product_stats[product_id]['total_revenue'] += item.unit_price * item.quantity
                product_stats[product_id]['total_quantity'] += item.quantity
                product_stats[product_id]['total_fifo_cost'] += fifo_cost
        
        # Step 2: Calculate gross profit
        total_gross_profit = Decimal('0.00')
        for product_id, stats in product_stats.items():
            if stats['total_quantity'] > 0:
                product_gross_profit = stats['total_revenue'] - stats['total_fifo_cost']
                total_gross_profit += product_gross_profit
        
        return total_gross_profit