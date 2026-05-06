from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

class Category(models.Model):
   TYPE_EXPENSE = 'expense'
   TYPE_INCOME = 'income'
   TYPE_CHOICES = [
      (TYPE_EXPENSE, 'Expense'),
      (TYPE_INCOME, 'Income'),
   ]

   user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='categories')
   name = models.CharField(max_length=100)
   type = models.CharField(max_length=20, choices=TYPE_CHOICES)
   is_predefined = models.BooleanField(default=False)
   parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
   created_at = models.DateTimeField(auto_now_add=True)

   class Meta:
      ordering = ['type', 'name']
      constraints = [
            models.UniqueConstraint(fields=['user', 'name', 'type'], name='unique_user_category')
      ]

   def __str__(self):
      return self.name

class Transaction(models.Model):
   TYPE_EXPENSE = 'expense'
   TYPE_INCOME = 'income'
   TYPE_CHOICES = [
      (TYPE_EXPENSE, 'Expense'),
      (TYPE_INCOME, 'Income'),
   ]

   user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
   type = models.CharField(max_length=20, choices=TYPE_CHOICES)
   category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
   amount = models.DecimalField(max_digits=14, decimal_places=2)
   date = models.DateField(default=timezone.now)
   description = models.CharField(max_length=255, blank=True)
   notes = models.TextField(blank=True)
   source = models.CharField(max_length=100, blank=True)
   created_at = models.DateTimeField(auto_now_add=True)

   class Meta:
      ordering = ['-date', '-created_at']

   def __str__(self):
      return f'{self.type} {self.amount}'

class Budget(models.Model):
   STATUS_ACTIVE = 'active'
   STATUS_EXCEEDED = 'exceeded'
   STATUS_COMPLETED = 'completed'
   STATUS_CHOICES = [
      (STATUS_ACTIVE, 'Active'),
      (STATUS_EXCEEDED, 'Exceeded'),
      (STATUS_COMPLETED, 'Completed'),
   ]

   user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
   name = models.CharField(max_length=100)
   month = models.PositiveSmallIntegerField()
   year = models.PositiveIntegerField()
   total_limit = models.DecimalField(max_digits=14, decimal_places=2)
   status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      ordering = ['-year', '-month']
      constraints = [
            models.UniqueConstraint(fields=['user', 'month', 'year'], name='unique_user_budget_period')
      ]

   def __str__(self):
      return f'{self.name} {self.month}/{self.year}'

   @property
   def spent(self):
      total = self.user.transactions.filter(
            type=Transaction.TYPE_EXPENSE,
            date__year=self.year,
            date__month=self.month,
      ).aggregate(total=Sum('amount'))['total']
      return total or 0

   def update_status(self):
      spent = self.spent
      if spent > self.total_limit:
            self.status = self.STATUS_EXCEEDED
      elif spent == self.total_limit:
            self.status = self.STATUS_COMPLETED
      else:
            self.status = self.STATUS_ACTIVE
      self.save(update_fields=['status'])

class BudgetCategoryLimit(models.Model):
   STATUS_ACTIVE = 'active'
   STATUS_CLOSE = 'close'
   STATUS_EXCEEDED = 'exceeded'
   STATUS_CHOICES = [
      (STATUS_ACTIVE, 'Active'),
      (STATUS_CLOSE, 'Close'),
      (STATUS_EXCEEDED, 'Exceeded'),
   ]

   budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='category_limits')
   category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budget_limits')
   limit = models.DecimalField(max_digits=14, decimal_places=2)
   spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
   status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

   class Meta:
      ordering = ['category__name']
      constraints = [
            models.UniqueConstraint(fields=['budget', 'category'], name='unique_budget_category_limit')
      ]

   @property
   def remaining(self):
      return max(self.limit - self.spent, 0)

   def update_status(self):
      if self.spent > self.limit:
         self.status = self.STATUS_EXCEEDED
      elif self.spent >= self.limit * Decimal('0.9'):
         self.status = self.STATUS_CLOSE
      else:
         self.status = self.STATUS_ACTIVE
      self.save(update_fields=['status'])

   def add_spent(self, amount):
      self.spent += amount
      self.save(update_fields=['spent'])
      self.update_status()

class SavingsGoal(models.Model):
   user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_goals')
   name = models.CharField(max_length=100)
   target_amount = models.DecimalField(max_digits=14, decimal_places=2)
   current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
   deadline = models.DateField(null=True, blank=True)
   completed = models.BooleanField(default=False)
   created_at = models.DateTimeField(auto_now_add=True)

   class Meta:
      ordering = ['-created_at']

   @property
   def progress(self):
      if self.target_amount <= 0:
         return 0
      return min(100, int((self.current_amount / self.target_amount) * 100))

   def add_contribution(self, amount):
      self.current_amount += amount
      if self.current_amount >= self.target_amount:
         self.completed = True
      self.save(update_fields=['current_amount', 'completed'])

      self.save(update_fields=['current_amount', 'completed'])
