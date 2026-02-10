"""
Django management command to create admin user
"""
from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Create admin user for production deployment'

    def handle(self, *args, **options):
        try:
            # Create admin user if doesn't exist
            if not User.objects.filter(username='admin').exists():
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='odhiambowaren89@gmail.com',
                    password='0790018750..'
                )

                # Create user profile
                UserProfile.objects.create(
                    user=admin_user,
                    role='ADMIN'
                )

                self.stdout.write(
                    self.style.SUCCESS('Admin user created successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Admin user already exists')
                )
        except (OperationalError, ProgrammingError) as exc:
            self.stdout.write(
                self.style.WARNING(f'Create admin skipped (database not ready): {exc}')
            )
