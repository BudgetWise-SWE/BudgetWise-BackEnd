"""
Root URL configuration for the BudgetWise project.

Defines the primary routing table for all applications (accounts, finance,
analytics, planning, notifications) and exposes OpenAPI schema endpoints.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('finance/', include('finance.urls')),
    path('analytics/', include('analytics.urls')),
    path('planning/', include('planning.urls')),
    path('notifications/', include('notifications.urls')),
    # API compatibility routes
    path('api/', include('accounts.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/planning/', include('planning.urls')),
    path('api/notifications/', include('notifications.urls')),
    # OpenAPI paths
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]   