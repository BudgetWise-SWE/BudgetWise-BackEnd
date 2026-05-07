"""
Serializers for the notifications application.

Handles the conversion of notification instances into JSON data.
"""
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Notification model.
    
    Exposes core fields including read status and creation timestamp.
    """
    
    class Meta:
        """Metadata for NotificationSerializer."""
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']