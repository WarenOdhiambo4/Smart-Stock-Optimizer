import os
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
from decimal import Decimal
from datetime import datetime
import uuid

# Import models at module level
from .models import Sale, Order, Expense, Stock, Branch, Logistics, SaleItem, Trip, VehicleMaintenance

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
            'name': 'KabisaKabisa',
            'address': 'P.O. Box 12345, Kisumu, Kenya',
            'phone': '+254762548428',
            'email': 'info@kabisakabisa.co.ke',
            'logo': None
        }
        self.auditor_info = {
            'name': 'Waren Odhiambo',
            'phone': '+254762548428',
            'address': 'Kisumu, Kenya'
        }
    
    def generate_sale_receipt(self, sale, format='html'):
        """Generate receipt for a sale transaction with related expenses"""
        # Get sale-related expenses
        sale_expenses = Expense.objects.filter(sale=sale, expense_type='SALE_RELATED')
        total_sale_expenses = sum(exp.amount for exp in sale_expenses)
        
        # Calculate actual profit using average selling price method
        actual_profit = self._calculate_actual_profit(sale)
        
        items = self._format_sale_items(sale)
        
        # Add expenses to items if any
        if sale_expenses.exists():
            items.append({'description': 'SALE EXPENSES BREAKDOWN', 'details': 'Related expenses for this sale', 'quantity': 1, 'unit': 'section', 'rate': Decimal('0.00'), 'total': Decimal('0.00')})
            for exp in sale_expenses:
                items.append({'description': f'Expense: {exp.description}', 'details': f'Receipt: {exp.receipt_number}' if exp.receipt_number else '', 'quantity': 1, 'unit': 'expense', 'rate': exp.amount, 'total': -exp.amount})
        
        net_amount = sale.total_amount - total_sale_expenses
        
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
            'items': items,
            'subtotal': sale.total_amount,
            'discount': total_sale_expenses,
            'tax': Decimal('0.00'),
            'tax_rate': 0,
            'grand_total': net_amount,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Net Amount = Sales Total - Related Expenses = {self.currency}{sale.total_amount} - {self.currency}{total_sale_expenses} = {self.currency}{net_amount}. Actual Profit: {self.currency}{actual_profit}. Thank you for your business.',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def _calculate_actual_profit(self, sale):
        """Calculate actual profit using average selling price method"""
        total_profit = Decimal('0.00')
        
        for sale_item in sale.items.all():
            product = sale_item.stock.product
            
            # Get all sales of this product in the same period (month)
            month_start = sale.created_at.replace(day=1)
            if sale.created_at.month == 12:
                month_end = sale.created_at.replace(year=sale.created_at.year + 1, month=1, day=1)
            else:
                month_end = sale.created_at.replace(month=sale.created_at.month + 1, day=1)
            
            # Calculate average selling price for this product in the period
            period_sales = SaleItem.objects.filter(
                stock__product=product,
                sale__created_at__gte=month_start,
                sale__created_at__lt=month_end
            )
            
            if period_sales.exists():
                # Calculate weighted average: (price1*qty1 + price2*qty2) / total_qty
                total_revenue = sum(item.unit_price * item.quantity for item in period_sales)
                total_quantity = sum(item.quantity for item in period_sales)
                avg_selling_price = total_revenue / total_quantity if total_quantity > 0 else product.unit_price
            else:
                avg_selling_price = product.unit_price
            
            # Calculate profit: (avg_selling_price - cost_price) * quantity_sold
            item_profit = (avg_selling_price - product.cost_price) * sale_item.quantity
            total_profit += item_profit
        
        return total_profit
    
    def generate_trip_receipt(self, trip=None, vehicle=None, format='html'):
        """Generate trip receipt - general or per vehicle"""
        if trip:
            trips = [trip]
            doc_title = f'Trip Report - {trip.trip_number}'
            doc_number = trip.trip_number
        elif vehicle:
            trips = Trip.objects.filter(vehicle=vehicle)
            doc_title = f'Vehicle Trip Report - {vehicle.registration_number}'
            doc_number = f'VTR-{vehicle.registration_number}'
        else:
            trips = Trip.objects.all()
            doc_title = 'General Trip Report'
            doc_number = f'GTR-{datetime.now().strftime("%Y%m%d")}'
        
        items = []
        total_revenue = Decimal('0.00')
        total_costs = Decimal('0.00')
        
        for t in trips:
            revenue = t.revenue or Decimal('0.00')
            costs = (t.fuel_cost or Decimal('0.00')) + (t.other_expenses or Decimal('0.00'))
            profit = revenue - costs
            
            items.append({
                'description': f'Trip {t.trip_number}',
                'details': f'{t.origin} → {t.destination} | Distance: {t.distance}km | Status: {t.status}',
                'quantity': 1,
                'unit': 'trip',
                'rate': profit,
                'total': profit
            })
            
            total_revenue += revenue
            total_costs += costs
        
        context = {
            'document_type': doc_title,
            'document_number': doc_number,
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Trip Analysis',
            'branch': 'Logistics Department',
            'customer_label': 'TRIP ANALYSIS',
            'customer': {'name': f'{len(trips)} trips analyzed', 'address': f'Total Distance: {sum(float(t.distance or 0) for t in trips):.2f} km', 'phone': f'Revenue: {self.currency}{total_revenue}', 'email': f'Costs: {self.currency}{total_costs}'},
            'items': items,
            'subtotal': total_revenue,
            'discount': total_costs,
            'grand_total': total_revenue - total_costs,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Trip analysis prepared by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_maintenance_receipt(self, maintenance=None, vehicle=None, format='html'):
        """Generate maintenance receipt - general or per vehicle"""
        if maintenance:
            maintenances = [maintenance]
            doc_title = f'Maintenance Report - {maintenance.maintenance_number}'
            doc_number = maintenance.maintenance_number
        elif vehicle:
            maintenances = VehicleMaintenance.objects.filter(vehicle=vehicle)
            doc_title = f'Vehicle Maintenance Report - {vehicle.registration_number}'
            doc_number = f'VMR-{vehicle.registration_number}'
        else:
            maintenances = VehicleMaintenance.objects.all()
            doc_title = 'General Maintenance Report'
            doc_number = f'GMR-{datetime.now().strftime("%Y%m%d")}'
        
        items = []
        total_cost = Decimal('0.00')
        
        for m in maintenances:
            cost = m.total_cost
            items.append({
                'description': f'Maintenance {m.maintenance_number}',
                'details': f'{m.description} | Provider: {m.service_provider} | Type: {m.maintenance_type}',
                'quantity': 1,
                'unit': 'service',
                'rate': cost,
                'total': cost
            })
            total_cost += cost
        
        context = {
            'document_type': doc_title,
            'document_number': doc_number,
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Maintenance Analysis',
            'branch': 'Maintenance Department',
            'customer_label': 'MAINTENANCE ANALYSIS',
            'customer': {'name': f'{len(maintenances)} maintenance records', 'address': f'Total Services: {len(maintenances)}', 'phone': f'Average Cost: {self.currency}{total_cost/len(maintenances) if maintenances else 0}', 'email': 'Vehicle maintenance tracking'},
            'items': items,
            'subtotal': total_cost,
            'discount': Decimal('0.00'),
            'grand_total': total_cost,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Maintenance analysis prepared by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_stock_receipt(self, stock=None, branch=None, format='html'):
        """Generate stock receipt - general or per branch"""
        if stock:
            stocks = [stock]
            doc_title = f'Stock Report - {stock.product.name}'
            doc_number = f'STR-{stock.product.sku}'
        elif branch:
            stocks = Stock.objects.filter(branch=branch)
            doc_title = f'Stock Report - {branch.name}'
            doc_number = f'STR-{branch.name.upper()[:3]}'
        else:
            stocks = Stock.objects.all()
            doc_title = 'General Stock Report'
            doc_number = f'GSR-{datetime.now().strftime("%Y%m%d")}'
        
        items = []
        total_value = Decimal('0.00')
        
        for stock in stocks:
            value = Decimal(str(stock.quantity * stock.product.cost_price))
            items.append({
                'description': stock.product.name,
                'details': f'SKU: {stock.product.sku} | Branch: {stock.branch.name} | Min: {stock.min_quantity}',
                'quantity': stock.quantity,
                'unit': 'pcs',
                'rate': stock.product.cost_price,
                'total': value
            })
            total_value += value
        
        context = {
            'document_type': doc_title,
            'document_number': doc_number,
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Stock Analysis',
            'branch': branch.name if branch else 'All Branches',
            'customer_label': 'STOCK ANALYSIS',
            'customer': {'name': f'{len(stocks)} stock items', 'address': f'Total Products: {len(set(s.product for s in stocks))}', 'phone': f'Low Stock Items: {len([s for s in stocks if s.quantity <= s.min_quantity])}', 'email': 'Inventory tracking'},
            'items': items,
            'subtotal': total_value,
            'discount': Decimal('0.00'),
            'grand_total': total_value,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Stock analysis prepared by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
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
    
    def generate_expense_receipt(self, expense=None, department=None, format='html'):
        """Generate expense receipt - general or per department"""
        if expense:
            expenses = [expense]
            doc_title = f'Expense Voucher - {expense.expense_number}'
            doc_number = expense.expense_number
        elif department:
            expenses = Expense.objects.filter(branch__name__icontains=department)
            doc_title = f'Department Expense Report - {department}'
            doc_number = f'DER-{department.upper()[:3]}'
        else:
            expenses = Expense.objects.all()
            doc_title = 'General Expense Report'
            doc_number = f'GER-{datetime.now().strftime("%Y%m%d")}'
        
        items = []
        total_amount = Decimal('0.00')
        
        for exp in expenses:
            items.append({
                'description': exp.description,
                'details': f'Receipt: {exp.receipt_number} | Type: {exp.get_expense_type_display()} | Branch: {exp.branch.name}' if exp.receipt_number else f'Type: {exp.get_expense_type_display()} | Branch: {exp.branch.name}',
                'quantity': 1,
                'unit': 'expense',
                'rate': exp.amount,
                'total': exp.amount
            })
            total_amount += exp.amount
        
        context = {
            'document_type': doc_title,
            'document_number': doc_number,
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Expense Analysis',
            'branch': department if department else 'All Departments',
            'customer_label': 'EXPENSE ANALYSIS',
            'customer': {'name': f'{len(expenses)} expense records', 'address': f'Total Expenses: {len(expenses)}', 'phone': f'Average Amount: {self.currency}{total_amount/len(expenses) if expenses else 0}', 'email': 'Expense tracking'},
            'items': items,
            'subtotal': total_amount,
            'discount': Decimal('0.00'),
            'grand_total': total_amount,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Expense analysis prepared by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
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
                response = HttpResponse(html_content, content_type='text/html')
                return response
            
            pdf_file = weasyprint.HTML(string=html_content).write_pdf()
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            
            return response
        except Exception as e:
            response = HttpResponse(html_content, content_type='text/html')
            return response
    
    def generate_notes_receipt(self, note=None, format='html'):
        """Generate notes receipt"""
        from .models import BusinessNote
        
        if note:
            notes = [note]
            doc_title = f'Business Note - Page {note.page_number}'
            doc_number = f'NOTE-{note.page_number}'
        else:
            notes = BusinessNote.objects.all()
            doc_title = 'Business Notes Report'
            doc_number = f'NOTES-{datetime.now().strftime("%Y%m%d")}'
        
        items = []
        
        for note in notes:
            items.append({
                'description': f'Page {note.page_number}',
                'details': note.content[:100] + '...' if len(note.content) > 100 else note.content,
                'quantity': 1,
                'unit': 'page',
                'rate': Decimal('0.00'),
                'total': Decimal('0.00')
            })
        
        context = {
            'document_type': doc_title,
            'document_number': doc_number,
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Notes Analysis',
            'branch': 'All Branches',
            'customer_label': 'NOTES ANALYSIS',
            'customer': {'name': f'{len(notes)} note pages', 'address': f'Total Pages: {len(notes)}', 'phone': 'Business documentation', 'email': 'Notes tracking'},
            'items': items,
            'subtotal': Decimal('0.00'),
            'discount': Decimal('0.00'),
            'grand_total': Decimal('0.00'),
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Notes analysis prepared by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    def generate_stock_report(self, report_data, format='html'):
        """Generate stock report without pricing information"""
        context = {
            'document_type': report_data.get('document_type', 'STOCK BALANCE REPORT'),
            'document_number': report_data.get('document_number', f'STOCK-{datetime.now().strftime("%Y%m%d-%H%M%S")}'),
            'document_date': report_data.get('document_date', datetime.now().strftime('%d %B %Y')),
            'prepared_by': report_data.get('prepared_by', 'admin'),
            'payment_terms': 'Stock Balance Report',
            'branch': report_data.get('branch', 'All Branches'),
            'customer_label': 'STOCK BALANCE REPORT',
            'customer': {
                'name': 'Stock Balance Report',
                'address': f'No: {report_data.get("document_number", "STOCK-" + datetime.now().strftime("%Y%m%d-%H%M%S"))}',
                'phone': f'Date: {report_data.get("document_date", datetime.now().strftime("%d %B %Y"))}',
                'email': f'Prepared By: {report_data.get("prepared_by", "admin")}'
            },
            'items': report_data.get('items', []),
            'subtotal': Decimal('0.00'),
            'discount': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'tax_rate': 0,
            'grand_total': Decimal('0.00'),
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': report_data.get('notes', 'Stock Balance Report showing current quantities and recent movements.'),
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_financial_report(self, report_data, format='html'):
        """Generate financial report from provided data"""
        context = {
            'document_type': report_data.get('document_type', 'Financial Report'),
            'document_number': report_data.get('document_number', f'RPT-{datetime.now().strftime("%Y%m%d")}'),
            'document_date': report_data.get('document_date', datetime.now().strftime('%d %B %Y')),
            'prepared_by': report_data.get('prepared_by', f'{self.auditor_info["name"]} (Auditor)'),
            'payment_terms': 'Financial Analysis',
            'branch': report_data.get('branch', 'All Branches'),
            'customer_label': 'FINANCIAL ANALYSIS',
            'customer': report_data.get('customer', {'name': 'Financial Report', 'address': 'Analysis', 'phone': 'Report', 'email': 'Data'}),
            'items': report_data.get('items', []),
            'subtotal': report_data.get('subtotal', Decimal('0.00')),
            'discount': report_data.get('discount', Decimal('0.00')),
            'tax': report_data.get('tax', Decimal('0.00')),
            'tax_rate': report_data.get('tax_rate', 0),
            'grand_total': report_data.get('grand_total', Decimal('0.00')),
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': report_data.get('notes', f'Financial report prepared by {self.auditor_info["name"]}, {self.auditor_info["address"]}. Contact: {self.auditor_info["phone"]}'),
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_business_master_receipt(self, start_date, end_date, format='html'):
        """Generate master business report"""
        from django.db.models import Sum
        from django.utils import timezone
        
        branches = Branch.objects.filter(is_active=True)
        items = []
        total_sales = Decimal('0.00')
        total_expenses = Decimal('0.00')
        
        for branch in branches:
            sales = Sale.objects.filter(
                branch=branch,
                created_at__gte=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
                created_at__lt=timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            expenses = Expense.objects.filter(
                branch=branch,
                expense_date__gte=start_date,
                expense_date__lt=end_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            profit = sales - expenses
            
            items.append({
                'description': f'{branch.name} Branch',
                'details': f'Sales: {self.currency}{sales} | Expenses: {self.currency}{expenses}',
                'quantity': 1,
                'unit': 'branch',
                'rate': profit,
                'total': profit
            })
            
            total_sales += sales
            total_expenses += expenses
        
        context = {
            'document_type': 'Business Master Report',
            'document_number': f'BMR-{start_date.strftime("%Y%m%d")}-{end_date.strftime("%Y%m%d")}',
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Master Analysis',
            'branch': 'All Branches',
            'customer_label': 'BUSINESS MASTER ANALYSIS',
            'customer': {
                'name': f'Business Performance {start_date} to {end_date}',
                'address': f'Total Sales: {self.currency}{total_sales}',
                'phone': f'Total Expenses: {self.currency}{total_expenses}',
                'email': f'Net Profit: {self.currency}{total_sales - total_expenses}'
            },
            'items': items,
            'subtotal': total_sales,
            'discount': total_expenses,
            'grand_total': total_sales - total_expenses,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Master business report for {start_date} to {end_date} prepared by {self.auditor_info["name"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)
    
    def generate_branch_monthly_receipt(self, branch, start_date, end_date, format='html'):
        """Generate monthly report for specific branch"""
        from django.db.models import Sum
        from django.utils import timezone
        
        sales = Sale.objects.filter(
            branch=branch,
            created_at__gte=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
            created_at__lt=timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
        )
        
        expenses = Expense.objects.filter(
            branch=branch,
            expense_date__gte=start_date,
            expense_date__lt=end_date
        )
        
        items = []
        
        # Add sales items
        for sale in sales:
            items.append({
                'description': f'Sale {sale.sale_number}',
                'details': f'Customer: {sale.customer_name or "Walk-in"} | Date: {sale.created_at.strftime("%Y-%m-%d")}',
                'quantity': 1,
                'unit': 'sale',
                'rate': sale.total_amount,
                'total': sale.total_amount
            })
        
        # Add expense items
        for expense in expenses:
            items.append({
                'description': f'Expense {expense.expense_number}',
                'details': f'Type: {expense.get_expense_type_display()} | Date: {expense.expense_date}',
                'quantity': 1,
                'unit': 'expense',
                'rate': -expense.amount,
                'total': -expense.amount
            })
        
        total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context = {
            'document_type': f'{branch.name} Period Report',
            'document_number': f'BPR-{branch.name.upper()[:3]}-{start_date.strftime("%Y%m%d")}-{end_date.strftime("%Y%m%d")}',
            'document_date': datetime.now().strftime('%d %B %Y'),
            'prepared_by': f'{self.auditor_info["name"]} (Auditor)',
            'payment_terms': 'Period Analysis',
            'branch': branch.name,
            'customer_label': 'PERIOD ANALYSIS',
            'customer': {
                'name': f'{branch.name} Performance {start_date} to {end_date}',
                'address': f'Sales: {sales.count()} transactions',
                'phone': f'Expenses: {expenses.count()} records',
                'email': f'Net Profit: {self.currency}{total_sales - total_expenses}'
            },
            'items': items,
            'subtotal': total_sales,
            'discount': total_expenses,
            'grand_total': total_sales - total_expenses,
            'currency': self.currency,
            'company': self.company_info,
            'terms_conditions': f'Period report for {branch.name} branch for {start_date} to {end_date} prepared by {self.auditor_info["name"]}',
            'generated_date': datetime.now().strftime('%d %B %Y at %H:%M')
        }
        
        return self._render_document(context, format)