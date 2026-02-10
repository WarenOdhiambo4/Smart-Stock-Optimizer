from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    AccountingPeriod,
    Branch,
    ChartOfAccount,
    BrokenProduct,
    GeneralLedger,
    LedgerTransaction,
    IncomeRegister,
    ExpenseRegister,
    LoansRegister,
    PayrollLedger,
    Product,
    SaleItem,
    Stock,
    StockMovement,
    Vehicle,
)


DEFAULT_ACCOUNT_CONFIG = {
    'CASH': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_CASH_ACCOUNT_CODE', '1000'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_CASH_ACCOUNT_NAME', 'Cash on Hand'),
        'type': 'ASSET',
    },
    'BANK': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_BANK_ACCOUNT_CODE', '1010'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_BANK_ACCOUNT_NAME', 'Bank Account'),
        'type': 'ASSET',
    },
    'MOBILE': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_MOBILE_ACCOUNT_CODE', '1020'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_MOBILE_ACCOUNT_NAME', 'Mobile Money'),
        'type': 'ASSET',
    },
    'CARD': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_CARD_ACCOUNT_CODE', '1030'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_CARD_ACCOUNT_NAME', 'Card Receipts'),
        'type': 'ASSET',
    },
    'OTHER': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_OTHER_ACCOUNT_CODE', '1099'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_OTHER_ACCOUNT_NAME', 'Undeposited Funds'),
        'type': 'ASSET',
    },
    'PAYROLL_EXPENSE': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_PAYROLL_EXPENSE_CODE', '5000'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_PAYROLL_EXPENSE_NAME', 'Payroll Expense'),
        'type': 'EXPENSE',
    },
    'LOAN_FUNDING': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_LOAN_FUNDING_CODE', '1010'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_LOAN_FUNDING_NAME', 'Bank Account'),
        'type': 'ASSET',
    },
    'REVENUE': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_REVENUE_ACCOUNT_CODE', '4000'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_REVENUE_ACCOUNT_NAME', 'Sales Revenue'),
        'type': 'INCOME',
    },
    'OPERATING_EXPENSE': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_EXPENSE_ACCOUNT_CODE', '6000'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_EXPENSE_ACCOUNT_NAME', 'Operating Expense'),
        'type': 'EXPENSE',
    },
    'INVENTORY_ASSET': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_INVENTORY_ACCOUNT_CODE', '1200'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_INVENTORY_ACCOUNT_NAME', 'Inventory'),
        'type': 'ASSET',
    },
    'LOSS_EXPENSE': {
        'code': getattr(settings, 'ACCOUNTING_DEFAULT_LOSS_ACCOUNT_CODE', '6100'),
        'name': getattr(settings, 'ACCOUNTING_DEFAULT_LOSS_ACCOUNT_NAME', 'Inventory Loss'),
        'type': 'EXPENSE',
    },
    'ANALYSIS_PROFIT': {
        'code': getattr(settings, 'ACCOUNTING_ANALYSIS_PROFIT_CODE', '4900'),
        'name': getattr(settings, 'ACCOUNTING_ANALYSIS_PROFIT_NAME', 'Product Profit (Analysis)'),
        'type': 'INCOME',
    },
    'ANALYSIS_LOSS': {
        'code': getattr(settings, 'ACCOUNTING_ANALYSIS_LOSS_CODE', '6900'),
        'name': getattr(settings, 'ACCOUNTING_ANALYSIS_LOSS_NAME', 'Product Loss (Analysis)'),
        'type': 'EXPENSE',
    },
    'ANALYSIS_CLEARING': {
        'code': getattr(settings, 'ACCOUNTING_ANALYSIS_CLEARING_CODE', '3999'),
        'name': getattr(settings, 'ACCOUNTING_ANALYSIS_CLEARING_NAME', 'Analysis Clearing'),
        'type': 'EQUITY',
    },
}


class AccountingError(Exception):
    pass


def get_or_create_system_account(code, name, account_type):
    account = ChartOfAccount.objects.filter(account_code=code).first()
    if account:
        return account

    account_by_name = ChartOfAccount.objects.filter(account_name__iexact=name).first()
    if account_by_name:
        return account_by_name

    account = ChartOfAccount.objects.create(
        account_code=code,
        account_name=name,
        account_type=account_type,
        opening_balance=Decimal('0.00'),
        is_active=True,
    )
    return account


