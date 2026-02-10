from datetime import datetime, time
from decimal import Decimal

from django.utils import timezone

from .models import (
    OrderFulfillment,
    OrderShipment,
    ShipmentItem,
    PaymentCollection,
    Vehicle,
)


def _coerce_datetime(value):
    if isinstance(value, datetime):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    if value:
        return timezone.make_aware(datetime.combine(value, time(hour=9)))
    return timezone.now()


def _safe_decimal(value, default=Decimal('0.00')):
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError):
        return default


def _map_payment_method(raw_value):
    text = (raw_value or '').strip().lower()
    if 'cash' in text:
        return 'CASH'
    if 'bank' in text or 'transfer' in text:
        return 'BANK_TRANSFER'
    if 'mpesa' in text or 'm-pesa' in text or 'mobile' in text:
        return 'MOBILE_MONEY'
    if 'cheque' in text:
        return 'CHEQUE'
    if 'card' in text or 'visa' in text or 'master' in text:
        return 'CARD'
    return 'OTHER'


def _map_shipment_status(raw_status):
    status = (raw_status or '').upper()
    if status == 'DELIVERED':
        return 'DELIVERED'
    if status == 'IN_TRANSIT':
        return 'IN_TRANSIT'
    if status == 'PROCESSING':
        return 'LOADING'
    if status == 'CANCELLED':
        return 'CANCELLED'
    return 'SCHEDULED'


def _resolve_vehicle(logistics):
    if logistics.vehicle:
        return logistics.vehicle
    if logistics.vehicle_number:
        return Vehicle.objects.filter(
            registration_number__iexact=logistics.vehicle_number.strip()
        ).first()
    return None


def _order_item_quantity(item):
    quantity_ordered = _safe_decimal(getattr(item, 'quantity_ordered', 0))
    return quantity_ordered if quantity_ordered > 0 else _safe_decimal(getattr(item, 'quantity', 0))


def get_or_create_fulfillment(order, user=None):
    fulfillment = OrderFulfillment.objects.filter(order=order).first()
    if fulfillment:
        return fulfillment

    total_items = sum(_order_item_quantity(item) for item in order.items.all())
    total_value = order.total_amount or Decimal('0.00')
    fulfillment_number = f"FUL-{order.order_number}"
    if len(fulfillment_number) > 50:
        fulfillment_number = f"FUL-{order.id}"

    return OrderFulfillment.objects.create(
        fulfillment_number=fulfillment_number,
        order=order,
        branch=order.branch,
        total_items_ordered=total_items,
        total_items_fulfilled=0,
        total_items_remaining=total_items,
        total_order_value=total_value,
        total_collected=Decimal('0.00'),
        total_remaining=total_value,
        created_by=user,
    )


def refresh_fulfillment_totals(fulfillment):
    fulfillment.total_order_value = fulfillment.order.total_amount or Decimal('0.00')
    fulfillment.calculate_fulfillment_status()
    return fulfillment


def create_shipment_from_logistics(logistics, user=None):
    if not logistics.sale or not logistics.sale.order:
        return None

    order = logistics.sale.order
    fulfillment = get_or_create_fulfillment(order, user=user)

    shipment_number = f"SHP-{logistics.tracking_number}"
    if len(shipment_number) > 50:
        shipment_number = f"SHP-{logistics.id}"

    existing = OrderShipment.objects.filter(shipment_number=shipment_number).first()
    if existing:
        return existing

    shipment_status = _map_shipment_status(logistics.status)
    scheduled_date = _coerce_datetime(logistics.delivery_date or logistics.created_at)
    vehicle = _resolve_vehicle(logistics)

    shipment = OrderShipment.objects.create(
        shipment_number=shipment_number,
        fulfillment=fulfillment,
        vehicle=vehicle,
        driver=logistics.driver,
        vehicle_capacity=0,
        items_loaded=0,
        status=shipment_status,
        scheduled_date=scheduled_date,
        actual_delivery_date=scheduled_date if shipment_status == 'DELIVERED' else None,
        delivery_address=logistics.to_address,
        customer_name=logistics.customer_name,
        customer_phone=logistics.customer_phone,
        delivery_fee=logistics.delivery_cost or Decimal('0.00'),
        notes=logistics.notes,
        created_by=user,
    )

    for item in order.items.all():
        qty_ordered = _order_item_quantity(item)
        qty_completed = _safe_decimal(getattr(item, 'quantity_completed', 0))

        if shipment_status == 'DELIVERED':
            if qty_completed > 0:
                qty_delivered = min(qty_completed, qty_ordered)
            elif order.status == 'COMPLETED':
                qty_delivered = qty_ordered
            else:
                qty_delivered = 0
        elif shipment_status == 'PARTIALLY_DELIVERED':
            qty_delivered = min(qty_completed, qty_ordered)
        else:
            qty_delivered = 0

        qty_remaining = max(qty_ordered - qty_delivered, Decimal('0.00'))

        ShipmentItem.objects.create(
            shipment=shipment,
            order_item=item,
            quantity_ordered=qty_ordered,
            quantity_delivered=qty_delivered,
            quantity_remaining=qty_remaining,
            unit_price=item.unit_price,
        )

    shipment.calculate_items_loaded()
    refresh_fulfillment_totals(fulfillment)
    return shipment


def create_payment_from_sale(sale, user=None):
    if not sale.order:
        return None
    if sale.total_amount <= 0:
        return None

    fulfillment = get_or_create_fulfillment(sale.order, user=user)

    payment_number = f"PAY-{sale.sale_number}"
    if len(payment_number) > 50:
        payment_number = f"PAY-{sale.id}"

    existing = PaymentCollection.objects.filter(payment_number=payment_number).first()
    if existing:
        return existing

    payment = PaymentCollection.objects.create(
        payment_number=payment_number,
        fulfillment=fulfillment,
        branch=sale.branch,
        amount_collected=sale.total_amount,
        payment_method=_map_payment_method(sale.payment_method),
        status='COMPLETED',
        payment_date=_coerce_datetime(sale.created_at),
        deposited_to_branch=sale.branch,
        is_deposited=False,
        reference_number=sale.sale_number,
        receipt_number=sale.sale_number,
        collected_by=user,
    )

    refresh_fulfillment_totals(fulfillment)
    return payment
