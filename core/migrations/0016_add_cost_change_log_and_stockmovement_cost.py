from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_add_unit_cost_at_sale'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockmovement',
            name='unit_cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='source_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='source_type',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.CreateModel(
            name='CostChangeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('new_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.TextField(blank=True)),
                ('change_date', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cost_changes', to='core.product')),
            ],
            options={
                'ordering': ['-change_date'],
            },
        ),
    ]
