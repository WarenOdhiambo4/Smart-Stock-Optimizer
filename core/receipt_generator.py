import os
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
from decimal import Decimal
from datetime import datetime
import uuid

# Import models at module level
from .models import Sale, Order, Expense, Stock, Branch, Logistics

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class ReceiptGenerator:
    """
    Enterprise-grade receipt/invoice generator with PDF export capability.
    Supports Sales, Orders, Expenses, and custom documents.
    """
    
    def __init__(self):
        self.currency = "KES "
        self.company_info = {
            'name': 'Kabisa Fraternity',
            'address': 'P.O. Box 12345, Kisumu, Kenya',
            'phone': '+254 790 018 750',
            'email': 'info@kabisafraternity.co.ke',
            'tax_id': 'KRA PIN: P051234567M',
            'logo': None
        }
        self.auditor_info = {
            'name': 'Waren Odhiambo',
            'phone': '0790018750',
            'address': 'Kisumu, Kenya'
        }
    
    def generate_sale_receipt(self, sale, format='html'):
        """Generate receipt for a sale transaction"""
        context = {
            'document_type': 'Sales Receipt',
            'document_number': sale.sale_number,
            'document_date': sale.created_at.strftime('%d %B %Y'),
            'due_date': None,
            'prepared_by': sale.created_by.get_full_name() if sale.created_by else 'System',
            'payment_terms': sale.payment_method,
            'branch': sale.branch.name,
            'customer_label': 'SOLD TO',
            'customer': {
                'name': sale.customer_name or 'Walk-in Customer',
                'address': None,
                'phone': sale.customer_phone,
                'email': None
            },
            'items': self._format_sale_items(sale),
            'subtotal': sale.total_amount,
            'discount': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'tax_rate': 0,
            'grand_total': sale.total_amount,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': 'Thank you for your business. All sales are final.',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_order_receipt(self, order, format='html'):
        """Generate receipt for an order"""
        context = {
            'document_type': 'Purchase Order',
            'document_number': order.order_number,
            'document_date': order.created_at.strftime('%d %B %Y'),
            'due_date': None,
            'prepared_by': order.created_by.get_full_name() if order.created_by else 'System',
            'payment_terms': 'Net 30',
            'branch': order.branch.name,
            'customer_label': 'SUPPLIER',
            'customer': {
                'name': order.supplier or 'Various Suppliers',
                'address': None,
                'phone': None,
                'email': None
            },
            'items': self._format_order_items(order),
            'subtotal': order.total_amount,
            'discount': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'tax_rate': 0,
            'grand_total': order.total_amount,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Order Status: {order.get_status_display()}. {order.notes}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_expense_receipt(self, expense, format='html'):
        """Generate receipt for an expense"""
        context = {
            'document_type': 'Expense Voucher',
            'document_number': expense.expense_number,
            'document_date': expense.expense_date.strftime('%d %B %Y'),
            'due_date': None,
            'prepared_by': expense.created_by.get_full_name() if expense.created_by else 'System',
            'payment_terms': 'Paid',
            'branch': expense.branch.name,
            'customer_label': 'EXPENSE DETAILS',
            'customer': {
                'name': expense.get_expense_type_display(),
                'address': None,
                'phone': None,
                'email': None
            },
            'items': [{
                'description': expense.description,
                'details': f'Receipt: {expense.receipt_number}' if expense.receipt_number else None,
                'quantity': 1,
                'unit': 'item',
                'rate': expense.amount,
                'total': expense.amount
            }],
            'subtotal': expense.amount,
            'discount': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'tax_rate': 0,
            'grand_total': expense.amount,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': expense.notes,
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_financial_report(self, report_data, format='html'):
        """Generate financial report receipt"""
        context = {
            'document_type': 'Financial Report',
            'document_number': f'RPT-{uuid.uuid4().hex[:8].upper()}',
            'document_date': datetime.now().strftime('%d %B %Y'),
            'due_date': None,
            'prepared_by': report_data.get('prepared_by', 'System'),
            'payment_terms': 'Report',
            'branch': report_data.get('branch', 'All Branches'),
            'customer_label': 'REPORT PERIOD',
            'customer': {
                'name': report_data.get('period', 'Current Period'),
                'address': None,
                'phone': None,
                'email': None
            },
            'items': report_data.get('items', []),
            'subtotal': report_data.get('subtotal', Decimal('0.00')),
            'discount': report_data.get('discount', Decimal('0.00')),
            'tax': report_data.get('tax', Decimal('0.00')),
            'tax_rate': report_data.get('tax_rate', 0),
            'grand_total': report_data.get('grand_total', Decimal('0.00')),
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': report_data.get('notes', 'This is a system-generated financial report.'),
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_branch_monthly_receipt(self, branch, year, month, format='html'):
        """Generate comprehensive monthly receipt for a branch"""
        from django.db.models import Sum
        
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        # Sales data
        sales = Sale.objects.filter(branch=branch, created_at__gte=start_date, created_at__lt=end_date)
        total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Expenses data
        expenses = Expense.objects.filter(branch=branch, expense_date__gte=start_date, expense_date__lt=end_date).exclude(expense_type='DELIVERY')
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Stock data
        stocks = Stock.objects.filter(branch=branch)
        total_stock_value = sum(s.quantity * s.product.cost_price for s in stocks)
        
        items = [
            {'description': 'Sales Revenue', 'details': f'{sales.count()} transactions', 'quantity': sales.count(), 'unit': 'sales', 'rate': total_sales / sales.count() if sales.count() > 0 else Decimal('0.00'), 'total': total_sales},
            {'description': 'Operating Expenses', 'details': f'{expenses.count()} expense items', 'quantity': expenses.count(), 'unit': 'expenses', 'rate': total_expenses / expenses.count() if expenses.count() > 0 else Decimal('0.00'), 'total': -total_expenses},
            {'description': 'Stock Value', 'details': f'{stocks.count()} products', 'quantity': stocks.count(), 'unit': 'products', 'rate': Decimal(str(total_stock_value)) / stocks.count() if stocks.count() > 0 else Decimal('0.00'), 'total': Decimal(str(total_stock_value))}
        ]
        
        context = {
            'document_type': 'Monthly Branch Report',
            'document_number': f'BR-{branch.name.upper()[:3]}-{year}{month:02d}',
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Monthly Report',
            'branch': branch.name,
            'customer_label': 'BRANCH PERFORMANCE',
            'customer': {'name': f'{branch.name} Branch', 'address': branch.address, 'phone': branch.phone, 'email': branch.email},
            'items': items,
            'subtotal': total_sales + Decimal(str(total_stock_value)),
            'discount': total_expenses,
            'grand_total': total_sales - total_expenses,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Monthly report for {datetime(year, month, 1).strftime("%B %Y")}. Audited by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_business_master_receipt(self, year, month, format='html'):
        """Generate master business receipt with detailed calculations"""
        from django.db.models import Sum
        from .delivery_manager import DeliveryChargesManager
        
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        branches = Branch.objects.filter(is_active=True)
        items = []
        total_business_sales = Decimal('0.00')
        total_business_expenses = Decimal('0.00')
        
        for branch in branches:
            branch_sales = Sale.objects.filter(branch=branch, created_at__gte=start_date, created_at__lt=end_date).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            branch_expenses = Expense.objects.filter(branch=branch, expense_date__gte=start_date, expense_date__lt=end_date).exclude(expense_type='DELIVERY').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            branch_profit = branch_sales - branch_expenses
            
            items.append({'description': f'{branch.name} Branch', 'details': f'Sales: {self.currency}{branch_sales:,.2f} | Expenses: {self.currency}{branch_expenses:,.2f}', 'quantity': 1, 'unit': 'branch', 'rate': branch_profit, 'total': branch_profit})
            
            total_business_sales += branch_sales
            total_business_expenses += branch_expenses
        
        delivery_expenses = DeliveryChargesManager.get_total_delivery_expenses(start_date, end_date)
        gross_profit = total_business_sales - total_business_expenses
        net_business_profit = gross_profit - delivery_expenses
        
        items.extend([
            {'description': 'CALCULATION BREAKDOWN', 'details': 'Mathematical verification', 'quantity': 1, 'unit': 'analysis', 'rate': Decimal('0.00'), 'total': Decimal('0.00')},
            {'description': 'Total Revenue', 'details': 'All branch sales', 'quantity': branches.count(), 'unit': 'branches', 'rate': total_business_sales / branches.count() if branches.count() > 0 else Decimal('0.00'), 'total': total_business_sales},
            {'description': 'Delivery Charges', 'details': 'Company-wide delivery', 'quantity': 1, 'unit': 'business', 'rate': delivery_expenses, 'total': -delivery_expenses}
        ])
        
        context = {
            'document_type': 'Master Business Report',
            'document_number': f'MBR-{year}{month:02d}-FINAL',
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Chief Auditor)',
            'payment_terms': 'Business Analysis',
            'branch': 'All Branches',
            'customer_label': 'BUSINESS PERFORMANCE',
            'customer': {'name': 'Kabisa Fraternity - Complete Operations', 'address': f'Audited by: {self.auditor_info["name"]}, {self.auditor_info["address"]}', 'phone': f'Contact: {self.auditor_info["phone"]}', 'email': 'Mathematical breakdown included'},
            'items': items,
            'subtotal': total_business_sales,
            'discount': total_business_expenses + delivery_expenses,
            'grand_total': net_business_profit,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'MATHEMATICAL VERIFICATION:\n1. Total Revenue = {self.currency}{total_business_sales:,.2f}\n2. Branch Expenses = {self.currency}{total_business_expenses:,.2f}\n3. Delivery Charges = {self.currency}{delivery_expenses:,.2f}\n4. Gross Profit = Revenue - Expenses = {self.currency}{gross_profit:,.2f}\n5. NET PROFIT = Gross - Delivery = {self.currency}{net_business_profit:,.2f}\n\nAudited by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def _format_sale_items(self, sale):
        """Format sale items for receipt"""
        items = []
        for item in sale.items.all():
            items.append({
                'description': item.stock.product.name,
                'details': f'SKU: {item.stock.product.sku}',
                'quantity': item.quantity,
                'unit': 'pcs',
                'rate': item.unit_price,
                'total': item.subtotal
            })
        return items
    
    def _format_order_items(self, order):
        """Format order items for receipt"""
        items = []
        for item in order.items.all():
            items.append({
                'description': item.product_name,
                'details': f'SKU: {item.product_sku}' if item.product_sku else None,
                'quantity': item.quantity_ordered,
                'unit': 'pcs',
                'rate': item.unit_price,
                'total': item.subtotal
            })
        return items
    
    def _render_document(self, context, format):
        """Render document in specified format"""
        # Add missing context fields
        context.update({
            'due_date': context.get('due_date'),
            'tax': context.get('tax', Decimal('0.00')),
            'tax_rate': context.get('tax_rate', 0),
            'discount': context.get('discount', Decimal('0.00'))
        })
        
        html_content = render_to_string('core/receipt_template.html', context)
        
        if format == 'pdf':
            return self._generate_pdf(html_content, context['document_number'])
        else:
            return html_content
    
    def _generate_pdf(self, html_content, filename):
        """Generate PDF from HTML content"""
        try:
            if not WEASYPRINT_AVAILABLE:
                # Fallback to HTML response if WeasyPrint not available
                response = HttpResponse(html_content, content_type='text/html')
                return response
            
            # Create PDF
            pdf_file = weasyprint.HTML(string=html_content).write_pdf()
            
            # Create HTTP response
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            
            return response
        except Exception as e:
            # Fallback to HTML if PDF generation fails
            response = HttpResponse(html_content, content_type='text/html')
            return response
    
    def get_print_url(self, document_type, document_id):
        """Get URL for printing document"""
        urls = {
            'sale': f'/sales/{document_id}/print/',
            'order': f'/orders/{document_id}/print/',
            'expense': f'/expenses/{document_id}/print/',
            'report': f'/reports/{document_id}/print/'
        }
        return urls.get(document_type, '#')


# Utility functions for easy access
def generate_sale_pdf(sale):
    """Quick function to generate sale PDF"""
    generator = ReceiptGenerator()
    return generator.generate_sale_receipt(sale, format='pdf')

def generate_order_pdf(order):
    """Quick function to generate order PDF"""
    generator = ReceiptGenerator()
    return generator.generate_order_receipt(order, format='pdf')

def generate_expense_pdf(expense):
    """Quick function to generate expense PDF"""
    generator = ReceiptGenerator()
    return generator.generate_expense_receipt(expense, format='pdf')