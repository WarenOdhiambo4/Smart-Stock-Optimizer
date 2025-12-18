"""
Airtable Adapter for Django ERP Models
This adapter allows Django models to sync with Airtable tables
"""
from .airtable_service import airtable_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AirtableAdapter:
    """Base adapter class for syncing Django models with Airtable"""
    
    def __init__(self, table_name, model_class):
        self.table_name = table_name
        self.model_class = model_class
        self.table = airtable_service.get_table(table_name)
    
    def django_to_airtable(self, instance):
        """Convert Django model instance to Airtable record format"""
        raise NotImplementedError("Subclasses must implement django_to_airtable")
    
    def airtable_to_django(self, record):
        """Convert Airtable record to Django model data"""
        raise NotImplementedError("Subclasses must implement airtable_to_django")
    
    def sync_to_airtable(self, instance):
        """Sync Django model instance to Airtable"""
        try:
            data = self.django_to_airtable(instance)
            if hasattr(instance, 'airtable_id') and instance.airtable_id:
                # Update existing record
                return airtable_service.update_record(self.table_name, instance.airtable_id, data)
            else:
                # Create new record
                result = airtable_service.create_record(self.table_name, data)
                # Store Airtable ID back to Django model
                instance.airtable_id = result['id']
                instance.save(update_fields=['airtable_id'])
                return result
        except Exception as e:
            logger.error(f"Error syncing {instance} to Airtable: {e}")
            return None
    
    def sync_from_airtable(self):
        """Sync all records from Airtable to Django"""
        try:
            records = airtable_service.get_records(self.table_name)
            for record in records:
                data = self.airtable_to_django(record)
                # Create or update Django model
                obj, created = self.model_class.objects.update_or_create(
                    airtable_id=record['id'],
                    defaults=data
                )
                if created:
                    logger.info(f"Created {obj} from Airtable")
                else:
                    logger.info(f"Updated {obj} from Airtable")
        except Exception as e:
            logger.error(f"Error syncing from Airtable: {e}")


class ProductAdapter(AirtableAdapter):
    """Adapter for Product model"""
    
    def __init__(self):
        from .models import Product
        super().__init__('Products', Product)
    
    def django_to_airtable(self, instance):
        return {
            'Name': instance.name,
            'SKU': instance.sku,
            'Price': float(instance.unit_price),
            'Category': instance.category,
            'Description': instance.description,
            'Active': instance.is_active,
            'Created': instance.created_at.isoformat() if instance.created_at else None,
        }
    
    def airtable_to_django(self, record):
        fields = record['fields']
        return {
            'name': fields.get('Name', ''),
            'sku': fields.get('SKU', ''),
            'unit_price': fields.get('Price', 0),
            'category': fields.get('Category', ''),
            'description': fields.get('Description', ''),
            'is_active': fields.get('Active', True),
        }


class OrderAdapter(AirtableAdapter):
    """Adapter for Order model"""
    
    def __init__(self):
        from .models import Order
        super().__init__('Orders', Order)
    
    def django_to_airtable(self, instance):
        return {
            'Order Number': instance.order_number,
            'Supplier': instance.supplier,
            'Status': instance.status,
            'Total Amount': float(instance.total_amount),
            'Notes': instance.notes,
            'Created': instance.created_at.isoformat() if instance.created_at else None,
        }
    
    def airtable_to_django(self, record):
        fields = record['fields']
        return {
            'order_number': fields.get('Order Number', ''),
            'supplier': fields.get('Supplier', ''),
            'status': fields.get('Status', 'PENDING'),
            'total_amount': fields.get('Total Amount', 0),
            'notes': fields.get('Notes', ''),
        }


