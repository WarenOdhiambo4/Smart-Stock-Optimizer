import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (
    Order,
    OrderItem,
    OrderItemCompletion,
    Sale,
    Logistics,
    Product,
    PriceChangeLog,
    CostChangeLog,
    Stock,
    StockBatch,
)
from .fulfillment_services import (
    get_or_create_fulfillment,
    refresh_fulfillment_totals,
    create_shipment_from_logistics,
    create_payment_from_sale,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def ensure_fulfillment_for_order(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        get_or_create_fulfillment(instance, user=instance.created_by)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Order fulfillment auto-create failed: %s", exc)


@receiver(post_save, sender=OrderItem)
def refresh_fulfillment_on_item_change(sender, instance, **kwargs):
    try:
        fulfillment = get_or_create_fulfillment(instance.order, user=instance.order.created_by)
        refresh_fulfillment_totals(fulfillment)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Order fulfillment refresh failed: %s", exc)


@receiver(post_save, sender=Sale)
def create_payment_for_sale(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        create_payment_from_sale(instance, user=instance.created_by)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Payment collection auto-create failed: %s", exc)


@receiver(post_save, sender=Logistics)
def create_shipment_for_logistics(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        create_shipment_from_logistics(instance, user=instance.created_by)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Shipment auto-create failed: %s", exc)


@receiver(post_save, sender=OrderItemCompletion)
def create_stock_batch_on_completion(sender, instance, created, **kwargs):
    if not created:
        return
    item = instance.order_item
    if not item.product:
        return
    try:
        stock, _ = Stock.objects.get_or_create(
            branch=instance.completion_branch,
            product=item.product,
            defaults={'quantity': 0}
        )
        batch_number = f"BAT-{item.order.order_number}-{instance.id}"
        StockBatch.objects.create(
            stock=stock,
            batch_number=batch_number,
            quantity=instance.quantity_completed,
            unit_purchase_price=item.unit_price,
            order=item.order,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Stock batch auto-create failed: %s", exc)


@receiver(pre_save, sender=Product)
def cache_old_price(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_unit_price = None
        instance._old_cost_price = None
        return
    try:
        instance._old_unit_price = Product.objects.filter(pk=instance.pk).values_list('unit_price', flat=True).first()
        instance._old_cost_price = Product.objects.filter(pk=instance.pk).values_list('cost_price', flat=True).first()
    except Exception:  # pragma: no cover - defensive logging
        instance._old_unit_price = None
        instance._old_cost_price = None


@receiver(post_save, sender=Product)
def log_price_change(sender, instance, created, **kwargs):
    if created:
        return
    old_price = getattr(instance, '_old_unit_price', None)
    if old_price is None:
        return
    if instance.unit_price == old_price:
        return
    try:
        PriceChangeLog.objects.create(
            product=instance,
            old_price=old_price,
            new_price=instance.unit_price,
            changed_by=None,
            reason='Auto log: unit price updated',
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Price change log failed: %s", exc)

    old_cost = getattr(instance, '_old_cost_price', None)
    if old_cost is None:
        return
    if instance.cost_price == old_cost:
        return
    try:
        CostChangeLog.objects.create(
            product=instance,
            old_cost=old_cost,
            new_cost=instance.cost_price,
            changed_by=None,
            reason='Auto log: cost price updated',
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Cost change log failed: %s", exc)
