from django.urls import path
from . import views_analytics

urlpatterns = [
    path('', views_analytics.modern_analytics_dashboard, name='modern_analytics_dashboard'),
    path('api/', views_analytics.analytics_api, name='analytics_api'),
    path('export/excel/', views_analytics.export_analytics_excel, name='export_analytics_excel'),
]