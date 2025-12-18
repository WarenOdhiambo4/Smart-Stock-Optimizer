from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_merge_20251218_1942'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
    ]