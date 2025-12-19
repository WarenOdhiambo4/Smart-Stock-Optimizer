from django.core.management.base import BaseCommand
from core.models import Branch, Product, Sale, Order, Stock, SaleItem

class Command(BaseCommand):
    help = 'Clear all data from database'

    def handle(self, *args, **options):
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        Order.objects.all().delete()
        Stock.objects.all().delete()
        Product.objects.all().delete()
        Branch.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('All data cleared!'))