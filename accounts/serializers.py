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
    """
    fullname = serializers.CharField(write_only=True, required=False)
    full_name = serializers.SerializerMethodField()
    total_balance = serializers.SerializerMethodField()

    class Meta:
        """Metadata for the UserSerializer."""
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'fullname', 'full_name', 'currency', 'language', 'password', 'total_balance']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_full_name(self, obj):
        """
        Return the user's full name.
        """
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_total_balance(self, obj):
        """
        Calculate the user's current total balance across all transactions.
        """
        from finance.models import Transaction
        from django.db.models import Sum
        
        income = Transaction.objects.filter(user=obj, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense = Transaction.objects.filter(user=obj, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        return income - expense

    def create(self, validated_data):
        """
        Create a new user using the custom manager.
        """
        fullname = validated_data.pop('fullname', None)
        if fullname:
            names = fullname.split(' ', 1)
            validated_data['first_name'] = names[0]
            validated_data['last_name'] = names[1] if len(names) > 1 else ''

        # [FRONTEND ALIGNMENT] Decode Base64 password if sent by frontend
        password = validated_data.get('password')
        if password:
            try:
                import base64
                decoded_password = base64.b64decode(password).decode('utf-8')
                validated_data['password'] = decoded_password
            except Exception:
                # Fallback to original if decoding fails (e.g., already plain text)
                pass

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