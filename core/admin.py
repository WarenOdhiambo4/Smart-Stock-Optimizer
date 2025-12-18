from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Branch, Employee, Product, Stock, StockMovement, Order, OrderItem, 
    Sale, SaleItem, UserProfile, Expense, Logistics, Vehicle, Trip, VehicleMaintenance,
    OrderFulfillment, OrderShipment, ShipmentItem, PaymentCollection, BusinessNote
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'address', 'email']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'position', 'is_active']
    list_filter = ['is_active', 'branches']
    search_fields = ['first_name', 'last_name', 'email']
    filter_horizontal = ['branches']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'unit_price', 'cost_price', 'category', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['name', 'sku', 'description']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'branch', 'quantity', 'min_quantity', 'is_low_stock']
    list_filter = ['branch']
    search_fields = ['product__name', 'branch__name']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['stock', 'movement_type', 'quantity', 'status', 'created_at']
    list_filter = ['movement_type', 'status']
    search_fields = ['stock__product__name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'branch', 'supplier', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'branch']
    search_fields = ['order_number', 'supplier']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'unit_price', 'subtotal']
    search_fields = ['product_name', 'order__order_number']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'branch', 'customer_name', 'total_amount', 'payment_method', 'created_at']
    list_filter = ['branch', 'payment_method']
    search_fields = ['sale_number', 'customer_name']


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'stock', 'quantity', 'unit_price', 'subtotal']
    search_fields = ['sale__sale_number']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'branch', 'phone']
    list_filter = ['role', 'branch']
    search_fields = ['user__username', 'user__email']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'branch', 'expense_type', 'amount', 'expense_date', 'sale', 'is_auto_generated']
    list_filter = ['expense_type', 'branch', 'expense_date']
    search_fields = ['expense_number', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'expense_date'
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('expense_number', 'branch', 'expense_type')
        }),
        ('Details', {
            'fields': ('description', 'amount', 'expense_date')
        }),
        ('References', {
            'fields': ('sale', 'receipt_number')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duplicate_expense', 'export_expenses']
    
    def is_auto_generated(self, obj):
        """Check if expense was auto-generated"""
        return obj.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-'))
    is_auto_generated.boolean = True
    is_auto_generated.short_description = 'Auto Generated'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of auto-generated expenses"""
        if obj and obj.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of auto-generated expenses"""
        if obj and obj.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
            return False
        return super().has_change_permission(request, obj)
    
    def duplicate_expense(self, request, queryset):
        """Duplicate selected expenses"""
        for expense in queryset:
            if not expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
                new_expense = Expense.objects.create(
                    expense_number=f"DUP-{expense.expense_number}",
                    branch=expense.branch,
                    expense_type=expense.expense_type,
                    description=f"Copy of: {expense.description}",
                    amount=expense.amount,
                    expense_date=expense.expense_date,
                    receipt_number=expense.receipt_number,
                    notes=expense.notes,
                    created_by=expense.created_by
                )
        self.message_user(request, f"Duplicated {queryset.count()} expenses")
    duplicate_expense.short_description = "Duplicate selected expenses"
    
    def export_expenses(self, request, queryset):
        """Export expenses to CSV"""
        # This will be implemented with CSV export functionality
        self.message_user(request, f"Expense export not yet implemented")
    export_expenses.short_description = "Export to CSV"


@admin.register(Logistics)
class LogisticsAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'customer_name', 'from_branch', 'vehicle', 'driver', 'status', 'delivery_date', 'delivery_cost']
    list_filter = ['status', 'from_branch', 'vehicle']
    search_fields = ['tracking_number', 'customer_name', 'customer_phone']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'vehicle_type', 'make', 'model', 'year', 'branch', 'assigned_driver', 'status', 'current_mileage']
    list_filter = ['status', 'vehicle_type', 'branch']
    search_fields = ['registration_number', 'make', 'model']
    readonly_fields = ['total_trips', 'total_revenue', 'total_maintenance_cost', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('registration_number', 'vehicle_type', 'make', 'model', 'year', 'color')
        }),
        ('Assignment', {
            'fields': ('branch', 'assigned_driver', 'status')
        }),
        ('Tracking', {
            'fields': ('current_mileage', 'fuel_capacity')
        }),
        ('Financial', {
            'fields': ('purchase_price', 'purchase_date', 'total_revenue', 'total_maintenance_cost')
        }),
        ('Compliance', {
            'fields': ('insurance_expiry', 'registration_expiry')
        }),
        ('Additional Info', {
            'fields': ('notes', 'total_trips', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['trip_number', 'vehicle', 'driver', 'trip_type', 'origin', 'destination', 'status', 'scheduled_date', 'revenue', 'net_profit']
    list_filter = ['status', 'trip_type', 'vehicle']
    search_fields = ['trip_number', 'origin', 'destination', 'customer_name']
    readonly_fields = ['net_profit', 'duration', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Trip Information', {
            'fields': ('trip_number', 'vehicle', 'driver', 'trip_type', 'status')
        }),
        ('Route Details', {
            'fields': ('origin', 'destination', 'distance')
        }),
        ('Related Records', {
            'fields': ('sale', 'logistics')
        }),
        ('Schedule & Timing', {
            'fields': ('scheduled_date', 'start_time', 'end_time', 'duration')
        }),
        ('Financial', {
            'fields': ('revenue', 'fuel_cost', 'other_expenses', 'net_profit')
        }),
        ('Mileage Tracking', {
            'fields': ('start_mileage', 'end_mileage')
        }),
        ('Customer Info', {
            'fields': ('customer_name', 'customer_phone'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['maintenance_number', 'vehicle', 'maintenance_type', 'service_date', 'status', 'total_cost', 'service_provider']
    list_filter = ['status', 'maintenance_type', 'service_date', 'vehicle']
    search_fields = ['maintenance_number', 'vehicle__registration_number', 'service_provider', 'description']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']
    date_hierarchy = 'service_date'
    
    fieldsets = (
        ('Maintenance Information', {
            'fields': ('maintenance_number', 'vehicle', 'maintenance_type', 'status')
        }),
        ('Service Details', {
            'fields': ('description', 'service_provider', 'service_date', 'completion_date')
        }),
        ('Costs', {
            'fields': ('parts_cost', 'labor_cost', 'other_costs', 'total_cost', 'receipt_number')
        }),
        ('Mileage Tracking', {
            'fields': ('mileage_at_service', 'next_service_mileage')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 1
    fields = ['order_item', 'quantity_ordered', 'quantity_delivered', 'quantity_remaining', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(OrderFulfillment)
class OrderFulfillmentAdmin(admin.ModelAdmin):
    list_display = [
        'fulfillment_number', 'order', 'branch', 'status', 
        'fulfillment_percentage', 'payment_percentage',
        'total_items_fulfilled', 'total_items_ordered',
        'total_collected', 'total_order_value', 'created_at'
    ]
    list_filter = ['status', 'branch', 'created_at']
    search_fields = ['fulfillment_number', 'order__order_number']
    readonly_fields = [
        'fulfillment_percentage', 'payment_percentage',
        'total_items_ordered', 'total_items_fulfilled', 'total_items_remaining',
        'total_collected', 'total_remaining', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Fulfillment Information', {
            'fields': ('fulfillment_number', 'order', 'branch', 'status')
        }),
        ('Item Tracking', {
            'fields': (
                ('total_items_ordered', 'total_items_fulfilled', 'total_items_remaining'),
                'fulfillment_percentage'
            ),
            'classes': ('wide',)
        }),
        ('Financial Tracking', {
            'fields': (
                ('total_order_value', 'total_collected', 'total_remaining'),
                'payment_percentage'
            ),
            'classes': ('wide',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_fulfillment_status']
    
    def recalculate_fulfillment_status(self, request, queryset):
        for fulfillment in queryset:
            fulfillment.calculate_fulfillment_status()
        self.message_user(request, f"Recalculated status for {queryset.count()} fulfillments")
    recalculate_fulfillment_status.short_description = "Recalculate fulfillment status"


@admin.register(OrderShipment)
class OrderShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'shipment_number', 'fulfillment', 'vehicle', 'driver', 
        'status', 'items_loaded', 'vehicle_capacity',
        'scheduled_date', 'actual_delivery_date', 'customer_name'
    ]
    list_filter = ['status', 'vehicle', 'scheduled_date', 'actual_delivery_date']
    search_fields = ['shipment_number', 'customer_name', 'customer_phone', 'fulfillment__fulfillment_number']
    readonly_fields = ['items_loaded', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    inlines = [ShipmentItemInline]
    
    fieldsets = (
        ('Shipment Information', {
            'fields': ('shipment_number', 'fulfillment', 'status')
        }),
        ('Vehicle & Capacity', {
            'fields': (
                ('vehicle', 'driver'),
                ('vehicle_capacity', 'items_loaded'),
                'trip'
            )
        }),
        ('Schedule & Delivery', {
            'fields': (
                'scheduled_date',
                'actual_delivery_date',
                'customer_signature'
            )
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'delivery_address')
        }),
        ('Financial', {
            'fields': ('delivery_fee',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_delivered', 'assign_to_branch_stock']
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='DELIVERED')
        self.message_user(request, f"Marked {queryset.count()} shipments as delivered")
    mark_as_delivered.short_description = "Mark as delivered"
    
    def assign_to_branch_stock(self, request, queryset):
        for shipment in queryset:
            shipment.assign_to_branch_stock()
        self.message_user(request, f"Assigned stock for {queryset.count()} shipments")
    assign_to_branch_stock.short_description = "Assign products to branch stock"


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = [
        'shipment', 'order_item', 
        'quantity_ordered', 'quantity_delivered', 'quantity_remaining',
        'unit_price', 'subtotal'
    ]
    list_filter = ['shipment__status', 'shipment__scheduled_date']
    search_fields = ['shipment__shipment_number', 'order_item__product_name']
    readonly_fields = ['subtotal', 'created_at']


@admin.register(PaymentCollection)
class PaymentCollectionAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'fulfillment', 'amount_collected',
        'payment_method', 'status', 'is_deposited',
        'deposited_to_branch', 'payment_date', 'is_outstanding'
    ]
    list_filter = [
        'status', 'payment_method', 'is_deposited',
        'payment_date', 'deposited_to_branch', 'branch'
    ]
    search_fields = ['payment_number', 'reference_number', 'receipt_number', 'fulfillment__fulfillment_number']
    readonly_fields = ['is_outstanding', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_number',
                ('fulfillment', 'shipment'),
                'branch'
            )
        }),
        ('Payment Details', {
            'fields': (
                'amount_collected',
                'payment_method',
                'status',
                'payment_date'
            )
        }),
        ('Deposit Tracking', {
            'fields': (
                'is_deposited',
                'deposited_to_branch',
                'deposit_date',
                'is_outstanding'
            ),
            'classes': ('wide',)
        }),
        ('References', {
            'fields': ('reference_number', 'receipt_number')
        }),
        ('Additional Info', {
            'fields': ('notes', 'collected_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_deposited', 'generate_payment_report']
    
    def mark_as_deposited(self, request, queryset):
        queryset.update(is_deposited=True)
        self.message_user(request, f"Marked {queryset.count()} payments as deposited")
    mark_as_deposited.short_description = "Mark as deposited"
    
    def generate_payment_report(self, request, queryset):
        # This will be implemented with Excel export functionality
        self.message_user(request, f"Payment report generation not yet implemented")
    generate_payment_report.short_description = "Generate payment report"


@admin.register(BusinessNote)
class BusinessNoteAdmin(admin.ModelAdmin):
    list_display = ['page_number', 'content_preview', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['page_number']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
