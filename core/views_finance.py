import json
from decimal import Decimal
from datetime import datetime
import re

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    AccountingPeriod,
    Branch,
    ChartOfAccount,
    GeneralLedger,
    LedgerTransaction,
    IncomeRegister,
    ExpenseRegister,
    LoansRegister,
    PayrollLedger,
    AllowanceRegister,
    Employee,
    Vehicle,
)
from .views import role_required
from .finance_services import (
    AccountingError,
    post_income_register,
    post_expense_register,
    post_loan_register,
    post_payroll_entry,
    sync_product_metrics_ledger,
    reverse_transaction,
)
from .views import role_required


def _employee_for_user(user):
    try:
        return user.employee
    except Employee.DoesNotExist:
        return None


def _ensure_open_period(date_value):
    closed_period = AccountingPeriod.objects.filter(
        is_closed=True,
        start_date__lte=date_value,
        end_date__gte=date_value,
    ).first()
    if closed_period:
        raise AccountingError("This period is closed. No edits or postings allowed.")


def _parse_decimal(value, default=Decimal('0.00')):
    if value in (None, ''):
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _parse_date(value):
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except Exception:
            continue
    return None


def _manual_allowed(setting_name: str) -> bool:
    return bool(getattr(settings, setting_name, True))


@login_required
@role_required('ADMIN', 'BOSS', 'MANAGER', 'FINANCE')
def ledger_list(request):
    accounts = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
    branches = Branch.objects.filter(is_active=True).order_by('name')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    parsed_date_from = _parse_date(date_from)
    parsed_date_to = _parse_date(date_to)
    account_id = request.GET.get('account')
    entry_type = request.GET.get('entry_type')
    branch_id = request.GET.get('branch')

    resolved_account = None
    if account_id:
        if str(account_id).isdigit():
            resolved_account = ChartOfAccount.objects.filter(id=account_id).first()
        else:
            resolved_account = ChartOfAccount.objects.filter(account_code=str(account_id)).first()
            if not resolved_account:
                resolved_account = ChartOfAccount.objects.filter(account_name__icontains=str(account_id)).first()
        if resolved_account:
            account_id = str(resolved_account.id)

    resolved_branch = None
    if branch_id:
        if str(branch_id).isdigit():
            resolved_branch = Branch.objects.filter(id=branch_id).first()
        else:
            resolved_branch = Branch.objects.filter(name__icontains=str(branch_id)).first()
        if resolved_branch:
            branch_id = str(resolved_branch.id)

    entries = GeneralLedger.objects.select_related(
        'transaction',
        'account',
        'transaction__branch',
        'transaction__vehicle',
    )

    if parsed_date_from:
        entries = entries.filter(transaction__transaction_date__gte=parsed_date_from)
    if parsed_date_to:
        entries = entries.filter(transaction__transaction_date__lte=parsed_date_to)
    if account_id:
        entries = entries.filter(account_id=account_id)
    if branch_id:
        entries = entries.filter(transaction__branch_id=branch_id)
    if entry_type == 'debit':
        entries = entries.filter(debit_amount__gt=0)
    elif entry_type == 'credit':
        entries = entries.filter(credit_amount__gt=0)

    entries = entries.order_by('transaction__transaction_date', 'transaction__id', 'id')

    entries_list = list(entries)

    running_balances = {}
    if account_id:
        account = ChartOfAccount.objects.filter(id=account_id).first()
        balance = account.opening_balance if account else Decimal('0.00')
        for entry in entries_list:
            if account and account.normal_balance == 'DEBIT':
                balance += entry.debit_amount - entry.credit_amount
            else:
                balance += entry.credit_amount - entry.debit_amount
            running_balances[entry.id] = balance

    metrics_pattern = re.compile(
        r"Product metrics (?P<month>\d{4}-\d{2}) - (?P<product>.+?) @ (?P<branch>.+?) "
        r"\| Units Sold: (?P<units>\d+) \| Avg Price: (?P<avg>[\d\.]+) "
        r"\| Unit Cost: (?P<cost>[\d\.]+) \| Restocked: (?P<restocked>\d+) "
        r"\| Broken Units: (?P<broken>\d+) \| Utilization: (?P<util>[\d\.]+)%"
    )

    for entry in entries_list:
        entry.running_balance = running_balances.get(entry.id) if account_id else None
        entry.metric_month = None
        entry.product_name = None
        entry.units_sold = None
        entry.avg_price = None
        entry.unit_cost = None
        entry.restocked_units = None
        entry.broken_units = None
        entry.utilization_rate = None

        if entry.transaction and entry.transaction.source_type == 'PRODUCT_METRICS':
            desc = entry.transaction.description or ''
            match = metrics_pattern.search(desc)
            if match:
                entry.metric_month = match.group('month')
                entry.product_name = match.group('product')
                entry.units_sold = int(match.group('units'))
                entry.avg_price = Decimal(match.group('avg'))
                entry.unit_cost = Decimal(match.group('cost'))
                entry.restocked_units = int(match.group('restocked'))
                entry.broken_units = int(match.group('broken'))
                entry.utilization_rate = match.group('util')
            else:
                ref = entry.transaction.reference or ''
                parts = {}
                for chunk in ref.split('|'):
                    if ':' in chunk:
                        key, value = chunk.split(':', 1)
                        parts[key.strip()] = value.strip()
                entry.units_sold = int(parts.get('US', '0') or 0)
                entry.avg_price = _parse_decimal(parts.get('AP'))
                entry.restocked_units = int(parts.get('RS', '0') or 0)
                entry.broken_units = int(parts.get('BR', '0') or 0)
                entry.utilization_rate = parts.get('UT', '').replace('%', '') or None

    paginator = Paginator(entries_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/ledger_list.html', {
        'page_obj': page_obj,
        'accounts': accounts,
        'branches': branches,
        'filters': {
            'date_from': date_from or '',
            'date_to': date_to or '',
            'account_id': int(account_id) if account_id and str(account_id).isdigit() else (resolved_account.id if resolved_account else None),
            'entry_type': entry_type or '',
            'branch_id': int(branch_id) if branch_id and str(branch_id).isdigit() else (resolved_branch.id if resolved_branch else None),
        }
    })


