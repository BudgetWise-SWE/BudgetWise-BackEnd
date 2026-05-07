"""
Admin configuration for the finance application.

Registers core financial models (Category, Transaction, Budget, etc.)
with the Django Admin site for easy data management and inspection.
"""
from django.contrib import admin
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for the Category model."""
    list_display = ('name', 'type', 'user', 'is_predefined')
    list_filter = ('type', 'is_predefined')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for the Transaction model."""
    list_display = ('id', 'user', 'type', 'amount', 'date', 'category')
    list_filter = ('type', 'date', 'category')
    search_fields = ('description', 'notes', 'user__email')

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Admin configuration for the Budget model."""
    list_display = ('name', 'user', 'month', 'year', 'total_limit', 'status')
    list_filter = ('status', 'year', 'month')

@admin.register(BudgetCategoryLimit)
class BudgetCategoryLimitAdmin(admin.ModelAdmin):
    """Admin configuration for the BudgetCategoryLimit model."""
    list_display = ('budget', 'category', 'limit', 'spent', 'status')
    list_filter = ('status',)

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    """Admin configuration for the SavingsGoal model."""
    list_display = ('name', 'user', 'target_amount', 'current_amount', 'completed', 'progress')
    list_filter = ('completed',)
