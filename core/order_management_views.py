from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal

from .models import Order, OrderItem, OrderItemCompletion, OrderStatusHistory, Branch, Product, Employee
from .views import role_required


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'SALES')
def order_edit(request, pk):
    """Edit order details including items, branch, and supplier"""
    try:
        order = get_object_or_404(Order, pk=pk)
        branches = Branch.objects.filter(is_active=True)
        
        if request.method == 'POST':
            with transaction.atomic():
                # Update basic order info
                old_branch = order.branch
                new_branch_id = request.POST.get('branch')
                new_branch = get_object_or_404(Branch, pk=new_branch_id)
                
                order.supplier = request.POST.get('supplier', '')
                order.notes = request.POST.get('notes', '')
                
                # Change branch if different
                if old_branch and old_branch.id != int(new_branch_id):
                    if hasattr(order, 'change_branch'):
                        try:
                            order.change_branch(new_branch, changed_by=getattr(request.user, 'employee', None))
                        except Exception as e:
                            order.branch = new_branch
                            order.save()
                    else:
                        order.branch = new_branch
                        order.save()
                else:
                    order.save()
                
                messages.success(request, f'Order {order.order_number} updated successfully!')
                return redirect('order_detail', pk=order.pk)
        
        return render(request, 'core/order_edit.html', {
            'order': order,
            'branches': branches,
            'action': 'Edit'
        })
    except Exception as e:
        messages.error(request, f'Error editing order: {str(e)}')
        return redirect('order_list')


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'SALES')
def order_partial_complete(request, pk):
    """Complete selected items or partial quantities from an order"""
    order = get_object_or_404(Order, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        with transaction.atomic():
            completion_branch_id = request.POST.get('completion_branch')
            completion_branch = get_object_or_404(Branch, pk=completion_branch_id)
            completed_by = getattr(request.user, 'employee', None)
            
            item_ids = request.POST.getlist('item_id')
            quantities_to_complete = request.POST.getlist('quantity_to_complete')
            
            completed_items = 0
            total_completed_value = Decimal('0.00')
            
            for i, item_id in enumerate(item_ids):
                if item_id and i < len(quantities_to_complete):
                    quantity = int(quantities_to_complete[i]) if quantities_to_complete[i] else 0
                    
                    if quantity > 0:
                        item = get_object_or_404(OrderItem, pk=item_id, order=order)
                        
                        # Complete the partial quantity
                        if hasattr(item, 'complete_partial_quantity'):
                            if item.complete_partial_quantity(quantity, completion_branch):
                                completed_items += 1
                                total_completed_value += quantity * item.unit_price
                                
                                # Log the completion if model exists
                                try:
                                    OrderItemCompletion.objects.create(
                                        order_item=item,
                                        quantity_completed=quantity,
                                        completion_branch=completion_branch,
                                        completed_by=completed_by,
                                        notes=f"Partial completion of {quantity} units"
                                    )
                                except:
                                    pass
            
            # Update order status
            if hasattr(order, 'update_completion_status'):
                order.update_completion_status()
            
            if completed_items > 0:
                messages.success(
                    request, 
                    f'Successfully completed {completed_items} items worth {total_completed_value} '
                    f'at {completion_branch.name}'
                )
            else:
                messages.warning(request, 'No items were completed.')
            
            return redirect('order_detail', pk=order.pk)
    
    # Get available items
    available_items = order.items.all()
    
    return render(request, 'core/order_partial_complete.html', {
        'order': order,
        'available_items': available_items,
        'branches': branches
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'SALES')
def order_change_branch(request, pk):
    """Change order branch"""
    order = get_object_or_404(Order, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        new_branch_id = request.POST.get('new_branch')
        new_branch = get_object_or_404(Branch, pk=new_branch_id)
        notes = request.POST.get('notes', '')
        
        if new_branch != order.branch:
            if hasattr(order, 'change_branch'):
                order.change_branch(
                    new_branch, 
                    changed_by=getattr(request.user, 'employee', None),
                    notes=notes
                )
            else:
                order.branch = new_branch
                order.save()
            
            messages.success(
                request, 
                f'Order {order.order_number} branch changed to {new_branch.name}'
            )
        else:
            messages.info(request, 'Order is already assigned to this branch.')
        
        return redirect('order_detail', pk=order.pk)
    
    return render(request, 'core/order_change_branch.html', {
        'order': order,
        'branches': branches
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'SALES')
def order_item_complete(request, order_pk, item_pk):
    """Complete a specific order item entirely"""
    order = get_object_or_404(Order, pk=order_pk)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    
    if request.method == 'POST':
        completion_branch_id = request.POST.get('completion_branch')
        completion_branch = get_object_or_404(Branch, pk=completion_branch_id)
        
        remaining_quantity = getattr(item, 'quantity_remaining', item.quantity)
        
        if remaining_quantity > 0:
            with transaction.atomic():
                # Complete remaining quantity
                if hasattr(item, 'complete_partial_quantity'):
                    item.complete_partial_quantity(remaining_quantity, completion_branch)
                
                # Log the completion if model exists
                try:
                    OrderItemCompletion.objects.create(
                        order_item=item,
                        quantity_completed=remaining_quantity,
                        completion_branch=completion_branch,
                        completed_by=getattr(request.user, 'employee', None),
                        notes=f"Full completion of remaining {remaining_quantity} units"
                    )
                except:
                    pass
                
                # Update order status
                if hasattr(order, 'update_completion_status'):
                    order.update_completion_status()
                
                messages.success(
                    request, 
                    f'Item "{item.product_name}" completed successfully at {completion_branch.name}'
                )
        else:
            messages.warning(request, 'This item is already completed.')
    
    return redirect('order_detail', pk=order.pk)


@login_required
def order_completion_history(request, pk):
    """View order completion history"""
    order = get_object_or_404(Order, pk=pk)
    
    # Get completions if model exists
    completions = []
    try:
        completions = OrderItemCompletion.objects.filter(
            order_item__order=order
        ).select_related('order_item', 'completion_branch', 'completed_by')
    except:
        pass
    
    # Get status history if model exists
    status_history = []
    try:
        status_history = order.status_history.all()
    except:
        pass
    
    return render(request, 'core/order_completion_history.html', {
        'order': order,
        'completions': completions,
        'status_history': status_history
    })


@login_required
def get_order_item_details(request, item_pk):
    """AJAX endpoint to get order item details"""
    item = get_object_or_404(OrderItem, pk=item_pk)
    
    data = {
        'id': item.id,
        'product_name': item.product_name,
        'quantity_ordered': getattr(item, 'quantity_ordered', item.quantity),
        'quantity_completed': getattr(item, 'quantity_completed', 0),
        'quantity_remaining': getattr(item, 'quantity_remaining', item.quantity),
        'unit_price': str(item.unit_price),
        'status': getattr(item, 'get_status_display', lambda: 'Pending')(),
        'completion_branch': getattr(item, 'completion_branch', {}).name if hasattr(item, 'completion_branch') and item.completion_branch else None,
    }
    
    return JsonResponse(data)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'SALES')
def bulk_order_operations(request):
    """Bulk operations on multiple orders"""
    try:
        if request.method == 'POST':
            action = request.POST.get('action')
            order_ids = request.POST.getlist('order_ids')
            
            if not order_ids:
                messages.error(request, 'No orders selected.')
                return redirect('order_list')
            
            orders = Order.objects.filter(id__in=order_ids)
            
            if action == 'change_branch':
                new_branch_id = request.POST.get('new_branch')
                new_branch = get_object_or_404(Branch, pk=new_branch_id)
                
                with transaction.atomic():
                    for order in orders:
                        if order.branch != new_branch:
                            if hasattr(order, 'change_branch'):
                                try:
                                    order.change_branch(
                                        new_branch,
                                        changed_by=getattr(request.user, 'employee', None),
                                        notes="Bulk branch change operation"
                                    )
                                except:
                                    order.branch = new_branch
                                    order.save()
                            else:
                                order.branch = new_branch
                                order.save()
                
                messages.success(
                    request, 
                    f'{orders.count()} orders moved to {new_branch.name}'
                )
            
            elif action == 'cancel':
                with transaction.atomic():
                    for order in orders:
                        if order.status != 'COMPLETED':
                            old_status = order.status
                            order.status = 'CANCELLED'
                            order.save()
                            
                            # Log status change if model exists
                            try:
                                OrderStatusHistory.objects.create(
                                    order=order,
                                    old_status=old_status,
                                    new_status='CANCELLED',
                                    changed_by=getattr(request.user, 'employee', None),
                                    notes="Bulk cancellation operation"
                                )
                            except:
                                pass
                
                messages.success(request, f'{orders.count()} orders cancelled')
            
            return redirect('order_list')
        
        # GET request - redirect to order list
        return redirect('order_list')
    except Exception as e:
        messages.error(request, f'Error in bulk operations: {str(e)}')
        return redirect('order_list')