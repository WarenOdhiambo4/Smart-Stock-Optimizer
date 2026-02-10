from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_add_system_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saleitem',
            name='quantity',
            field=models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='saleitem',
            name='is_broken_sale',
            field=models.BooleanField(default=False),
        ),
    ]
