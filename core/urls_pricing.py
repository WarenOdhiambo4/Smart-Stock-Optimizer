from django.urls import path
from . import views_pricing

urlpatterns = [
    path('', views_pricing.price_management_dashboard, name='price_management_dashboard'),
    path('change/', views_pricing.change_product_price, name='change_product_price'),
    path('bulk-update/', views_pricing.bulk_price_update, name='bulk_price_update'),
    path('products/<int:product_id>/elasticity/', views_pricing.price_elasticity_analysis, name='price_elasticity_analysis'),
    path('products/<int:product_id>/history/', views_pricing.product_price_history, name='product_price_history'),
    path('products/<int:product_id>/optimize/', views_pricing.pricing_optimization, name='pricing_optimization'),
]