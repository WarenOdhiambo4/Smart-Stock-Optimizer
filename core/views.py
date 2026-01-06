from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from decimal import Decimal
from functools import wraps
from datetime import datetime, timedelta
import uuid

from .models import Branch, Employee, Product, Stock, StockMovement, Order, OrderItem, OrderItemCompletion, OrderStatusHistory, Sale, SaleItem, UserProfile, Expense, Logistics, Vehicle, Trip, VehicleMaintenance, BusinessNote, TwoFactorAuth


def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            try:
                profile = request.user.profile
                if profile.role in roles or profile.role == 'ADMIN' or profile.role == 'BOSS':
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'You do not have permission to access this page.')
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User profile not found. Please contact administrator.')
                return redirect('login')
        return wrapped_view
    return decorator


def create_transfer_alert(stock_movement):
    """Create alert for receiving branch when transfer is requested"""
    pass  # Simplified for now


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


def generate_verification_code(user):
    """Generate 6-digit verification code"""
    import random
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        from .models import TwoFactorAuth
        
        # Invalidate old codes
        TwoFactorAuth.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new code
        code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=5)  # 5 minute expiry
        
        TwoFactorAuth.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
        
        return code
    except Exception as e:
        print(f"Error generating verification code: {e}")
        # Fallback: return a simple code
        return str(random.randint(100000, 999999))


def send_verification_email(user, code):
    """Send verification code via Supabase email API"""
    import requests
    from django.conf import settings
    
    # Try Supabase email API first
    try:
        supabase_url = getattr(settings, 'SUPABASE_URL', None)
        if supabase_url:
            # Use Supabase email API
            headers = {
                'Authorization': f'Bearer {getattr(settings, "SUPABASE_ANON_KEY", "")}',
                'Content-Type': 'application/json'
            }
            
            email_data = {
                'to': user.email,
                'subject': 'Kabisa ERP - Login Verification Code',
                'html': f'''
                <h2>Kabisa ERP Login Verification</h2>
                <p>Hello {user.get_full_name() or user.username},</p>
                <p>Your verification code is: <strong>{code}</strong></p>
                <p>This code will expire in 5 minutes.</p>
                <p>If you did not request this code, please ignore this email.</p>
                <p>Best regards,<br>Kabisa ERP Team</p>
                '''
            }
            
            response = requests.post(
                f'{supabase_url}/auth/v1/admin/generate_link',
                headers=headers,
                json=email_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Email sent successfully via Supabase to {user.email}")
                return
    except Exception as e:
        print(f"Supabase email failed: {e}")
    
    # Fallback to Django email
    try:
        from django.core.mail import send_mail
        
        subject = 'Kabisa ERP - Login Verification Code'
        message = f'''
Hello {user.get_full_name() or user.username},

Your verification code for Kabisa ERP login is: {code}

This code will expire in 5 minutes.

If you did not request this code, please ignore this email.

Best regards,
Kabisa ERP Team
'''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        print(f"Email sent successfully via Django to {user.email}")
    except Exception as e:
        print(f"Django email failed: {e}")
        # Show code in console as final fallback
        print(f"VERIFICATION CODE FOR {user.email}: {code}")


def verify_code(user_id, code):
    """Verify the provided code"""
    from django.utils import timezone
    
    try:
        from .models import TwoFactorAuth
        
        auth_code = TwoFactorAuth.objects.get(
            user_id=user_id,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        auth_code.is_used = True
        auth_code.save()
        return True
    except Exception as e:
        print(f"Error verifying code: {e}")
        return False


def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    from .delivery_manager import DeliveryChargesManager
    
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    
    # Filter data based on user role
    if user_profile and user_profile.role == 'SALES' and user_profile.branch:
        # Sales person sees only their branch
        branches = Branch.objects.filter(id=user_profile.branch.id, is_active=True)
        sales_filter = Q(branch=user_profile.branch)
        expense_filter = Q(branch=user_profile.branch)
    elif user_profile and user_profile.role in ['MANAGER'] and user_profile.branch:
        # Manager sees their branch
        branches = Branch.objects.filter(id=user_profile.branch.id, is_active=True)
        sales_filter = Q(branch=user_profile.branch)
        expense_filter = Q(branch=user_profile.branch)
    else:
        # Admin, Boss, Finance see all
        branches = Branch.objects.filter(is_active=True)
        sales_filter = Q()
        expense_filter = Q()
    
    total_branches = branches.count()
    total_employees = Employee.objects.filter(is_active=True).count()
    total_products = Product.objects.filter(is_active=True).count()
    
    # Financial metrics
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    total_sales = Sale.objects.filter(sales_filter).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    monthly_sales = Sale.objects.filter(sales_filter, created_at__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_expenses = Expense.objects.filter(expense_filter).exclude(expense_type='DELIVERY').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_expenses = Expense.objects.filter(expense_filter, expense_date__gte=month_start).exclude(expense_type='DELIVERY').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Calculate delivery expenses separately (business-wide)
    delivery_expenses = DeliveryChargesManager.get_total_delivery_expenses()
    monthly_delivery_expenses = DeliveryChargesManager.get_total_delivery_expenses(start_date=month_start)
    
    total_profit = total_sales - total_expenses - delivery_expenses
    monthly_profit = monthly_sales - monthly_expenses - monthly_delivery_expenses
    
    recent_sales = Sale.objects.filter(sales_filter).select_related('branch')[:5]
    recent_orders = Order.objects.select_related('branch')[:5]
    recent_expenses = Expense.objects.filter(expense_filter).select_related('branch')[:5]
    
    low_stock_items = Stock.objects.filter(quantity__lte=F('min_quantity')).select_related('product', 'branch')[:10]
    pending_orders = Order.objects.filter(status='PENDING').count()
    pending_transfers = StockMovement.objects.filter(movement_type='TRANSFER', status='PENDING').count()
    pending_logistics = Logistics.objects.filter(status__in=['PENDING', 'PROCESSING', 'IN_TRANSIT']).count()
    
    context = {
        'user_profile': user_profile,
        'total_branches': total_branches,
        'total_employees': total_employees,
        'total_products': total_products,
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'total_expenses': total_expenses,
        'monthly_expenses': monthly_expenses,
        'total_profit': total_profit,
        'monthly_profit': monthly_profit,
        'recent_sales': recent_sales,
        'recent_orders': recent_orders,
        'recent_expenses': recent_expenses,
        'low_stock_items': low_stock_items,
        'pending_orders': pending_orders,
        'pending_transfers': pending_transfers,
        'pending_logistics': pending_logistics,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def branch_list(request):
    search = request.GET.get('search', '')
    branches = Branch.objects.all()
    if search:
        branches = branches.filter(Q(name__icontains=search) | Q(address__icontains=search))
    
    paginator = Paginator(branches, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/branch_list.html', {
        'page_obj': page_obj,
        'branches': page_obj,
        'search': search
    })


def branch_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        
        Branch.objects.create(name=name, address=address, phone=phone, email=email)
        messages.success(request, 'Branch created successfully!')
        return redirect('branch_list')
    return render(request, 'core/branch_form.html', {'action': 'Create'})


def branch_edit(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.name = request.POST.get('name')
        branch.address = request.POST.get('address', '')
        branch.phone = request.POST.get('phone', '')
        branch.email = request.POST.get('email', '')
        branch.is_active = request.POST.get('is_active') == 'on'
        branch.save()
        messages.success(request, 'Branch updated successfully!')
        return redirect('branch_list')
    return render(request, 'core/branch_form.html', {'branch': branch, 'action': 'Edit'})


def branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.delete()
        messages.success(request, 'Branch deleted successfully!')
    return redirect('branch_list')


def employee_list(request):
    search = request.GET.get('search', '')
    employees = Employee.objects.prefetch_related('branches').all()
    if search:
        employees = employees.filter(
            Q(first_name__icontains=search) | 
            Q(last_name__icontains=search) | 
            Q(email__icontains=search)
        )
    
    paginator = Paginator(employees, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/employee_list.html', {
        'page_obj': page_obj,
        'employees': page_obj,
        'search': search
    })


def employee_create(request):
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        employee = Employee.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            position=request.POST.get('position', ''),
        )
        branch_ids = request.POST.getlist('branches')
        employee.branches.set(branch_ids)
        messages.success(request, 'Employee created successfully!')
        return redirect('employee_list')
    return render(request, 'core/employee_form.html', {'branches': branches, 'action': 'Create'})


def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.email = request.POST.get('email')
        employee.phone = request.POST.get('phone', '')
        employee.position = request.POST.get('position', '')
        employee.is_active = request.POST.get('is_active') == 'on'
        employee.save()
        branch_ids = request.POST.getlist('branches')
        employee.branches.set(branch_ids)
        messages.success(request, 'Employee updated successfully!')
        return redirect('employee_list')
    return render(request, 'core/employee_form.html', {'employee': employee, 'branches': branches, 'action': 'Edit'})


def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully!')
    return redirect('employee_list')


def product_list(request):
    search = request.GET.get('search', '')
    products = Product.objects.all()
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) | 
            Q(category__icontains=search)
        )
    
    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/product_list.html', {
        'page_obj': page_obj,
        'products': page_obj,
        'search': search
    })


