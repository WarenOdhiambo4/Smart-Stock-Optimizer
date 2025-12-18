"""
Admin views for user management
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .admin_airtable import user_manager

@staff_member_required
def admin_user_management(request):
    """Admin page for user management"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role')
            branch_name = request.POST.get('branch_name')
            
            result = user_manager.create_user_in_airtable(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                branch_name=branch_name
            )
            
            messages.success(
                request, 
                f"User created successfully! Username: {result['django_user'].username}, "
                f"Password: {result['password']} (Save this password!)"
            )
            
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
    
    # Get all users from Airtable
    try:
        airtable_users = user_manager.get_all_users()
    except:
        airtable_users = []
    
    context = {
        'airtable_users': airtable_users,
        'roles': ['ADMIN', 'BOSS', 'MANAGER', 'FINANCE', 'SALES', 'LOGISTICS']
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
        
        is_valid, result = user_manager.validate_email_exists(email)
        
        return JsonResponse({
            'valid': is_valid,
            'message': result if not is_valid else 'Email is valid',
            'email': result if is_valid else email
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'message': str(e),
            'email': email
        })

@staff_member_required
def sync_users(request):
    """Sync users from Airtable"""
    try:
        synced_users = user_manager.sync_users_from_airtable()
        messages.success(request, f"Synced {len(synced_users)} users from Airtable")
    except Exception as e:
        messages.error(request, f"Error syncing users: {str(e)}")
    
    return redirect('admin_user_management')