from django.core.management.base import BaseCommand

from core.fulfillment_services import (
    get_or_create_fulfillment,
    create_shipment_from_logistics,
    create_payment_from_sale,
)
from core.models import Order, Logistics, Sale


class Command(BaseCommand):
    help = "Backfill order fulfillments, shipments, and payment collections from existing data."

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Apply changes to the database. Without this flag, runs in dry-run mode.'
        )

    def handle(self, *args, **options):
        commit = options.get('commit', False)

        missing_fulfillments = 0
        created_fulfillments = 0
        missing_shipments = 0
        created_shipments = 0
        missing_payments = 0
        created_payments = 0

        for order in Order.objects.all().order_by('created_at'):
            exists = order.fulfillments.exists()
            if not exists:
                missing_fulfillments += 1
                if commit:
                    get_or_create_fulfillment(order, user=order.created_by)
                    created_fulfillments += 1

        for logistics in Logistics.objects.select_related('sale', 'sale__order').order_by('created_at'):
            if not logistics.sale or not logistics.sale.order:
                continue
            shipment_number = f"SHP-{logistics.tracking_number}"
            if not logistics.sale.order.fulfillments.exists():
                missing_shipments += 1
                if commit:
                    create_shipment_from_logistics(logistics, user=logistics.created_by)
                    created_shipments += 1
                continue
            if not logistics.sale.order.fulfillments.filter(shipments__shipment_number=shipment_number).exists():
                missing_shipments += 1
                if commit:
                    create_shipment_from_logistics(logistics, user=logistics.created_by)
                    created_shipments += 1

        for sale in Sale.objects.select_related('order').order_by('created_at'):
            if not sale.order:
                continue
            payment_number = f"PAY-{sale.sale_number}"
            if not sale.order.fulfillments.filter(payments__payment_number=payment_number).exists():
                missing_payments += 1
                if commit:
                    create_payment_from_sale(sale, user=sale.created_by)
                    created_payments += 1

        if commit:
            self.stdout.write(self.style.SUCCESS(
                "Backfill complete. "
                f"Fulfillments created: {created_fulfillments}, "
                f"Shipments created: {created_shipments}, "
                f"Payments created: {created_payments}."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "Dry run only. Use --commit to apply changes. "
                f"Missing fulfillments: {missing_fulfillments}, "
                f"missing shipments: {missing_shipments}, "
                f"missing payments: {missing_payments}."
            ))
