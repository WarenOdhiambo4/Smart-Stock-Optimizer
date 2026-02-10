from decimal import Decimal
from django.db import migrations, models


def backfill_unit_cost_at_sale(apps, schema_editor):
    SaleItem = apps.get_model('core', 'SaleItem')
    HistoricalProduct = apps.get_model('core', 'HistoricalProduct')

    qs = SaleItem.objects.select_related('sale', 'stock__product').filter(unit_cost_at_sale__isnull=True)
    for item in qs.iterator():
        cost = None
        sale_date = None
        if item.sale_id and item.sale and item.sale.created_at:
            sale_date = item.sale.created_at
        if sale_date:
            hist = HistoricalProduct.objects.filter(id=item.stock.product_id, history_date__lte=sale_date).order_by('-history_date').first()
            if hist and getattr(hist, 'cost_price', None) is not None:
                cost = hist.cost_price
        if cost is None:
            cost = item.stock.weighted_avg_purchase_price or item.stock.product.cost_price or Decimal('0.00')
        item.unit_cost_at_sale = cost
        item.save(update_fields=['unit_cost_at_sale'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_historicalledgertransaction_branch_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleitem',
            name='unit_cost_at_sale',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.RunPython(backfill_unit_cost_at_sale, migrations.RunPython.noop),
    ]
