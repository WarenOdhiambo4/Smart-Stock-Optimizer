"""
Django management command to create admin user.
Credentials are read from environment variables.
"""
import os
from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Create admin user for production deployment'

    def handle(self, *args, **options):
        try:
            username = os.getenv('ADMIN_USERNAME')
            email = os.getenv('ADMIN_EMAIL')
            password = os.getenv('ADMIN_PASSWORD')

            if not username or not email or not password:
                self.stdout.write(
                    self.style.WARNING('Admin credentials not provided. Set ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD.')
                )
                return

            # Create admin user if doesn't exist
            if not User.objects.filter(username=username).exists():
                admin_user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
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
