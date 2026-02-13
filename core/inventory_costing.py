from decimal import Decimal
from django.db import transaction, connection
from .models import InventoryLayer


def consume_fifo_layers(stock, quantity):
    qty = Decimal(quantity or 0)
    if qty <= 0:
        return Decimal('0.00'), Decimal('0.00')
    remaining = qty
    total_cost = Decimal('0.00')
    base_qs = (
        InventoryLayer.objects
        .filter(stock=stock, remaining_quantity__gt=0)
        .order_by('created_at', 'id')
        .only('id', 'remaining_quantity', 'unit_cost')
    )
    if connection.vendor == 'postgresql':
        layers = base_qs.select_for_update(skip_locked=True)
    else:
        layers = base_qs

    full_layer_ids = []
    partial_layer = None

    for layer in layers.iterator(chunk_size=500):
        if remaining <= 0:
            break
        available = layer.remaining_quantity
        if available <= 0:
            continue
        if available <= remaining:
            total_cost += available * layer.unit_cost
            full_layer_ids.append(layer.id)
            remaining -= available
        else:
            total_cost += remaining * layer.unit_cost
            partial_layer = (layer.id, available - remaining)
            remaining = Decimal('0.00')
            break

    if full_layer_ids:
        InventoryLayer.objects.filter(id__in=full_layer_ids).update(remaining_quantity=Decimal('0.00'))
    if partial_layer:
        InventoryLayer.objects.filter(id=partial_layer[0]).update(remaining_quantity=partial_layer[1])

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
