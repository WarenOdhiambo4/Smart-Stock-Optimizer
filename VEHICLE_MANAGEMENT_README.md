# Vehicle Management System - Database Documentation

## Overview
This document describes the newly added **Vehicle Management System** for tracking company vehicles, trips, and maintenance operations. The system integrates seamlessly with the existing inventory and sales modules.

---

## 🚗 New Database Models

### 1. **Vehicle Model**
Represents company-owned vehicles that can be assigned to trips and require maintenance.

#### Key Attributes:
- **registration_number** (Unique) - License plate number
- **vehicle_type** - Type of vehicle (Truck, Van, Pickup, Car, Motorcycle, Other)
- **make** - Manufacturer (e.g., Toyota, Ford)
- **model** - Model name
- **year** - Manufacturing year
- **color** - Vehicle color
- **branch** (FK) - Branch that owns the vehicle
- **assigned_driver** (FK to Employee) - Current assigned driver
- **status** - Current status (Active, Under Maintenance, Inactive, Retired)
- **current_mileage** - Current odometer reading in KM
- **fuel_capacity** - Fuel tank capacity in liters
- **purchase_price** - Vehicle purchase price
- **purchase_date** - Date of purchase
- **insurance_expiry** - Insurance expiration date
- **registration_expiry** - Registration renewal date

#### Computed Properties:
- `total_trips` - Count of all trips made by this vehicle
- `total_revenue` - Sum of revenue from all completed trips
- `total_maintenance_cost` - Sum of all maintenance expenses
- `is_due_for_maintenance` - Boolean flag if vehicle needs service (>5000 KM since last service)

#### Business Logic:
- Vehicle status automatically changes when maintenance starts/completes
- Mileage automatically updates when trips are completed

---

### 2. **Trip Model**
Represents vehicle journeys that generate revenue for the business.

#### Key Attributes:
- **trip_number** (Unique) - Trip identifier
- **vehicle** (FK) - Vehicle used for the trip
- **driver** (FK to Employee) - Driver assigned
- **trip_type** - Type of trip (Delivery, Pickup, Transport, Rental, Other)
- **origin** - Starting location
- **destination** - Destination location
- **distance** - Distance traveled in KM
- **sale** (FK) - Related sale record (optional)
- **logistics** (FK) - Related logistics record (optional)
- **status** - Trip status (Scheduled, In Progress, Completed, Cancelled)
- **scheduled_date** - When trip is scheduled
- **start_time** - Actual start time
- **end_time** - Actual completion time
- **revenue** - Money earned from this trip
- **fuel_cost** - Fuel expenses
- **other_expenses** - Tolls, parking, etc.
- **start_mileage** - Odometer reading at start
- **end_mileage** - Odometer reading at end
- **customer_name** - Customer information
- **customer_phone** - Customer contact

#### Computed Properties:
- `net_profit` - Revenue minus all expenses (fuel + other)
- `duration` - Time taken for trip completion

#### Business Logic:
- **Auto-update vehicle mileage**: When trip status changes to "COMPLETED", vehicle's current_mileage is automatically updated
- **Auto-create expense records**: When trip completes, automatically creates an Expense record with trip costs
- Expense is categorized as "TRANSPORT" type
- Links expense to the related Sale if applicable

---

### 3. **VehicleMaintenance Model**
Tracks maintenance, repairs, and service records for vehicles.

#### Key Attributes:
- **maintenance_number** (Unique) - Maintenance record identifier
- **vehicle** (FK) - Vehicle being serviced
- **maintenance_type** - Type of service (Routine Service, Repair, Inspection, Tire, Brake, Engine, Electrical, Bodywork, Other)
- **description** - Details of work performed
- **service_provider** - Garage/mechanic name
- **service_date** - Date service started
- **completion_date** - Date service completed
- **parts_cost** - Cost of replacement parts
- **labor_cost** - Labor charges
- **other_costs** - Additional costs
- **mileage_at_service** - Vehicle mileage at time of service
- **next_service_mileage** - When next service is due
- **status** - Maintenance status (Scheduled, In Progress, Completed, Cancelled)
- **receipt_number** - Service invoice number

#### Computed Properties:
- `total_cost` - Sum of parts_cost + labor_cost + other_costs

