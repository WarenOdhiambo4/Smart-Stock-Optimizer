from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    ChartOfAccount, IncomeRegister, ExpenseRegister, LoansRegister, PayrollLedger
)


class Command(BaseCommand):
    help = "Seed minimal accounting data for testing the ledger UI"

    def handle(self, *args, **options):
        accounts = [
            ('1000', 'Cash on Hand', 'ASSET'),
            ('1010', 'Bank Account', 'ASSET'),
            ('2000', 'Loans Payable', 'LIABILITY'),
            ('4000', 'Sales Income', 'INCOME'),
            ('5000', 'Payroll Expense', 'EXPENSE'),
            ('5100', 'Operating Expense', 'EXPENSE'),
        ]

        for code, name, acc_type in accounts:
            ChartOfAccount.objects.get_or_create(
                account_code=code,
                defaults={
                    'account_name': name,
                    'account_type': acc_type,
                    'opening_balance': Decimal('0.00'),
                    'is_active': True,
                }
            )

        sales_account = ChartOfAccount.objects.get(account_code='4000')
        expense_account = ChartOfAccount.objects.get(account_code='5100')
        loan_account = ChartOfAccount.objects.get(account_code='2000')

        today = timezone.now().date()

        IncomeRegister.objects.get_or_create(
            receipt_no='RCPT-001',
            defaults={
                'date': today,
                'source': 'Sample Client',
                'account_credited': sales_account,
                'amount': Decimal('1500.00'),
                'payment_method': 'CASH',
                'reference': 'Seed income',
            }
        )

        ExpenseRegister.objects.get_or_create(
            voucher_no='VCHR-001',
            defaults={
                'date': today,
                'category': 'Office Supplies',
                'account_debited': expense_account,
                'amount': Decimal('250.00'),
                'payment_method': 'CASH',
                'reference': 'Seed expense',
                'approved': True,
            }
        )

        LoansRegister.objects.get_or_create(
            loan_id='LOAN-001',
            defaults={
                'lender': 'Sample Bank',
                'account': loan_account,
                'principal': Decimal('5000.00'),
                'interest_rate': Decimal('6.50'),
                'amount_paid': Decimal('0.00'),
                'due_date': today,
                'status': 'ACTIVE',
            }
        )

        PayrollLedger.objects.get_or_create(
            pay_period='Jan 2026',
            employee_name='Sample Employee',
            defaults={
                'basic_salary': Decimal('1200.00'),
                'allowances': Decimal('100.00'),
                'deductions': Decimal('50.00'),
                'payment_date': today,
                'reference': 'Seed payroll',
            }
        )

        self.stdout.write(self.style.SUCCESS('Accounting seed data created.'))
