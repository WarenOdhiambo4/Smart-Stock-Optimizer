from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from simple_history.models import HistoricalRecords


class Branch(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Branches"
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=50, blank=True)
    branches = models.ManyToManyField(Branch, related_name='employees')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Enterprise audit trail - tracks every price change
    history = HistoricalRecords()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.unit_price > 0:
            return ((self.unit_price - self.cost_price) / self.unit_price) * 100
        return 0


class Stock(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='stocks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0)
    min_quantity = models.IntegerField(default=10)
    # Track weighted average purchase price for profit calculation
    weighted_avg_purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['branch', 'product']
        ordering = ['product__name']

    def __str__(self):
        return f"{self.product.name} @ {self.branch.name}: {self.quantity}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity
    
    def update_purchase_price(self, new_quantity, new_unit_price):
        """Update weighted average purchase price when new stock arrives"""
        if self.quantity == 0:
            self.weighted_avg_purchase_price = new_unit_price
        else:
            total_value = (self.quantity * self.weighted_avg_purchase_price) + (new_quantity * new_unit_price)
            total_quantity = self.quantity + new_quantity
            self.weighted_avg_purchase_price = total_value / total_quantity if total_quantity > 0 else Decimal('0.00')
        self.quantity += new_quantity
        self.save()


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('TRANSFER', 'Inter-Branch Transfer'),
        ('ADJUSTMENT', 'Adjustment'),
        ('SALE', 'Sale'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    from_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    _processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.movement_type}: {self.quantity} of {self.stock.product.name}"

    def apply_stock_adjustment(self):
        if self._processed:
            return
        
        if self.movement_type in ['OUT', 'SALE']:
            self.stock.quantity -= abs(self.quantity)
            self.stock.save()
        elif self.movement_type == 'IN':
            self.stock.quantity += abs(self.quantity)
            self.stock.save()
        elif self.movement_type == 'TRANSFER':
            self.stock.quantity -= abs(self.quantity)
            self.stock.save()
            if self.to_branch:
                to_stock, created = Stock.objects.get_or_create(
                    branch=self.to_branch,
                    product=self.stock.product,
                    defaults={'quantity': 0}
                )
                to_stock.quantity += abs(self.quantity)
                to_stock.save()
        
        self._processed = True
        self.save(update_fields=['_processed'])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.status == 'APPROVED' and not self._processed:
            self.apply_stock_adjustment()


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='orders')
    supplier = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_by = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        if not self.product:
            product, created = Product.objects.get_or_create(
                sku=self.product_sku or f"AUTO-{self.product_name[:20].upper().replace(' ', '-')}",
                defaults={
                    'name': self.product_name,
                    'unit_price': self.unit_price,
                    'cost_price': self.unit_price,
                }
            )
            self.product = product

        super().save(*args, **kwargs)

        if self.order.status == 'COMPLETED':
            stock, created = Stock.objects.get_or_create(
                branch=self.order.branch,
                product=self.product,
                defaults={'quantity': 0}
            )
            stock.quantity += self.quantity
            stock.save()