def get_payment_account(payment_method):
    method = payment_method or 'OTHER'
    config = DEFAULT_ACCOUNT_CONFIG.get(method, DEFAULT_ACCOUNT_CONFIG['OTHER'])
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_payroll_expense_account():
    config = DEFAULT_ACCOUNT_CONFIG['PAYROLL_EXPENSE']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_loan_funding_account():
    config = DEFAULT_ACCOUNT_CONFIG['LOAN_FUNDING']
    return get_or_create_system_account(config['code'], config['name'], config['type'])

def get_default_revenue_account():
    config = DEFAULT_ACCOUNT_CONFIG['REVENUE']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_default_expense_account():
    config = DEFAULT_ACCOUNT_CONFIG['OPERATING_EXPENSE']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_inventory_account():
    config = DEFAULT_ACCOUNT_CONFIG['INVENTORY_ASSET']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_loss_expense_account():
    config = DEFAULT_ACCOUNT_CONFIG['LOSS_EXPENSE']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_analysis_profit_account():
    config = DEFAULT_ACCOUNT_CONFIG['ANALYSIS_PROFIT']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_analysis_loss_account():
    config = DEFAULT_ACCOUNT_CONFIG['ANALYSIS_LOSS']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def get_analysis_clearing_account():
    config = DEFAULT_ACCOUNT_CONFIG['ANALYSIS_CLEARING']
    return get_or_create_system_account(config['code'], config['name'], config['type'])


def normalize_payment_method(raw_value):
    if raw_value is None:
        return 'OTHER'
    text = str(raw_value).strip().lower()
    if not text:
        return 'OTHER'
    if 'cash' in text:
        return 'CASH'
    if 'mpesa' in text or 'm-pesa' in text or 'mobile' in text:
        return 'MOBILE'
    if 'bank' in text or 'transfer' in text:
        return 'BANK'
    if 'card' in text or 'visa' in text or 'master' in text:
        return 'CARD'
    return 'OTHER'


@transaction.atomic
def create_income_from_sale(sale, user=None):
    if sale.total_amount <= 0:
        return None

    if IncomeRegister.objects.filter(receipt_no=sale.sale_number).exists():
        return None

    entry = IncomeRegister.objects.create(
        date=sale.created_at.date() if sale.created_at else timezone.now().date(),
        receipt_no=sale.sale_number,
        source=sale.customer_name or f"Sale {sale.sale_number}",
        account_credited=get_default_revenue_account(),
        amount=sale.total_amount,
        payment_method=normalize_payment_method(sale.payment_method),
        reference=sale.sale_number,
    )
    return post_income_register(entry, user=user, branch=sale.branch)


@transaction.atomic
def create_expense_from_core(expense, user=None):
    if expense.amount <= 0:
        return None

    if ExpenseRegister.objects.filter(voucher_no=expense.expense_number).exists():
        return None

    entry = ExpenseRegister.objects.create(
        date=expense.expense_date,
        voucher_no=expense.expense_number,
        category=expense.expense_type,
        account_debited=get_default_expense_account(),
        amount=expense.amount,
        payment_method='OTHER',
        reference=expense.receipt_number or expense.expense_number,
        approved=True,
    )
    return post_expense_register(entry, user=user, branch=expense.branch)


@transaction.atomic
def create_logistics_from_core(logistics, user=None):
    if not logistics.delivery_cost or logistics.delivery_cost <= 0:
        return None

    if LedgerTransaction.objects.filter(source_type='LOGISTICS', source_id=logistics.id).exists():
        return None

    expense_account = get_default_expense_account()
    payment_account = get_payment_account('OTHER')

    vehicle = logistics.vehicle
    if vehicle is None and getattr(logistics, 'vehicle_number', ''):
        vehicle = Vehicle.objects.filter(
            registration_number__iexact=logistics.vehicle_number.strip()
        ).first()

    txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('LOG'),
        transaction_date=logistics.delivery_date or logistics.created_at.date(),
        description=f"Logistics {logistics.tracking_number}",
        reference=logistics.tracking_number,
        source_type='LOGISTICS',
        source_id=logistics.id,
        branch=logistics.from_branch,
        vehicle=vehicle,
        created_by=user,
    )

    GeneralLedger.objects.create(
        transaction=txn,
        account=expense_account,
        debit_amount=logistics.delivery_cost,
        credit_amount=Decimal('0.00'),
    )
    GeneralLedger.objects.create(
        transaction=txn,
        account=payment_account,
        debit_amount=Decimal('0.00'),
        credit_amount=logistics.delivery_cost,
    )

    return txn

