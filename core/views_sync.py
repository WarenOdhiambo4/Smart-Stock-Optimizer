"""
Views for manual sync operations
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from io import StringIO

@staff_member_required
def sync_from_airtable_view(request):
    """Manual sync from Airtable"""
    try:
        out = StringIO()
        call_command('sync_from_airtable', stdout=out)
        messages.success(request, f"Sync completed: {out.getvalue()}")
    except Exception as e:
        messages.error(request, f"Sync failed: {e}")
    
    return redirect('dashboard')

@staff_member_required
def sync_to_airtable_view(request):
    """Manual sync to Airtable"""
    try:
        out = StringIO()
        call_command('sync_airtable', '--direction', 'to_airtable', stdout=out)
        messages.success(request, f"Sync completed: {out.getvalue()}")
    except Exception as e:
        messages.error(request, f"Sync failed: {e}")
    
    return redirect('dashboard')