def product_create(request):
    if request.method == 'POST':
        Product.objects.create(
            name=request.POST.get('name'),
            sku=request.POST.get('sku'),
            description=request.POST.get('description', ''),
            unit_price=Decimal(request.POST.get('unit_price', '0')),
            cost_price=Decimal(request.POST.get('cost_price', '0')),
            category=request.POST.get('category', ''),
        )
        messages.success(request, 'Product created successfully!')
        return redirect('product_list')
    return render(request, 'core/product_form.html', {'action': 'Create'})


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.sku = request.POST.get('sku')
        product.description = request.POST.get('description', '')
        product.unit_price = Decimal(request.POST.get('unit_price', '0'))
        product.cost_price = Decimal(request.POST.get('cost_price', '0'))
        product.category = request.POST.get('category', '')
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('product_list')
    return render(request, 'core/product_form.html', {'product': product, 'action': 'Edit'})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    return redirect('product_list')


def stock_list(request):
    search = request.GET.get('search', '')
    branch_id = request.GET.get('branch', '')
    stocks = Stock.objects.select_related('product', 'branch').all()
    
    if search:
        stocks = stocks.filter(
            Q(product__name__icontains=search) | 
            Q(product__sku__icontains=search)
        )
    if branch_id:
        stocks = stocks.filter(branch_id=branch_id)
    
    paginator = Paginator(stocks, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'core/stock_list.html', {
        'page_obj': page_obj,
        'stocks': page_obj,
        'branches': branches,
        'search': search,
        'selected_branch': branch_id
    })


def stock_create(request):
    branches = Branch.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 0))
        min_quantity = int(request.POST.get('min_quantity', 10))
        date_added = request.POST.get('date_added')
        
        stock, created = Stock.objects.get_or_create(
            branch_id=branch_id,
            product_id=product_id,
            defaults={'quantity': quantity, 'min_quantity': min_quantity}
        )
        if not created:
            stock.quantity += quantity
            stock.min_quantity = min_quantity
            stock.save()
        
        # Set created_at to the provided date
        if date_added:
            from datetime import datetime
            from django.utils import timezone
            stock_datetime = datetime.strptime(date_added, '%Y-%m-%d')
            stock.created_at = timezone.make_aware(stock_datetime)
            stock.save()
        
        messages.success(request, 'Stock updated successfully!')
        return redirect('stock_list')
    return render(request, 'core/stock_form.html', {
        'branches': branches, 
        'products': products,
        'action': 'Add'
    })


def stock_movement_list(request):
    search = request.GET.get('search', '')
    branch_id = request.GET.get('branch', '')
    movements = StockMovement.objects.select_related('stock__product', 'stock__branch', 'from_branch', 'to_branch').all()
    
    # Branch filter
    if branch_id:
        movements = movements.filter(
            Q(stock__branch_id=branch_id) | 
            Q(from_branch_id=branch_id) | 
            Q(to_branch_id=branch_id)
        )
    
    if search:
        movements = movements.filter(
            Q(stock__product__name__icontains=search) | 
            Q(notes__icontains=search)
        )
    
    paginator = Paginator(movements, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'core/stock_movement_list.html', {
        'page_obj': page_obj,
        'movements': page_obj,
        'search': search,
        'branches': branches,
        'selected_branch': branch_id
    })


def stock_transfer(request):
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        from_branch_id = request.POST.get('from_branch')
        to_branch_id = request.POST.get('to_branch')
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        from_branch = get_object_or_404(Branch, pk=from_branch_id)
        to_branch = get_object_or_404(Branch, pk=to_branch_id)
        product = get_object_or_404(Product, pk=product_id)
        
        stock = get_object_or_404(Stock, branch=from_branch, product=product)
        
        if stock.quantity < quantity:
            messages.error(request, 'Insufficient stock for transfer!')
            return redirect('stock_transfer')
        
        movement = StockMovement.objects.create(
            stock=stock,
            movement_type='TRANSFER',
            quantity=quantity,
            from_branch=from_branch,
            to_branch=to_branch,
            status='PENDING',
            notes=notes,
            created_by=None  # Will be fixed when Employee-User relationship is properly set up
        )
        
        # Create alert for receiving branch users
        create_transfer_alert(movement)
        
        messages.success(request, f'Transfer request created and sent to {to_branch.name} for approval.')
        return redirect('stock_movement_list')
    
    products = Product.objects.filter(is_active=True)
    return render(request, 'core/stock_transfer_form.html', {
        'branches': branches,
        'products': products
    })


def approve_transfer(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk, movement_type='TRANSFER', status='PENDING')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            with transaction.atomic():
                movement.status = 'APPROVED'
                movement.save()
                movement.apply_stock_adjustment()
                
                # Transfer approved - notification would go here
                
            messages.success(request, 'Transfer approved!')
        else:
            movement.status = 'REJECTED'
            movement.save()
            
            pass
            
            messages.info(request, 'Transfer rejected.')
    return redirect('stock_movement_list')


def order_list(request):
    search = request.GET.get('search', '')
    orders = Order.objects.select_related('branch').prefetch_related('items').all()
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) | 
            Q(supplier__icontains=search)
        )
    
    # Order Management Metrics
    total_orders = orders.count()
    pending_orders = orders.filter(status='PENDING').count()
    processing_orders = orders.filter(status='PROCESSING').count()
    partially_completed_orders = orders.filter(status='PARTIALLY_COMPLETED').count()
    completed_orders = orders.filter(status='COMPLETED').count()
    
    # Order value metrics
    total_order_value = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    completed_order_value = orders.filter(status='COMPLETED').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    pending_order_value = orders.exclude(status='COMPLETED').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Orders needing attention
    orders_needing_attention = orders.filter(status__in=['PENDING', 'PROCESSING', 'PARTIALLY_COMPLETED'])
    
    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/order_list.html', {
        'page_obj': page_obj,
        'orders': page_obj,
        'search': search,
        # Order Management Dashboard
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'partially_completed_orders': partially_completed_orders,
        'completed_orders': completed_orders,
        'total_order_value': total_order_value,
        'completed_order_value': completed_order_value,
        'pending_order_value': pending_order_value,
        'orders_needing_attention': orders_needing_attention,
    })


