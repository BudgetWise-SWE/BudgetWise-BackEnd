"""
Models for the notifications application.

Defines the structure for systemic and event-driven notifications
sent to users (e.g., budget alerts, goal achievements).
"""
from django.db import models
from django.conf import settings

class Notification(models.Model):
    """
    Represents a single message or alert sent to a user.
    
    Attributes:
        user (ForeignKey): The recipient of the notification.
        type (CharField): Classification (Budget Alert, System, etc.).
        title (CharField): Short descriptive heading.
        message (TextField): The full body content.
        is_read (BooleanField): Tracks if the user has seen the alert.
        created_at (DateTimeField): When the alert was generated.
    """
    
    TYPE_BUDGET_ALERT = 'budget_alert'
    TYPE_SAVINGS_REMINDER = 'savings_reminder'
    TYPE_TRANSACTION_ALERT = 'transaction_alert'
    TYPE_GOAL_ACHIEVEMENT = 'goal_achievement'
    TYPE_SYSTEM = 'system'

    TYPE_CHOICES = [
        (TYPE_BUDGET_ALERT, 'Budget Alert'),
        (TYPE_SAVINGS_REMINDER, 'Savings Reminder'),
        (TYPE_TRANSACTION_ALERT, 'Transaction Alert'),
        (TYPE_GOAL_ACHIEVEMENT, 'Goal Achievement'),
        (TYPE_SYSTEM, 'System'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadata for the Notification model."""
        ordering = ['-created_at']

    def __str__(self):
        """Return a string summary of the notification."""
        return f'{self.type} - {self.title}'
