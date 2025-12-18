"""
Views for managing broken products and proper profit calculation
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Avg
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import Stock, BrokenProduct, MonthlyProfitAnalysis, Branch, Product, Employee
from .views import role_required
from .profit_engine import ProfitCalculationEngine


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def broken_products_list(request):
    """List all broken products"""
    search = request.GET.get('search', '')
    broken_items = BrokenProduct.objects.select_related('stock__product', 'stock__branch', 'reported_by').all()
    
    if search:
        broken_items = broken_items.filter(
            stock__product__name__icontains=search
        )
    
    from django.core.paginator import Paginator
    paginator = Paginator(broken_items, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/broken_products_list.html', {
        'page_obj': page_obj,
        'broken_items': page_obj,
        'search': search
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def report_broken_product(request):
    """Report a broken/damaged product"""
    stocks = Stock.objects.select_related('product', 'branch').filter(quantity__gt=0)
    
    if request.method == 'POST':
        stock_id = request.POST.get('stock')
        quantity = int(request.POST.get('quantity', 0))
        damage_type = request.POST.get('damage_type')
        description = request.POST.get('description', '')
        
        stock = get_object_or_404(Stock, pk=stock_id)
        
        if quantity > stock.quantity:
            messages.error(request, 'Cannot report more items than available in stock!')
            return redirect('report_broken_product')
        
        # Use weighted average purchase price for cost calculation
        unit_cost = stock.weighted_avg_purchase_price
        
        BrokenProduct.objects.create(
            stock=stock,
            quantity=quantity,
            damage_type=damage_type,
            unit_cost=unit_cost,
            description=description,
            reported_by=request.user.profile.employee if hasattr(request.user, 'profile') else None
        )
        
        messages.success(request, f'Reported {quantity} broken {stock.product.name} items')
        return redirect('broken_products_list')
    
    return render(request, 'core/report_broken_product.html', {
        'stocks': stocks,
        'action': 'Report'
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'FINANCE')
def monthly_profit_analysis(request):
    """View monthly profit analysis"""
    branch_id = request.GET.get('branch')
    month = request.GET.get('month')
    
    if month:
        try:
            month_date = timezone.datetime.strptime(month, '%Y-%m').date().replace(day=1)
        except ValueError:
            month_date = timezone.now().date().replace(day=1)
    else:
        month_date = timezone.now().date().replace(day=1)
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    # Get or generate profit analysis
    engine = ProfitCalculationEngine(branch=branch, month=month_date)
    engine.calculate_monthly_profit_analysis()
    
    # Get analysis results
    analyses = MonthlyProfitAnalysis.objects.filter(month=month_date)
    if branch:
        analyses = analyses.filter(branch=branch)
    
    # Get summary
    profit_summary = engine.generate_profit_summary()
    loss_making = engine.get_loss_making_products()
    most_profitable = engine.get_most_profitable_products(10)
    slow_moving = engine.get_slow_moving_stock()
    
    branches = Branch.objects.filter(is_active=True)
    
    context = {
        'analyses': analyses.select_related('product', 'branch'),
        'profit_summary': profit_summary,
        'loss_making': loss_making,
        'most_profitable': most_profitable,
        'slow_moving': slow_moving,
        'branches': branches,
        'selected_branch': branch,
        'selected_month': month_date,
        'month_display': month_date.strftime('%B %Y')
    }
    
    return render(request, 'core/monthly_profit_analysis.html', context)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'FINANCE')
def profit_analysis_api(request):
    """API endpoint for profit analysis data"""
    branch_id = request.GET.get('branch')
    month = request.GET.get('month')
    
    if month:
        try:
            month_date = timezone.datetime.strptime(month, '%Y-%m').date().replace(day=1)
        except ValueError:
            month_date = timezone.now().date().replace(day=1)
    else:
        month_date = timezone.now().date().replace(day=1)
    
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            pass
    
    try:
        engine = ProfitCalculationEngine(branch=branch, month=month_date)
        engine.calculate_monthly_profit_analysis()
        
        profit_summary = engine.generate_profit_summary()
        loss_making = engine.get_loss_making_products()
        most_profitable = engine.get_most_profitable_products(5)
        
        response_data = {
            'success': True,
            'summary': profit_summary,
            'loss_making': [
                {
                    'product': item.product.name,
                    'branch': item.branch.name,
                    'net_loss': float(item.net_profit),
                    'margin': float(item.profit_margin),
                    'turnover': float(item.stock_turnover_ratio)
                } for item in loss_making[:10]
            ],
            'most_profitable': [
                {
                    'product': item.product.name,
                    'branch': item.branch.name,
                    'net_profit': float(item.net_profit),
                    'margin': float(item.profit_margin),
                    'turnover': float(item.stock_turnover_ratio)
                } for item in most_profitable
            ]
        }
        
    except Exception as e:
        response_data = {
            'success': False,
            'error': str(e)
        }
    
    return JsonResponse(response_data)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def update_stock_purchase_price(request, stock_id):
    """Update stock purchase price when new inventory arrives"""
    stock = get_object_or_404(Stock, pk=stock_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        unit_price = Decimal(request.POST.get('unit_price', '0.00'))
        
        if quantity > 0 and unit_price > 0:
            # Update weighted average purchase price
            engine = ProfitCalculationEngine()
            engine.update_stock_purchase_price(stock, quantity, unit_price)
            
            messages.success(request, f'Updated {stock.product.name} stock: +{quantity} units at ${unit_price} each')
        else:
            messages.error(request, 'Invalid quantity or price')
        
        return redirect('stock_list')
    
    return render(request, 'core/update_stock_price.html', {
        'stock': stock,
        'action': 'Update Purchase Price'
    })


def get_stock_profit_data(request, stock_id):
    """Get profit data for a specific stock item"""
    stock = get_object_or_404(Stock, pk=stock_id)
    
    # Get current month analysis
    current_month = timezone.now().date().replace(day=1)
    
    try:
        analysis = MonthlyProfitAnalysis.objects.get(
            branch=stock.branch,
            product=stock.product,
            month=current_month
        )
        
        data = {
            'product_name': stock.product.name,
            'branch_name': stock.branch.name,
            'current_stock': stock.quantity,
            'weighted_avg_purchase_price': float(stock.weighted_avg_purchase_price),
            'monthly_analysis': {
                'quantity_sold': analysis.total_quantity_sold,
                'revenue': float(analysis.total_revenue),
                'avg_selling_price': float(analysis.average_selling_price),
                'gross_profit': float(analysis.gross_profit),
                'net_profit': float(analysis.net_profit),
                'profit_margin': float(analysis.profit_margin),
                'stock_turnover': float(analysis.stock_turnover_ratio),
                'broken_quantity': analysis.broken_quantity,
                'broken_cost': float(analysis.broken_cost)
            }
        }
        
    except MonthlyProfitAnalysis.DoesNotExist:
        data = {
            'product_name': stock.product.name,
            'branch_name': stock.branch.name,
            'current_stock': stock.quantity,
            'weighted_avg_purchase_price': float(stock.weighted_avg_purchase_price),
            'message': 'No analysis data available for current month'
        }
    
    return JsonResponse(data)