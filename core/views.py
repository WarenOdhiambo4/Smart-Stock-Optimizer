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

from .models import Branch, Employee, Product, Stock, StockMovement, Order, OrderItem, Sale, SaleItem, UserProfile, Expense, Logistics, Vehicle, Trip, VehicleMaintenance, BusinessNote


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


def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
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
    
    total_expenses = Expense.objects.filter(expense_filter).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_expenses = Expense.objects.filter(expense_filter, expense_date__gte=month_start).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_profit = total_sales - total_expenses
    monthly_profit = monthly_sales - monthly_expenses
    
    recent_sales = Sale.objects.filter(sales_filter).select_related('branch')[:5]
    recent_orders = Order.objects.select_related('branch')[:5]
    recent_expenses = Expense.objects.filter(expense_filter).select_related('branch')[:5]
    
    low_stock_items = Stock.objects.filter(quantity__lte=F('min_quantity')).select_related('product', 'branch')[:10]
    pending_orders = Order.objects.filter(status='PENDING').count()
    pending_transfers = StockMovement.objects.filter(movement_type='TRANSFER', status='PENDING').count()
    pending_logistics = Logistics.objects.filter(status__in=['PENDING', 'PROCESSING', 'IN_TRANSIT']).count()
    
    # Get transfer alerts for user's branch
    transfer_alerts = []
    
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
        'transfer_alerts': transfer_alerts,
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
        
        stock, created = Stock.objects.get_or_create(
            branch_id=branch_id,
            product_id=product_id,
            defaults={'quantity': quantity, 'min_quantity': min_quantity}
        )
        if not created:
            stock.quantity += quantity
            stock.min_quantity = min_quantity
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
    
    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/order_list.html', {
        'page_obj': page_obj,
        'orders': page_obj,
        'search': search
    })


def order_create(request):
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        order = Order.objects.create(
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            branch_id=request.POST.get('branch'),
            supplier=request.POST.get('supplier', ''),
            notes=request.POST.get('notes', ''),
        )
        
        product_names = request.POST.getlist('product_name')
        product_skus = request.POST.getlist('product_sku')
        quantities = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')
        
        for i in range(len(product_names)):
            if product_names[i]:
                OrderItem.objects.create(
                    order=order,
                    product_name=product_names[i],
                    product_sku=product_skus[i] if i < len(product_skus) else '',
                    quantity=int(quantities[i]) if i < len(quantities) else 1,
                    unit_price=Decimal(unit_prices[i]) if i < len(unit_prices) else Decimal('0'),
                )
        
        order.calculate_total()
        messages.success(request, f'Order {order.order_number} created!')
        return redirect('order_list')
    
    return render(request, 'core/order_form.html', {'branches': branches, 'action': 'Create'})


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'core/order_detail.html', {'order': order})


def order_complete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.status = 'COMPLETED'
        order.save()
        
        for item in order.items.all():
            stock, created = Stock.objects.get_or_create(
                branch=order.branch,
                product=item.product,
                defaults={'quantity': 0}
            )
            stock.quantity += item.quantity
            stock.save()
            
            StockMovement.objects.create(
                stock=stock,
                movement_type='IN',
                quantity=item.quantity,
                status='APPROVED',
                notes=f"Order #{order.order_number} completed"
            )
        
        messages.success(request, f'Order {order.order_number} completed! Stock updated.')
    return redirect('order_list')


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'FINANCE', 'SALES')
def sale_list(request):
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
        sales = sales.filter(created_at__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__lte=date_to + ' 23:59:59')
    
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
        sale = Sale.objects.create(
            sale_number=f"SALE-{uuid.uuid4().hex[:8].upper()}",
            branch_id=branch_id,
            customer_name=request.POST.get('customer_name', ''),
            customer_phone=request.POST.get('customer_phone', ''),
            payment_method=request.POST.get('payment_method', 'Cash'),
            notes=request.POST.get('notes', ''),
        )
        
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
        
        # Add expense if provided
        expense_amount = request.POST.get('expense_amount')
        if expense_amount and Decimal(expense_amount) > 0:
            Expense.objects.create(
                expense_number=f"EXP-{uuid.uuid4().hex[:8].upper()}",
                branch_id=branch_id,
                sale=sale,
                expense_type='SALE_RELATED',
                description=request.POST.get('expense_description', 'Sale related expense'),
                amount=Decimal(expense_amount),
                expense_date=timezone.now().date(),
                notes=request.POST.get('expense_notes', ''),
            )
        
        messages.success(request, f'Sale {sale.sale_number} created successfully!')
        return redirect('sale_list')
    
    return render(request, 'core/sale_form.html', {'branches': branches, 'action': 'Create'})


def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'core/sale_detail.html', {'sale': sale})


def get_branch_stocks(request, branch_id):
    stocks = Stock.objects.filter(branch_id=branch_id, quantity__gt=0).select_related('product')
    data = [
        {
            'id': s.id,
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
        expense = Expense.objects.create(
            expense_number=f"EXP-{uuid.uuid4().hex[:8].upper()}",
            branch_id=request.POST.get('branch'),
            sale_id=request.POST.get('sale') if request.POST.get('sale') else None,
            expense_type=request.POST.get('expense_type'),
            description=request.POST.get('description'),
            amount=Decimal(request.POST.get('amount', '0')),
            expense_date=request.POST.get('expense_date'),
            receipt_number=request.POST.get('receipt_number', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Expense {expense.expense_number} created!')
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
    # Get date range from request or default to current month
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Calculate date range
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
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
        
        expenses = Expense.objects.filter(
            branch=branch,
            expense_date__gte=start_date,
            expense_date__lt=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
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
    
    context = {
        'branch_reports': branch_reports,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'year': year,
        'month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
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
        trip = Trip.objects.create(
            trip_number=f"TRIP-{uuid.uuid4().hex[:8].upper()}",
            vehicle_id=request.POST.get('vehicle'),
            driver_id=request.POST.get('driver'),
            trip_type=request.POST.get('trip_type'),
            origin=request.POST.get('origin'),
            destination=request.POST.get('destination'),
            distance=Decimal(request.POST.get('distance', '0')),
            sale_id=request.POST.get('sale') if request.POST.get('sale') else None,
            scheduled_date=request.POST.get('scheduled_date'),
            revenue=Decimal(request.POST.get('revenue', '0')),
            fuel_cost=Decimal(request.POST.get('fuel_cost', '0')),
            other_expenses=Decimal(request.POST.get('other_expenses', '0')),
            customer_name=request.POST.get('customer_name', ''),
            customer_phone=request.POST.get('customer_phone', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Trip {trip.trip_number} created successfully!')
        return redirect('trip_list')
    
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
