"""
URL routing for the notifications application.

Registers the NotificationViewSet to handle user alerts and their read status.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

# Initialize the router and register the notifications endpoint
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]