@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def logistics_ledger(request):
    vehicles = Vehicle.objects.order_by('registration_number')
    vehicle_id = request.GET.get('vehicle')

    entries = GeneralLedger.objects.select_related(
        'transaction',
        'account',
        'transaction__branch',
        'transaction__vehicle',
    ).filter(transaction__source_type='LOGISTICS')

    if vehicle_id:
        entries = entries.filter(transaction__vehicle_id=vehicle_id)

    entries = entries.order_by('transaction__transaction_date', 'transaction__id', 'id')

    paginator = Paginator(entries, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/logistics_ledger.html', {
        'page_obj': page_obj,
        'vehicles': vehicles,
        'filters': {
            'vehicle_id': int(vehicle_id) if vehicle_id else None,
        }
    })


@login_required
@role_required('ADMIN')
def chart_of_accounts(request):
    accounts = ChartOfAccount.objects.all().order_by('account_code')

    ledger_sums = GeneralLedger.objects.values('account_id').annotate(
        debit_sum=Sum('debit_amount'),
        credit_sum=Sum('credit_amount')
    )
    ledger_map = {item['account_id']: item for item in ledger_sums}

    for account in accounts:
        sums = ledger_map.get(account.id, {'debit_sum': Decimal('0.00'), 'credit_sum': Decimal('0.00')})
        debit_sum = sums['debit_sum'] or Decimal('0.00')
        credit_sum = sums['credit_sum'] or Decimal('0.00')
        if account.normal_balance == 'DEBIT':
            account.current_balance = account.opening_balance + debit_sum - credit_sum
        else:
            account.current_balance = account.opening_balance + credit_sum - debit_sum

    return render(request, 'core/chart_of_accounts.html', {
        'accounts': accounts,
        'account_types': ChartOfAccount.ACCOUNT_TYPES,
    })


