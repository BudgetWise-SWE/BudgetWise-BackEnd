from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
class UserManager(BaseUserManager):
    """Custom manager for the User model where email is the unique identifier."""
    
    """
    Custom manager for the User model where email is the unique identifier.
    """

    def create_user (self ,email , password=None ,**extra_fields):
        if not email :
            raise ValueError('The Email field must be set')
        
        email=self.normalize_email(email)
        
        user= self.model(email=email , **extra_fields)
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create an admin user (SuperUser)."""
        """
        Create an admin user (SuperUser).
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
    """User Model."""

    """
    Custom User model.
    """
    username = None
    email = models.EmailField(unique=True, max_length=100)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    
    currency = models.CharField(max_length=5, default='EGP' ,blank=True)
    status = models.CharField(max_length=20, default='Onboarding')
    language = models.CharField(max_length=20, default='English')


    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    class Meta:
        ordering = ["email"]