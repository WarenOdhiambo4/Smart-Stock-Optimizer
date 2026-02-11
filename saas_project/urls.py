from django.contrib import admin
from django.urls import path, include

from core.pwa_views import manifest, service_worker
from core.admin_views import admin_user_management, validate_email_ajax

urlpatterns = [
    path('manifest.json', manifest, name='manifest'),
    path('sw.js', service_worker, name='service_worker'),
    path('admin/', admin.site.urls),
    path('admin/users/', admin_user_management, name='admin_user_management'),
    path('admin/validate-email/', validate_email_ajax, name='validate_email_ajax'),
    path('api/v1/', include('core.api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('core.urls')),
]