def ensure_open_period(date_value):
    closed_period = AccountingPeriod.objects.filter(
        is_closed=True,
        start_date__lte=date_value,
        end_date__gte=date_value,
    ).first()
    if closed_period:
        raise AccountingError("This period is closed. No edits or postings allowed.")


def generate_transaction_id(prefix='GL'):
    return f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{timezone.now().strftime('%H%M%S%f')}"


@transaction.atomic
def post_income_register(entry: IncomeRegister, user=None, branch=None, vehicle=None):
    if entry.posted:
        raise AccountingError("Income register entry already posted.")
    ensure_open_period(entry.date)

    debit_account = get_payment_account(entry.payment_method)
    credit_account = entry.account_credited

    if not credit_account.is_active:
        raise AccountingError("Credited account is inactive.")

    txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('INC'),
        transaction_date=entry.date,
        description=entry.source,
        reference=entry.reference or entry.receipt_no,
        source_type='INCOME_REGISTER',
        source_id=entry.id,
        branch=branch,
        vehicle=vehicle,
        created_by=user,
    )

    GeneralLedger.objects.create(
        transaction=txn,
        account=debit_account,
        debit_amount=entry.amount,
        credit_amount=Decimal('0.00'),
    )
    GeneralLedger.objects.create(
        transaction=txn,
        account=credit_account,
        debit_amount=Decimal('0.00'),
        credit_amount=entry.amount,
    )

    entry.posted = True
    entry.posted_at = timezone.now()
    entry.posted_by = user
    entry.ledger_transaction = txn
    entry.save(update_fields=['posted', 'posted_at', 'posted_by', 'ledger_transaction'])
    return txn


@transaction.atomic
def post_expense_register(entry: ExpenseRegister, user=None, branch=None, vehicle=None):
    if entry.posted:
        raise AccountingError("Expense register entry already posted.")
    if not entry.approved:
        raise AccountingError("Expense must be approved before posting.")
    ensure_open_period(entry.date)

    debit_account = entry.account_debited
    credit_account = get_payment_account(entry.payment_method)

    if not debit_account.is_active:
        raise AccountingError("Debited account is inactive.")

    txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('EXP'),
        transaction_date=entry.date,
        description=entry.category,
        reference=entry.reference or entry.voucher_no,
        source_type='EXPENSE_REGISTER',
        source_id=entry.id,
        branch=branch,
        vehicle=vehicle,
        created_by=user,
    )

    GeneralLedger.objects.create(
        transaction=txn,
        account=debit_account,
        debit_amount=entry.amount,
        credit_amount=Decimal('0.00'),
    )
    GeneralLedger.objects.create(
        transaction=txn,
        account=credit_account,
        debit_amount=Decimal('0.00'),
        credit_amount=entry.amount,
    )

    entry.posted = True
    entry.posted_at = timezone.now()
    entry.posted_by = user
    entry.ledger_transaction = txn
    entry.save(update_fields=['posted', 'posted_at', 'posted_by', 'ledger_transaction'])
    return txn


@transaction.atomic
def post_loan_register(entry: LoansRegister, user=None, branch=None, vehicle=None):
    if entry.posted:
        raise AccountingError("Loan register entry already posted.")
    ensure_open_period(entry.due_date)

    funding_account = get_loan_funding_account()
    liability_account = entry.account

    if not liability_account.is_active:
        raise AccountingError("Loan account is inactive.")

    txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('LOAN'),
        transaction_date=entry.due_date,
        description=f"Loan from {entry.lender}",
        reference=entry.loan_id,
        source_type='LOANS_REGISTER',
        source_id=entry.id,
        branch=branch,
        vehicle=vehicle,
        created_by=user,
    )

    GeneralLedger.objects.create(
        transaction=txn,
        account=funding_account,
        debit_amount=entry.principal,
        credit_amount=Decimal('0.00'),
    )
    GeneralLedger.objects.create(
        transaction=txn,
        account=liability_account,
        debit_amount=Decimal('0.00'),
        credit_amount=entry.principal,
    )

    entry.posted = True
    entry.posted_at = timezone.now()
    entry.posted_by = user
    entry.ledger_transaction = txn
    entry.save(update_fields=['posted', 'posted_at', 'posted_by', 'ledger_transaction'])
    return txn