@require_POST
@login_required
@role_required('ADMIN', 'BOSS')
def chart_of_accounts_create(request):
    data = json.loads(request.body or '{}')
    account_code = data.get('account_code')
    account_name = data.get('account_name')
    account_type = data.get('account_type')
    opening_balance = _parse_decimal(data.get('opening_balance'))
    is_active = str(data.get('is_active', 'true')).lower() == 'true'

    if not account_code or not account_name or not account_type:
        return JsonResponse({'error': 'Account code, name, and type are required.'}, status=400)

    account = ChartOfAccount.objects.create(
        account_code=account_code,
        account_name=account_name,
        account_type=account_type,
        opening_balance=opening_balance,
        is_active=is_active,
    )
    return JsonResponse({'id': account.id})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS')
def chart_of_accounts_update(request, pk):
    account = get_object_or_404(ChartOfAccount, pk=pk)
    data = json.loads(request.body or '{}')
    field = data.get('field')
    value = data.get('value')

    if field in ['account_code', 'account_name', 'account_type']:
        setattr(account, field, value)
    elif field == 'opening_balance':
        account.opening_balance = _parse_decimal(value)
    elif field == 'is_active':
        account.is_active = str(value).lower() == 'true'
    else:
        return JsonResponse({'error': 'Invalid field'}, status=400)

    account.save()
    return JsonResponse({'status': 'ok'})


@login_required
@role_required('ADMIN')
def income_register(request):
    entries = IncomeRegister.objects.select_related('account_credited').order_by('-date', '-id')
    accounts = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
    return render(request, 'core/income_register.html', {
        'entries': entries,
        'accounts': accounts,
        'payment_methods': IncomeRegister.PAYMENT_METHODS,
        'manual_allowed': _manual_allowed('ACCOUNTING_MANUAL_INCOME_REGISTER'),
    })


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def income_register_create(request):
    if not _manual_allowed('ACCOUNTING_MANUAL_INCOME_REGISTER'):
        return JsonResponse({'error': 'Income register is auto-generated from Sales. Edit in Sales module.'}, status=403)
    data = json.loads(request.body or '{}')
    date_value = _parse_date(data.get('date'))
    if not date_value:
        return JsonResponse({'error': 'Date is required.'}, status=400)

    _ensure_open_period(date_value)

    receipt_no = data.get('receipt_no') or f"RCPT-{timezone.now().strftime('%H%M%S')}"
    source = data.get('source')
    account_id = data.get('account_credited')
    amount = _parse_decimal(data.get('amount'))
    payment_method = data.get('payment_method') or 'CASH'
    reference = data.get('reference', '')

    if not source or not account_id or amount <= 0:
        return JsonResponse({'error': 'Source, account, and amount are required.'}, status=400)

    entry = IncomeRegister.objects.create(
        date=date_value,
        receipt_no=receipt_no,
        source=source,
        account_credited_id=account_id,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
    )
    return JsonResponse({'id': entry.id})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def income_register_update(request, pk):
    if not _manual_allowed('ACCOUNTING_MANUAL_INCOME_REGISTER'):
        return JsonResponse({'error': 'Income register is auto-generated from Sales. Edit in Sales module.'}, status=403)
    entry = get_object_or_404(IncomeRegister, pk=pk)
    if entry.posted:
        return JsonResponse({'error': 'Posted entries cannot be edited.'}, status=400)

    data = json.loads(request.body or '{}')
    field = data.get('field')
    value = data.get('value')

    if field == 'date':
        parsed = _parse_date(value)
        if not parsed:
            return JsonResponse({'error': 'Invalid date.'}, status=400)
        _ensure_open_period(parsed)
        entry.date = parsed
    elif field in ['receipt_no', 'source', 'reference', 'payment_method']:
        setattr(entry, field, value)
    elif field == 'account_credited':
        entry.account_credited_id = value
    elif field == 'amount':
        entry.amount = _parse_decimal(value)
    else:
        return JsonResponse({'error': 'Invalid field.'}, status=400)

    entry.save()
    return JsonResponse({'status': 'ok'})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def income_register_post(request, pk):
    entry = get_object_or_404(IncomeRegister, pk=pk)
    try:
        txn = post_income_register(entry, _employee_for_user(request.user))
        return JsonResponse({'transaction_id': txn.transaction_id})
    except AccountingError as exc:
        return JsonResponse({'error': str(exc)}, status=400)


