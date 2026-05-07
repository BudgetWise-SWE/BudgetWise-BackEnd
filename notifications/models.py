from django.db import models
from django.conf import settings

class Notification(models.Model):
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
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.type} - {self.title}'
