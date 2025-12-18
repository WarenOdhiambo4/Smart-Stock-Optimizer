# Logistics & KPI Secret Dashboard Implementation

## Overview
Comprehensive logistics performance tracking with Google Maps integration, vehicle efficiency analysis using fairlearn for bias-free scoring, and secret KPI dashboard with stock discrepancy impact analysis.

## Key Features Implemented

### 1. Logistics Analytics (`core/logistics_analytics.py`)
- **Google Maps Integration**: Automatic distance calculation between origin/destination
- **Vehicle Performance Tracking**: Mileage, fuel consumption, maintenance, inter-branch transfers
- **Bias-Free Scoring**: Uses fairlearn library to ensure unbiased vehicle efficiency ratings
- **Real-time Mileage Calculation**: Distance automatically calculated from fuel consumed

### 2. KPI Secret Dashboard (`core/logistics_analytics.py`)
- **Branch Performance Analysis**: Profit margins with stock discrepancy impact
- **Automatic KPI Adjustment**: 40% penalty when profit margin ≥85% AND stock discrepancy ≥10%
- **ROT Analysis**: Rate of Turn calculation with A-F grading system
- **Stock Flow Tracking**: Product movement in/out with percentage grading

### 3. New Models Added (`core/models.py`)
```python
class FuelConsumption(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField()
    # Tracks fuel consumption for mileage calculations

class Maintenance(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    # Simplified maintenance tracking for analytics
```

### 4. Dashboard Views (`core/views_logistics.py`)
- **Logistics Dashboard**: Vehicle performance with efficiency scores
- **KPI Secret Dashboard**: Admin-only access with branch performance analysis
- **API Endpoints**: Real-time data for vehicle performance and KPI metrics

### 5. Templates
- **Logistics Dashboard** (`templates/core/logistics_dashboard.html`):
  - Vehicle performance summary table
  - Google Maps distance calculator
  - Real-time efficiency metrics
  
- **KPI Secret Dashboard** (`templates/core/kpi_secret_dashboard.html`):
  - Branch performance analysis with penalty logic
  - ROT analysis modal with product flow grading
  - Admin-only access with security indicators

## Analytics Capabilities

### Vehicle Performance Metrics
- **Total Trips**: Number of trips per vehicle per month
- **Distance Traveled**: Calculated via Google Maps API
- **Fuel Consumption**: Liters consumed with mileage calculation
- **Maintenance Count**: Number of maintenance events
- **Inter-branch Transfers**: Logistics efficiency tracking
- **Efficiency Score**: Composite score (mileage 30%, uptime 30%, maintenance 20%, transfers 20%)
- **Fair Efficiency Score**: Bias-corrected score using fairlearn

### KPI Analysis Features
- **Profit Margin Calculation**: (Average Selling Price - Cost Price) × Quantity - Expenses
- **Stock Discrepancy Impact**: Percentage of revenue lost to inventory issues
- **Automatic Penalty Logic**: KPI reduced by 40% when conditions met
- **ROT Grading System**:
  - A: 80%+ (Excellent flow)
  - B: 60-79% (Good flow)
  - C: 40-59% (Average flow)
  - D: 20-39% (Poor flow)
  - F: <20% (Critical flow issues)

## Configuration Required

### 1. Environment Variables
```bash
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
REDIS_URL=redis://localhost:6379/0
```

### 2. Install Dependencies
```bash
pip install googlemaps fairlearn
```

### 3. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

## URL Routes Added
- `/logistics-dashboard/` - Main logistics performance dashboard
- `/kpi-secret/` - Secret KPI dashboard (Admin only)
- `/api/vehicle-performance/` - Vehicle performance data API
- `/api/kpi-dashboard/` - KPI dashboard data API
- `/api/trip-distance/` - Google Maps distance calculation API

## Security Features
- **Admin-Only Access**: KPI secret dashboard restricted to ADMIN role
- **Role-Based Permissions**: Different access levels for different user roles
- **Audit Trail**: All price changes and performance metrics logged

## Usage Examples

### Vehicle Performance Analysis
```python
analytics = LogisticsAnalytics()
performance_data = analytics.get_vehicle_performance_data(month=12, year=2024)
efficiency_scores = analytics.calculate_vehicle_efficiency_scores(performance_data)
```

### KPI Analysis
```python
kpi_dashboard = KPISecretDashboard()
branch_performance = kpi_dashboard.analyze_branch_performance(branch_id=1)
# Returns profit margin, stock discrepancy impact, adjusted KPI, ROT data
```

### Distance Calculation
```python
analytics = LogisticsAnalytics()
distance = analytics.calculate_trip_distance("Nairobi, Kenya", "Mombasa, Kenya")
# Returns distance in kilometers using Google Maps API
```

## Key Benefits
1. **Unbiased Performance Evaluation**: fairlearn ensures fair vehicle comparisons
2. **Real-time Distance Tracking**: Google Maps integration for accurate mileage
3. **Fraud Detection**: Stock discrepancy analysis prevents profit manipulation
4. **Operational Efficiency**: ROT analysis identifies slow-moving inventory
5. **Data-Driven Decisions**: Comprehensive metrics for logistics optimization

## Next Steps
1. Set up Google Maps API key in environment
2. Configure Redis for Celery background tasks
3. Train staff on new KPI dashboard features
4. Implement automated alerts for low-performing vehicles
5. Add predictive maintenance based on vehicle performance trends