@login_required
@role_required('ADMIN')
def expense_register(request):
    entries = ExpenseRegister.objects.select_related('account_debited').order_by('-date', '-id')
    accounts = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
    return render(request, 'core/expense_register.html', {
        'entries': entries,
        'accounts': accounts,
        'payment_methods': ExpenseRegister.PAYMENT_METHODS,
        'manual_allowed': _manual_allowed('ACCOUNTING_MANUAL_EXPENSE_REGISTER'),
    })


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def expense_register_create(request):
    if not _manual_allowed('ACCOUNTING_MANUAL_EXPENSE_REGISTER'):
        return JsonResponse({'error': 'Expense register is auto-generated from Expenses. Edit in Expenses module.'}, status=403)
    data = json.loads(request.body or '{}')
    date_value = _parse_date(data.get('date'))
    if not date_value:
        return JsonResponse({'error': 'Date is required.'}, status=400)

    _ensure_open_period(date_value)

    voucher_no = data.get('voucher_no') or f"VCHR-{timezone.now().strftime('%H%M%S')}"
    category = data.get('category')
    account_id = data.get('account_debited')
    amount = _parse_decimal(data.get('amount'))
    payment_method = data.get('payment_method') or 'CASH'
    reference = data.get('reference', '')
    approved = str(data.get('approved', 'false')).lower() == 'true'

    if not category or not account_id or amount <= 0:
        return JsonResponse({'error': 'Category, account, and amount are required.'}, status=400)

    entry = ExpenseRegister.objects.create(
        date=date_value,
        voucher_no=voucher_no,
        category=category,
        account_debited_id=account_id,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        approved=approved,
    )
    return JsonResponse({'id': entry.id})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def expense_register_update(request, pk):
    if not _manual_allowed('ACCOUNTING_MANUAL_EXPENSE_REGISTER'):
        return JsonResponse({'error': 'Expense register is auto-generated from Expenses. Edit in Expenses module.'}, status=403)
    entry = get_object_or_404(ExpenseRegister, pk=pk)
    if entry.posted:
        return JsonResponse({'error': 'Posted entries cannot be edited.'}, status=400)

    data = json.loads(request.body or '{}')
    field = data.get('field')
    value = data.get('value')

    if field == 'date':
        parsed = _parse_date(value)
        if not parsed:
            return JsonResponse({'error': 'Invalid date.'}, status=400)
        _ensure_open_period(parsed)
        entry.date = parsed
    elif field in ['voucher_no', 'category', 'reference', 'payment_method']:
        setattr(entry, field, value)
    elif field == 'account_debited':
        entry.account_debited_id = value
    elif field == 'amount':
        entry.amount = _parse_decimal(value)
    elif field == 'approved':
        entry.approved = str(value).lower() == 'true'
    else:
        return JsonResponse({'error': 'Invalid field.'}, status=400)

    entry.save()
    return JsonResponse({'status': 'ok'})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def expense_register_post(request, pk):
    entry = get_object_or_404(ExpenseRegister, pk=pk)
    try:
        txn = post_expense_register(entry, _employee_for_user(request.user))
        return JsonResponse({'transaction_id': txn.transaction_id})
    except AccountingError as exc:
        return JsonResponse({'error': str(exc)}, status=400)