@transaction.atomic
def post_payroll_entry(entry: PayrollLedger, user=None, branch=None, vehicle=None):
    if entry.posted:
        raise AccountingError("Payroll entry already posted.")
    ensure_open_period(entry.payment_date)

    payroll_expense_account = get_payroll_expense_account()
    funding_account = get_loan_funding_account()

    amount = entry.net_pay

    txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('PAY'),
        transaction_date=entry.payment_date,
        description=f"Payroll for {entry.employee_name} ({entry.pay_period})",
        reference=entry.reference,
        source_type='PAYROLL_LEDGER',
        source_id=entry.id,
        branch=branch,
        vehicle=vehicle,
        created_by=user,
    )

    GeneralLedger.objects.create(
        transaction=txn,
        account=payroll_expense_account,
        debit_amount=amount,
        credit_amount=Decimal('0.00'),
    )
    GeneralLedger.objects.create(
        transaction=txn,
        account=funding_account,
        debit_amount=Decimal('0.00'),
        credit_amount=amount,
    )

    entry.posted = True
    entry.posted_at = timezone.now()
    entry.posted_by = user
    entry.ledger_transaction = txn
    entry.save(update_fields=['posted', 'posted_at', 'posted_by', 'ledger_transaction'])
    return txn


@transaction.atomic
def post_inventory_loss(broken_product, user=None):
    ensure_open_period(broken_product.reported_date.date())

    loss_account = get_loss_expense_account()
    inventory_account = get_inventory_account()

    if not loss_account.is_active or not inventory_account.is_active:
        raise AccountingError("Loss or inventory account is inactive.")

    txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('LOSS'),
        transaction_date=broken_product.reported_date.date(),
        description=f"Inventory loss: {broken_product.damage_type} - {broken_product.stock.product.name}",
        reference=f"LOSS-{broken_product.id}",
        source_type='BROKEN_PRODUCT',
        source_id=broken_product.id,
        branch=broken_product.stock.branch,
        vehicle=None,
        created_by=user,
    )

    GeneralLedger.objects.create(
        transaction=txn,
        account=loss_account,
        debit_amount=broken_product.total_loss,
        credit_amount=Decimal('0.00'),
    )
    GeneralLedger.objects.create(
        transaction=txn,
        account=inventory_account,
        debit_amount=Decimal('0.00'),
        credit_amount=broken_product.total_loss,
    )

    return txn


@transaction.atomic
def reverse_transaction(transaction: LedgerTransaction, user=None):
    ensure_open_period(transaction.transaction_date)

    reversal_txn = LedgerTransaction.objects.create(
        transaction_id=generate_transaction_id('REV'),
        transaction_date=timezone.now().date(),
        description=f"Reversal of {transaction.transaction_id}",
        reference=transaction.reference,
        source_type='REVERSAL',
        source_id=transaction.id,
        reversal_of=transaction,
        created_by=user,
    )

    for entry in transaction.entries.all():
        GeneralLedger.objects.create(
            transaction=reversal_txn,
            account=entry.account,
            debit_amount=entry.credit_amount,
            credit_amount=entry.debit_amount,
        )

    return reversal_txn


