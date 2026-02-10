from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BranchViewSet, EmployeeViewSet, ProductViewSet, StockViewSet,
    StockMovementViewSet, OrderViewSet, OrderItemViewSet, SaleViewSet,
    SaleItemViewSet, ExpenseViewSet, VehicleViewSet, TripViewSet,
    VehicleMaintenanceViewSet, OrderFulfillmentViewSet, OrderShipmentViewSet,
    ShipmentItemViewSet, PaymentCollectionViewSet, LogisticsViewSet,
    ChartOfAccountViewSet, LedgerTransactionViewSet, GeneralLedgerViewSet,
    IncomeRegisterViewSet, ExpenseRegisterViewSet, LoansRegisterViewSet,
    PayrollLedgerViewSet, AllowanceRegisterViewSet
)

# Create enterprise-grade API router
router = DefaultRouter()

# Register all viewsets
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stock', StockViewSet, basename='stock')
router.register(r'stock-movements', StockMovementViewSet, basename='stockmovement')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'sale-items', SaleItemViewSet, basename='saleitem')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'vehicle-maintenance', VehicleMaintenanceViewSet, basename='vehiclemaintenance')
router.register(r'order-fulfillments', OrderFulfillmentViewSet, basename='orderfulfillment')
router.register(r'order-shipments', OrderShipmentViewSet, basename='ordershipment')
router.register(r'shipment-items', ShipmentItemViewSet, basename='shipmentitem')
router.register(r'payment-collections', PaymentCollectionViewSet, basename='paymentcollection')
router.register(r'logistics', LogisticsViewSet, basename='logistics')
router.register(r'chart-of-accounts', ChartOfAccountViewSet, basename='chartofaccounts')
router.register(r'ledger-transactions', LedgerTransactionViewSet, basename='ledgertransactions')
router.register(r'general-ledger', GeneralLedgerViewSet, basename='generalledger')
router.register(r'income-register', IncomeRegisterViewSet, basename='incomeregister')
router.register(r'expense-register', ExpenseRegisterViewSet, basename='expenseregister')
router.register(r'loans-register', LoansRegisterViewSet, basename='loansregister')
router.register(r'payroll-ledger', PayrollLedgerViewSet, basename='payrollledger')
router.register(r'allowances-register', AllowanceRegisterViewSet, basename='allowancesregister')

urlpatterns = [
    path('', include(router.urls)),
]
