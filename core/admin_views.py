"""
Admin views for user management (Django-only, no Airtable dependency)
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from email_validator import validate_email, EmailNotValidError
import json
import secrets
import string

from .models import UserProfile, Branch


def validate_email_exists(email):
    """Validate email exists using DNS lookup"""
    try:
        valid = validate_email(email, check_deliverability=True)
        return True, valid.email
    except EmailNotValidError as e:
        return False, str(e)


def generate_password(length=12):
    """Generate secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def build_unique_username(email):
    base = email.split('@')[0]
    username = base
    if User.objects.filter(username=username).exists():
        username = f"{base}_{secrets.randbelow(1000)}"
    return username


def create_user_in_django(email, first_name, last_name, role, branch_id=None):
    """Create Django user and profile with validated email"""
    is_valid, result = validate_email_exists(email)
    if not is_valid:
        raise ValidationError(f"Invalid email: {result}")

    password = generate_password()
    username = build_unique_username(result)

    user = User.objects.create_user(
        username=username,
        email=result,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            branch = None

    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            'role': role,
            'branch': branch
        }
    )

    return user, password


@staff_member_required
def admin_user_management(request):
    """Admin page for user management"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role')
            branch_id = request.POST.get('branch_id') or None

            user, password = create_user_in_django(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                branch_id=branch_id
            )

            messages.success(
                request,
                f"User created successfully! Username: {user.username}, "
                f"Password: {password} (Save this password!)"
            )
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")

    users = User.objects.all().order_by('username')
    user_rows = []
    for user in users:
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = None
        user_rows.append({
            'user': user,
            'role': profile.role if profile else '',
            'branch': profile.branch.name if profile and profile.branch else '',
            'is_active': user.is_active,
        })
    branches = Branch.objects.filter(is_active=True).order_by('name')

    context = {
        'user_rows': user_rows,
        'roles': ['ADMIN', 'BOSS', 'MANAGER', 'FINANCE', 'SALES', 'LOGISTICS'],
        'branches': branches,
    }

    return render(request, 'admin/user_management.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def validate_email_ajax(request):
    """AJAX endpoint to validate email"""
    try:
        data = json.loads(request.body)
        email = data.get('email')

        is_valid, result = validate_email_exists(email)

        return JsonResponse({
            'valid': is_valid,
            'message': result if not is_valid else 'Email is valid',
            'email': result if is_valid else email
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'message': str(e),
            'email': None
        })