def _month_end(date_value):
    next_month = (date_value.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
    return next_month - timezone.timedelta(days=1)


@transaction.atomic
def sync_product_metrics_ledger(month_start, month_end=None, user=None):
    month_end = month_end or _month_end(month_start)

    sale_items = SaleItem.objects.select_related(
        'stock__product',
        'stock__branch',
        'sale',
    ).filter(
        sale__created_at__date__range=(month_start, month_end)
    )

    restock_movements = StockMovement.objects.select_related(
        'stock__product',
        'stock__branch',
    ).filter(
        movement_type='IN',
        created_at__date__range=(month_start, month_end),
    )

    broken_items = BrokenProduct.objects.select_related(
        'stock__product',
        'stock__branch',
    ).filter(
        reported_date__date__range=(month_start, month_end)
    )

    sales_map = {}
    for item in sale_items:
        branch_id = item.sale.branch_id if item.sale_id else item.stock.branch_id
        key = (branch_id, item.stock.product_id)
        bucket = sales_map.setdefault(key, {'units': 0, 'revenue': Decimal('0.00'), 'cost': Decimal('0.00')})
        bucket['units'] += item.quantity
        bucket['revenue'] += (item.unit_price or Decimal('0.00')) * item.quantity
        item_cost = item.unit_cost_at_sale
        if item_cost is None:
            item_cost = item.stock.weighted_avg_purchase_price or item.stock.product.cost_price or Decimal('0.00')
        bucket['cost'] += (item_cost or Decimal('0.00')) * item.quantity

    restock_map = {}
    for mov in restock_movements:
        key = (mov.stock.branch_id, mov.stock.product_id)
        restock_map[key] = restock_map.get(key, 0) + mov.quantity

    broken_map = {}
    for broken in broken_items:
        key = (broken.stock.branch_id, broken.stock.product_id)
        broken_map[key] = broken_map.get(key, 0) + broken.quantity

    keys = set(sales_map) | set(restock_map) | set(broken_map)
    if not keys:
        return

    stocks = Stock.objects.select_related('product', 'branch').filter(
        branch_id__in=[key[0] for key in keys],
        product_id__in=[key[1] for key in keys],
    )
    stock_map = {(stock.branch_id, stock.product_id): stock for stock in stocks}

    profit_account = get_analysis_profit_account()
    loss_account = get_analysis_loss_account()
    clearing_account = get_analysis_clearing_account()

    for (branch_id, product_id) in keys:
        stock = stock_map.get((branch_id, product_id))
        if not stock:
            continue

        branch = stock.branch
        product = stock.product

        sold_units = sales_map.get((branch_id, product_id), {}).get('units', 0)
        total_revenue = sales_map.get((branch_id, product_id), {}).get('revenue', Decimal('0.00'))
        total_cost = sales_map.get((branch_id, product_id), {}).get('cost', Decimal('0.00'))
        avg_price = (total_revenue / sold_units) if sold_units > 0 else Decimal('0.00')
        avg_cost = (total_cost / sold_units) if sold_units > 0 else Decimal('0.00')
        gross_profit = total_revenue - total_cost

        broken_units = broken_map.get((branch_id, product_id), 0)
        broken_loss = (avg_price * broken_units) if broken_units > 0 else Decimal('0.00')

        restocked_units = restock_map.get((branch_id, product_id), 0)
        closing_stock = stock.quantity or 0
        utilization_rate = (sold_units / (sold_units + closing_stock) * 100) if (sold_units + closing_stock) > 0 else 0

        profit_amount = gross_profit if gross_profit > 0 else Decimal('0.00')
        loss_amount = (abs(gross_profit) if gross_profit < 0 else Decimal('0.00')) + broken_loss

        if profit_amount == 0 and loss_amount == 0:
            continue

        txn_id = f"PRD-{branch_id}-{product_id}-{month_start.strftime('%Y%m')}"
        reference = f"US:{sold_units}|AP:{avg_price:.2f}|RS:{restocked_units}|BR:{broken_units}|UT:{utilization_rate:.1f}%"
        description = (
            f"Product metrics {month_start.strftime('%Y-%m')} - {product.name} @ {branch.name} | "
            f"Units Sold: {sold_units} | Avg Price: {avg_price:.2f} | Unit Cost: {avg_cost:.2f} | "
            f"Restocked: {restocked_units} | Broken Units: {broken_units} | Utilization: {utilization_rate:.1f}%"
        )

        txn = LedgerTransaction.objects.filter(transaction_id=txn_id).first()
        if txn:
            txn.transaction_date = month_end
            txn.description = description
            txn.reference = reference[:100]
            txn.source_type = 'PRODUCT_METRICS'
            txn.source_id = product_id
            txn.branch = branch
            txn.vehicle = None
            txn.created_by = user
            txn.save(update_fields=['transaction_date', 'description', 'reference', 'source_type', 'source_id', 'branch', 'vehicle', 'created_by'])
            txn.entries.all().delete()
        else:
            txn = LedgerTransaction.objects.create(
                transaction_id=txn_id,
                transaction_date=month_end,
                description=description,
                reference=reference[:100],
                source_type='PRODUCT_METRICS',
                source_id=product_id,
                branch=branch,
                vehicle=None,
                created_by=user,
            )

        if profit_amount > 0:
            GeneralLedger.objects.create(
                transaction=txn,
                account=clearing_account,
                debit_amount=profit_amount,
                credit_amount=Decimal('0.00'),
            )
            GeneralLedger.objects.create(
                transaction=txn,
                account=profit_account,
                debit_amount=Decimal('0.00'),
                credit_amount=profit_amount,
            )

        if loss_amount > 0:
            GeneralLedger.objects.create(
                transaction=txn,
                account=loss_account,
                debit_amount=loss_amount,
                credit_amount=Decimal('0.00'),
            )
            GeneralLedger.objects.create(
                transaction=txn,
                account=clearing_account,
                debit_amount=Decimal('0.00'),
                credit_amount=loss_amount,
            )
