from django.contrib import admin
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal

admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(BudgetCategoryLimit)
admin.site.register(SavingsGoal)