@login_required
@role_required('ADMIN')
def loans_register(request):
    entries = LoansRegister.objects.select_related('account').order_by('-due_date', '-id')
    accounts = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
    return render(request, 'core/loans_register.html', {
        'entries': entries,
        'accounts': accounts,
        'status_choices': LoansRegister.STATUS_CHOICES,
    })


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def loans_register_create(request):
    data = json.loads(request.body or '{}')
    due_date = _parse_date(data.get('due_date'))
    if not due_date:
        return JsonResponse({'error': 'Due date is required.'}, status=400)

    _ensure_open_period(due_date)

    loan_id = data.get('loan_id') or f"LOAN-{timezone.now().strftime('%H%M%S')}"
    lender = data.get('lender')
    account_id = data.get('account')
    principal = _parse_decimal(data.get('principal'))
    interest_rate = _parse_decimal(data.get('interest_rate'))
    amount_paid = _parse_decimal(data.get('amount_paid'))

    if not lender or not account_id or principal <= 0:
        return JsonResponse({'error': 'Lender, account, and principal are required.'}, status=400)

    entry = LoansRegister.objects.create(
        loan_id=loan_id,
        lender=lender,
        account_id=account_id,
        principal=principal,
        interest_rate=interest_rate,
        amount_paid=amount_paid,
        due_date=due_date,
    )
    return JsonResponse({'id': entry.id})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def loans_register_update(request, pk):
    entry = get_object_or_404(LoansRegister, pk=pk)
    if entry.posted:
        return JsonResponse({'error': 'Posted entries cannot be edited.'}, status=400)

    data = json.loads(request.body or '{}')
    field = data.get('field')
    value = data.get('value')

    if field in ['loan_id', 'lender', 'status']:
        setattr(entry, field, value)
    elif field == 'account':
        entry.account_id = value
    elif field == 'principal':
        entry.principal = _parse_decimal(value)
    elif field == 'interest_rate':
        entry.interest_rate = _parse_decimal(value)
    elif field == 'amount_paid':
        entry.amount_paid = _parse_decimal(value)
    elif field == 'due_date':
        parsed = _parse_date(value)
        if not parsed:
            return JsonResponse({'error': 'Invalid date.'}, status=400)
        _ensure_open_period(parsed)
        entry.due_date = parsed
    else:
        return JsonResponse({'error': 'Invalid field.'}, status=400)

    entry.save()
    return JsonResponse({'status': 'ok'})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def loans_register_post(request, pk):
    entry = get_object_or_404(LoansRegister, pk=pk)
    try:
        txn = post_loan_register(entry, _employee_for_user(request.user))
        return JsonResponse({'transaction_id': txn.transaction_id})
    except AccountingError as exc:
        return JsonResponse({'error': str(exc)}, status=400)


@login_required
@role_required('ADMIN')
def payroll_ledger(request):
    entries = PayrollLedger.objects.order_by('-payment_date', '-id')
    return render(request, 'core/payroll_ledger.html', {
        'entries': entries,
        'manual_allowed': _manual_allowed('ACCOUNTING_MANUAL_PAYROLL_LEDGER'),
    })


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def payroll_ledger_create(request):
    if not _manual_allowed('ACCOUNTING_MANUAL_PAYROLL_LEDGER'):
        return JsonResponse({'error': 'Payroll ledger is auto-generated from Payroll module.'}, status=403)
    data = json.loads(request.body or '{}')
    payment_date = _parse_date(data.get('payment_date'))
    if not payment_date:
        return JsonResponse({'error': 'Payment date is required.'}, status=400)

    _ensure_open_period(payment_date)

    entry = PayrollLedger.objects.create(
        pay_period=data.get('pay_period', ''),
        employee_name=data.get('employee_name', ''),
        basic_salary=_parse_decimal(data.get('basic_salary')),
        allowances=_parse_decimal(data.get('allowances')),
        deductions=_parse_decimal(data.get('deductions')),
        payment_date=payment_date,
        reference=data.get('reference', ''),
    )
    return JsonResponse({'id': entry.id})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def payroll_ledger_update(request, pk):
    if not _manual_allowed('ACCOUNTING_MANUAL_PAYROLL_LEDGER'):
        return JsonResponse({'error': 'Payroll ledger is auto-generated from Payroll module.'}, status=403)
    entry = get_object_or_404(PayrollLedger, pk=pk)
    if entry.posted:
        return JsonResponse({'error': 'Posted entries cannot be edited.'}, status=400)

    data = json.loads(request.body or '{}')
    field = data.get('field')
    value = data.get('value')

    if field in ['pay_period', 'employee_name', 'reference']:
        setattr(entry, field, value)
    elif field in ['basic_salary', 'allowances', 'deductions']:
        setattr(entry, field, _parse_decimal(value))
    elif field == 'payment_date':
        parsed = _parse_date(value)
        if not parsed:
            return JsonResponse({'error': 'Invalid date.'}, status=400)
        _ensure_open_period(parsed)
        entry.payment_date = parsed
    else:
        return JsonResponse({'error': 'Invalid field.'}, status=400)

    entry.save()
    return JsonResponse({'status': 'ok'})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def payroll_ledger_post(request, pk):
    entry = get_object_or_404(PayrollLedger, pk=pk)
    try:
        txn = post_payroll_entry(entry, _employee_for_user(request.user))
        return JsonResponse({'transaction_id': txn.transaction_id})
    except AccountingError as exc:
        return JsonResponse({'error': str(exc)}, status=400)


