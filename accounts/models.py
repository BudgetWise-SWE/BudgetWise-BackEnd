"""
Models for the accounts application.

This module defines the custom user model and its associated manager.
The system uses email as the primary identifier for authentication.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager for the User model where email is the unique identifier.
    
    Provides methods to create regular users and superusers using email
    instead of a username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        
        Args:
            email (str): The unique email address of the user.
            password (str, optional): The raw password for the user.
            **extra_fields: Additional fields to be saved in the User model.
            
        Returns:
            User: The newly created user instance.
            
        Raises:
            ValueError: If the email field is not provided.
        """
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with elevated permissions.
        
        Args:
            email (str): The unique email address of the superuser.
            password (str, optional): The raw password for the superuser.
            **extra_fields: Additional fields to be saved in the User model.
            
        Returns:
            User: The newly created superuser instance.
            
        Raises:
            ValueError: If is_staff or is_superuser is not set to True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model that uses email as the unique identifier.
    
    Attributes:
        email (EmailField): The unique email of the user (primary identifier).
        first_name (CharField): The user's first name.
        last_name (CharField): The user's last name.
        currency (CharField): The preferred currency code (e.g., 'EGP', 'USD').
        status (CharField): Current user status (e.g., 'Onboarding', 'Active').
        language (CharField): Preferred interface language.
        is_superuser (BooleanField): Designates that this user has all permissions.
        is_staff (BooleanField): Designates whether the user can log into this admin site.
        is_active (BooleanField): Designates whether this user should be treated as active.
    """

    username = None
    email = models.EmailField(unique=True, max_length=100)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)

    currency = models.CharField(max_length=5, default='EGP', blank=True)
    status = models.CharField(max_length=20, default='Onboarding')
    language = models.CharField(max_length=20, default='English')

    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        """Return the string representation of the user (their email)."""
        return self.email

    class Meta:
        """Metadata options for the User model."""
        ordering = ['email']