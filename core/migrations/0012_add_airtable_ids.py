
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
    ]
