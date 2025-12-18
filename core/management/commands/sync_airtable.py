"""
Django management command to sync data with Airtable
"""
from django.core.management.base import BaseCommand
from core.airtable_adapter import sync_all_to_airtable, sync_all_from_airtable

class Command(BaseCommand):
    help = 'Sync data between Django and Airtable'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            choices=['to_airtable', 'from_airtable', 'both'],
            default='both',
            help='Sync direction: to_airtable, from_airtable, or both'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        
        if direction in ['to_airtable', 'both']:
            self.stdout.write('Syncing Django data to Airtable...')
            try:
                sync_all_to_airtable()
                self.stdout.write(
                    self.style.SUCCESS('Successfully synced data to Airtable')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing to Airtable: {e}')
                )
        
        if direction in ['from_airtable', 'both']:
            self.stdout.write('Syncing Airtable data to Django...')
            try:
                sync_all_from_airtable()
                self.stdout.write(
                    self.style.SUCCESS('Successfully synced data from Airtable')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing from Airtable: {e}')
                )