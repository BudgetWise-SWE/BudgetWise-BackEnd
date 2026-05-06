"""
Views for handling user notifications and read status.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for listing, creating, and managing user notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the notifications belonging to the authenticated user."""
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Attach the authenticated user to the new notification."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark every notification for the authenticated user as read."""
        self.get_queryset().update(is_read=True)
        return Response({'message': 'All notifications marked as read'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read by its ID."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