class Sale(models.Model):
    sale_number = models.CharField(max_length=50, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sales')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50, default='Cash')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale #{self.sale_number}"

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.stock.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            StockMovement.objects.create(
                stock=self.stock,
                movement_type='SALE',
                quantity=self.quantity,
                status='APPROVED',
                notes=f"Sale #{self.sale.sale_number}"
            )


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('BOSS', 'Boss'),
        ('MANAGER', 'Manager'),
        ('FINANCE', 'Finance Officer'),
        ('SALES', 'Salesperson'),
        ('LOGISTICS', 'Logistics Officer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SALES')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Expense(models.Model):
    EXPENSE_TYPES = [
        ('OPERATIONAL', 'Operational Expense'),
        ('SALE_RELATED', 'Sale Related Expense'),
        ('TRANSPORT', 'Transport/Delivery'),
        ('UTILITIES', 'Utilities'),
        ('SALARY', 'Salary'),
        ('RENT', 'Rent'),
        ('MAINTENANCE', 'Maintenance'),
        ('OTHER', 'Other'),
    ]
    
    expense_number = models.CharField(max_length=50, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    receipt_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"Expense #{self.expense_number}: {self.amount}"


class Vehicle(models.Model):
    """Company vehicles that can be assigned to trips and require maintenance"""
    VEHICLE_TYPES = [
        ('TRUCK', 'Truck'),
        ('VAN', 'Van'),
        ('PICKUP', 'Pickup'),
        ('CAR', 'Car'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('INACTIVE', 'Inactive'),
        ('RETIRED', 'Retired'),
    ]
    
    registration_number = models.CharField(max_length=50, unique=True, help_text="License plate number")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    make = models.CharField(max_length=100, help_text="Manufacturer (e.g., Toyota, Ford)")
    model = models.CharField(max_length=100, help_text="Model name")
    year = models.IntegerField(help_text="Manufacturing year")
    color = models.CharField(max_length=50, blank=True)
    
    # Ownership & assignment
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='vehicles')
    assigned_driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicles')
    
    # Status & tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    current_mileage = models.IntegerField(default=0, help_text="Current odometer reading in KM")
    fuel_capacity = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Fuel tank capacity in liters")
    
    # Financial tracking
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    purchase_date = models.DateField(null=True, blank=True)
    
    # Insurance & compliance
    insurance_expiry = models.DateField(null=True, blank=True)
    registration_expiry = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['registration_number']
    
    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"
    
    @property
    def total_trips(self):
        return self.trips.count()
    
    @property
    def total_revenue(self):
        """Total revenue earned from all trips"""
        return sum(trip.revenue for trip in self.trips.filter(status='COMPLETED'))
    
    @property
    def total_maintenance_cost(self):
        """Total spent on maintenance"""
        return sum(maintenance.total_cost for maintenance in self.maintenance_records.all())
    
    @property
    def is_due_for_maintenance(self):
        """Check if vehicle needs maintenance based on last service"""
        last_maintenance = self.maintenance_records.order_by('-service_date').first()
        if not last_maintenance:
            return True
        # Simple check: if more than 5000 KM since last service
        return (self.current_mileage - last_maintenance.mileage_at_service) > 5000


class Trip(models.Model):
    """Vehicle trips that generate revenue for the business"""
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TRIP_TYPES = [
        ('DELIVERY', 'Delivery'),
        ('PICKUP', 'Pickup'),
        ('TRANSPORT', 'Transport'),
        ('RENTAL', 'Rental'),
        ('OTHER', 'Other'),
    ]
    
    trip_number = models.CharField(max_length=50, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='trips_driven')
    
    # Trip details
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPES, default='DELIVERY')
    origin = models.CharField(max_length=200, help_text="Starting location")
    destination = models.CharField(max_length=200, help_text="Destination location")
    distance = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Distance in KM")
    
    # Related entities
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips', help_text="Related sale if this is a delivery trip")
    logistics = models.ForeignKey('Logistics', on_delete=models.SET_NULL, null=True, blank=True, related_name='trips', help_text="Related logistics record")
    
    # Status & timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    scheduled_date = models.DateTimeField()
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Financial
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Revenue earned from this trip")
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Fuel expense for this trip")
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Tolls, parking, etc.")
    
    # Tracking
    start_mileage = models.IntegerField(null=True, blank=True, help_text="Odometer at trip start")
    end_mileage = models.IntegerField(null=True, blank=True, help_text="Odometer at trip end")
    
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date', '-created_at']
    
    def __str__(self):
        return f"Trip #{self.trip_number} - {self.vehicle.registration_number}"
    
    @property
    def net_profit(self):
        """Calculate profit: revenue - all expenses"""
        return self.revenue - (self.fuel_cost + self.other_expenses)
    
    @property
    def duration(self):
        """Calculate trip duration if completed"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update vehicle mileage when trip is completed
        if self.status == 'COMPLETED' and self.end_mileage:
            self.vehicle.current_mileage = self.end_mileage
            self.vehicle.save(update_fields=['current_mileage'])
        
        # Create expense record for trip costs if completed
        if not is_new and self.status == 'COMPLETED' and (self.fuel_cost > 0 or self.other_expenses > 0):
            total_trip_expense = self.fuel_cost + self.other_expenses
            if total_trip_expense > 0:
                expense_number = f"TRIP-{self.trip_number}"
                # Check if expense already exists
                if not Expense.objects.filter(expense_number=expense_number).exists():
                    Expense.objects.create(
                        expense_number=expense_number,
                        branch=self.vehicle.branch,
                        sale=self.sale,
                        expense_type='TRANSPORT',
                        description=f"Trip expenses for {self.trip_number}: {self.origin} to {self.destination}",
                        amount=total_trip_expense,
                        expense_date=self.end_time.date() if self.end_time else self.scheduled_date.date(),
                        notes=f"Fuel: {self.fuel_cost}, Other: {self.other_expenses}",
                        created_by=self.created_by
                    )


class VehicleMaintenance(models.Model):
    """Maintenance and repair records for vehicles"""
    MAINTENANCE_TYPES = [
        ('ROUTINE', 'Routine Service'),
        ('REPAIR', 'Repair'),
        ('INSPECTION', 'Inspection'),
        ('TIRE', 'Tire Service'),
        ('BRAKE', 'Brake Service'),
        ('ENGINE', 'Engine Work'),
        ('ELECTRICAL', 'Electrical'),
        ('BODYWORK', 'Body Work'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    maintenance_number = models.CharField(max_length=50, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    
    # Service details
    description = models.TextField(help_text="What work was done")
    service_provider = models.CharField(max_length=200, help_text="Garage/mechanic name")
    service_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    # Financial
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_costs = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Tracking
    mileage_at_service = models.IntegerField(help_text="Vehicle mileage at time of service")
    next_service_mileage = models.IntegerField(null=True, blank=True, help_text="When next service is due")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    receipt_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-service_date', '-created_at']
        verbose_name_plural = 'Vehicle Maintenance Records'
    
    def __str__(self):
        return f"Maintenance #{self.maintenance_number} - {self.vehicle.registration_number}"
    
    @property
    def total_cost(self):
        """Total maintenance cost"""
        return self.parts_cost + self.labor_cost + self.other_costs
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update vehicle status when maintenance starts
        if self.status == 'IN_PROGRESS' and self.vehicle.status != 'MAINTENANCE':
            self.vehicle.status = 'MAINTENANCE'
            self.vehicle.save(update_fields=['status'])
        
        # Update vehicle status when maintenance completes
        if self.status == 'COMPLETED':
            if self.vehicle.status == 'MAINTENANCE':
                self.vehicle.status = 'ACTIVE'
                self.vehicle.save(update_fields=['status'])
            
            # Create expense record for maintenance
            if not is_new and self.total_cost > 0:
                expense_number = f"MAINT-{self.maintenance_number}"
                # Check if expense already exists
                if not Expense.objects.filter(expense_number=expense_number).exists():
                    Expense.objects.create(
                        expense_number=expense_number,
                        branch=self.vehicle.branch,
                        expense_type='MAINTENANCE',
                        description=f"Vehicle maintenance: {self.description}",
                        amount=self.total_cost,
                        expense_date=self.completion_date or self.service_date,
                        receipt_number=self.receipt_number,
                        notes=f"Parts: {self.parts_cost}, Labor: {self.labor_cost}, Other: {self.other_costs}",
                        created_by=self.created_by
                    )


class StockBatch(models.Model):
    """Track individual batches of stock with their purchase prices"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    quantity = models.IntegerField()
    unit_purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    received_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['received_date']
    
    def __str__(self):
        return f"Batch {self.batch_number} - {self.stock.product.name}"


class BrokenProduct(models.Model):
    """Track broken/damaged products that affect profitability"""
    DAMAGE_TYPES = [
        ('BROKEN', 'Broken'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('DEFECTIVE', 'Defective'),
        ('LOST', 'Lost'),
        ('STOLEN', 'Stolen'),
        ('OTHER', 'Other'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='broken_items')
    quantity = models.IntegerField()
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPES)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost per unit when purchased")
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    reported_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-reported_date']
    
    def __str__(self):
        return f"{self.damage_type}: {self.quantity} x {self.stock.product.name}"
    
    @property
    def total_loss(self):
        return self.quantity * self.unit_cost
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Reduce stock quantity
        self.stock.quantity -= self.quantity
        self.stock.save()
        
        # Create expense record for the loss
        Expense.objects.create(
            expense_number=f"LOSS-{self.id}",
            branch=self.stock.branch,
            expense_type='OTHER',
            description=f"Product loss: {self.damage_type} - {self.stock.product.name}",
            amount=self.total_loss,
            expense_date=self.reported_date.date(),
            notes=self.description,
            created_by=self.reported_by
        )


class MonthlyProfitAnalysis(models.Model):
    """Monthly profit analysis per product per branch"""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    month = models.DateField(help_text="First day of the month")
    
    # Sales data
    total_quantity_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Cost data
    weighted_avg_purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Losses
    broken_quantity = models.IntegerField(default=0)
    broken_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Expenses allocated to this product
    allocated_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Calculated fields
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Stock turnover
    opening_stock = models.IntegerField(default=0)
    closing_stock = models.IntegerField(default=0)
    stock_turnover_ratio = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['branch', 'product', 'month']
        ordering = ['-month', 'branch', 'product']
    
    def __str__(self):
        return f"{self.product.name} @ {self.branch.name} - {self.month.strftime('%Y-%m')}"
    
    def calculate_profit(self):
        """Calculate all profit metrics"""
        # Gross profit = Revenue - Cost of Goods Sold
        self.gross_profit = self.total_revenue - self.total_purchase_cost
        
        # Net profit = Gross profit - Allocated expenses - Losses
        self.net_profit = self.gross_profit - self.allocated_expenses - self.broken_cost
        
        # Profit margin
        if self.total_revenue > 0:
            self.profit_margin = (self.net_profit / self.total_revenue) * 100
        else:
            self.profit_margin = Decimal('0.00')
        
        # Stock turnover ratio
        if self.opening_stock > 0:
            avg_stock = (self.opening_stock + self.closing_stock) / 2
            if avg_stock > 0:
                self.stock_turnover_ratio = self.total_quantity_sold / avg_stock
        
        self.save()


class OrderFulfillment(models.Model):
    """
    Track order fulfillment with sophisticated partial delivery and vehicle capacity management.
    An order can be fulfilled across multiple shipments based on vehicle capacity.
    """
    FULFILLMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_FULFILLED', 'Partially Fulfilled'),
        ('FULLY_FULFILLED', 'Fully Fulfilled'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    fulfillment_number = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='fulfillments')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='order_fulfillments')
    status = models.CharField(max_length=30, choices=FULFILLMENT_STATUS, default='PENDING')
    
    # Capacity and tracking
    total_items_ordered = models.IntegerField(default=0, help_text="Total items in the order")
    total_items_fulfilled = models.IntegerField(default=0, help_text="Total items delivered so far")
    total_items_remaining = models.IntegerField(default=0, help_text="Items still to be delivered")
    
    # Financial tracking
    total_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_collected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Total payments collected")
    total_remaining = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Outstanding balance")
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Fulfillment #{self.fulfillment_number} for Order #{self.order.order_number}"
    
    def calculate_fulfillment_status(self):
        """Auto-calculate fulfillment progress"""
        self.total_items_ordered = sum(item.quantity for item in self.order.items.all())
        self.total_items_fulfilled = sum(
            shipment_item.quantity_delivered 
            for shipment in self.shipments.all() 
            for shipment_item in shipment.items.all()
        )
        self.total_items_remaining = self.total_items_ordered - self.total_items_fulfilled
        
        # Calculate collected payments
        self.total_collected = sum(
            payment.amount_collected 
            for payment in self.payments.filter(status='COMPLETED')
        )
        self.total_remaining = self.total_order_value - self.total_collected
        
        # Update status
        if self.total_items_fulfilled == 0:
            self.status = 'PENDING'
        elif self.total_items_fulfilled < self.total_items_ordered:
            self.status = 'PARTIALLY_FULFILLED'
        else:
            self.status = 'FULLY_FULFILLED'
        
        self.save()
    
    @property
    def fulfillment_percentage(self):
        """Calculate percentage of order fulfilled"""
        if self.total_items_ordered > 0:
            return (self.total_items_fulfilled / self.total_items_ordered) * 100
        return 0
    
    @property
    def payment_percentage(self):
        """Calculate percentage of payment collected"""
        if self.total_order_value > 0:
            return (self.total_collected / self.total_order_value) * 100
        return 0


class OrderShipment(models.Model):
    """
    Individual shipment within an order fulfillment.
    Multiple shipments may be needed if vehicle capacity is limited.
    """
    SHIPMENT_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('LOADING', 'Loading'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('PARTIALLY_DELIVERED', 'Partially Delivered'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    shipment_number = models.CharField(max_length=50, unique=True)
    fulfillment = models.ForeignKey(OrderFulfillment, on_delete=models.CASCADE, related_name='shipments')
    
    # Vehicle and capacity tracking
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_shipments')
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_shipments_driven')
    vehicle_capacity = models.IntegerField(default=0, help_text="Maximum items this vehicle can carry")
    items_loaded = models.IntegerField(default=0, help_text="Actual items loaded in this shipment")
    
    # Trip integration
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_shipments')
    
    # Status and timing
    status = models.CharField(max_length=30, choices=SHIPMENT_STATUS, default='SCHEDULED')
    scheduled_date = models.DateTimeField()
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    
    # Delivery details
    delivery_address = models.TextField()
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_signature = models.BooleanField(default=False, help_text="Customer signed for delivery")
    
    # Financial
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date', '-created_at']
    
    def __str__(self):
        return f"Shipment #{self.shipment_number} - {self.get_status_display()}"
    
    def calculate_items_loaded(self):
        """Calculate total items loaded in this shipment"""
        self.items_loaded = sum(item.quantity_delivered for item in self.items.all())
        self.save()
    
    def assign_to_branch_stock(self):
        """
        When shipment is delivered, assign products to the destination branch.
        This is crucial for orders where products are distributed to branches.
        """
        if self.status == 'DELIVERED':
            destination_branch = self.fulfillment.branch
            for shipment_item in self.items.all():
                # Get or create stock at destination branch
                stock, created = Stock.objects.get_or_create(
                    branch=destination_branch,
                    product=shipment_item.order_item.product,
                    defaults={'quantity': 0}
                )
                # Add delivered quantity to branch stock
                stock.quantity += shipment_item.quantity_delivered
                stock.save()
                
                # Create stock movement record
                StockMovement.objects.create(
                    stock=stock,
                    movement_type='IN',
                    quantity=shipment_item.quantity_delivered,
                    from_branch=self.fulfillment.order.branch,
                    to_branch=destination_branch,
                    status='APPROVED',
                    notes=f"Delivered via Shipment #{self.shipment_number}",
                    created_by=self.created_by
                )


class ShipmentItem(models.Model):
    """
    Individual items within a shipment. Tracks what was delivered in each trip.
    """
    shipment = models.ForeignKey(OrderShipment, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='shipment_deliveries')
    
    quantity_ordered = models.IntegerField(help_text="Original quantity ordered")
    quantity_delivered = models.IntegerField(help_text="Quantity delivered in this shipment")
    quantity_remaining = models.IntegerField(help_text="Quantity still to be delivered")
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.order_item.product_name} - {self.quantity_delivered}/{self.quantity_ordered} delivered"
    
    @property
    def subtotal(self):
        return self.quantity_delivered * self.unit_price


class PaymentCollection(models.Model):
    """
    Track payments collected from customers for order fulfillments.
    Payments can be collected partially across multiple deliveries.
    """
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHEQUE', 'Cheque'),
        ('CARD', 'Credit/Debit Card'),
        ('OTHER', 'Other'),
    ]
    
    payment_number = models.CharField(max_length=50, unique=True)
    fulfillment = models.ForeignKey(OrderFulfillment, on_delete=models.CASCADE, related_name='payments')
    shipment = models.ForeignKey(OrderShipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', help_text="Payment collected during this shipment")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='payment_collections')
    
    # Payment details
    amount_collected = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount collected in this payment")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    
    # Tracking
    payment_date = models.DateTimeField()
    deposited_to_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='deposits_received', help_text="Which branch received this money")
    deposit_date = models.DateTimeField(null=True, blank=True, help_text="When was money deposited to branch")
    is_deposited = models.BooleanField(default=False, help_text="Has this payment been deposited to a branch?")
    
    # Reference
    reference_number = models.CharField(max_length=100, blank=True, help_text="Transaction ID, cheque number, etc.")
    receipt_number = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    collected_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_collected')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"Payment #{self.payment_number} - {self.amount_collected} ({self.get_payment_method_display()})"
    
    @property
    def is_outstanding(self):
        """Check if payment is outstanding (collected but not deposited)"""
        return self.status == 'COMPLETED' and not self.is_deposited


class PriceChangeLog(models.Model):
    """Enterprise price change audit log"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_changes')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    change_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-change_date']
    
    def __str__(self):
        return f"{self.product.name}: {self.old_price} → {self.new_price}"
    
    @property
    def price_change_percent(self):
        if self.old_price > 0:
            return ((self.new_price - self.old_price) / self.old_price) * 100
        return 0


class FuelConsumption(models.Model):
    """Track fuel consumption for vehicles"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_records')
    liters = models.DecimalField(max_digits=8, decimal_places=2, help_text="Liters of fuel consumed")
    cost_per_liter = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    mileage_at_fill = models.IntegerField(help_text="Vehicle mileage when fuel was added")
    fuel_station = models.CharField(max_length=200, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.liters}L on {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.total_cost:
            self.total_cost = self.liters * self.cost_per_liter
        super().save(*args, **kwargs)


class Maintenance(models.Model):
    """Simplified maintenance model for logistics analytics"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_logs')
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.description}"


class BusinessNote(models.Model):
    content = models.TextField(blank=True)
    page_number = models.IntegerField(default=1)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['page_number']
    
    def __str__(self):
        return f"Page {self.page_number}"
    
    @property
    def lines(self):
        return self.content.split('\n')[:7]  # Max 7 lines per page


class Logistics(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    tracking_number = models.CharField(max_length=50, unique=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='logistics')
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='outgoing_logistics')
    to_address = models.TextField()
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    delivery_date = models.DateField(null=True, blank=True)
    
    # Updated to use Vehicle model instead of plain text
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='logistics_assignments')
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='logistics_deliveries')
    
    # Keep legacy fields for backward compatibility
    driver_name = models.CharField(max_length=100, blank=True, help_text="Legacy field - use driver FK instead")
    vehicle_number = models.CharField(max_length=50, blank=True, help_text="Legacy field - use vehicle FK instead")
    
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Logistics'
    
    def __str__(self):
        return f"Logistics #{self.tracking_number}"
