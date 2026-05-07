"""
URL routing for the accounts application.

Maps the AuthViewSet actions to specific endpoints using the REST Framework router.
The base path is 'auth/', providing routes for login, logout, and profile management.
"""
from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet

# Initialize the router and register the AuthViewSet
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]