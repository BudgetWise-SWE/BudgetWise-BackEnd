"""
URL routing for the finance application.

Registers viewsets for all financial entities including categories, transactions,
budgets, and savings goals. Also includes the aggregated reports endpoint.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    TransactionViewSet,
    BudgetViewSet,
    BudgetCategoryLimitViewSet,
    SavingsGoalViewSet,
    ReportViewSet,
)

# Initialize the router and register finance viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'budget-category-limits', BudgetCategoryLimitViewSet, basename='budget-category-limit')
router.register(r'savings-goals', SavingsGoalViewSet, basename='savings-goal')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]