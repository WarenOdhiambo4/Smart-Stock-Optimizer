# Vehicle Management - Quick Reference Guide

## 🚀 Quick Start

### Step 1: Run Migration
```bash
python manage.py migrate core
```

### Step 2: Access Admin
```bash
python manage.py runserver
# Go to: http://localhost:8000/admin/
```

---

## 📊 Model Overview

### **VEHICLE** 🚗
```
What: Your company vehicles (trucks, vans, cars, etc.)
Who owns: Branch
Who drives: Employee (assigned_driver)
Status: Active | Maintenance | Inactive | Retired
Tracks: Mileage, insurance, registration dates
Auto-calculates: Total revenue, total maintenance cost
```

### **TRIP** 🛣️
```
What: Journeys that earn money
Uses: Vehicle + Driver
Links to: Sale, Logistics
Tracks: Origin, destination, distance, revenue, costs
Status: Scheduled → In Progress → Completed
Auto-updates: Vehicle mileage
Auto-creates: Expense record (TRANSPORT type)
Auto-calculates: Net profit (revenue - costs)
```

### **MAINTENANCE** 🔧
```
What: Vehicle service and repairs
For: Vehicle
Tracks: Parts cost, labor cost, other costs
Types: Routine, Repair, Tire, Brake, Engine, etc.
Auto-updates: Vehicle status (MAINTENANCE/ACTIVE)
Auto-creates: Expense record (MAINTENANCE type)
Auto-calculates: Total cost
```

---

## 🔄 Workflows

### Complete a Delivery Trip
```
1. Customer buys → Sale created
2. Create Logistics → assign Vehicle + Driver
3. Create Trip:
   - Link to Sale + Logistics
   - Set revenue (delivery fee)
   - Enter fuel cost and tolls
   - Set status = SCHEDULED

4. Driver starts → status = IN_PROGRESS
   - Record start_mileage

5. Driver completes → status = COMPLETED
   - Record end_mileage
   
AUTOMATIC:
✅ Vehicle mileage updated
✅ Expense created (TRANSPORT)
✅ Net profit calculated
```

### Vehicle Maintenance
```
1. Create Maintenance record
2. Set status = IN_PROGRESS

AUTOMATIC:
✅ Vehicle status = MAINTENANCE (unavailable)

3. Enter costs:
   - Parts cost
   - Labor cost
   - Other costs

4. Set status = COMPLETED

AUTOMATIC:
✅ Vehicle status = ACTIVE (available again)
✅ Expense created (MAINTENANCE)
✅ Total cost calculated
```

---

## 📈 Quick Analytics

### Vehicle Profitability
```python
vehicle.total_revenue - vehicle.total_maintenance_cost = Net Profit
```

### Trip Profitability
```python
trip.revenue - trip.fuel_cost - trip.other_expenses = Net Profit
(Already calculated as trip.net_profit)
```

### Driver Performance
```python
# Count trips
driver.trips_driven.count()

# Total revenue
driver.trips_driven.aggregate(Sum('revenue'))

# Total distance
driver.trips_driven.aggregate(Sum('distance'))
```

### Maintenance Due
```python
# Check if vehicle needs service
vehicle.is_due_for_maintenance  # True if >5000 KM since last service
```

---

## 🎯 Common Tasks

### Add a New Vehicle
```
Admin → Vehicles → Add Vehicle
Required:
- Registration number (license plate)
- Vehicle type (Truck, Van, etc.)
- Make (Toyota, Ford, etc.)
- Model
- Year
- Branch
- Status (usually "Active")
- Current mileage
```

### Record a Trip
```
Admin → Trips → Add Trip
Required:
- Trip number (e.g., TRIP-001)
- Vehicle
- Driver
- Origin
- Destination
- Distance (KM)
- Revenue (money earned)
- Fuel cost
- Status

Optional:
- Sale (if delivery)
- Logistics (if delivery)
- Other expenses
- Customer info
```

### Schedule Maintenance
```
Admin → Vehicle Maintenance → Add Maintenance
Required:
- Maintenance number (e.g., MAINT-001)
- Vehicle
- Maintenance type
- Description
- Service provider
- Service date
- Mileage at service
- Status

Costs:
- Parts cost
- Labor cost
- Other costs
```

