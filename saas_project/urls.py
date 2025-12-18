from django.contrib import admin
from django.urls import path, include
from core.admin_views import admin_user_management, validate_email_ajax, sync_users
from core.views_sync import sync_from_airtable_view, sync_to_airtable_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/users/', admin_user_management, name='admin_user_management'),
    path('admin/validate-email/', validate_email_ajax, name='validate_email_ajax'),
    path('admin/sync-users/', sync_users, name='sync_users'),
    path('sync/from-airtable/', sync_from_airtable_view, name='sync_from_airtable'),
    path('sync/to-airtable/', sync_to_airtable_view, name='sync_to_airtable'),
    path('api/v1/', include('core.api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('core.urls')),
]
