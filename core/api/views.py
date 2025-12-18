from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.db import models

from core.models import (
    Branch, Employee, Product, Stock, StockMovement, Order, OrderItem,
    Sale, SaleItem, Expense, Vehicle, Trip, VehicleMaintenance,
    OrderFulfillment, OrderShipment, ShipmentItem, PaymentCollection,
    Logistics
)
from .serializers import (
    BranchSerializer, EmployeeSerializer, ProductSerializer, StockSerializer,
    StockMovementSerializer, OrderSerializer, OrderItemSerializer,
    SaleSerializer, SaleItemSerializer, ExpenseSerializer, VehicleSerializer,
    TripSerializer, VehicleMaintenanceSerializer, OrderFulfillmentSerializer,
    OrderShipmentSerializer, ShipmentItemSerializer, PaymentCollectionSerializer,
    LogisticsSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Enterprise-standard pagination"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'address', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'position', 'branches']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['first_name']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'category']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'unit_price', 'created_at']
    ordering = ['name']


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related('branch', 'product')
    serializer_class = StockSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'product']
    search_fields = ['product__name', 'branch__name']
    ordering_fields = ['quantity', 'updated_at']
    ordering = ['-updated_at']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock"""
        low_stock_items = self.queryset.filter(quantity__lte=models.F('min_quantity'))
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related('stock', 'from_branch', 'to_branch')
    serializer_class = StockMovementSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['movement_type', 'status', 'from_branch', 'to_branch']
    search_fields = ['stock__product__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('branch').prefetch_related('items')
    serializer_class = OrderSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'branch']
    search_fields = ['order_number', 'supplier']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related('order', 'product')
    serializer_class = OrderItemSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['product_name', 'order__order_number']


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related('branch').prefetch_related('items')
    serializer_class = SaleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'payment_method']
    search_fields = ['sale_number', 'customer_name']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's sales"""
        from django.utils import timezone
        today = timezone.now().date()
        today_sales = self.queryset.filter(created_at__date=today)
        serializer = self.get_serializer(today_sales, many=True)
        return Response(serializer.data)


