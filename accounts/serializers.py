from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and profile retrieval."""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'currency', 'language', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """Create a new user using the custom manager (hashes password correctly)."""
        return User.objects.create_user(**validated_data)

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for partial profile updates (name, currency, language)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'currency', 'language']