#### Business Logic:
- **Auto-update vehicle status**: 
  - When maintenance status is "IN_PROGRESS", vehicle status changes to "MAINTENANCE"
  - When maintenance completes, vehicle status returns to "ACTIVE"
- **Auto-create expense records**: When maintenance completes, automatically creates an Expense record
- Expense is categorized as "MAINTENANCE" type
- Detailed cost breakdown stored in expense notes

---

### 4. **Logistics Model (Updated)**
The existing Logistics model has been enhanced with vehicle tracking.

#### New/Updated Fields:
- **vehicle** (FK to Vehicle) - Vehicle assigned to delivery (replaces vehicle_number text field)
- **driver** (FK to Employee) - Driver assigned (replaces driver_name text field)
- **driver_name** (Legacy) - Kept for backward compatibility
- **vehicle_number** (Legacy) - Kept for backward compatibility

#### Integration:
- Logistics records can now be linked to formal Vehicle and Employee records
- Trip records can reference Logistics for delivery tracking

---

## 📊 Database Relationships

### Visual Relationship Map:

```
Branch
  ├── Vehicles (1:Many)
  │     ├── Trips (1:Many)
  │     │     ├── Sale (Many:1, optional)
  │     │     ├── Logistics (Many:1, optional)
  │     │     └── Auto-creates → Expense (when completed)
  │     │
  │     └── VehicleMaintenance (1:Many)
  │           └── Auto-creates → Expense (when completed)
  │
  ├── Logistics (1:Many)
  │     ├── Vehicle (Many:1)
  │     ├── Driver/Employee (Many:1)
  │     └── Sale (Many:1)
  │
  └── Expenses (1:Many)
        ├── Sale (Many:1, optional)
        └── Created by Trips and Maintenance

Employee
  ├── Assigned Vehicles (1:Many)
  ├── Trips Driven (1:Many)
  └── Logistics Deliveries (1:Many)

Sale
  ├── Trips (1:Many)
  └── Logistics (1:Many)
```

---

## 🔄 Automated Business Workflows

### 1. **Trip Completion Workflow**
```
Trip Status → COMPLETED
  ↓
Vehicle.current_mileage = Trip.end_mileage
  ↓
Create Expense Record:
  - Type: TRANSPORT
  - Amount: fuel_cost + other_expenses
  - Linked to Sale (if any)
  - Expense Number: "TRIP-{trip_number}"
```

### 2. **Maintenance Workflow**
```
Maintenance Status → IN_PROGRESS
  ↓
Vehicle.status = MAINTENANCE
  ↓
Maintenance Status → COMPLETED
  ↓
Vehicle.status = ACTIVE
  ↓
Create Expense Record:
  - Type: MAINTENANCE
  - Amount: parts_cost + labor_cost + other_costs
  - Expense Number: "MAINT-{maintenance_number}"
```

### 3. **Logistics-Trip Integration**
```
Sale Created
  ↓
Logistics Record Created
  ↓
Assign Vehicle + Driver
  ↓
Create Trip (linked to Logistics + Sale)
  ↓
Trip generates revenue
  ↓
Expenses auto-tracked
```

---

## 💡 Use Cases

### Use Case 1: Delivery Trip
1. Customer makes a purchase (Sale)
2. Logistics record created for delivery
3. Assign a Vehicle and Driver
4. Create Trip:
   - Link to Sale and Logistics
   - Set revenue (delivery fee)
   - Track fuel and other costs
5. On completion:
   - Vehicle mileage updates
   - Expenses auto-recorded
   - Net profit calculated

### Use Case 2: Vehicle Maintenance
1. Vehicle reaches 5000 KM since last service (is_due_for_maintenance = True)
2. Schedule VehicleMaintenance record
3. Set status to "IN_PROGRESS"
4. Vehicle status becomes "MAINTENANCE" (unavailable for trips)
5. Record costs (parts, labor)
6. Set status to "COMPLETED"
7. Vehicle returns to "ACTIVE"
8. Maintenance expense auto-recorded

### Use Case 3: Rental/Transport Service
1. Create Trip without Sale/Logistics link
2. Set trip_type = "RENTAL" or "TRANSPORT"
3. Enter customer details directly
4. Set revenue amount
5. Track all costs
6. Calculate net_profit automatically

---

## 📈 Financial Tracking

