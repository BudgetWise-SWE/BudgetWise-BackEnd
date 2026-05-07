"""
Views for handling user notifications and read status.

Provides endpoints to list notifications, mark them as read individually,
or mark all as read simultaneously.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    
    Supports listing, creation (systemic), and state changes (marking as read).
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return notifications filtered by the currently authenticated user.
        
        Returns:
            QuerySet: Authenticated user's notifications.
        """
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically link the authenticated user to newly created notifications.
        
        Args:
            serializer (NotificationSerializer): The validated notification serializer.
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Mark All Notifications as Read",
        description="Updates all notifications for the authenticated user to 'is_read=True'.",
        request=None, 
        responses={200: None}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark every notification for the user as read.
        
        Returns:
            Response: Success confirmation message.
        """
        self.get_queryset().update(is_read=True)
        return Response({'message': 'All notifications marked as read'})

    @extend_schema(
        summary="Mark Notification as Read",
        description="Sets 'is_read=True' for a specific notification identified by ID.",
        request=None, 
        responses={200: None}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark a single notification as read by its primary key.
        
        Args:
            pk (int): Primary key of the notification.
            
        Returns:
            Response: Success confirmation message.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
