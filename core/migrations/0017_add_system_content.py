from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_cost_change_log_and_stockmovement_cost'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200, unique=True)),
                ('value', models.TextField()),
                ('module', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['key'],
            },
        ),
    ]
