"""
Modern Financial Analytics Dashboard Views
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Branch
from .financial_analytics import FinancialAnalytics
from .views import role_required


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
def modern_analytics_dashboard(request):
    """Modern analytics dashboard with real-time data"""
    branches = Branch.objects.filter(is_active=True)
    
    context = {
        'branches': branches,
        'page_title': 'Financial Analytics Dashboard'
    }
    return render(request, 'core/modern_analytics.html', context)


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE', 'MANAGER')
@require_GET
def analytics_api(request):
    """API endpoint for analytics data"""
    try:
        branch_id = request.GET.get('branch')
        days = int(request.GET.get('days', 365))
        
        if branch_id:
            branch_id = int(branch_id)
        
        data = FinancialAnalytics.get_dashboard_data(branch_id, days)
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def export_analytics_excel(request):
    """Export analytics to Excel"""
    try:
        from django.http import HttpResponse
        import xlsxwriter
        from io import BytesIO
        
        branch_id = request.GET.get('branch')
        days = int(request.GET.get('days', 365))
        
        if branch_id:
            branch_id = int(branch_id)
        
        data = FinancialAnalytics.get_dashboard_data(branch_id, days)
        
        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Summary sheet
        summary_sheet = workbook.add_worksheet('Financial Summary')
        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '$#,##0.00'})
        
        summary_sheet.write('A1', 'Kabisa Enterprise Financial Report', bold)
        summary_sheet.write('A3', 'Total Revenue', bold)
        summary_sheet.write('B3', data['profitability']['total_revenue'], money)
        summary_sheet.write('A4', 'Total Expenses', bold)
        summary_sheet.write('B4', data['profitability']['total_expenses'], money)
        summary_sheet.write('A5', 'Net Profit', bold)
        summary_sheet.write('B5', data['profitability']['net_profit'], money)
        summary_sheet.write('A6', 'Profit Margin %', bold)
        summary_sheet.write('B6', data['profitability']['profit_margin'])
        
        # Risk sheet
        if 'risk' in data and 'error' not in data['risk']:
            risk_sheet = workbook.add_worksheet('Risk Analysis')
            risk_sheet.write('A1', 'Risk Assessment', bold)
            risk_sheet.write('A3', 'Value at Risk (95%)', bold)
            risk_sheet.write('B3', data['risk']['value_at_risk_95'], money)
            risk_sheet.write('A4', 'Risk Level', bold)
            risk_sheet.write('B4', data['risk']['risk_level'])
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=kabisa_analytics.xlsx'
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})