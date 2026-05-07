"""
Serializers for the accounts application.

Handles data validation and transformation for user registration,
profile retrieval, and partial updates.
"""
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration and profile retrieval.
    
    Includes basic profile information and ensures the password is write-only.
    """

    class Meta:
        """Metadata for the UserSerializer."""
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'currency', 'language', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """
        Create a new user using the custom manager.
        
        This method ensures that the password is hashed correctly by calling
        User.objects.create_user instead of the default ModelSerializer.create.
        
        Args:
            validated_data (dict): The data validated by the serializer.
            
        Returns:
            User: The newly created user instance.
        """
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for partial profile updates.
    
    Allows users to update specific fields like names, currency, and language
    without touching core authentication data like email or password.
    """

    class Meta:
        """Metadata for the UserUpdateSerializer."""
        model = User
        fields = ['first_name', 'last_name', 'currency', 'language']