# 🚀 Kabisakabisa Enterprise ERP - Quick Start Guide

## Installation & Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
cd /home/user/webapp
pip install -r requirements.txt
```

### Step 2: Run Migrations
```bash
python manage.py migrate
```

### Step 3: Create Superuser
```bash
python manage.py createsuperuser
# Enter username, email, and password
```

### Step 4: Start Server
```bash
python manage.py runserver
```

### Step 5: Access System
- **Admin Panel**: http://localhost:8000/admin/
- **REST API**: http://localhost:8000/api/v1/
- **API Docs**: http://localhost:8000/api/v1/ (browsable)

---

## 🎯 Quick Demo: Complete Order Fulfillment Workflow

### Scenario
Customer orders **100 bags of cement**. Your truck can only carry **30 bags** per trip.

### Step-by-Step Demo

#### 1. Create a Branch
```bash
# Admin → Branches → Add Branch
Name: Main Warehouse
Address: 123 Industry Road
Phone: +1234567890
```

#### 2. Create a Product
```bash
# Admin → Products → Add Product
Name: Premium Cement 50kg
SKU: CEM-001
Unit Price: 500.00
Cost Price: 350.00
```

#### 3. Add Stock to Branch
```bash
# Admin → Stock → Add Stock
Branch: Main Warehouse
Product: Premium Cement 50kg
Quantity: 500 bags
Min Quantity: 50
```

#### 4. Create an Order
```bash
# Admin → Orders → Add Order
Order Number: ORD-001
Branch: Main Warehouse
Supplier: Cement Factory Ltd
Status: COMPLETED
```

#### 5. Add Order Items
```bash
# Admin → Order Items → Add Order Item
Order: ORD-001
Product: Premium Cement 50kg
Quantity: 100
Unit Price: 500.00
# Subtotal automatically calculates: 50,000.00
```

#### 6. Create Order Fulfillment
```bash
# Admin → Order Fulfillments → Add Order Fulfillment
Fulfillment Number: FUL-001
Order: ORD-001
Branch: Branch B (destination)
Total Order Value: 50000.00
```

#### 7. Add a Vehicle
```bash
# Admin → Vehicles → Add Vehicle
Registration Number: ABC-123
Vehicle Type: Truck
Make: Toyota
Model: Hilux
Branch: Main Warehouse
Status: Active
```

#### 8. Create First Shipment (30 bags)
```bash
# Admin → Order Shipments → Add Order Shipment
Shipment Number: SHIP-001
Fulfillment: FUL-001
Vehicle: ABC-123 (Toyota Hilux)
Vehicle Capacity: 30
Scheduled Date: Today 8:00 AM
Customer Name: John Doe
Delivery Address: Customer Location
```

#### 9. Add Items to Shipment
```bash
# In the same form, scroll to "Shipment Items" inline
Order Item: Premium Cement (from ORD-001)
Quantity Ordered: 100
Quantity Delivered: 30    # This shipment
Quantity Remaining: 70    # Still to deliver
Unit Price: 500.00
# Subtotal: 15,000.00
```

#### 10. Mark Shipment as Delivered
```bash
# Edit SHIP-001
Status: Delivered
Actual Delivery Date: Today 10:30 AM
Customer Signature: ✓ Checked

# Save → System automatically:
# - Adds 30 bags to Branch B stock
# - Creates stock movement record
# - Updates fulfillment to "PARTIALLY_FULFILLED"
```

#### 11. Collect Payment
```bash
# Admin → Payment Collections → Add Payment Collection
Payment Number: PAY-001
Fulfillment: FUL-001
Shipment: SHIP-001
Branch: Branch B
Amount Collected: 15000.00
Payment Method: Cash
Payment Date: Today 10:30 AM
Is Deposited: No ⚠️ (money collected, not yet deposited)
```

#### 12. Check Fulfillment Status
```bash
# Admin → Order Fulfillments → Click FUL-001
View:
  Total Items Ordered: 100
  Total Items Fulfilled: 30
  Total Items Remaining: 70
  Fulfillment Percentage: 30%
  
  Total Order Value: 50,000.00
  Total Collected: 15,000.00
  Total Remaining: 35,000.00
  Payment Percentage: 30%
  
  Status: PARTIALLY_FULFILLED
