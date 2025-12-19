from django.core.management.base import BaseCommand
from core.models import Branch, Product, Sale, Order, Stock
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Create branches
        branches_data = [
            {'name': 'Main Branch', 'address': 'Nairobi CBD', 'phone': '+254700000001', 'email': 'main@kabisa.com'},
            {'name': 'Westlands Branch', 'address': 'Westlands', 'phone': '+254700000002', 'email': 'westlands@kabisa.com'},
            {'name': 'Mombasa Branch', 'address': 'Mombasa', 'phone': '+254700000003', 'email': 'mombasa@kabisa.com'},
        ]
        
        for data in branches_data:
            branch, created = Branch.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'Created branch: {branch.name}')
        
        # Create products
        products_data = [
            {'name': 'Laptop Computer', 'sku': 'LAP001', 'category': 'Electronics', 'unit_price': Decimal('1200.00'), 'cost_price': Decimal('800.00')},
            {'name': 'Office Chair', 'sku': 'CHR001', 'category': 'Furniture', 'unit_price': Decimal('250.00'), 'cost_price': Decimal('150.00')},
            {'name': 'Smartphone', 'sku': 'PHN001', 'category': 'Electronics', 'unit_price': Decimal('800.00'), 'cost_price': Decimal('500.00')},
            {'name': 'Desk Lamp', 'sku': 'LMP001', 'category': 'Furniture', 'unit_price': Decimal('45.00'), 'cost_price': Decimal('25.00')},
            {'name': 'Wireless Mouse', 'sku': 'MSE001', 'category': 'Electronics', 'unit_price': Decimal('35.00'), 'cost_price': Decimal('20.00')},
        ]
        
        for data in products_data:
            product, created = Product.objects.get_or_create(sku=data['sku'], defaults=data)
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        # Create stock and sales
        if Branch.objects.exists() and Product.objects.exists():
            branches = list(Branch.objects.all())
            products = list(Product.objects.all())
            
            # Create stock for products
            for branch in branches:
                for product in products:
                    stock, created = Stock.objects.get_or_create(
                        branch=branch,
                        product=product,
                        defaults={'quantity': 50, 'min_quantity': 10}
                    )
                    if created:
                        self.stdout.write(f'Created stock: {product.name} at {branch.name}')
            
            # Create sample sales
            sales_data = [
                {'sale_number': 'SAL001', 'branch': branches[0], 'customer_name': 'John Customer', 'total_amount': Decimal('2400.00')},
                {'sale_number': 'SAL002', 'branch': branches[0], 'customer_name': 'Jane Buyer', 'total_amount': Decimal('250.00')},
                {'sale_number': 'SAL003', 'branch': branches[1] if len(branches) > 1 else branches[0], 'customer_name': 'Mike Client', 'total_amount': Decimal('2400.00')},
            ]
            
            for data in sales_data:
                sale, created = Sale.objects.get_or_create(sale_number=data['sale_number'], defaults=data)
                if created:
                    self.stdout.write(f'Created sale: {sale.sale_number} - ${sale.total_amount}')
        
        # Print final counts
        self.stdout.write(self.style.SUCCESS(f'Database populated successfully!'))
        self.stdout.write(f'Branches: {Branch.objects.count()}')
        self.stdout.write(f'Products: {Product.objects.count()}')
        self.stdout.write(f'Stock records: {Stock.objects.count()}')
        self.stdout.write(f'Sales: {Sale.objects.count()}')
        self.stdout.write(f'Orders: {Order.objects.count()}')