@login_required
@role_required('ADMIN')
def allowances_register(request):
    entries = AllowanceRegister.objects.order_by('-effective_date', '-id')
    return render(request, 'core/allowances_register.html', {
        'entries': entries,
        'fixed_types': AllowanceRegister.FIXED_TYPES,
        'status_choices': AllowanceRegister.STATUS_CHOICES,
    })


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def allowances_register_create(request):
    data = json.loads(request.body or '{}')
    effective_date = _parse_date(data.get('effective_date'))
    if not effective_date:
        return JsonResponse({'error': 'Effective date is required.'}, status=400)

    entry = AllowanceRegister.objects.create(
        employee_name=data.get('employee_name', ''),
        allowance_type=data.get('allowance_type', ''),
        fixed_or_variable=data.get('fixed_or_variable', 'FIXED'),
        amount=_parse_decimal(data.get('amount')),
        effective_date=effective_date,
        status=data.get('status', 'ACTIVE'),
    )
    return JsonResponse({'id': entry.id})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def allowances_register_update(request, pk):
    entry = get_object_or_404(AllowanceRegister, pk=pk)
    data = json.loads(request.body or '{}')
    field = data.get('field')
    value = data.get('value')

    if field in ['employee_name', 'allowance_type', 'fixed_or_variable', 'status']:
        setattr(entry, field, value)
    elif field == 'amount':
        entry.amount = _parse_decimal(value)
    elif field == 'effective_date':
        parsed = _parse_date(value)
        if not parsed:
            return JsonResponse({'error': 'Invalid date.'}, status=400)
        entry.effective_date = parsed
    else:
        return JsonResponse({'error': 'Invalid field.'}, status=400)

    entry.save()
    return JsonResponse({'status': 'ok'})


@require_POST
@login_required
@role_required('ADMIN', 'BOSS', 'FINANCE')
def ledger_reverse(request, pk):
    transaction_obj = get_object_or_404(LedgerTransaction, pk=pk)
    try:
        reversal = reverse_transaction(transaction_obj, _employee_for_user(request.user))
        return JsonResponse({'transaction_id': reversal.transaction_id})
    except AccountingError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    # Refresh product metrics ledger based on filter range (monthly scope)
    today = timezone.now().date()
    if parsed_date_from or parsed_date_to:
        start_date = parsed_date_from or parsed_date_to
        end_date = parsed_date_to or parsed_date_from
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        current = start_month
        while current <= end_month:
            sync_product_metrics_ledger(current, user=_employee_for_user(request.user))
            next_month = (current.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
            current = next_month
    else:
        month_start = today.replace(day=1)
        sync_product_metrics_ledger(month_start, user=_employee_for_user(request.user))
