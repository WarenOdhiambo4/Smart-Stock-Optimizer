from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import *

class Command(BaseCommand):
    help = 'Delete all data except branches while preserving relationships'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Delete in reverse dependency order to avoid foreign key conflicts
            
            # Level 4 - Most dependent tables
            ShipmentItem.objects.all().delete()
            PaymentCollection.objects.all().delete()
            FuelConsumption.objects.all().delete()
            Maintenance.objects.all().delete()
            PriceChangeLog.objects.all().delete()
            HistoricalProduct.objects.all().delete()
            
            # Level 3 - Dependent on Level 4
            OrderShipment.objects.all().delete()
            OrderFulfillment.objects.all().delete()
            StockBatch.objects.all().delete()
            MonthlyProfitAnalysis.objects.all().delete()
            BrokenProduct.objects.all().delete()
            BusinessNote.objects.all().delete()
            
            # Level 2 - Core business data
            Trip.objects.all().delete()
            Sale.objects.all().delete()
            Order.objects.all().delete()
            Expense.objects.all().delete()
            Stock.objects.all().delete()
            
            # Level 1 - Base entities (keep branches)
            Vehicle.objects.all().delete()
            Employee.objects.all().delete()
            Product.objects.all().delete()
            
            # Keep Branch table intact
            
            self.stdout.write(self.style.SUCCESS('Successfully deleted all data except branches'))
            self.stdout.write(f'Remaining branches: {Branch.objects.count()}')