class SaleAdapter(AirtableAdapter):
    """Adapter for Sale model"""
    
    def __init__(self):
        from .models import Sale
        super().__init__('Sales', Sale)
    
    def django_to_airtable(self, instance):
        return {
            'Sale Number': instance.sale_number,
            'Customer Name': instance.customer_name,
            'Customer Phone': instance.customer_phone,
            'Total Amount': float(instance.total_amount),
            'Payment Method': instance.payment_method,
            'Notes': instance.notes,
            'Created': instance.created_at.isoformat() if instance.created_at else None,
        }
    
    def airtable_to_django(self, record):
        fields = record['fields']
        return {
            'sale_number': fields.get('Sale Number', ''),
            'customer_name': fields.get('Customer Name', ''),
            'customer_phone': fields.get('Customer Phone', ''),
            'total_amount': fields.get('Total Amount', 0),
            'payment_method': fields.get('Payment Method', 'Cash'),
            'notes': fields.get('Notes', ''),
        }


class BranchAdapter(AirtableAdapter):
    """Adapter for Branch model"""
    
    def __init__(self):
        from .models import Branch
        super().__init__('Branches', Branch)
    
    def django_to_airtable(self, instance):
        return {
            'Name': instance.name,
            'Address': instance.address,
            'Phone': instance.phone,
            'Email': instance.email,
            'Active': instance.is_active,
            'Created': instance.created_at.date().isoformat() if instance.created_at else None,
        }
    
    def airtable_to_django(self, record):
        fields = record['fields']
        return {
            'name': fields.get('Name', ''),
            'address': fields.get('Address', ''),
            'phone': fields.get('Phone', ''),
            'email': fields.get('Email', ''),
            'is_active': fields.get('Active', True),
        }


class ExpenseAdapter(AirtableAdapter):
    """Adapter for Expense model"""
    
    def __init__(self):
        from .models import Expense
        super().__init__('Expenses', Expense)
    
    def django_to_airtable(self, instance):
        return {
            'Expense Number': instance.expense_number,
            'Type': instance.expense_type,
            'Description': instance.description,
            'Amount': float(instance.amount),
            'Date': instance.expense_date.isoformat() if instance.expense_date else None,
            'Receipt Number': instance.receipt_number,
            'Notes': instance.notes,
            'Created': instance.created_at.isoformat() if instance.created_at else None,
        }
    
    def airtable_to_django(self, record):
        fields = record['fields']
        expense_date = None
        if fields.get('Date'):
            try:
                expense_date = datetime.fromisoformat(fields['Date']).date()
            except:
                expense_date = datetime.now().date()
        
        return {
            'expense_number': fields.get('Expense Number', ''),
            'expense_type': fields.get('Type', 'OTHER'),
            'description': fields.get('Description', ''),
            'amount': fields.get('Amount', 0),
            'expense_date': expense_date or datetime.now().date(),
            'receipt_number': fields.get('Receipt Number', ''),
            'notes': fields.get('Notes', ''),
        }


# Global adapter instances
branch_adapter = BranchAdapter()
product_adapter = ProductAdapter()
order_adapter = OrderAdapter()
sale_adapter = SaleAdapter()
expense_adapter = ExpenseAdapter()

# Sync functions
def sync_all_to_airtable():
    """Sync all Django data to Airtable"""
    from .models import Branch, Product, Order, Sale, Expense
    
    # Sync branches
    for branch in Branch.objects.all():
        branch_adapter.sync_to_airtable(branch)
    
    # Sync products
    for product in Product.objects.all():
        product_adapter.sync_to_airtable(product)
    
    # Sync orders
    for order in Order.objects.all():
        order_adapter.sync_to_airtable(order)
    
    # Sync sales
    for sale in Sale.objects.all():
        sale_adapter.sync_to_airtable(sale)
    
    # Sync expenses
    for expense in Expense.objects.all():
        expense_adapter.sync_to_airtable(expense)

def sync_all_from_airtable():
    """Sync all Airtable data to Django"""
    branch_adapter.sync_from_airtable()
    product_adapter.sync_from_airtable()
    order_adapter.sync_from_airtable()
    sale_adapter.sync_from_airtable()
    expense_adapter.sync_from_airtable()