"""
URL routing for the planning application.

Provides shortcut endpoints for setting budget limits and managing
savings goals during the user onboarding or quick-planning phase.
"""
from django.urls import path
from .views import BudgetLimitView, SavingsGoalView

urlpatterns = [
    path('budget-limit/', BudgetLimitView.as_view(), name='budget-limit'),
    path('savings-goal/', SavingsGoalView.as_view(), name='savings-goal'),
]