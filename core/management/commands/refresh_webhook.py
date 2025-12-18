from django.core.management.base import BaseCommand
from core.webhook_manager import AirtableWebhookManager
import os

class Command(BaseCommand):
    help = 'Refresh Airtable webhook to prevent expiry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook-id',
            type=str,
            help='Webhook ID to refresh',
            default=os.getenv('AIRTABLE_WEBHOOK_ID')
        )

    def handle(self, *args, **options):
        webhook_id = options['webhook_id']
        
        if not webhook_id:
            self.stdout.write(
                self.style.ERROR('No webhook ID provided. Use --webhook-id or set AIRTABLE_WEBHOOK_ID')
            )
            return
            
        manager = AirtableWebhookManager()
        
        try:
            result = manager.refresh_webhook(webhook_id)
            
            if result.get('expirationTime'):
                self.stdout.write(
                    self.style.SUCCESS(f'Webhook refreshed! New expiry: {result["expirationTime"]}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to refresh webhook: {result}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error refreshing webhook: {str(e)}')
            )