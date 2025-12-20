from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix migration conflicts by marking problematic migrations as applied'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Mark specific migrations as applied without running them
            migrations_to_fake = [
                ('core', '0002_add_airtable_fields'),
                ('core', '0003_stock_weighted_avg_purchase_price_brokenproduct_and_more'),
            ]
            
            for app, migration in migrations_to_fake:
                cursor.execute(
                    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW()) ON CONFLICT DO NOTHING",
                    [app, migration]
                )
                self.stdout.write(f"Marked {app}.{migration} as applied")
        
        self.stdout.write(self.style.SUCCESS('Migration conflicts resolved'))