class SaleItemViewSet(viewsets.ModelViewSet):
    queryset = SaleItem.objects.select_related('sale', 'stock')
    serializer_class = SaleItemSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['sale__sale_number', 'stock__product__name']


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related('branch', 'sale')
    serializer_class = ExpenseSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['expense_type', 'branch']
    search_fields = ['expense_number', 'description']
    ordering_fields = ['expense_date', 'amount']
    ordering = ['-expense_date']
    
    def update(self, request, *args, **kwargs):
        """Update expense with validation"""
        expense = self.get_object()
        
        # Check if expense is auto-generated (prevent modification of system expenses)
        if expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
            return Response(
                {'error': 'Cannot modify auto-generated expenses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete expense with validation"""
        expense = self.get_object()
        
        # Check if expense is auto-generated
        if expense.expense_number.startswith(('TRIP-', 'MAINT-', 'LOSS-')):
            return Response(
                {'error': 'Cannot delete auto-generated expenses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get expenses grouped by type"""
        from django.db.models import Sum
        expense_summary = self.queryset.values('expense_type').annotate(
            total_amount=Sum('amount'),
            count=models.Count('id')
        ).order_by('-total_amount')
        
        return Response(expense_summary)
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly expense summary"""
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth
        
        monthly_expenses = self.queryset.annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            count=models.Count('id')
        ).order_by('-month')
        
        return Response(monthly_expenses)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related('branch', 'assigned_driver')
    serializer_class = VehicleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'vehicle_type', 'branch']
    search_fields = ['registration_number', 'make', 'model']
    ordering_fields = ['registration_number', 'current_mileage']
    ordering = ['registration_number']
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available vehicles (active status)"""
        available_vehicles = self.queryset.filter(status='ACTIVE')
        serializer = self.get_serializer(available_vehicles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def maintenance_due(self, request):
        """Get vehicles due for maintenance"""
        vehicles = [v for v in self.queryset.all() if v.is_due_for_maintenance]
        serializer = self.get_serializer(vehicles, many=True)
        return Response(serializer.data)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.select_related('vehicle', 'driver', 'sale')
    serializer_class = TripSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'trip_type', 'vehicle', 'driver']
    search_fields = ['trip_number', 'origin', 'destination']
    ordering_fields = ['scheduled_date', 'revenue']
    ordering = ['-scheduled_date']
    
    @action(detail=False, methods=['get'])
    def profitability(self, request):
        """Get profitability analysis of trips"""
        trips = self.queryset.filter(status='COMPLETED')
        total_revenue = sum(t.revenue for t in trips)
        total_costs = sum(t.fuel_cost + t.other_expenses for t in trips)
        total_profit = total_revenue - total_costs
        
        return Response({
            'total_trips': trips.count(),
            'total_revenue': total_revenue,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'average_profit_per_trip': total_profit / trips.count() if trips.count() > 0 else 0
        })


class VehicleMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = VehicleMaintenance.objects.select_related('vehicle')
    serializer_class = VehicleMaintenanceSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'maintenance_type', 'vehicle']
    search_fields = ['maintenance_number', 'vehicle__registration_number']
    ordering_fields = ['service_date', 'total_cost']
    ordering = ['-service_date']


class OrderFulfillmentViewSet(viewsets.ModelViewSet):
    queryset = OrderFulfillment.objects.select_related('order', 'branch').prefetch_related('shipments', 'payments')
    serializer_class = OrderFulfillmentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'branch']
    search_fields = ['fulfillment_number', 'order__order_number']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """Recalculate fulfillment status"""
        fulfillment = self.get_object()
        fulfillment.calculate_fulfillment_status()
        serializer = self.get_serializer(fulfillment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_payments(self, request):
        """Get fulfillments with pending payments"""
        pending = self.queryset.filter(total_remaining__gt=0)
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)


class OrderShipmentViewSet(viewsets.ModelViewSet):
    queryset = OrderShipment.objects.select_related('fulfillment', 'vehicle', 'driver').prefetch_related('items')
    serializer_class = OrderShipmentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'vehicle', 'driver']
    search_fields = ['shipment_number', 'customer_name']
    ordering_fields = ['scheduled_date']
    ordering = ['-scheduled_date']
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark shipment as delivered"""
        shipment = self.get_object()
        shipment.status = 'DELIVERED'
        shipment.save()
        shipment.assign_to_branch_stock()
        serializer = self.get_serializer(shipment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def in_transit(self, request):
        """Get shipments currently in transit"""
        in_transit = self.queryset.filter(status='IN_TRANSIT')
        serializer = self.get_serializer(in_transit, many=True)
        return Response(serializer.data)


class ShipmentItemViewSet(viewsets.ModelViewSet):
    queryset = ShipmentItem.objects.select_related('shipment', 'order_item')
    serializer_class = ShipmentItemSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['shipment__shipment_number', 'order_item__product_name']


class PaymentCollectionViewSet(viewsets.ModelViewSet):
    queryset = PaymentCollection.objects.select_related('fulfillment', 'branch', 'deposited_to_branch')
    serializer_class = PaymentCollectionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'is_deposited', 'branch', 'deposited_to_branch']
    search_fields = ['payment_number', 'reference_number']
    ordering_fields = ['payment_date', 'amount_collected']
    ordering = ['-payment_date']
    
    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """Get outstanding payments (collected but not deposited)"""
        outstanding = self.queryset.filter(status='COMPLETED', is_deposited=False)
        total_outstanding = sum(p.amount_collected for p in outstanding)
        
        serializer = self.get_serializer(outstanding, many=True)
        return Response({
            'count': outstanding.count(),
            'total_amount': total_outstanding,
            'payments': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_deposited(self, request, pk=None):
        """Mark payment as deposited"""
        payment = self.get_object()
        payment.is_deposited = True
        payment.save()
        serializer = self.get_serializer(payment)
        return Response(serializer.data)


class LogisticsViewSet(viewsets.ModelViewSet):
    queryset = Logistics.objects.select_related('sale', 'from_branch', 'vehicle', 'driver')
    serializer_class = LogisticsSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'from_branch', 'vehicle']
    search_fields = ['tracking_number', 'customer_name']
    ordering_fields = ['created_at', 'delivery_date']
    ordering = ['-created_at']
