from django.core.management.base import BaseCommand
from core.models import Branch, Product, Sale, Order
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Create branches
        branches_data = [
            {'name': 'Main Branch', 'location': 'Nairobi CBD', 'manager': 'John Doe', 'phone': '+254700000001', 'email': 'main@kabisa.com'},
            {'name': 'Westlands Branch', 'location': 'Westlands', 'manager': 'Jane Smith', 'phone': '+254700000002', 'email': 'westlands@kabisa.com'},
            {'name': 'Mombasa Branch', 'location': 'Mombasa', 'manager': 'Mike Johnson', 'phone': '+254700000003', 'email': 'mombasa@kabisa.com'},
        ]
        
        for data in branches_data:
            branch, created = Branch.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'Created branch: {branch.name}')
        
        # Create products
        products_data = [
            {'name': 'Laptop Computer', 'category': 'Electronics', 'price': Decimal('1200.00'), 'cost': Decimal('800.00'), 'stock_quantity': 15},
            {'name': 'Office Chair', 'category': 'Furniture', 'price': Decimal('250.00'), 'cost': Decimal('150.00'), 'stock_quantity': 8},
            {'name': 'Smartphone', 'category': 'Electronics', 'price': Decimal('800.00'), 'cost': Decimal('500.00'), 'stock_quantity': 25},
            {'name': 'Desk Lamp', 'category': 'Furniture', 'price': Decimal('45.00'), 'cost': Decimal('25.00'), 'stock_quantity': 12},
            {'name': 'Wireless Mouse', 'category': 'Electronics', 'price': Decimal('35.00'), 'cost': Decimal('20.00'), 'stock_quantity': 30},
        ]
        
        for data in products_data:
            product, created = Product.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        # Create sales
        if Branch.objects.exists() and Product.objects.exists():
            branches = list(Branch.objects.all())
            products = list(Product.objects.all())
            
            sales_data = [
                {'product': products[0], 'branch': branches[0], 'quantity': 2, 'unit_price': Decimal('1200.00'), 'total_amount': Decimal('2400.00')},
                {'product': products[1], 'branch': branches[0], 'quantity': 1, 'unit_price': Decimal('250.00'), 'total_amount': Decimal('250.00')},
                {'product': products[2], 'branch': branches[1] if len(branches) > 1 else branches[0], 'quantity': 3, 'unit_price': Decimal('800.00'), 'total_amount': Decimal('2400.00')},
                {'product': products[3], 'branch': branches[2] if len(branches) > 2 else branches[0], 'quantity': 5, 'unit_price': Decimal('45.00'), 'total_amount': Decimal('225.00')},
            ]
            
            for data in sales_data:
                if not Sale.objects.filter(product=data['product'], branch=data['branch'], quantity=data['quantity']).exists():
                    sale = Sale.objects.create(**data)
                    self.stdout.write(f'Created sale: {sale.product.name} - ${sale.total_amount}')
        
        # Print final counts
        self.stdout.write(self.style.SUCCESS(f'Database populated successfully!'))
        self.stdout.write(f'Branches: {Branch.objects.count()}')
        self.stdout.write(f'Products: {Product.objects.count()}')
        self.stdout.write(f'Sales: {Sale.objects.count()}')
        self.stdout.write(f'Orders: {Order.objects.count()}')