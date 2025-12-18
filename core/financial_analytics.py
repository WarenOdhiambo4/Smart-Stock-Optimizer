"""
Modern Financial Analytics Engine
Enterprise-grade algorithms for Fortune 500 level insights
"""
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json

from .models import Sale, Expense, Stock, Product, Branch, Trip, SaleItem


class FinancialAnalytics:
    """Enterprise Financial Analytics Engine"""
    
    @staticmethod
    def get_dashboard_data(branch_id=None, days=365):
        """Get comprehensive dashboard analytics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Calculate correct net profit
        profit_data = FinancialAnalytics.calculate_correct_net_profit(branch_id, start_date, end_date)
        
        total_revenue = profit_data['total_revenue']
        net_profit = profit_data['net_profit']
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Risk assessment
        risk_data = FinancialAnalytics.calculate_risk_metrics(branch_id, days)
        
        # Sales forecast
        forecast_data = FinancialAnalytics.generate_sales_forecast(branch_id)
        
        # Inventory optimization
        inventory_data = FinancialAnalytics.optimize_inventory(branch_id)
        
        # Route optimization
        route_data = FinancialAnalytics.optimize_routes(branch_id, days)
        
        return {
            'profitability': {
                'total_revenue': float(total_revenue),
                'total_expenses': float(profit_data['total_expenses']),
                'gross_profit': float(profit_data['gross_profit']),
                'net_profit': float(net_profit),
                'profit_margin': float(profit_margin)
            },
            'risk': risk_data,
            'forecast': forecast_data,
            'inventory': inventory_data,
            'routes': route_data,
            'charts': FinancialAnalytics.generate_charts(branch_id, days)
        }
    
    @staticmethod
    def calculate_risk_metrics(branch_id=None, days=365):
        """Calculate Value at Risk and other risk metrics"""
        try:
            # Get daily profit/loss data
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            filter_q = Q(created_at__gte=start_date)
            if branch_id:
                filter_q &= Q(branch_id=branch_id)
            
            # Daily sales
            daily_sales = Sale.objects.filter(filter_q).extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                revenue=Sum('total_amount')
            ).order_by('day')
            
            # Daily expenses
            daily_expenses = Expense.objects.filter(
                expense_date__gte=start_date.date()
            ).values('expense_date').annotate(
                expenses=Sum('amount')
            ).order_by('expense_date')
            
            if not daily_sales or len(daily_sales) < 30:
                return {'error': 'Insufficient data for risk analysis'}
            
            # Convert to DataFrame
            sales_df = pd.DataFrame(daily_sales)
            expenses_df = pd.DataFrame(daily_expenses)
            
            # Calculate daily profits
            sales_df['day'] = pd.to_datetime(sales_df['day'])
            expenses_df['expense_date'] = pd.to_datetime(expenses_df['expense_date'])
            
            # Merge and calculate daily profit
            merged = pd.merge(sales_df, expenses_df, 
                            left_on='day', right_on='expense_date', how='outer').fillna(0)
            merged['daily_profit'] = merged['revenue'] - merged['expenses']
            
            profits = merged['daily_profit'].values
            
            # Risk calculations
            var_95 = np.percentile(profits, 5)  # 95% VaR
            max_drawdown = np.min(profits)
            volatility = np.std(profits)
            mean_profit = np.mean(profits)
            
            # Sharpe ratio (simplified)
            sharpe_ratio = mean_profit / volatility if volatility > 0 else 0
            
            # Risk level determination
            if var_95 < -1000 or volatility > mean_profit:
                risk_level = 'HIGH'
            elif var_95 < -500 or volatility > mean_profit * 0.5:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'value_at_risk_95': float(var_95),
                'maximum_drawdown': float(max_drawdown),
                'volatility': float(volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'risk_level': risk_level,
                'probability_of_loss_pct': float(len(profits[profits < 0]) / len(profits) * 100)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def generate_sales_forecast(branch_id=None, days=30):
        """Generate sales forecast using Prophet-like algorithm"""
        try:
            # Get historical sales data
            filter_q = Q()
            if branch_id:
                filter_q = Q(branch_id=branch_id)
            
            sales_data = Sale.objects.filter(filter_q).extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                revenue=Sum('total_amount')
            ).order_by('day')
            
            if len(sales_data) < 30:
                return {'error': 'Insufficient data for forecasting'}
            
            # Convert to DataFrame
            df = pd.DataFrame(sales_data)
            df['day'] = pd.to_datetime(df['day'])
            df = df.set_index('day').resample('D').sum().fillna(0)
            
            # Simple trend-based forecast (simplified Prophet)
            recent_data = df.tail(30)['revenue'].values
            trend = np.polyfit(range(len(recent_data)), recent_data, 1)[0]
            
            # Generate forecast
            forecast_dates = pd.date_range(
                start=df.index[-1] + timedelta(days=1),
                periods=days,
                freq='D'
            )
            
            base_value = recent_data[-1]
            forecast_values = []
            
            for i in range(days):
                # Add trend + some seasonality simulation
                seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 7)  # Weekly pattern
                predicted = base_value + (trend * (i + 1)) * seasonal_factor
                forecast_values.append(max(0, predicted))
            
            return {
                'forecast_dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
                'predicted_sales': forecast_values,
                'total_predicted': sum(forecast_values),
                'trend': 'increasing' if trend > 0 else 'decreasing',
                'confidence': min(95, max(60, 80 - len(recent_data) * 0.5))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def optimize_inventory(branch_id=None):
        """EOQ-based inventory optimization"""
        try:
            filter_q = Q(is_active=True)
            if branch_id:
                filter_q &= Q(stocks__branch_id=branch_id)
            
            products = Product.objects.filter(filter_q).distinct()
            
            optimization_results = []
            total_investment = 0
            items_needing_reorder = 0
            
            for product in products:
                stocks = product.stocks.filter(branch_id=branch_id) if branch_id else product.stocks.all()
                
                for stock in stocks:
                    # Simplified EOQ calculation
                    annual_demand = 365  # Simplified
                    ordering_cost = 50   # Simplified
                    holding_cost = float(product.cost_price) * 0.2  # 20% holding cost
                    
                    if holding_cost > 0:
                        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
                        reorder_point = stock.min_quantity
                        
                        if stock.quantity <= reorder_point:
                            items_needing_reorder += 1
                            investment_needed = float(product.cost_price) * eoq
                            total_investment += investment_needed
                            
                            optimization_results.append({
                                'product': product.name,
                                'current_stock': stock.quantity,
                                'eoq': int(eoq),
                                'reorder_point': reorder_point,
                                'investment_needed': investment_needed
                            })
            
            return {
                'total_items_analyzed': products.count(),
                'items_needing_reorder': items_needing_reorder,
                'total_investment_needed': total_investment,
                'optimization_details': optimization_results[:10]  # Top 10
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def optimize_routes(branch_id=None, days=30):
        """Route optimization analysis"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            filter_q = Q(scheduled_date__gte=start_date)
            if branch_id:
                filter_q &= Q(vehicle__branch_id=branch_id)
            
            trips = Trip.objects.filter(filter_q)
            
            if not trips.exists():
                return {'message': 'No trip data available for analysis'}
            
            total_trips = trips.count()
            total_distance = trips.aggregate(Sum('distance'))['distance'] or 0
            total_revenue = trips.aggregate(Sum('revenue'))['revenue'] or 0
            total_fuel_cost = trips.aggregate(Sum('fuel_cost'))['fuel_cost'] or 0
            total_other_expenses = trips.aggregate(Sum('other_expenses'))['other_expenses'] or 0
            
            total_profit = float(total_revenue) - float(total_fuel_cost) - float(total_other_expenses)
            profit_per_km = total_profit / float(total_distance) if total_distance > 0 else 0
            
            return {
                'total_trips': total_trips,
                'total_distance_km': float(total_distance),
                'total_revenue': float(total_revenue),
                'total_fuel_cost': float(total_fuel_cost),
                'total_profit': total_profit,
                'profit_per_km': profit_per_km,
                'efficiency_score': min(100, max(0, profit_per_km * 10))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def generate_charts(branch_id=None, days=365):
        """Generate interactive charts using Plotly"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            filter_q = Q(created_at__gte=start_date)
            if branch_id:
                filter_q &= Q(branch_id=branch_id)
            
            # Revenue trend chart
            daily_sales = Sale.objects.filter(filter_q).extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                revenue=Sum('total_amount')
            ).order_by('day')
            
            if daily_sales:
                df = pd.DataFrame(daily_sales)
                df['day'] = pd.to_datetime(df['day'])
                
                fig = px.line(df, x='day', y='revenue', 
                             title='Revenue Trend',
                             labels={'revenue': 'Revenue ($)', 'day': 'Date'})
                fig.update_layout(template='plotly_white')
                
                revenue_chart = json.dumps(fig, cls=PlotlyJSONEncoder)
            else:
                revenue_chart = None
            
            return {
                'revenue_trend': revenue_chart
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def calculate_correct_net_profit(branch_id=None, start_date=None, end_date=None):
        """Calculate net profit correctly: (avg_selling_price - cost_price) * quantity - expenses"""
        try:
            if branch_id:
                branches = Branch.objects.filter(id=branch_id)
            else:
                branches = Branch.objects.filter(is_active=True)
            
            total_revenue = Decimal('0.00')
            total_gross_profit = Decimal('0.00')
            total_expenses = Decimal('0.00')
            
            for branch in branches:
                branch_gross_profit = Decimal('0.00')
                branch_revenue = Decimal('0.00')
                
                # Get all products sold in this branch during period
                sale_items = SaleItem.objects.filter(
                    sale__branch=branch,
                    sale__created_at__gte=start_date,
                    sale__created_at__lte=end_date
                ).select_related('stock__product', 'sale')
                
                # Group by product to calculate average selling price
                product_profits = {}
                
                for item in sale_items:
                    product = item.stock.product
                    product_id = product.id
                    
                    if product_id not in product_profits:
                        product_profits[product_id] = {
                            'total_quantity': 0,
                            'total_revenue': Decimal('0.00'),
                            'cost_price': product.cost_price
                        }
                    
                    product_profits[product_id]['total_quantity'] += item.quantity
                    product_profits[product_id]['total_revenue'] += item.subtotal
                
                # Calculate profit per product
                for product_id, data in product_profits.items():
                    if data['total_quantity'] > 0:
                        # Average selling price = total_revenue / total_quantity
                        avg_selling_price = data['total_revenue'] / data['total_quantity']
                        
                        # Profit per unit = avg_selling_price - cost_price
                        profit_per_unit = avg_selling_price - data['cost_price']
                        
                        # Total profit = profit_per_unit * quantity
                        product_gross_profit = profit_per_unit * data['total_quantity']
                        
                        branch_gross_profit += product_gross_profit
                        branch_revenue += data['total_revenue']
                
                # Get branch expenses
                branch_expenses = Expense.objects.filter(
                    branch=branch,
                    expense_date__gte=start_date.date(),
                    expense_date__lte=end_date.date()
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                
                total_revenue += branch_revenue
                total_gross_profit += branch_gross_profit
                total_expenses += branch_expenses
            
            # Net profit = gross profit - expenses
            net_profit = total_gross_profit - total_expenses
            
            return {
                'total_revenue': total_revenue,
                'gross_profit': total_gross_profit,
                'total_expenses': total_expenses,
                'net_profit': net_profit
            }
            
        except Exception as e:
            return {
                'total_revenue': Decimal('0.00'),
                'gross_profit': Decimal('0.00'),
                'total_expenses': Decimal('0.00'),
                'net_profit': Decimal('0.00'),
                'error': str(e)
            }