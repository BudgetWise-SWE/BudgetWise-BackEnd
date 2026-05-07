"""
Admin configuration for the accounts application.

Customizes the Django Admin interface for the User model, ensuring that
email is the primary display and search field.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    """
    Customizes the user administration panel.
    
    Attributes:
        ordering (tuple): Default sort order for users (by email).
    """
    ordering = ('email',)

# Register the User model with the customized admin class
admin.site.register(User, CustomUserAdmin)