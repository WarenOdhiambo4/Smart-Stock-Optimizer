from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Create missing user profiles'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        
        for user in users_without_profiles:
            UserProfile.objects.create(
                user=user,
                role='ADMIN' if user.is_superuser else 'SALES'
            )
            self.stdout.write(f'Created profile for {user.username}')
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {users_without_profiles.count()} user profiles'))