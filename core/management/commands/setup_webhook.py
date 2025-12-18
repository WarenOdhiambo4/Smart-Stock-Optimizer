from django.core.management.base import BaseCommand
from core.webhook_manager import AirtableWebhookManager
import os

class Command(BaseCommand):
    help = 'Register Airtable webhook for real-time sync'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='Webhook notification URL (your Django server endpoint)',
            default='https://kabisa-enterprise-ltd.onrender.com/webhook/'
        )

    def handle(self, *args, **options):
        manager = AirtableWebhookManager()
        notify_url = options['url']
        
        self.stdout.write(f'Registering webhook with URL: {notify_url}')
        
        try:
            result = manager.register_webhook(notify_url)
            
            if 'id' in result:
                webhook_id = result['id']
                self.stdout.write(
                    self.style.SUCCESS(f'Webhook registered successfully! ID: {webhook_id}')
                )
                self.stdout.write(f'Save this webhook ID: {webhook_id}')
                
                # Save webhook ID to environment or settings
                with open('.env', 'a') as f:
                    f.write(f'\nAIRTABLE_WEBHOOK_ID={webhook_id}\n')
                    
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to register webhook: {result}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error registering webhook: {str(e)}')
            )