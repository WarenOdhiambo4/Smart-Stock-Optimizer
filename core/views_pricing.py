"""
Enterprise Pricing Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
import json

from .models import Product, PriceChangeLog
from .price_management import PriceManager
from .views import role_required


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def price_management_dashboard(request):
    """Price management dashboard with analytics"""
    from django.core.paginator import Paginator
    
    recent_changes = PriceChangeLog.objects.select_related('product', 'changed_by').all()
    products = Product.objects.filter(is_active=True)
    
    # Paginate recent changes
    changes_paginator = Paginator(recent_changes, 5)
    changes_page = request.GET.get('changes_page')
    changes_page_obj = changes_paginator.get_page(changes_page)
    
    # Paginate products
    products_paginator = Paginator(products, 5)
    products_page = request.GET.get('products_page')
    products_page_obj = products_paginator.get_page(products_page)
    
    context = {
        'recent_changes_page_obj': changes_page_obj,
        'recent_changes': changes_page_obj,
        'products_page_obj': products_page_obj,
        'products': products_page_obj
    }
    return render(request, 'core/price_management.html', context)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
@require_POST
def change_product_price(request):
    """Handle single product price change"""
    try:
        product_id = request.POST.get('product_id')
        new_price = request.POST.get('new_price')
        reason = request.POST.get('reason', '')
        
        if not product_id or not new_price:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        success = PriceManager.change_product_price(
            product_id=int(product_id),
            new_price=Decimal(new_price),
            changed_by=request.user,
            reason=reason
        )
        
        if success:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                'success': True,
                'message': f'Price updated for {product.name}',
                'new_price': str(product.unit_price)
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to update price'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required('ADMIN', 'BOSS')
@require_POST
def bulk_price_update(request):
    """Handle bulk price updates"""
    try:
        data = json.loads(request.body)
        price_changes = data.get('price_changes', [])
        reason = data.get('reason', 'Bulk price update')
        
        if not price_changes:
            return JsonResponse({'success': False, 'error': 'No price changes provided'})
        
        # Validate data
        for change in price_changes:
            if 'product_id' not in change or 'new_price' not in change:
                return JsonResponse({'success': False, 'error': 'Invalid price change data'})
        
        success = PriceManager.bulk_price_update(
            price_changes=price_changes,
            changed_by=request.user,
            reason=reason
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'Bulk update initiated for {len(price_changes)} products'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to initiate bulk update'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def price_elasticity_analysis(request, product_id):
    """Get price elasticity analysis for a product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        analysis = PriceManager.analyze_price_elasticity(product_id)
        
        return JsonResponse({
            'success': True,
            'product': product.name,
            'analysis': analysis
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def product_price_history(request, product_id):
    """Get price change history for a product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Get price changes
        changes = PriceChangeLog.objects.filter(product=product).select_related('changed_by')[:50]
        
        # Get historical records from django-simple-history
        history = product.history.all()[:50]
        
        context = {
            'product': product,
            'price_changes': changes,
            'history': history
        }
        
        return render(request, 'core/product_price_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading price history: {str(e)}')
        return redirect('price_management_dashboard')


@login_required
@role_required('ADMIN', 'BOSS')
def pricing_optimization(request, product_id):
    """Get pricing optimization recommendations"""
    try:
        from .price_management import optimize_pricing_strategy
        
        # Run optimization in background and return task ID
        task = optimize_pricing_strategy.delay(product_id)
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': 'Optimization started. Check back in a few minutes.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})