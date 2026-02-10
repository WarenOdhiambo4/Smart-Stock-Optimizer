from django.conf import settings
from django.core.management.base import BaseCommand

from core.finance_services import create_income_from_sale, create_expense_from_core, create_logistics_from_core, AccountingError
from core.models import Sale, Expense, Logistics


class Command(BaseCommand):
    help = "Backfill finance registers and ledger from existing Sales/Expenses."

    def handle(self, *args, **options):
        if not getattr(settings, 'ACCOUNTING_AUTO_POST_FROM_CORE', True):
            self.stdout.write(self.style.WARNING("ACCOUNTING_AUTO_POST_FROM_CORE is disabled; no auto-posting performed."))
            return

        sales_created = 0
        expense_created = 0
        logistics_created = 0

        for sale in Sale.objects.order_by('created_at'):
            try:
                result = create_income_from_sale(sale, user=sale.created_by)
                if result:
                    sales_created += 1
            except AccountingError as exc:
                self.stdout.write(self.style.WARNING(f"Sale {sale.sale_number} skipped: {exc}"))

        for expense in Expense.objects.order_by('expense_date'):
            try:
                result = create_expense_from_core(expense, user=expense.created_by)
                if result:
                    expense_created += 1
            except AccountingError as exc:
                self.stdout.write(self.style.WARNING(f"Expense {expense.expense_number} skipped: {exc}"))

        for record in Logistics.objects.order_by('created_at'):
            try:
                result = create_logistics_from_core(record, user=record.created_by)
                if result:
                    logistics_created += 1
            except AccountingError as exc:
                self.stdout.write(self.style.WARNING(f"Logistics {record.tracking_number} skipped: {exc}"))

        self.stdout.write(self.style.SUCCESS(
            "Backfill complete. "
            f"New income posts: {sales_created}, "
            f"new expense posts: {expense_created}, "
            f"new logistics posts: {logistics_created}."
        ))