### Revenue Sources:
- **Trip.revenue** - Direct income from vehicle trips
- **Sale.total_amount** - Related sales revenue

### Cost Tracking:
- **Trip Costs**:
  - fuel_cost
  - other_expenses (tolls, parking)
  
- **Maintenance Costs**:
  - parts_cost
  - labor_cost
  - other_costs

### Profitability Analysis:
```python
# Per Vehicle Analysis
vehicle.total_revenue - vehicle.total_maintenance_cost = Vehicle Net Profit

# Per Trip Analysis
trip.revenue - (trip.fuel_cost + trip.other_expenses) = Trip Net Profit

# All Trips Net Profit
Sum(all_trips.net_profit)

# Maintenance Cost Analysis
Sum(vehicle_maintenance.total_cost) grouped by vehicle or date range
```

---

## 🔍 Sample Queries & Reports

### 1. Vehicle Performance Report
```python
from core.models import Vehicle

# Get vehicle with best revenue
best_vehicle = Vehicle.objects.annotate(
    revenue=Sum('trips__revenue', filter=Q(trips__status='COMPLETED'))
).order_by('-revenue').first()

# Vehicles due for maintenance
vehicles_needing_service = [v for v in Vehicle.objects.all() if v.is_due_for_maintenance]
```

### 2. Trip Profitability
```python
from core.models import Trip

# Most profitable trips
profitable_trips = Trip.objects.filter(
    status='COMPLETED'
).annotate(
    profit=F('revenue') - F('fuel_cost') - F('other_expenses')
).order_by('-profit')[:10]
```

### 3. Maintenance Cost Analysis
```python
from core.models import VehicleMaintenance
from django.db.models import Sum

# Total maintenance costs by vehicle
maintenance_by_vehicle = VehicleMaintenance.objects.values(
    'vehicle__registration_number'
).annotate(
    total_cost=Sum(F('parts_cost') + F('labor_cost') + F('other_costs'))
).order_by('-total_cost')
```

### 4. Driver Performance
```python
from core.models import Trip
from django.db.models import Count, Sum

# Driver statistics
driver_stats = Trip.objects.filter(
    status='COMPLETED'
).values('driver__first_name', 'driver__last_name').annotate(
    total_trips=Count('id'),
    total_revenue=Sum('revenue'),
    total_distance=Sum('distance')
)
```

---

## 🚀 Getting Started

### 1. Run Migrations
```bash
cd /home/user/webapp
python manage.py migrate core
```

### 2. Create Sample Data (Optional)
```python
from core.models import Branch, Vehicle, Employee
from decimal import Decimal

# Create a vehicle
branch = Branch.objects.first()
driver = Employee.objects.first()

vehicle = Vehicle.objects.create(
    registration_number="ABC-123",
    vehicle_type="TRUCK",
    make="Toyota",
    model="Hilux",
    year=2020,
    branch=branch,
    assigned_driver=driver,
    status="ACTIVE",
    current_mileage=15000,
    fuel_capacity=Decimal("80.00"),
    purchase_price=Decimal("35000.00")
)
```

### 3. Access Admin Panel
```bash
python manage.py runserver
# Navigate to http://localhost:8000/admin/
# You'll see new sections: Vehicles, Trips, Vehicle Maintenance Records
```

---

## 🎯 Key Benefits

### 1. **Revenue Tracking**
- Track income from vehicle operations
- Link trips to sales for comprehensive revenue analysis

### 2. **Cost Management**
- Automatic expense recording for trips and maintenance
- Detailed cost breakdown (fuel, parts, labor)
- Calculate net profitability per trip and per vehicle

### 3. **Fleet Management**
- Monitor vehicle status and availability
- Track maintenance schedules
- Assign vehicles to drivers and branches

### 4. **Performance Analytics**
- Vehicle utilization rates
- Driver performance metrics
- Trip profitability analysis
- Maintenance cost trends

### 5. **Compliance Tracking**
- Insurance expiry alerts
- Registration renewal tracking
- Service history maintenance

---

## 📋 Model Summary Table

| Model | Purpose | Key Relationships | Auto-Creates |
|-------|---------|-------------------|--------------|
| **Vehicle** | Fleet asset management | Branch, Employee (driver) | - |
| **Trip** | Journey tracking & revenue | Vehicle, Employee, Sale, Logistics | Expense (on completion) |
| **VehicleMaintenance** | Service records & costs | Vehicle, Employee | Expense (on completion) |
| **Logistics** (updated) | Delivery management | Vehicle, Employee, Sale | - |

