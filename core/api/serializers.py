from rest_framework import serializers
from core.models import (
    Branch, Employee, Product, Stock, StockMovement, Order, OrderItem,
    Sale, SaleItem, Expense, Vehicle, Trip, VehicleMaintenance,
    OrderFulfillment, OrderShipment, ShipmentItem, PaymentCollection,
    Logistics,
    ChartOfAccount, LedgerTransaction, GeneralLedger,
    IncomeRegister, ExpenseRegister, LoansRegister, PayrollLedger, AllowanceRegister
)


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Stock
        fields = '__all__'


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'


class SaleItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    product_name = serializers.CharField(source='stock.product.name', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = '__all__'


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Sale
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Expense
        fields = '__all__'


class VehicleSerializer(serializers.ModelSerializer):
    total_trips = serializers.ReadOnlyField()
    total_revenue = serializers.ReadOnlyField()
    total_maintenance_cost = serializers.ReadOnlyField()
    is_due_for_maintenance = serializers.ReadOnlyField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    driver_name = serializers.CharField(source='assigned_driver.full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'


class TripSerializer(serializers.ModelSerializer):
    net_profit = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    
    class Meta:
        model = Trip
        fields = '__all__'


class VehicleMaintenanceSerializer(serializers.ModelSerializer):
    total_cost = serializers.ReadOnlyField()
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    
    class Meta:
        model = VehicleMaintenance
        fields = '__all__'


class ShipmentItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    product_name = serializers.CharField(source='order_item.product_name', read_only=True)
    
    class Meta:
        model = ShipmentItem
        fields = '__all__'


class OrderShipmentSerializer(serializers.ModelSerializer):
    items = ShipmentItemSerializer(many=True, read_only=True)
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    fulfillment_number = serializers.CharField(source='fulfillment.fulfillment_number', read_only=True)
    
    class Meta:
        model = OrderShipment
        fields = '__all__'


class PaymentCollectionSerializer(serializers.ModelSerializer):
    is_outstanding = serializers.ReadOnlyField()
    fulfillment_number = serializers.CharField(source='fulfillment.fulfillment_number', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    deposited_branch_name = serializers.CharField(source='deposited_to_branch.name', read_only=True)
    
    class Meta:
        model = PaymentCollection
        fields = '__all__'


class OrderFulfillmentSerializer(serializers.ModelSerializer):
    shipments = OrderShipmentSerializer(many=True, read_only=True)
    payments = PaymentCollectionSerializer(many=True, read_only=True)
    fulfillment_percentage = serializers.ReadOnlyField()
    payment_percentage = serializers.ReadOnlyField()
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = OrderFulfillment
        fields = '__all__'


class LogisticsSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    sale_number = serializers.CharField(source='sale.sale_number', read_only=True)
    
    class Meta:
        model = Logistics
        fields = '__all__'


class ChartOfAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartOfAccount
        fields = '__all__'


class LedgerTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerTransaction
        fields = '__all__'


class GeneralLedgerSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    account_code = serializers.CharField(source='account.account_code', read_only=True)
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    transaction_date = serializers.DateField(source='transaction.transaction_date', read_only=True)

    class Meta:
        model = GeneralLedger
        fields = '__all__'


class IncomeRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeRegister
        fields = '__all__'


class ExpenseRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseRegister
        fields = '__all__'


class LoansRegisterSerializer(serializers.ModelSerializer):
    outstanding_balance = serializers.ReadOnlyField()

    class Meta:
        model = LoansRegister
        fields = '__all__'


class PayrollLedgerSerializer(serializers.ModelSerializer):
    gross_pay = serializers.ReadOnlyField()
    net_pay = serializers.ReadOnlyField()

    class Meta:
        model = PayrollLedger
        fields = '__all__'


class AllowanceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowanceRegister
        fields = '__all__'
