import pandas as pd
import numpy as np
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Sale, Expense, Stock, Product, Branch
import json

class FinancialAnalytics:
    
    @staticmethod
    def get_revenue_metrics(branch_id=None, days=365):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        sales_qs = Sale.objects.filter(created_at__gte=start_date)
        if branch_id:
            sales_qs = sales_qs.filter(branch_id=branch_id)
        
        total_revenue = float(sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0)
        
        expenses_qs = Expense.objects.filter(expense_date__gte=start_date.date())
        if branch_id:
            expenses_qs = expenses_qs.filter(branch_id=branch_id)
        
        total_expenses = float(expenses_qs.aggregate(total=Sum('amount'))['total'] or 0)
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'profit_margin': profit_margin
        }
    
    @staticmethod
    def sales_forecast_data():
        # Get last 30 days of sales data
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        sales = Sale.objects.filter(created_at__gte=start_date).values('created_at__date').annotate(
            daily_sales=Sum('total_amount')
        ).order_by('created_at__date')
        
        if not sales:
            return []
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(list(sales))
        df['created_at__date'] = pd.to_datetime(df['created_at__date'])
        df['daily_sales'] = df['daily_sales'].astype(float)
        
        # Simple linear trend forecast for next 7 days
        forecast_data = []
        if len(df) >= 7:
            recent_trend = df['daily_sales'].tail(7).mean()
            growth_rate = 0.02  # 2% daily growth assumption
            
            for i in range(1, 8):
                forecast_date = end_date.date() + timedelta(days=i)
                predicted_sales = recent_trend * (1 + growth_rate) ** i
                confidence = max(0.6, 0.95 - (i * 0.05))  # Decreasing confidence
                
                forecast_data.append({
                    'period': forecast_date.strftime('%Y-%m-%d'),
                    'predicted_sales': round(predicted_sales, 2),
                    'confidence': round(confidence * 100, 1)
                })
        
        return forecast_data
    
    @staticmethod
    def risk_assessment():
        # Calculate basic risk metrics
        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)
        
        sales = Sale.objects.filter(created_at__gte=start_date)
        daily_sales = []
        
        for i in range(90):
            day = start_date + timedelta(days=i)
            day_sales = sales.filter(created_at__date=day.date()).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            daily_sales.append(float(day_sales))
        
        if daily_sales:
            df = pd.Series(daily_sales)
            mean_sales = df.mean()
            std_sales = df.std()
            
            # Value at Risk (95% confidence)
            var_95 = mean_sales - (1.645 * std_sales)
            
            # Risk level based on coefficient of variation
            cv = (std_sales / mean_sales) if mean_sales > 0 else 0
            
            if cv < 0.2:
                risk_level = "LOW"
            elif cv < 0.5:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            return {
                'var_95': round(var_95, 2),
                'volatility': round(cv * 100, 2),
                'risk_level': risk_level,
                'mean_daily_sales': round(mean_sales, 2)
            }
        
        return {
            'var_95': 0,
            'volatility': 0,
            'risk_level': 'UNKNOWN',
            'mean_daily_sales': 0
        }
    
    @staticmethod
    def inventory_analysis():
        stocks = Stock.objects.select_related('product').filter(quantity__gt=0)
        
        inventory_data = []
        for stock in stocks:
            # Simple EOQ calculation
            annual_demand = 1000  # Simplified assumption
            ordering_cost = 50
            holding_cost = float(stock.product.unit_price) * 0.2  # 20% of unit price
            
            if holding_cost > 0:
                eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
                reorder_point = max(10, int(eoq * 0.3))
            else:
                eoq = 100
                reorder_point = 10
            
            status = "Reorder" if stock.quantity <= reorder_point else "OK"
            
            inventory_data.append({
                'product': stock.product.name,
                'current_stock': stock.quantity,
                'reorder_point': reorder_point,
                'status': status,
                'eoq': round(eoq, 0)
            })
        
        return inventory_data[:10]  # Return top 10
    
    @staticmethod
    def route_optimization():
        # Simplified route analysis based on recent trips
        from .models import Trip
        
        trips = Trip.objects.filter(status='COMPLETED').select_related('vehicle')[:10]
        
        route_data = []
        for trip in trips:
            distance = float(trip.distance) if trip.distance else 0
            revenue = float(trip.revenue) if trip.revenue else 0
            expenses = float(trip.fuel_cost) + float(trip.other_expenses)
            
            profit = revenue - expenses
            efficiency = (profit / distance) if distance > 0 else 0
            
            route_data.append({
                'route': f"{trip.origin} → {trip.destination}",
                'distance': distance,
                'profit': round(profit, 2),
                'efficiency': round(efficiency, 2)
            })
        
        return route_data
    
    @staticmethod
    def get_chart_data():
        # Revenue trend for last 12 months
        end_date = timezone.now()
        months_data = []
        
        for i in range(12):
            month_start = end_date.replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            revenue = Sale.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            months_data.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': float(revenue)
            })
        
        return list(reversed(months_data))