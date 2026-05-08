"""
Models for the finance application.

Defines core financial entities such as Categories, Transactions,
Budgets, and Savings Goals. Includes logic for tracking spending
relative to budget limits.
"""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Category(models.Model):
    """
    Classifies transactions into broad types (e.g., Food, Salary, Rent).
    
    Categories are flat-structured for simplicity and speed. They can be 
    system-wide (predefined) or custom-created by individual users.
    """

    TYPE_EXPENSE = 'expense'
    TYPE_INCOME = 'income'
    TYPE_CHOICES = [
        (TYPE_EXPENSE, 'Expense'),
        (TYPE_INCOME, 'Income'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories',
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_predefined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadata for the Category model."""
        ordering = ['type', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'type'],
                name='unique_user_category',
            )
        ]

    def __str__(self):
        """Return the category name."""
        return self.name


class Transaction(models.Model):
    """
    Records an individual financial movement (income or expense).
    
    The system is optimized for rapid entry, requiring only core data 
    while intelligently handling optional metadata and category resolution.
    """

    TYPE_EXPENSE = 'expense'
    TYPE_INCOME = 'income'
    TYPE_CHOICES = [
        (TYPE_EXPENSE, 'Expense'),
        (TYPE_INCOME, 'Income'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=100, blank=True , null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadata for the Transaction model."""
        ordering = ['-date', '-created_at']

    def __str__(self):
        """Return a formatted summary of the transaction."""
        return f'{self.type} {self.amount}'


class Budget(models.Model):
    """
    Defines a user's total spending allowance for a specific month.
    
    Attributes:
        user (ForeignKey): The budget owner.
        name (CharField): Descriptive name (e.g., 'May 2026 Budget').
        month (int): 1-12.
        year (int): YYYY.
        total_limit (Decimal): The maximum total spending allowed.
        status (str): Current standing (Active, Exceeded, Completed).
    """

    STATUS_ACTIVE = 'active'
    STATUS_EXCEEDED = 'exceeded'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXCEEDED, 'Exceeded'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    name = models.CharField(max_length=100)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    total_limit = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadata for the Budget model."""
        ordering = ['-year', '-month']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'month', 'year'],
                name='unique_user_budget_period',
            )
        ]

    def __str__(self):
        """Return the budget name and period."""
        return f'{self.name} {self.month}/{self.year}'

    @property
    def spent(self):
        """
        Calculate total expenses for this budget's month and year.
        
        Returns:
            Decimal: Sum of all expenses in the matching period.
        """
        total = self.user.transactions.filter(
            type=Transaction.TYPE_EXPENSE,
            date__year=self.year,
            date__month=self.month,
        ).aggregate(total=Sum('amount'))['total']
        return total or 0

    def update_status(self):
        """
        Evaluate and update the budget status based on current spending.
        
        Compares total spent against total_limit and persists the status field.
        """
        spent = self.spent
        if spent > self.total_limit:
            self.status = self.STATUS_EXCEEDED
        elif spent == self.total_limit:
            self.status = self.STATUS_COMPLETED
        else:
            self.status = self.STATUS_ACTIVE
        self.save(update_fields=['status'])


class BudgetCategoryLimit(models.Model):
    """
    Sets a specific spending cap for a single category within a larger budget.
    
    Attributes:
        budget (ForeignKey): Parent budget.
        category (ForeignKey): The category to limit.
        limit (Decimal): The capped amount for this category.
        spent (Decimal): Running total of expenses in this category.
        status (str): Standing (Active, Close, Exceeded).
    """

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
        """Metadata for the BudgetCategoryLimit model."""
        ordering = ['category__name']
        constraints = [
            models.UniqueConstraint(
                fields=['budget', 'category'],
                name='unique_budget_category_limit',
            )
        ]

    @property
    def remaining(self):
        """
        Calculate available funds remaining for this category.
        
        Returns:
            Decimal: Difference between limit and spent.
        """
        return max(self.limit - self.spent, 0)

    def update_status(self):
        """
        Evaluate status based on consumption percentage.
        
        'Close' status is triggered at 90% consumption.
        """
        if self.spent > self.limit:
            self.status = self.STATUS_EXCEEDED
        elif self.spent >= self.limit * Decimal('0.9'):
            self.status = self.STATUS_CLOSE
        else:
            self.status = self.STATUS_ACTIVE
        self.save(update_fields=['status'])

    def add_spent(self, amount):
        """
        Increase the spent tally and refresh the status.
        
        Args:
            amount (Decimal): Value to add.
        """
        self.spent += amount
        self.save(update_fields=['spent'])
        self.update_status()


class SavingsGoal(models.Model):
    """
    Defines a long-term savings target.
    
    Attributes:
        user (ForeignKey): Goal owner.
        name (CharField): Name of the goal (e.g., 'New Car').
        target_amount (Decimal): Total money required.
        current_amount (Decimal): Money saved so far.
        deadline (DateField): Target date for completion.
        completed (BooleanField): Completion status.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='savings_goals',
    )
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadata for the SavingsGoal model."""
        ordering = ['-created_at']

    @property
    def progress(self):
        """
        Calculate the percentage towards the goal.
        
        Returns:
            int: Progress percentage (0-100).
        """
        if self.target_amount <= 0:
            return 0
        return min(100, int((self.current_amount / self.target_amount) * 100))

    def add_contribution(self, amount):
        """
        Log a contribution and check for goal completion.
        
        Args:
            amount (Decimal): Contribution value.
        """
        self.current_amount += amount
        if self.current_amount >= self.target_amount:
            self.completed = True
        self.save(update_fields=['current_amount', 'completed'])
