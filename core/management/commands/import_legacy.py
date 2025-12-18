# import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from datetime import datetime
from core.models import Branch, Product, Sale, SaleItem, Stock, Expense
import os


class Command(BaseCommand):
    help = 'Import legacy sales data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='OLD_DATA/SALES SYSTEM@ KABISAKABISA - KISUMU.csv',
            help='Path to CSV file relative to project root'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        
        # Get absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        csv_path = os.path.join(base_dir, csv_file)
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_path}'))
            return
        
        self.stdout.write(f'Starting import from: {csv_path}')
        
        # Create default branch
        branch, created = Branch.objects.get_or_create(
            name='Kisumu Branch',
            defaults={'address': 'Kisumu, Kenya', 'is_active': True}
        )
        if created:
            self.stdout.write(f'Created branch: {branch.name}')
        
        # Read CSV with pandas
        try:
            df = pd.read_csv(csv_path)
            self.stdout.write(f'Loaded {len(df)} rows from CSV')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading CSV: {e}'))
            return
        
        # Clean and process data
        df = df.dropna(subset=['DATE', 'PRODUCT NAME'])  # Remove rows without date or product
        df = df[df['PRODUCT NAME'].str.strip() != '']  # Remove empty product names
        
        self.stdout.write(f'Processing {len(df)} valid rows...')
        
        imported_count = 0
        error_count = 0
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Parse date
                    date_str = str(row['DATE']).strip()
                    if not date_str or date_str == 'nan':
                        continue
                    
                    # Handle different date formats
                    try:
                        if '/' in date_str:
                            sale_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                        else:
                            sale_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        continue
                    
                    # Extract product info
                    product_name = str(row['PRODUCT NAME']).strip()
                    if not product_name or product_name == 'nan':
                        continue
                    
                    # Parse quantities and prices
                    quantity = self._parse_number(row.get('SALE QUANTITY', 0))
                    unit_price = self._parse_number(row.get('UNIT PRIICE', 0))  # Note: typo in CSV
                    total_sales = self._parse_number(row.get('TOTAL SALES', 0))
                    
                    if quantity <= 0 or unit_price <= 0:
                        continue
                    
                    # Create/get product
                    product, created = Product.objects.get_or_create(
                        name=product_name,
                        defaults={
                            'sku': self._generate_sku(product_name),
                            'unit_price': Decimal(str(unit_price)),
                            'cost_price': Decimal(str(unit_price * 0.7)),  # Assume 30% margin
                            'category': self._categorize_product(product_name)
                        }
                    )
                    
                    # Create/get stock
                    stock, created = Stock.objects.get_or_create(
                        branch=branch,
                        product=product,
                        defaults={'quantity': 1000, 'min_quantity': 10}  # Default stock
                    )
                    
                    # Generate sale number
                    sale_number = f"LEG-{sale_date.strftime('%Y%m%d')}-{index}"
                    
                    # Create sale
                    sale, created = Sale.objects.get_or_create(
                        sale_number=sale_number,
                        defaults={
                            'branch': branch,
                            'total_amount': Decimal(str(total_sales)) if total_sales > 0 else Decimal(str(quantity * unit_price)),
                            'payment_method': self._get_payment_method(row),
                            'created_at': datetime.combine(sale_date, datetime.min.time())
                        }
                    )
                    
                    if created:
                        # Create sale item
                        SaleItem.objects.create(
                            sale=sale,
                            stock=stock,
                            quantity=int(quantity),
                            unit_price=Decimal(str(unit_price))
                        )
                        
                        # Handle expenses if present
                        self._create_expense_if_exists(row, branch, sale, sale_date)
                        
                        imported_count += 1
                        
                        if imported_count % 100 == 0:
                            self.stdout.write(f'Imported {imported_count} records...')
                
                except Exception as e:
                    error_count += 1
                    if error_count <= 10:  # Only show first 10 errors
                        self.stdout.write(self.style.WARNING(f'Error on row {index}: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed! Imported: {imported_count}, Errors: {error_count}'
            )
        )

    def _parse_number(self, value):
        """Parse number from string, handling commas and quotes"""
        if pd.isna(value) or value == '':
            return 0
        
        # Convert to string and clean
        str_val = str(value).replace(',', '').replace('"', '').strip()
        
        try:
            return float(str_val)
        except:
            return 0

    def _generate_sku(self, product_name):
        """Generate SKU from product name"""
        # Take first 3 words, uppercase, replace spaces with dashes
        words = product_name.upper().split()[:3]
        sku = '-'.join(words).replace(' ', '-')[:20]
        return sku

    def _categorize_product(self, product_name):
        """Categorize product based on name"""
        name_lower = product_name.lower()
        
        if 'mm' in name_lower and ('x' in name_lower or '×' in name_lower):
            return 'Tiles'
        elif 'grout' in name_lower:
            return 'Grout'
        elif 'cornerstrip' in name_lower or 'corner' in name_lower:
            return 'Corner Strips'
        elif 'adhesive' in name_lower:
            return 'Adhesive'
        elif 'spacer' in name_lower:
            return 'Spacers'
        elif 'ass.' in name_lower or 'assorted' in name_lower:
            return 'Assorted Tiles'
        else:
            return 'Other'

    def _get_payment_method(self, row):
        """Determine payment method from row data"""
        payment_mode = str(row.get('PAYMENT MODE', '')).upper()
        
        if 'BANK' in payment_mode:
            return 'Bank Transfer'
        elif 'CASH' in payment_mode:
            return 'Cash'
        else:
            return 'Cash'  # Default

    def _create_expense_if_exists(self, row, branch, sale, sale_date):
        """Create expense record if expense data exists in row"""
        expense_key = str(row.get('EXPENSE KEY', '')).strip()
        expense_value = self._parse_number(row.get('EXPENSE VALUE', 0))
        expense_category = str(row.get('EXPENSE CATEGORY', '')).strip()
        
        if expense_key and expense_value > 0:
            # Generate expense number
            expense_number = f"LEG-EXP-{sale_date.strftime('%Y%m%d')}-{sale.id}"
            
            # Determine expense type
            expense_type = 'OTHER'
            if 'FUEL' in expense_key.upper():
                expense_type = 'TRANSPORT'
            elif any(word in expense_key.upper() for word in ['OFFLOAD', 'LOAD', 'TRANSPORT']):
                expense_type = 'TRANSPORT'
            elif 'PERSONAL' in expense_category.upper():
                expense_type = 'OTHER'
            elif 'RESTOCKING' in expense_category.upper():
                expense_type = 'OPERATIONAL'
            
            Expense.objects.get_or_create(
                expense_number=expense_number,
                defaults={
                    'branch': branch,
                    'sale': sale,
                    'expense_type': expense_type,
                    'description': f"Legacy expense: {expense_key}",
                    'amount': Decimal(str(expense_value)),
                    'expense_date': sale_date,
                    'notes': f"Category: {expense_category}"
                }
            )