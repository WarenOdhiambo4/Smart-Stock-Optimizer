# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_safe_order_enhancement'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryLayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('remaining_quantity', models.PositiveIntegerField()),
                ('unit_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('source_type', models.CharField(choices=[('ORDER', 'From Order'), ('MANUAL', 'Manual Stock Addition'), ('TRANSFER', 'Stock Transfer')], max_length=20)),
                ('source_id', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='layers', to='core.stock')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]