---

## 🔧 Admin Interface Features

### Vehicle Admin
- List view shows: registration, type, make, model, branch, driver, status, mileage
- Filter by: status, type, branch
- Search: registration number, make, model
- Readonly fields: total trips, revenue, maintenance costs
- Organized fieldsets for easy data entry

### Trip Admin
- List view shows: trip number, vehicle, driver, origin, destination, status, revenue, profit
- Filter by: status, type, vehicle, date
- Date hierarchy for easy navigation
- Readonly fields: net profit, duration
- Comprehensive fieldsets

### Vehicle Maintenance Admin
- List view shows: maintenance number, vehicle, type, date, status, total cost
- Filter by: status, type, date, vehicle
- Date hierarchy navigation
- Readonly fields: total cost
- Cost breakdown fields

---

## ⚠️ Important Notes

1. **Automatic Expense Creation**: Trip and maintenance expenses are auto-created to avoid duplicate expenses
2. **Vehicle Status Management**: Status changes automatically based on maintenance state
3. **Mileage Tracking**: Vehicle mileage updates automatically when trips complete
4. **Legacy Field Support**: Old logistics fields (driver_name, vehicle_number) are kept for backward compatibility
5. **Validation**: Ensure trip end_mileage > start_mileage when completing trips

---

## 📞 Sample Workflows

### Complete Delivery Workflow
```python
from core.models import Vehicle, Trip, Sale, Logistics
from django.utils import timezone
from decimal import Decimal

# 1. Get vehicle and driver
vehicle = Vehicle.objects.get(registration_number="ABC-123")
driver = vehicle.assigned_driver

# 2. Create or get sale and logistics
sale = Sale.objects.get(sale_number="SALE-001")
logistics = Logistics.objects.create(
    tracking_number="LOG-001",
    sale=sale,
    from_branch=vehicle.branch,
    vehicle=vehicle,
    driver=driver,
    to_address="123 Customer St",
    customer_name="John Doe",
    customer_phone="+1234567890",
    delivery_cost=Decimal("50.00")
)

# 3. Create trip
trip = Trip.objects.create(
    trip_number="TRIP-001",
    vehicle=vehicle,
    driver=driver,
    trip_type="DELIVERY",
    origin=vehicle.branch.address,
    destination=logistics.to_address,
    distance=Decimal("25.50"),
    sale=sale,
    logistics=logistics,
    status="SCHEDULED",
    scheduled_date=timezone.now(),
    revenue=Decimal("50.00"),
    fuel_cost=Decimal("15.00"),
    other_expenses=Decimal("5.00"),
    start_mileage=vehicle.current_mileage
)

# 4. Start trip
trip.status = "IN_PROGRESS"
trip.start_time = timezone.now()
trip.save()

# 5. Complete trip
trip.status = "COMPLETED"
trip.end_time = timezone.now()
trip.end_mileage = vehicle.current_mileage + 26  # 25.5 km rounded up
trip.save()

# Vehicle mileage is now updated automatically
# Expense record created automatically
# Net profit calculated: $50 - $15 - $5 = $30
```

---

## 🎓 Best Practices

1. **Always set mileage**: Record start_mileage and end_mileage for trips
2. **Complete maintenance**: Mark maintenance as "COMPLETED" to return vehicle to service
3. **Track all costs**: Record fuel, tolls, parking for accurate profitability
4. **Regular service**: Use is_due_for_maintenance property to schedule services
5. **Driver assignment**: Always assign a driver to trips for accountability
6. **Link records**: Connect trips to sales/logistics for complete tracking

---

## 📊 Reporting Capabilities

The new models enable rich reporting:

1. **Vehicle ROI**: Revenue vs. maintenance costs per vehicle
2. **Trip Efficiency**: Revenue per kilometer, fuel efficiency
3. **Driver Performance**: Trips completed, revenue generated, safety records
4. **Maintenance Trends**: Costs over time, service frequency
5. **Branch Comparison**: Vehicle utilization by branch
6. **Profitability Analysis**: Identify most/least profitable routes and vehicles

---

## End of Documentation

For questions or feature requests, please contact the development team.
