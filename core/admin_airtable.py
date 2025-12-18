"""
Admin interface for user management with Airtable integration
"""
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from email_validator import validate_email, EmailNotValidError
from .airtable_service import airtable_service
import secrets
import string

class AirtableUserManager:
    def __init__(self):
        self.users_table = airtable_service.get_table('Users')
    
    def validate_email_exists(self, email):
        """Validate email exists using DNS lookup"""
        try:
            valid = validate_email(email, check_deliverability=True)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)
    
    def generate_password(self, length=12):
        """Generate secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_user_in_airtable(self, email, first_name, last_name, role, branch_name=None):
        """Create user in Airtable and Django"""
        # Validate email
        is_valid, result = self.validate_email_exists(email)
        if not is_valid:
            raise ValidationError(f"Invalid email: {result}")
        
        # Generate password
        password = self.generate_password()
        
        # Create Django user
        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{secrets.randbelow(1000)}"
        
        django_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create in Airtable
        airtable_data = {
            'Email': email,
            'First Name': first_name,
            'Last Name': last_name,
            'Role': role,
            'Branch': branch_name or '',
            'Username': username,
            'Active': True,
            'Django User ID': django_user.id,
            'Created': django_user.date_joined.isoformat()
        }
        
        airtable_record = self.users_table.create(airtable_data)
        
        return {
            'django_user': django_user,
            'airtable_record': airtable_record,
            'password': password,
            'email_valid': True
        }
    
    def get_all_users(self):
        """Get all users from Airtable"""
        return self.users_table.all()
    
    def update_user_status(self, airtable_id, active=True):
        """Update user active status"""
        return self.users_table.update(airtable_id, {'Active': active})
    
    def sync_users_from_airtable(self):
        """Sync users from Airtable to Django"""
        airtable_users = self.get_all_users()
        synced_users = []
        
        for record in airtable_users:
            fields = record['fields']
            email = fields.get('Email')
            
            if not email:
                continue
            
            # Check if Django user exists
            django_user_id = fields.get('Django User ID')
            if django_user_id:
                try:
                    django_user = User.objects.get(id=django_user_id)
                    # Update user info
                    django_user.first_name = fields.get('First Name', '')
                    django_user.last_name = fields.get('Last Name', '')
                    django_user.is_active = fields.get('Active', True)
                    django_user.save()
                    synced_users.append(django_user)
                except User.DoesNotExist:
                    pass
        
        return synced_users

# Global instance
user_manager = AirtableUserManager()