---

## 💰 Financial Reports

### Total Vehicle Revenue
```
Admin → Vehicles → Click vehicle
See: "Total revenue" (read-only field)
```

### Total Maintenance Costs
```
Admin → Vehicles → Click vehicle
See: "Total maintenance cost" (read-only field)
```

### Trip Profits
```
Admin → Trips → View list
Column: "Net profit" shows profit for each trip
```

### Expense Breakdown
```
Admin → Expenses
Filter by:
- Expense type = "TRANSPORT" (trip costs)
- Expense type = "MAINTENANCE" (maintenance costs)
```

---

## 🔍 Filters & Search

### Find Trips by Vehicle
```
Admin → Trips → Filter: Vehicle = [select vehicle]
```

### Find Vehicles Due for Service
```
Admin → Vehicles → Check "is_due_for_maintenance" field
```

### View Driver's Trips
```
Admin → Trips → Filter: Driver = [select driver]
```

### Maintenance by Date
```
Admin → Vehicle Maintenance → Date hierarchy (click year/month)
```

---

## 📱 Integration Points

### With Sales
```
Sale → Logistics → Trip
Revenue from delivery fee tracked in Trip
Expense linked to Sale
```

### With Expenses
```
Trip (completed) → Auto-creates Expense (TRANSPORT)
Maintenance (completed) → Auto-creates Expense (MAINTENANCE)
```

### With Logistics
```
Logistics now has:
- vehicle (FK) instead of vehicle_number (text)
- driver (FK) instead of driver_name (text)
```

---

## ⚠️ Important Notes

### Auto-Creation Rules
- **Expenses are auto-created ONCE** when:
  - Trip status changes to COMPLETED
  - Maintenance status changes to COMPLETED
- Expense number format:
  - Trips: "TRIP-{trip_number}"
  - Maintenance: "MAINT-{maintenance_number}"

### Vehicle Status
- **ACTIVE**: Available for trips
- **MAINTENANCE**: Under service (can't assign trips)
- **INACTIVE**: Not in use
- **RETIRED**: Permanently removed from service

### Mileage Tracking
- Always record start_mileage when trip starts
- Always record end_mileage when trip completes
- Vehicle's current_mileage updates automatically on trip completion

---

## 🎨 Admin Sections Location

```
Django Admin Panel
├── CORE
│   ├── Branches
│   ├── Employees
│   ├── Products
│   ├── Stock
│   ├── Stock movements
│   ├── Orders
│   ├── Order items
│   ├── Sales
│   ├── Sale items
│   ├── Expenses
│   ├── Logistics
│   ├── 🆕 Vehicles ← NEW!
│   ├── 🆕 Trips ← NEW!
│   └── 🆕 Vehicle Maintenance Records ← NEW!
```

---

## 🔑 Key Field Meanings

### Vehicle Fields
- **registration_number**: License plate (e.g., "ABC-123")
- **current_mileage**: Odometer reading in KM
- **fuel_capacity**: Tank size in liters
- **is_due_for_maintenance**: Needs service if >5000 KM since last

### Trip Fields
- **trip_number**: Unique identifier (e.g., "TRIP-001")
- **origin**: Starting location
- **destination**: End location
- **distance**: KM traveled
- **revenue**: Money earned from trip
- **fuel_cost**: Fuel expenses
- **other_expenses**: Tolls, parking, etc.
- **net_profit**: Auto-calculated (revenue - all costs)

### Maintenance Fields
- **maintenance_number**: Unique identifier (e.g., "MAINT-001")
- **parts_cost**: Replacement parts
- **labor_cost**: Mechanic/garage charges
- **other_costs**: Additional expenses
- **total_cost**: Auto-calculated (sum of all costs)
- **mileage_at_service**: Odometer at service time
- **next_service_mileage**: When next service is due

---

## 📞 Support

For detailed information:
- **Technical docs**: `VEHICLE_MANAGEMENT_README.md`
- **Implementation details**: `IMPLEMENTATION_SUMMARY.md`
- **Pull Request**: https://github.com/WarenOdhiambo1/Kabisa_enterprise_erp/pull/2

---

**Quick tip**: Start by adding 1 vehicle, then create 1 trip, then mark it completed. You'll see all the automation in action! 🚀
