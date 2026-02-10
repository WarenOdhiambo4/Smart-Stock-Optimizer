from decimal import Decimal
from django.db import transaction
from .models import InventoryLayer


def consume_fifo_layers(stock, quantity):
    qty = Decimal(quantity or 0)
    if qty <= 0:
        return Decimal('0.00'), Decimal('0.00')
    remaining = qty
    total_cost = Decimal('0.00')
    layers = (
        InventoryLayer.objects.select_for_update()
        .filter(stock=stock, remaining_quantity__gt=0)
        .order_by('created_at', 'id')
    )
    for layer in layers:
        if remaining <= 0:
            break
        take = min(layer.remaining_quantity, remaining)
        if take <= 0:
            continue
        total_cost += take * layer.unit_cost
        layer.remaining_quantity -= take
        layer.save(update_fields=['remaining_quantity'])
        remaining -= take

    if remaining > 0:
        fallback = stock.weighted_avg_purchase_price or stock.product.cost_price or Decimal('0.00')
        total_cost += remaining * fallback

    avg_cost = total_cost / qty if qty > 0 else Decimal('0.00')
    return total_cost, avg_cost


def restore_fifo_layers(stock, quantity, unit_cost, source_type='ADJUSTMENT', source_id=None):
    qty = Decimal(quantity or 0)
    if qty <= 0:
        return None
    cost = Decimal(unit_cost or 0)
    return InventoryLayer.objects.create(
        stock=stock,
        quantity=qty,
        remaining_quantity=qty,
        unit_cost=cost,
        source_type=source_type,
        source_id=source_id,
    )