def order_create(request):
    from .delivery_manager import DeliveryChargesManager
    
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        try:
            order_date = request.POST.get('order_date')
            delivery_charges_str = request.POST.get('delivery_charges', '0')
            delivery_charges = Decimal(delivery_charges_str) if delivery_charges_str else Decimal('0')
            
            order = Order.objects.create(
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                branch_id=request.POST.get('branch'),
                supplier=request.POST.get('supplier', ''),
                notes=request.POST.get('notes', ''),
            )
            
            # Set created_at to the provided date
            if order_date:
                try:
                    from datetime import datetime
                    from django.utils import timezone
                    order_datetime = datetime.strptime(order_date, '%Y-%m-%d')
                    order.created_at = timezone.make_aware(order_datetime)
                    order.save()
                except Exception as date_error:
                    print(f"Date parsing error: {date_error}")
                    pass  # Use default created_at
            
            # Set delivery charges using manager
            DeliveryChargesManager.set_delivery_charges(
                order, 
                delivery_charges, 
                created_by=getattr(request.user, 'employee', None)
            )
            
            product_names = request.POST.getlist('product_name')
            product_skus = request.POST.getlist('product_sku')
            quantities = request.POST.getlist('quantity')
            unit_prices = request.POST.getlist('unit_price')
            
            for i in range(len(product_names)):
                if product_names[i]:
                    try:
                        quantity = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                        unit_price = Decimal(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else Decimal('0')
                    except (ValueError, IndexError):
                        quantity = 1
                        unit_price = Decimal('0')
                    
                    OrderItem.objects.create(
                        order=order,
                        product_name=product_names[i],
                        product_sku=product_skus[i] if i < len(product_skus) else '',
                        quantity_ordered=quantity,
                        unit_price=unit_price,
                    )
            
            order.calculate_total()
            messages.success(request, f'Order {order.order_number} created!')
            return redirect('order_list')
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return render(request, 'core/order_form.html', {'branches': branches, 'action': 'Create'})
    
    return render(request, 'core/order_form.html', {'branches': branches, 'action': 'Create'})


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Get completion history
    completions = OrderItemCompletion.objects.filter(
        order_item__order=order
    ).select_related('order_item', 'completion_branch', 'completed_by')[:10]
    
    # Get status history
    status_history = order.status_history.all()[:5]
    
    context = {
        'order': order,
        'completions': completions,
        'status_history': status_history,
        'completion_summary': order.items_completion_summary,
    }
    
    return render(request, 'core/order_detail.html', context)


def order_complete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        completion_branch_id = request.POST.get('completion_branch')
        completion_branch = get_object_or_404(Branch, pk=completion_branch_id)
        
        with transaction.atomic():
            completed_items = 0
            
            for item in order.items.exclude(status='COMPLETED'):
                remaining_qty = item.quantity_remaining
                if remaining_qty > 0:
                    # Complete remaining quantity
                    item.complete_partial_quantity(remaining_qty, completion_branch)
                    
                    # Log completion
                    OrderItemCompletion.objects.create(
                        order_item=item,
                        quantity_completed=remaining_qty,
                        completion_branch=completion_branch,
                        completed_by=getattr(request.user, 'employee', None),
                        notes=f"Full order completion - {remaining_qty} units"
                    )
                    
                    completed_items += 1
            
            # Update order status
            order.update_completion_status()
            
            if completed_items > 0:
                messages.success(
                    request, 
                    f'Order {order.order_number} completed! {completed_items} items added to {completion_branch.name} stock.'
                )
            else:
                messages.info(request, 'Order was already completed.')
        
        return redirect('order_list')
    
    # Show completion form
    pending_items = order.items.exclude(status='COMPLETED')
    return render(request, 'core/order_complete.html', {
        'order': order,
        'pending_items': pending_items,
        'branches': branches
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'FINANCE', 'SALES')
def sale_list(request):
    from django.utils import timezone
    search = request.GET.get('search', '')
    branch_id = request.GET.get('branch', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    sales = Sale.objects.select_related('branch').prefetch_related('items__stock__product').all()
    
    # Filter by branch for sales users
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    if user_profile and user_profile.role == 'SALES' and user_profile.branch:
        sales = sales.filter(branch=user_profile.branch)
    
    # Apply filters
    if branch_id:
        sales = sales.filter(branch_id=branch_id)
    
    if search:
        sales = sales.filter(
            Q(sale_number__icontains=search) | 
            Q(customer_name__icontains=search)
        )
    
    if date_from:
        try:
            from datetime import datetime
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            date_from_aware = timezone.make_aware(date_from_dt)
            sales = sales.filter(created_at__gte=date_from_aware)
        except:
            pass
    if date_to:
        try:
            from datetime import datetime
            date_to_dt = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            date_to_aware = timezone.make_aware(date_to_dt)
            sales = sales.filter(created_at__lte=date_to_aware)
        except:
            pass
    
    # Pagination - 5 sales per page
    paginator = Paginator(sales, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'core/sale_list.html', {
        'page_obj': page_obj,
        'sales': page_obj,
        'search': search,
        'branches': branches,
        'selected_branch': branch_id,
        'date_from': date_from,
        'date_to': date_to
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'SALES')
def sale_create(request):
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Check if confirmation is required
            if request.POST.get('confirm') != 'true':
                # First submission - show confirmation
                return render(request, 'core/sale_form.html', {
                    'branches': branches,
                    'action': 'Create',
                    'confirm_data': request.POST,
                    'show_confirmation': True
                })
            
            # Confirmed submission
            branch_id = request.POST.get('branch')
            sale_date = request.POST.get('sale_date')
            sale = Sale.objects.create(
                sale_number=f"SALE-{uuid.uuid4().hex[:8].upper()}",
                branch_id=branch_id,
                customer_name=request.POST.get('customer_name', ''),
                customer_phone=request.POST.get('customer_phone', ''),
                payment_method=request.POST.get('payment_method', 'Cash'),
                notes=request.POST.get('notes', ''),
            )
            
            # Set created_at to the provided date
            if sale_date:
                from datetime import datetime
                from django.utils import timezone
                sale_datetime = datetime.strptime(sale_date, '%Y-%m-%d')
                sale.created_at = timezone.make_aware(sale_datetime)
                sale.save()
            
            stock_ids = request.POST.getlist('stock_id')
            quantities = request.POST.getlist('quantity')
            unit_prices = request.POST.getlist('unit_price')
            
            for i in range(len(stock_ids)):
                if stock_ids[i]:
                    stock = get_object_or_404(Stock, pk=stock_ids[i])
                    qty = int(quantities[i]) if i < len(quantities) else 1
                    price = Decimal(unit_prices[i]) if i < len(unit_prices) else stock.product.unit_price
                    
                    SaleItem.objects.create(
                        sale=sale,
                        stock=stock,
                        quantity=qty,
                        unit_price=price,
                    )
            
            sale.calculate_total()
            
            # Add multiple expenses if provided
            expense_descriptions = request.POST.getlist('expense_description')
            expense_amounts = request.POST.getlist('expense_amount')
            expense_receipts = request.POST.getlist('expense_receipt')
            
            for i in range(len(expense_descriptions)):
                if expense_descriptions[i] and expense_amounts[i] and Decimal(expense_amounts[i]) > 0:
                    Expense.objects.create(
                        expense_number=f"EXP-{uuid.uuid4().hex[:8].upper()}",
                        branch_id=branch_id,
                        sale=sale,
                        expense_type='SALE_RELATED',
                        description=expense_descriptions[i],
                        amount=Decimal(expense_amounts[i]),
                        expense_date=timezone.now().date(),
                        receipt_number=expense_receipts[i] if i < len(expense_receipts) else '',
                        notes=f"Sale related expense for {sale.sale_number}",
                    )
            
            messages.success(request, f'Sale {sale.sale_number} created successfully!')
            return redirect('sale_list')
        except Exception as e:
            messages.error(request, f'Error creating sale: {str(e)}')
            return render(request, 'core/sale_form.html', {'branches': branches, 'action': 'Create'})
    
    return render(request, 'core/sale_form.html', {'branches': branches, 'action': 'Create'})


def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'core/sale_detail.html', {'sale': sale})


def get_branch_stocks(request, branch_id):
    stocks = Stock.objects.filter(branch_id=branch_id, quantity__gt=0).select_related('product')
    data = [
        {
            'id': s.id,
            'product_id': s.product.id,
            'product_name': s.product.name,
            'product_sku': s.product.sku,
            'quantity': s.quantity,
            'unit_price': str(s.product.unit_price)
        }
        for s in stocks
    ]
    return JsonResponse(data, safe=False)


# Expense Management
@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'FINANCE', 'SALES')
def expense_list(request):
    search = request.GET.get('search', '')
    expenses = Expense.objects.select_related('branch', 'sale', 'created_by').all()
    
    # Filter by branch for sales users
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    if user_profile and user_profile.role == 'SALES' and user_profile.branch:
        expenses = expenses.filter(branch=user_profile.branch)
    
    if search:
        expenses = expenses.filter(
            Q(expense_number__icontains=search) | 
            Q(description__icontains=search)
        )
    
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/expense_list.html', {
        'page_obj': page_obj,
        'expenses': page_obj,
        'search': search
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'FINANCE', 'SALES')
def expense_create(request):
    branches = Branch.objects.filter(is_active=True)
    sales = Sale.objects.select_related('branch').all()
    
    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        expense_type = request.POST.get('expense_type')
        expense_date = request.POST.get('expense_date')
        sale_id = request.POST.get('sale') if request.POST.get('sale') else None
        notes = request.POST.get('notes', '')
        
        # Get expense items
        item_descriptions = request.POST.getlist('item_description')
        item_amounts = request.POST.getlist('item_amount')
        item_receipts = request.POST.getlist('item_receipt')
        
        # Create multiple expenses
        for i in range(len(item_descriptions)):
            if item_descriptions[i] and item_amounts[i]:
                Expense.objects.create(
                    expense_number=f"EXP-{uuid.uuid4().hex[:8].upper()}",
                    branch_id=branch_id,
                    sale_id=sale_id,
                    expense_type=expense_type,
                    description=item_descriptions[i],
                    amount=Decimal(item_amounts[i]),
                    expense_date=expense_date,
                    receipt_number=item_receipts[i] if i < len(item_receipts) else '',
                    notes=notes,
                )
        
        messages.success(request, f'{len(item_descriptions)} expenses created!')
        return redirect('expense_list')
    
    return render(request, 'core/expense_form.html', {
        'branches': branches,
        'sales': sales,
        'action': 'Create'
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'FINANCE')
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    # Check if auto-generated
    if expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
        messages.error(request, 'Cannot modify auto-generated expenses')
        return redirect('expense_list')
    
    branches = Branch.objects.filter(is_active=True)
    sales = Sale.objects.select_related('branch').all()
    
    if request.method == 'POST':
        expense.branch_id = request.POST.get('branch')
        expense.sale_id = request.POST.get('sale') if request.POST.get('sale') else None
        expense.expense_type = request.POST.get('expense_type')
        expense.description = request.POST.get('description')
        expense.amount = Decimal(request.POST.get('amount', '0'))
        expense.expense_date = request.POST.get('expense_date')
        expense.receipt_number = request.POST.get('receipt_number', '')
        expense.notes = request.POST.get('notes', '')
        expense.save()
        messages.success(request, f'Expense {expense.expense_number} updated!')
        return redirect('expense_list')
    
    return render(request, 'core/expense_form.html', {
        'expense': expense,
        'branches': branches,
        'sales': sales,
        'action': 'Update'
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'FINANCE')
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    # Check if auto-generated
    if expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
        messages.error(request, 'Cannot delete auto-generated expenses')
        return redirect('expense_list')
    
    if request.method == 'POST':
        expense_number = expense.expense_number
        expense.delete()
        messages.success(request, f'Expense {expense_number} deleted successfully')
        return redirect('expense_list')
    
    return redirect('expense_list')


# Logistics Management
@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'LOGISTICS', 'SALES')
def logistics_list(request):
    search = request.GET.get('search', '')
    logistics = Logistics.objects.select_related('sale', 'from_branch', 'created_by').all()
    
    if search:
        logistics = logistics.filter(
            Q(tracking_number__icontains=search) | 
            Q(customer_name__icontains=search)
        )
    
    paginator = Paginator(logistics, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/logistics_list.html', {
        'page_obj': page_obj,
        'logistics': page_obj,
        'search': search
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'LOGISTICS')
def logistics_create(request):
    sales = Sale.objects.select_related('branch').all()
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        logistics = Logistics.objects.create(
            tracking_number=f"TRK-{uuid.uuid4().hex[:8].upper()}",
            sale_id=request.POST.get('sale'),
            from_branch_id=request.POST.get('from_branch'),
            to_address=request.POST.get('to_address'),
            customer_name=request.POST.get('customer_name'),
            customer_phone=request.POST.get('customer_phone'),
            delivery_date=request.POST.get('delivery_date') if request.POST.get('delivery_date') else None,
            driver_name=request.POST.get('driver_name', ''),
            vehicle_number=request.POST.get('vehicle_number', ''),
            delivery_cost=Decimal(request.POST.get('delivery_cost', '0')),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Logistics {logistics.tracking_number} created!')
        return redirect('logistics_list')
    
    return render(request, 'core/logistics_form.html', {
        'sales': sales,
        'branches': branches,
        'action': 'Create'
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'BOSS', 'LOGISTICS')
def logistics_update_status(request, pk):
    logistics = get_object_or_404(Logistics, pk=pk)
    if request.method == 'POST':
        logistics.status = request.POST.get('status')
        logistics.save()
        messages.success(request, f'Logistics status updated to {logistics.get_status_display()}!')
    return redirect('logistics_list')


# Financial Reports
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def financial_reports(request):
    from .delivery_manager import DeliveryChargesManager
    
    # Get date range from request or default to current month
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date() + timedelta(days=1)
    else:
        # Default to current month
        today = timezone.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get all branches or filter by user
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    if user_profile and user_profile.role == 'MANAGER' and user_profile.branch:
        branches = [user_profile.branch]
    else:
        branches = Branch.objects.filter(is_active=True)
    
    # Calculate financials per branch
    branch_reports = []
    total_sales = Decimal('0.00')
    total_expenses = Decimal('0.00')
    total_profit = Decimal('0.00')
    
    for branch in branches:
        sales = Sale.objects.filter(
            branch=branch,
            created_at__gte=start_date,
            created_at__lt=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Branch-specific expenses (excluding delivery charges)
        expenses = Expense.objects.filter(
            branch=branch,
            expense_date__gte=start_date,
            expense_date__lt=end_date
        ).exclude(expense_type='DELIVERY').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        profit = sales - expenses
        
        branch_reports.append({
            'branch': branch,
            'sales': sales,
            'expenses': expenses,
            'profit': profit,
        })
        
        total_sales += sales
        total_expenses += expenses
        total_profit += profit
    
    # Calculate total delivery expenses (business-wide)
    delivery_expenses = DeliveryChargesManager.get_total_delivery_expenses(start_date, end_date)
    
    # Adjust business net profit by subtracting delivery expenses
    business_net_profit = total_profit - delivery_expenses
    
    context = {
        'branch_reports': branch_reports,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'delivery_expenses': delivery_expenses,
        'business_net_profit': business_net_profit,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'core/financial_reports.html', context)


# Branch Detail Page
@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def branch_detail(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    
    # Get current month data
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Financial metrics
    monthly_sales = Sale.objects.filter(branch=branch, created_at__gte=month_start).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    monthly_expenses = Expense.objects.filter(branch=branch, expense_date__gte=month_start).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    monthly_profit = monthly_sales - monthly_expenses
    
    # Stock information
    total_stock_value = Stock.objects.filter(branch=branch).annotate(
        value=F('quantity') * F('product__cost_price')
    ).aggregate(total=Sum('value'))['total'] or Decimal('0.00')
    
    low_stock_count = Stock.objects.filter(branch=branch, quantity__lte=F('min_quantity')).count()
    
    # Recent activities
    recent_sales = Sale.objects.filter(branch=branch).select_related('created_by')[:10]
    recent_expenses = Expense.objects.filter(branch=branch).select_related('created_by')[:10]
    
    context = {
        'branch': branch,
        'monthly_sales': monthly_sales,
        'monthly_expenses': monthly_expenses,
        'monthly_profit': monthly_profit,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'recent_sales': recent_sales,
        'recent_expenses': recent_expenses,
    }
    return render(request, 'core/branch_detail.html', context)


# User Management
@login_required
@role_required('ADMIN', 'BOSS')
def user_list(request):
    users = User.objects.select_related('profile').all()
    
    paginator = Paginator(users, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/user_list.html', {
        'page_obj': page_obj,
        'users': page_obj
    })


@login_required
@role_required('ADMIN', 'BOSS')
def user_create(request):
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        branch_id = request.POST.get('branch')
        phone = request.POST.get('phone', '')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
        )
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            role=role,
            branch_id=branch_id if branch_id else None,
            phone=phone,
        )
        
        messages.success(request, f'User {username} created successfully!')
        return redirect('user_list')
    
    return render(request, 'core/user_form.html', {
        'branches': branches,
        'action': 'Create'
    })


@login_required
@role_required('ADMIN', 'BOSS')
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = user.profile if hasattr(user, 'profile') else None
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        
        if profile:
            profile.role = request.POST.get('role')
            profile.branch_id = request.POST.get('branch') if request.POST.get('branch') else None
            profile.phone = request.POST.get('phone', '')
            profile.save()
        else:
            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role'),
                branch_id=request.POST.get('branch') if request.POST.get('branch') else None,
                phone=request.POST.get('phone', ''),
            )
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('user_list')
    
    return render(request, 'core/user_form.html', {
        'user': user,
        'profile': profile,
        'branches': branches,
        'action': 'Edit'
    })


# Vehicle Management Views
@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def vehicle_list(request):
    search = request.GET.get('search', '')
    vehicles = Vehicle.objects.select_related('branch', 'assigned_driver').all()
    
    if search:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search) | 
            Q(make__icontains=search) | 
            Q(model__icontains=search)
        )
    
    paginator = Paginator(vehicles, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/vehicle_list.html', {
        'page_obj': page_obj,
        'vehicles': page_obj,
        'search': search
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def vehicle_create(request):
    branches = Branch.objects.filter(is_active=True)
    drivers = Employee.objects.filter(is_active=True)
    
    if request.method == 'POST':
        vehicle = Vehicle.objects.create(
            registration_number=request.POST.get('registration_number'),
            vehicle_type=request.POST.get('vehicle_type'),
            make=request.POST.get('make'),
            model=request.POST.get('model'),
            year=int(request.POST.get('year')),
            color=request.POST.get('color', ''),
            branch_id=request.POST.get('branch'),
            assigned_driver_id=request.POST.get('assigned_driver') if request.POST.get('assigned_driver') else None,
            current_mileage=int(request.POST.get('current_mileage', 0)),
            fuel_capacity=Decimal(request.POST.get('fuel_capacity', '0')),
            purchase_price=Decimal(request.POST.get('purchase_price', '0')),
            purchase_date=request.POST.get('purchase_date') if request.POST.get('purchase_date') else None,
            insurance_expiry=request.POST.get('insurance_expiry') if request.POST.get('insurance_expiry') else None,
            registration_expiry=request.POST.get('registration_expiry') if request.POST.get('registration_expiry') else None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Vehicle {vehicle.registration_number} created successfully!')
        return redirect('vehicle_list')
    
    return render(request, 'core/vehicle_form.html', {
        'branches': branches,
        'drivers': drivers,
        'action': 'Create'
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def trip_list(request):
    search = request.GET.get('search', '')
    vehicle_id = request.GET.get('vehicle', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    trips = Trip.objects.select_related('vehicle', 'driver', 'sale').all()
    
    if search:
        trips = trips.filter(
            Q(trip_number__icontains=search) | 
            Q(origin__icontains=search) | 
            Q(destination__icontains=search)
        )
    
    if vehicle_id:
        trips = trips.filter(vehicle_id=vehicle_id)
    
    if date_from:
        trips = trips.filter(scheduled_date__gte=date_from)
    if date_to:
        trips = trips.filter(scheduled_date__lte=date_to + ' 23:59:59')
    
    # Pagination - 5 trips per page
    paginator = Paginator(trips, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    vehicles = Vehicle.objects.all().order_by('registration_number')
    
    return render(request, 'core/trip_list.html', {
        'page_obj': page_obj,
        'trips': page_obj,  # For backward compatibility
        'search': search,
        'vehicles': vehicles,
        'selected_vehicle': vehicle_id,
        'date_from': date_from,
        'date_to': date_to
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def trip_create(request):
    vehicles = Vehicle.objects.filter(status='ACTIVE')
    drivers = Employee.objects.filter(is_active=True)
    sales = Sale.objects.all()[:50]
    
    if request.method == 'POST':
        try:
            # Handle decimal fields safely
            distance = request.POST.get('distance', '0')
            revenue = request.POST.get('revenue', '0')
            fuel_cost = request.POST.get('fuel_cost', '0')
            other_expenses = request.POST.get('other_expenses', '0')
            
            # Convert to Decimal with error handling
            try:
                distance = Decimal(distance) if distance else Decimal('0')
            except (ValueError, TypeError):
                distance = Decimal('0')
            
            try:
                revenue = Decimal(revenue) if revenue else Decimal('0')
            except (ValueError, TypeError):
                revenue = Decimal('0')
            
            try:
                fuel_cost = Decimal(fuel_cost) if fuel_cost else Decimal('0')
            except (ValueError, TypeError):
                fuel_cost = Decimal('0')
            
            try:
                other_expenses = Decimal(other_expenses) if other_expenses else Decimal('0')
            except (ValueError, TypeError):
                other_expenses = Decimal('0')
            
            # Handle date field
            scheduled_date = request.POST.get('scheduled_date')
            if not scheduled_date:
                messages.error(request, 'Scheduled date is required')
                return render(request, 'core/trip_form.html', {
                    'vehicles': vehicles,
                    'drivers': drivers,
                    'sales': sales,
                    'action': 'Create'
                })
            
            trip = Trip.objects.create(
                trip_number=f"TRIP-{uuid.uuid4().hex[:8].upper()}",
                vehicle_id=request.POST.get('vehicle'),
                driver_id=request.POST.get('driver') if request.POST.get('driver') else None,
                trip_type=request.POST.get('trip_type', 'DELIVERY'),
                origin=request.POST.get('origin', ''),
                destination=request.POST.get('destination', ''),
                distance=distance,
                sale_id=request.POST.get('sale') if request.POST.get('sale') else None,
                scheduled_date=scheduled_date,
                revenue=revenue,
                fuel_cost=fuel_cost,
                other_expenses=other_expenses,
                customer_name=request.POST.get('customer_name', ''),
                customer_phone=request.POST.get('customer_phone', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Trip {trip.trip_number} created successfully!')
            return redirect('trip_list')
        except Exception as e:
            messages.error(request, f'Error creating trip: {str(e)}')
            return render(request, 'core/trip_form.html', {
                'vehicles': vehicles,
                'drivers': drivers,
                'sales': sales,
                'action': 'Create'
            })
    
    return render(request, 'core/trip_form.html', {
        'vehicles': vehicles,
        'drivers': drivers,
        'sales': sales,
        'action': 'Create'
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def trip_update(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    vehicles = Vehicle.objects.filter(status='ACTIVE')
    drivers = Employee.objects.filter(is_active=True)
    sales = Sale.objects.all()[:50]
    
    if request.method == 'POST':
        trip.vehicle_id = request.POST.get('vehicle')
        trip.driver_id = request.POST.get('driver')
        trip.trip_type = request.POST.get('trip_type')
        trip.origin = request.POST.get('origin')
        trip.destination = request.POST.get('destination')
        trip.distance = Decimal(request.POST.get('distance', '0'))
        trip.sale_id = request.POST.get('sale') if request.POST.get('sale') else None
        trip.scheduled_date = request.POST.get('scheduled_date')
        trip.revenue = Decimal(request.POST.get('revenue', '0'))
        trip.fuel_cost = Decimal(request.POST.get('fuel_cost', '0'))
        trip.other_expenses = Decimal(request.POST.get('other_expenses', '0'))
        trip.customer_name = request.POST.get('customer_name', '')
        trip.customer_phone = request.POST.get('customer_phone', '')
        trip.notes = request.POST.get('notes', '')
        trip.save()
        messages.success(request, f'Trip {trip.trip_number} updated successfully!')
        return redirect('trip_list')
    
    return render(request, 'core/trip_form.html', {
        'trip': trip,
        'vehicles': vehicles,
        'drivers': drivers,
        'sales': sales,
        'action': 'Update'
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    
    if request.method == 'POST':
        trip_number = trip.trip_number
        trip.delete()
        messages.success(request, f'Trip {trip_number} deleted successfully!')
        return redirect('trip_list')
    
    return redirect('trip_list')


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def maintenance_list(request):
    search = request.GET.get('search', '')
    maintenance = VehicleMaintenance.objects.select_related('vehicle').all()
    
    if search:
        maintenance = maintenance.filter(
            Q(maintenance_number__icontains=search) | 
            Q(vehicle__registration_number__icontains=search) | 
            Q(service_provider__icontains=search)
        )
    
    # Pagination - 5 maintenance records per page
    paginator = Paginator(maintenance, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/maintenance_list.html', {
        'page_obj': page_obj,
        'maintenance': page_obj,
        'search': search
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    drivers = Employee.objects.filter(is_active=True)
    
    if request.method == 'POST':
        vehicle.registration_number = request.POST.get('registration_number')
        vehicle.vehicle_type = request.POST.get('vehicle_type')
        vehicle.make = request.POST.get('make')
        vehicle.model = request.POST.get('model')
        vehicle.year = int(request.POST.get('year'))
        vehicle.color = request.POST.get('color', '')
        vehicle.branch_id = request.POST.get('branch')
        vehicle.assigned_driver_id = request.POST.get('assigned_driver') if request.POST.get('assigned_driver') else None
        vehicle.status = request.POST.get('status')
        vehicle.current_mileage = int(request.POST.get('current_mileage', 0))
        vehicle.fuel_capacity = Decimal(request.POST.get('fuel_capacity', '0'))
        vehicle.purchase_price = Decimal(request.POST.get('purchase_price', '0'))
        vehicle.purchase_date = request.POST.get('purchase_date') if request.POST.get('purchase_date') else None
        vehicle.insurance_expiry = request.POST.get('insurance_expiry') if request.POST.get('insurance_expiry') else None
        vehicle.registration_expiry = request.POST.get('registration_expiry') if request.POST.get('registration_expiry') else None
        vehicle.notes = request.POST.get('notes', '')
        vehicle.save()
        messages.success(request, f'Vehicle {vehicle.registration_number} updated successfully!')
        return redirect('vehicle_list')
    
    return render(request, 'core/vehicle_form.html', {
        'vehicle': vehicle,
        'branches': branches,
        'drivers': drivers,
        'action': 'Edit'
    })


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'LOGISTICS')
def maintenance_create(request):
    vehicles = Vehicle.objects.all()
    
    if request.method == 'POST':
        maintenance = VehicleMaintenance.objects.create(
            maintenance_number=f"MAINT-{uuid.uuid4().hex[:8].upper()}",
            vehicle_id=request.POST.get('vehicle'),
            maintenance_type=request.POST.get('maintenance_type'),
            description=request.POST.get('description'),
            service_provider=request.POST.get('service_provider'),
            service_date=request.POST.get('service_date'),
            parts_cost=Decimal(request.POST.get('parts_cost', '0')),
            labor_cost=Decimal(request.POST.get('labor_cost', '0')),
            other_costs=Decimal(request.POST.get('other_costs', '0')),
            mileage_at_service=int(request.POST.get('mileage_at_service', 0)),
            next_service_mileage=int(request.POST.get('next_service_mileage', 0)) if request.POST.get('next_service_mileage') else None,
            receipt_number=request.POST.get('receipt_number', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Maintenance {maintenance.maintenance_number} created successfully!')
        return redirect('maintenance_list')
    
    return render(request, 'core/maintenance_form.html', {
        'vehicles': vehicles,
        'action': 'Create'
    })


@login_required
def note_list(request):
    search = request.GET.get('search', '')
    priority = request.GET.get('priority', '')
    notes = BusinessNote.objects.select_related('created_by').all()
    
    if search:
        notes = notes.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search) | 
            Q(tags__icontains=search)
        )
    
    if priority:
        notes = notes.filter(priority=priority)
    
    paginator = Paginator(notes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/note_list.html', {
        'page_obj': page_obj,
        'notes': page_obj,
        'search': search,
        'selected_priority': priority
    })


@login_required
def note_create(request):
    if request.method == 'POST':
        note = BusinessNote.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            priority=request.POST.get('priority', 'MEDIUM'),
            tags=request.POST.get('tags', ''),
            created_by=getattr(request.user, 'employee', None)
        )
        messages.success(request, f'Note "{note.title}" created successfully!')
        return redirect('note_list')
    
    return render(request, 'core/note_form.html', {'action': 'Create'})


@login_required
def note_update(request, pk):
    note = get_object_or_404(BusinessNote, pk=pk)
    
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.content = request.POST.get('content')
        note.priority = request.POST.get('priority', 'MEDIUM')
        note.tags = request.POST.get('tags', '')
        note.save()
        messages.success(request, f'Note "{note.title}" updated successfully!')
        return redirect('note_list')
    
    return render(request, 'core/note_form.html', {'note': note, 'action': 'Update'})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(BusinessNote, pk=pk)
    
    if request.method == 'POST':
        title = note.title
        note.delete()
        messages.success(request, f'Note "{title}" deleted successfully!')
        return redirect('note_list')
    
    return redirect('note_list')


@login_required
def notebook(request):
    try:
        page_param = request.GET.get('page', '1')
        page_number = int(page_param) if page_param else 1
    except (ValueError, TypeError):
        page_number = 1
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        note, created = BusinessNote.objects.get_or_create(
            page_number=page_number,
            defaults={'content': content}
        )
        if not created:
            note.content = content
            note.save()
        return JsonResponse({'status': 'saved'})
    
    note = BusinessNote.objects.filter(page_number=page_number).first()
    content = note.content if note else ''
    
    return render(request, 'core/notebook.html', {
        'content': content,
        'page_number': page_number
    })


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def analytics_dashboard(request):
    from .analytics import FinancialAnalytics
    import json
    
    branch_id = request.GET.get('branch')
    period_days = int(request.GET.get('period', 365))
    
    # Get financial metrics
    metrics = FinancialAnalytics.get_revenue_metrics(branch_id, period_days)
    
    # Get analytics data
    forecast_data = FinancialAnalytics.sales_forecast_data()
    risk_data = FinancialAnalytics.risk_assessment()
    inventory_data = FinancialAnalytics.inventory_analysis()
    route_data = FinancialAnalytics.route_optimization()
    chart_data = FinancialAnalytics.get_chart_data()
    
    branches = Branch.objects.filter(is_active=True)
    
    context = {
        'metrics': metrics,
        'forecast_data': forecast_data,
        'risk_data': risk_data,
        'inventory_data': inventory_data,
        'route_data': route_data,
        'chart_data': json.dumps(chart_data),
        'branches': branches,
        'selected_branch': branch_id,
        'selected_period': period_days
    }
    
    return render(request, 'core/analytics_dashboard.html', context)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def physical_count(request):
    branches = Branch.objects.filter(is_active=True)
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    
    # Filter branches for managers
    if user_profile and user_profile.role == 'MANAGER' and user_profile.branch:
        branches = branches.filter(id=user_profile.branch.id)
    
    return render(request, 'core/physical_count.html', {'branches': branches})


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def physical_count_submit(request):
    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        product_id = request.POST.get('product')
        physical_quantity = int(request.POST.get('physical_quantity', 0))
        notes = request.POST.get('notes', '')
        
        branch = get_object_or_404(Branch, pk=branch_id)
        product = get_object_or_404(Product, pk=product_id)
        
        # Get current stock
        try:
            stock = Stock.objects.get(branch=branch, product=product)
            system_quantity = stock.quantity
        except Stock.DoesNotExist:
            system_quantity = 0
        
        # Calculate discrepancy
        discrepancy = physical_quantity - system_quantity
        discrepancy_value = discrepancy * product.cost_price
        
        # Update stock if there's a discrepancy
        if discrepancy != 0:
            if stock:
                stock.quantity = physical_quantity
                stock.save()
            else:
                Stock.objects.create(
                    branch=branch,
                    product=product,
                    quantity=physical_quantity
                )
            
            # Create stock movement record
            StockMovement.objects.create(
                stock=stock if stock else Stock.objects.get(branch=branch, product=product),
                movement_type='ADJUSTMENT',
                quantity=discrepancy,
                status='APPROVED',
                notes=f'Physical count adjustment: {notes}'
            )
        
        discrepancy_type = "shortage" if discrepancy < 0 else "excess" if discrepancy > 0 else "match"
        
        if discrepancy == 0:
            messages.success(request, f'Stock count matches! No discrepancy found for {product.name}.')
        else:
            messages.warning(
                request, 
                f'Discrepancy found: {abs(discrepancy)} units {discrepancy_type} for {product.name}. '
                f'Value: KES {abs(discrepancy_value)}. Stock adjusted automatically.'
            )
        
        return JsonResponse({
            'status': 'success',
            'discrepancy': discrepancy,
            'discrepancy_value': float(discrepancy_value),
            'discrepancy_type': discrepancy_type
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# PDF Generation Views
@login_required
def sale_print(request, pk):
    """Generate PDF receipt for sale"""
    from .receipt_generator import ReceiptGenerator
    
    sale = get_object_or_404(Sale, pk=pk)
    generator = ReceiptGenerator()
    
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_sale_receipt(sale, format=format_type)


@login_required
def order_print(request, pk):
    """Generate PDF receipt for order"""
    from .receipt_generator import ReceiptGenerator
    
    order = get_object_or_404(Order, pk=pk)
    generator = ReceiptGenerator()
    
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_order_receipt(order, format=format_type)


@login_required
def expense_print(request, pk):
    """Generate PDF receipt for expense"""
    from .receipt_generator import ReceiptGenerator
    
    expense = get_object_or_404(Expense, pk=pk)
    generator = ReceiptGenerator()
    
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_expense_receipt(expense, format=format_type)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def financial_report_print(request):
    """Generate PDF for financial report"""
    from .receipt_generator import ReceiptGenerator
    from .delivery_manager import DeliveryChargesManager
    
    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date() + timedelta(days=1)
    else:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
    
    # Get financial data
    branches = Branch.objects.filter(is_active=True)
    report_items = []
    total_sales = Decimal('0.00')
    total_expenses = Decimal('0.00')
    
    for branch in branches:
        sales = Sale.objects.filter(
            branch=branch,
            created_at__gte=start_date,
            created_at__lt=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        expenses = Expense.objects.filter(
            branch=branch,
            expense_date__gte=start_date,
            expense_date__lt=end_date
        ).exclude(expense_type='DELIVERY').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        profit = sales - expenses
        
        report_items.append({
            'description': f'{branch.name} Branch Performance',
            'details': f'Sales: KES {sales:,.2f} | Expenses: KES {expenses:,.2f}',
            'quantity': 1,
            'unit': 'branch',
            'rate': profit,
            'total': profit
        })
        
        total_sales += sales
        total_expenses += expenses
    
    # Add delivery expenses
    delivery_expenses = DeliveryChargesManager.get_total_delivery_expenses(start_date, end_date)
    total_expenses += delivery_expenses
    
    if delivery_expenses > 0:
        report_items.append({
            'description': 'Business Delivery Charges',
            'details': 'Company-wide delivery expenses',
            'quantity': 1,
            'unit': 'total',
            'rate': -delivery_expenses,
            'total': -delivery_expenses
        })
    
    net_profit = total_sales - total_expenses
    
    report_data = {
        'prepared_by': request.user.get_full_name() or request.user.username,
        'branch': 'All Branches',
        'period': f'{datetime(year, month, 1).strftime("%B %Y")}',
        'items': report_items,
        'subtotal': total_sales,
        'discount': total_expenses,
        'tax': Decimal('0.00'),
        'tax_rate': 0,
        'grand_total': net_profit,
        'notes': f'Financial summary for {start_date} to {end_date - timedelta(days=1)}. Net business profit after all expenses including delivery charges.'
    }
    
    generator = ReceiptGenerator()
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_financial_report(report_data, format=format_type)


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER')
def branch_monthly_report(request, branch_id):
    """Generate monthly report for specific branch"""
    from .receipt_generator import ReceiptGenerator
    
    branch = get_object_or_404(Branch, pk=branch_id)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date() + timedelta(days=1)
    else:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
    
    generator = ReceiptGenerator()
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_branch_monthly_receipt(branch, start_date, end_date, format=format_type)


@login_required
@role_required('ADMIN', 'BOSS')
def business_master_report(request):
    """Generate master business report with all calculations"""
    from .receipt_generator import ReceiptGenerator
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date() + timedelta(days=1)
    else:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
    
    generator = ReceiptGenerator()
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_business_master_receipt(start_date, end_date, format=format_type)


@login_required
def trip_print(request, pk):
    """Generate PDF receipt for single trip"""
    from .receipt_generator import ReceiptGenerator
    
    trip = get_object_or_404(Trip, pk=pk)
    generator = ReceiptGenerator()
    
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_trip_receipt(trip=trip, format=format_type)


@login_required
def maintenance_print(request, pk):
    """Generate PDF receipt for single maintenance"""
    from .receipt_generator import ReceiptGenerator
    
    maintenance = get_object_or_404(VehicleMaintenance, pk=pk)
    generator = ReceiptGenerator()
    
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_maintenance_receipt(maintenance=maintenance, format=format_type)


@login_required
def logistics_print(request, pk):
    """Generate PDF receipt for logistics"""
    from .receipt_generator import ReceiptGenerator
    
    logistics = get_object_or_404(Logistics, pk=pk)
    generator = ReceiptGenerator()
    
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_expense_receipt(logistics, format=format_type)


@login_required
def trip_print(request, pk):
    """Generate PDF receipt for trip"""
    from .receipt_generator import ReceiptGenerator
    
    trip = get_object_or_404(Trip, pk=pk)
    
    context = {
        'document_type': 'Trip Receipt',
        'document_number': trip.trip_number,
        'document_date': trip.scheduled_date.strftime('%d %B %Y'),
        'prepared_by': trip.created_by.get_full_name() if trip.created_by else 'System',
        'branch': trip.vehicle.branch.name if trip.vehicle else 'N/A',
        'customer': {
            'name': trip.customer_name or 'Company Trip',
            'phone': trip.customer_phone,
        },
        'items': [{
            'description': f'Trip: {trip.origin} → {trip.destination}',
            'details': f'Vehicle: {trip.vehicle.registration_number if trip.vehicle else "N/A"} | Driver: {trip.driver.full_name if trip.driver else "N/A"}',
            'quantity': 1,
            'unit': 'trip',
            'rate': trip.revenue,
            'total': trip.revenue
        }],
        'subtotal': trip.revenue,
        'discount': trip.fuel_cost + trip.other_expenses,
        'grand_total': trip.net_profit,
        'notes': f'Distance: {trip.distance}km | Fuel Cost: KES {trip.fuel_cost} | Other Expenses: KES {trip.other_expenses}'
    }
    
    generator = ReceiptGenerator()
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_financial_report(context, format=format_type)


@login_required
def logistics_print(request, pk):
    """Generate PDF receipt for logistics"""
    from .receipt_generator import ReceiptGenerator
    
    logistics = get_object_or_404(Logistics, pk=pk)
    
    context = {
        'document_type': 'Logistics Receipt',
        'document_number': logistics.tracking_number,
        'document_date': logistics.created_at.strftime('%d %B %Y'),
        'prepared_by': logistics.created_by.get_full_name() if logistics.created_by else 'System',
        'branch': logistics.from_branch.name,
        'customer': {
            'name': logistics.customer_name,
            'phone': logistics.customer_phone,
            'address': logistics.to_address
        },
        'items': [{
            'description': f'Delivery Service - {logistics.get_status_display()}',
            'details': f'From: {logistics.from_branch.name} | Vehicle: {logistics.vehicle_number or "TBD"} | Driver: {logistics.driver_name or "TBD"}',
            'quantity': 1,
            'unit': 'delivery',
            'rate': logistics.delivery_cost,
            'total': logistics.delivery_cost
        }],
        'subtotal': logistics.delivery_cost,
        'grand_total': logistics.delivery_cost,
        'notes': f'Delivery Date: {logistics.delivery_date or "TBD"} | Status: {logistics.get_status_display()}'
    }
    
    generator = ReceiptGenerator()
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_financial_report(context, format=format_type)


@login_required
def maintenance_print(request, pk):
    """Generate PDF receipt for maintenance"""
    from .receipt_generator import ReceiptGenerator
    
    maintenance = get_object_or_404(VehicleMaintenance, pk=pk)
    
    context = {
        'document_type': 'Maintenance Receipt',
        'document_number': maintenance.maintenance_number,
        'document_date': maintenance.service_date.strftime('%d %B %Y'),
        'prepared_by': maintenance.created_by.get_full_name() if maintenance.created_by else 'System',
        'branch': maintenance.vehicle.branch.name,
        'customer': {
            'name': maintenance.service_provider,
            'address': f'Vehicle: {maintenance.vehicle.registration_number}'
        },
        'items': [{
            'description': f'{maintenance.get_maintenance_type_display()} - {maintenance.description}',
            'details': f'Mileage: {maintenance.mileage_at_service}km | Receipt: {maintenance.receipt_number or "N/A"}',
            'quantity': 1,
            'unit': 'service',
            'rate': maintenance.total_cost,
            'total': maintenance.total_cost
        }],
        'subtotal': maintenance.total_cost,
        'grand_total': maintenance.total_cost,
        'notes': f'Status: {maintenance.get_status_display()} | Next Service: {maintenance.next_service_mileage or "TBD"}km'
    }
    
    generator = ReceiptGenerator()
    format_type = request.GET.get('format', 'pdf')
    return generator.generate_financial_report(context, format=format_type)

@login_required
def trips_print(request):
    """Generate PDF for trips list"""
    from .receipt_generator import ReceiptGenerator
    
    # Get filters
    search = request.GET.get('search', '')
    vehicle_id = request.GET.get('vehicle', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    trips = Trip.objects.select_related('vehicle', 'driver', 'sale').all()
    
    if search:
        trips = trips.filter(
            Q(trip_number__icontains=search) | 
            Q(origin__icontains=search) | 
            Q(destination__icontains=search)
        )
    if vehicle_id:
        trips = trips.filter(vehicle_id=vehicle_id)
    if date_from:
        trips = trips.filter(scheduled_date__gte=date_from)
    if date_to:
        trips = trips.filter(scheduled_date__lte=date_to + ' 23:59:59')
    
    # Prepare report data
    report_items = []
    total_revenue = Decimal('0.00')
    total_costs = Decimal('0.00')
    
    for trip in trips:
        costs = trip.fuel_cost + trip.other_expenses
        profit = trip.revenue - costs
        
        report_items.append({
            'description': f'{trip.trip_number} - {trip.origin} → {trip.destination}',
            'details': f'Vehicle: {trip.vehicle.registration_number if trip.vehicle else "N/A"} | Driver: {trip.driver.full_name if trip.driver else "N/A"} | Date: {trip.scheduled_date}',
            'quantity': 1,
            'unit': 'trip',
            'rate': trip.revenue,
            'total': profit
        })
        total_revenue += trip.revenue
        total_costs += costs
    
    report_data = {
        'document_type': 'Trips Report',
        'document_number': f'TRIPS-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
        'document_date': timezone.now().strftime('%d %B %Y'),
        'prepared_by': request.user.get_full_name() or request.user.username,
        'branch': 'All Branches',
        'items': report_items,
        'subtotal': total_revenue,
        'discount': total_costs,
        'grand_total': total_revenue - total_costs,
        'notes': f'Total Trips: {trips.count()} | Total Revenue: KES {total_revenue:,.2f} | Total Costs: KES {total_costs:,.2f} | Net Profit: KES {total_revenue - total_costs:,.2f}'
    }
    
    generator = ReceiptGenerator()
    return generator.generate_financial_report(report_data, format='pdf')


@login_required
def stock_print(request):
    """Generate PDF for stock list"""
    from .receipt_generator import ReceiptGenerator
    from .models import StockMovement
    
    search = request.GET.get('search', '')
    branch_id = request.GET.get('branch', '')
    stocks = Stock.objects.select_related('product', 'branch').all()
    
    if search:
        stocks = stocks.filter(
            Q(product__name__icontains=search) | 
            Q(product__sku__icontains=search)
        )
    if branch_id:
        stocks = stocks.filter(branch_id=branch_id)
    
    # Determine branch name for header
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
            branch_name = branch.name.upper()
        except Branch.DoesNotExist:
            branch_name = 'UNKNOWN BRANCH'
    else:
        branch_name = 'ALL BRANCHES'
    
    report_items = []
    
    for stock in stocks:
        # Get recent stock movements to show how balance was reached
        movements = StockMovement.objects.filter(
            stock=stock
        ).order_by('-created_at')[:5]
        
        movement_details = []
        for mov in movements:
            movement_details.append(f'{mov.get_movement_type_display()}: {mov.quantity} ({mov.created_at.strftime("%m/%d")})')
        
        report_items.append({
            'description': f'{stock.product.name} ({stock.product.sku})',
            'details': f'Branch: {stock.branch.name} | Min Qty: {stock.min_quantity} | Recent: {" | ".join(movement_details[:3]) if movement_details else "No movements"}',
            'quantity': stock.quantity,
            'unit': 'units',
            'rate': 0,
            'total': 0
        })
    
    report_data = {
        'document_type': 'STOCK BALANCE REPORT',
        'document_number': f'STOCK-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
        'document_date': timezone.now().strftime('%d %B %Y'),
        'prepared_by': request.user.get_full_name() or request.user.username,
        'branch': branch_name,
        'items': report_items,
        'notes': f'Stock Balance Report - {stocks.count()} items. Shows current quantities and recent movements that led to current balance.'
    }
    
    generator = ReceiptGenerator()
    return generator.generate_stock_report(report_data, format='pdf')


@login_required
def stock_movements_print(request):
    """Generate PDF for stock movements"""
    from .receipt_generator import ReceiptGenerator
    
    search = request.GET.get('search', '')
    branch_id = request.GET.get('branch', '')
    movements = StockMovement.objects.select_related('stock__product', 'stock__branch', 'from_branch', 'to_branch').all()
    
    if branch_id:
        movements = movements.filter(
            Q(stock__branch_id=branch_id) | 
            Q(from_branch_id=branch_id) | 
            Q(to_branch_id=branch_id)
        )
    
    if search:
        movements = movements.filter(
            Q(stock__product__name__icontains=search) | 
            Q(notes__icontains=search)
        )
    
    report_items = []
    for movement in movements:
        value = abs(movement.quantity) * movement.stock.product.cost_price
        report_items.append({
            'description': f'{movement.get_movement_type_display()} - {movement.stock.product.name}',
            'details': f'From: {movement.from_branch.name if movement.from_branch else "N/A"} | To: {movement.to_branch.name if movement.to_branch else "N/A"} | Status: {movement.get_status_display()}',
            'quantity': abs(movement.quantity),
            'unit': 'units',
            'rate': movement.stock.product.cost_price,
            'total': value
        })
    
    report_data = {
        'document_type': 'Stock Movements Report',
        'document_number': f'MOVEMENTS-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
        'document_date': timezone.now().strftime('%d %B %Y'),
        'prepared_by': request.user.get_full_name() or request.user.username,
        'branch': 'All Branches',
        'items': report_items,
        'notes': f'Total Movements: {movements.count()}'
    }
    
    generator = ReceiptGenerator()
    return generator.generate_financial_report(report_data, format='pdf')


@login_required
def expenses_print(request):
    """Generate PDF for expenses list"""
    from .receipt_generator import ReceiptGenerator
    
    search = request.GET.get('search', '')
    expenses = Expense.objects.select_related('branch', 'sale', 'created_by').all()
    
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    if user_profile and user_profile.role == 'SALES' and user_profile.branch:
        expenses = expenses.filter(branch=user_profile.branch)
    
    if search:
        expenses = expenses.filter(
            Q(expense_number__icontains=search) | 
            Q(description__icontains=search)
        )
    
    report_items = []
    total_amount = Decimal('0.00')
    
    for expense in expenses:
        report_items.append({
            'description': f'{expense.expense_number} - {expense.description}',
            'details': f'Branch: {expense.branch.name} | Type: {expense.get_expense_type_display()} | Date: {expense.expense_date}',
            'quantity': 1,
            'unit': 'expense',
            'rate': expense.amount,
            'total': expense.amount
        })
        total_amount += expense.amount
    
    report_data = {
        'document_type': 'Expenses Report',
        'document_number': f'EXPENSES-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
        'document_date': timezone.now().strftime('%d %B %Y'),
        'prepared_by': request.user.get_full_name() or request.user.username,
        'branch': 'All Branches',
        'items': report_items,
        'subtotal': total_amount,
        'grand_total': total_amount,
        'notes': f'Total Expenses: {expenses.count()} | Total Amount: KES {total_amount:,.2f}'
    }
    
    generator = ReceiptGenerator()
    return generator.generate_financial_report(report_data, format='pdf')


@login_required
def notes_print(request):
    """Generate PDF for notes list"""
    from .receipt_generator import ReceiptGenerator
    
    search = request.GET.get('search', '')
    priority = request.GET.get('priority', '')
    notes = BusinessNote.objects.select_related('created_by').all()
    
    if search:
        notes = notes.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search) | 
            Q(tags__icontains=search)
        )
    
    if priority:
        notes = notes.filter(priority=priority)
    
    report_items = []
    for note in notes:
        report_items.append({
            'description': f'{note.title}',
            'details': f'Priority: {note.get_priority_display()} | Tags: {note.tags or "None"} | Created: {note.created_at.strftime("%Y-%m-%d")}',
            'quantity': 1,
            'unit': 'note',
            'rate': 0,
            'total': 0
        })
    
    report_data = {
        'document_type': 'Business Notes Report',
        'document_number': f'NOTES-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
        'document_date': timezone.now().strftime('%d %B %Y'),
        'prepared_by': request.user.get_full_name() or request.user.username,
        'branch': 'All Branches',
        'items': report_items,
        'notes': f'Total Notes: {notes.count()}'
    }
    
    generator = ReceiptGenerator()
    return generator.generate_financial_report(report_data, format='pdf')