```

#### 13. Create More Shipments
Repeat steps 8-11 for remaining 70 bags:
- **SHIP-002**: 30 bags (Payment: $15,000)
- **SHIP-003**: 30 bags (Payment: $15,000)
- **SHIP-004**: 10 bags (Payment: $5,000)

After all deliveries:
```
Status: FULLY_FULFILLED
Fulfillment %: 100%
Payment %: 100%
```

---

## 📊 Using the REST API

### Get All Fulfillments
```bash
curl http://localhost:8000/api/v1/order-fulfillments/
```

### Get Outstanding Payments
```bash
curl http://localhost:8000/api/v1/payment-collections/outstanding/
```

### Filter Shipments by Status
```bash
curl "http://localhost:8000/api/v1/order-shipments/?status=IN_TRANSIT"
```

### Mark Payment as Deposited
```bash
curl -X POST http://localhost:8000/api/v1/payment-collections/1/mark_deposited/
```

---

## 🎨 Enterprise UI/UX Requirements

### Clean Tables (No Icons)
```
┌─────────────────┬────────────┬──────────────┬─────────────┐
│ Order Number    │ Status     │ Items        │ Amount      │
├─────────────────┼────────────┼──────────────┼─────────────┤
│ ORD-001         │ Completed  │ 100 units    │ $50,000.00  │
│ ORD-002         │ Pending    │ 50 units     │ $25,000.00  │
└─────────────────┴────────────┴──────────────┴─────────────┘
```

### Professional Color Scheme
- **Headers**: `#2C3E50` (Dark blue-gray)
- **Table Borders**: `#BDC3C7` (Light gray)
- **Alternate Rows**: `#ECF0F1` (Very light gray)
- **Text**: `#2C3E50` (Dark)
- **Success**: `#27AE60` (Green)
- **Warning**: `#F39C12` (Orange)
- **Danger**: `#E74C3C` (Red)

### Typography
- **Font**: `Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif`
- **Headers**: 16px, Bold, Uppercase
- **Body**: 14px, Regular
- **Numbers**: Tabular figures for alignment

---

## 📦 Included Enterprise Libraries

### Financial Analytics
- **pandas** - Data manipulation and analysis
- **numpy** - Mathematical operations
- **scipy** - Optimization algorithms
- **statsmodels** - Statistical models
- **prophet** - Time series forecasting
- **scikit-learn** - Machine learning

### Report Generation
- **xlsxwriter** - Excel file generation
- **reportlab** - PDF document creation
- **openpyxl** - Excel file manipulation

### Operations Research
- **pulp** - Linear programming for route optimization

### Example: Generate Excel Report
```python
from django_pandas.io import read_frame
import pandas as pd
from core.models import OrderFulfillment

# Get data
fulfillments = OrderFulfillment.objects.all()
df = read_frame(fulfillments)

# Export
df.to_excel('fulfillments.xlsx', index=False, engine='xlsxwriter')
```

---

## 🔥 Key Features Built

### ✅ Order Fulfillment System
- Partial delivery tracking
- Vehicle capacity management
- Multi-shipment orders
- Automatic stock assignment

### ✅ Payment Collection System
- Per-shipment payment tracking
- Outstanding payment reports
- Deposit status monitoring
- Branch-wise collection

### ✅ Vehicle Management
- Fleet tracking
- Trip assignments
- Maintenance scheduling
- Cost tracking

### ✅ Financial Analytics
- Profit calculation
- Expense tracking
- Revenue analysis
- Forecasting support

### ✅ REST API
- Full CRUD operations
- Filtering & search
- Pagination (50 per page)
- Custom actions

### ✅ Admin Interface
- Enterprise-grade UI
- Custom actions
- Inline editing
- Comprehensive filtering

---

## 📞 Common Questions

### Q: How do I track outstanding payments?
**A:** Admin → Payment Collections → Filter: "Is deposited: No"

Or via API: `GET /api/v1/payment-collections/outstanding/`

### Q: How do I assign delivered products to a branch?
**A:** When you mark a shipment as "Delivered", the system automatically assigns products to the destination branch.

Or manually: Admin → Order Shipments → Select shipment → Actions → "Assign products to branch stock"

### Q: How do I split a large order across multiple vehicles?
**A:** Create multiple Order Shipments for the same Order Fulfillment. The system tracks what's been delivered and what remains.

### Q: How do I generate financial reports?
**A:** Use the included pandas/xlsxwriter libraries:
```python
from core.models import Sale
import pandas as pd

sales = Sale.objects.filter(created_at__year=2025)
df = pd.DataFrame(sales.values())
df.to_excel('sales_2025.xlsx')
```

---

## 🎯 Next Steps

1. ✅ Install and run the system
2. ✅ Create sample data (branches, products, vehicles)
3. ✅ Test order fulfillment workflow
4. ✅ Test payment collection
5. ⏳ Build React frontend (next phase)
6. ⏳ Implement advanced analytics dashboards
7. ⏳ Add route optimization
8. ⏳ Deploy to production

---

## 📚 Documentation

- **Full Documentation**: `ORDER_FULFILLMENT_README.md`
- **Vehicle Management**: `VEHICLE_MANAGEMENT_README.md`
- **API Reference**: http://localhost:8000/api/v1/

---

## 🎉 You're Ready!

Your enterprise ERP system is now fully operational with:
- Sophisticated order fulfillment
- Vehicle capacity management
- Payment tracking
- Outstanding payment monitoring
- REST API for frontend integration
- Enterprise-grade admin interface

**Start testing with the demo workflow above!** 🚀
