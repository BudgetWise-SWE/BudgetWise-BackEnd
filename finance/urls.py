from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import *

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