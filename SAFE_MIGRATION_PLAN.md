# SAFE ORDER MANAGEMENT ENHANCEMENT PLAN
# This plan ensures NO DATA LOSS and maintains backward compatibility

## PHASE 1: ADD NEW FIELDS SAFELY (All fields are optional/nullable)

### 1. New OrderItem fields (all with defaults to preserve existing data):
- quantity_ordered = models.IntegerField(default=1)  # Will copy from existing 'quantity' field
- quantity_completed = models.IntegerField(default=0)  # Safe default
- quantity_remaining = models.IntegerField(default=0)  # Will be calculated
- status = models.CharField(default='PENDING')  # Safe default
- completion_branch = models.ForeignKey(null=True, blank=True)  # Optional
- updated_at = models.DateTimeField(auto_now=True)  # Safe to add

### 2. New Order fields (all with safe defaults):
- completed_amount = models.DecimalField(default=Decimal('0.00'))  # Safe default
- remaining_amount = models.DecimalField(default=Decimal('0.00'))  # Will be calculated
- updated_at = models.DateTimeField(auto_now=True)  # Safe to add

### 3. New models (completely separate, won't affect existing data):
- OrderItemCompletion (new table)
- OrderStatusHistory (new table)

## PHASE 2: DATA MIGRATION SCRIPT (Preserves all existing data)

```python
# This script will:
# 1. Copy existing 'quantity' to 'quantity_ordered' 
# 2. Set quantity_remaining = quantity_ordered for pending orders
# 3. For completed orders, set quantity_completed = quantity_ordered
# 4. Calculate remaining_amount for all orders
# 5. NO DATA IS DELETED OR MODIFIED DESTRUCTIVELY
```

## PHASE 3: BACKWARD COMPATIBILITY

### Keep existing 'quantity' field as property:
```python
@property
def quantity(self):
    return self.quantity_ordered  # Maintains compatibility
```

### All existing views will continue to work because:
- order.items.all() still works
- item.quantity still works (via property)
- item.subtotal still works
- All existing templates will work unchanged

## SAFETY GUARANTEES:

1. ✅ NO existing data will be deleted
2. ✅ NO existing fields will be removed
3. ✅ All existing functionality will continue to work
4. ✅ New fields are optional/nullable with safe defaults
5. ✅ Migration can be rolled back if needed
6. ✅ Existing orders and items remain fully functional

## IMPLEMENTATION STEPS:

1. First: Create migration with new fields (all optional)
2. Second: Run data migration to populate new fields from existing data
3. Third: Add new views and templates (existing ones unchanged)
4. Fourth: Test thoroughly on development copy
5. Fifth: Deploy with zero downtime

Would you like me to proceed with this SAFE approach?