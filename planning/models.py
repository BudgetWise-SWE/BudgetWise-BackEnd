from django.db import models
from django.conf import settings
# You'll need to import ExpenseCategory from the finance app
# to link your budget limits to specific spending types[cite: 1].
# from finance.models import ExpenseCategory
import uuid

class Budget(models.Model):
    """
    Defines the monthly spending plan and tracks overall status[cite: 1].
    """
    budget_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    total_budget_limit = models.DecimalField(max_digits=10, decimal_places=2)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    STATUS_CHOICES = [('active', 'Active'), ('exceeded', 'Exceeded'), ('completed', 'Completed')]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    class Meta:
        # Ensures a user only has one "Parent Budget" record per month/year[cite: 1]
        unique_together = ('user', 'month', 'year')

class BudgetCategoryLimit(models.Model):
    """
    Sets specific spending caps for categories like 'Food' or 'Rent'[cite: 1].
    """
    limit_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    budget = models.ForeignKey(Budget, related_name='category_limits', on_delete=models.CASCADE)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    spending_limit = models.DecimalField(max_digits=10, decimal_places=2)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        # Exceptional Scenario: Prevents duplicate budgets for the same category in one month
        unique_together = ('budget', 'category')

class SavingsGoal(models.Model):
    """
    Tracks progress toward specific long-term financial targets[cite: 1].
    """
    goal_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deadline = models.DateField()
    status = models.CharField(max_length=15, default='active')